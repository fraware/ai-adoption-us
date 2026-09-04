#!/usr/bin/env python3
"""Re-fetch and exactly rehydrate a reviewed Observatory v1 candidate.

The review package is rights-safe and contains no private RPS source bytes. This
command runs only on the exact reviewed repository commit, re-fetches the
rights-cleared aggregate RPS source, requires the reviewed scientific source
identity, rebuilds the private RPS and global candidates, re-stages the global
candidate, and proves that every reviewed candidate/stage identity is unchanged.

Private source bytes remain inside ``output_root``. The only artifact intended to
leave that private workspace is ``rehydration_identity.json``, which contains
hashes and release identities but no source observations or local input paths.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from genai_at_work.claim_surfaces import (
    ClaimSurfaceBindingError,
    bind_claim_surfaces,
    claim_ids_from_inventory,
    validate_claim_surface_bindings,
)
from genai_at_work.observatory_baseline import ObservatoryBaselineError
from genai_at_work.observatory_rps_bindings import (
    BINDINGS_REPOSITORY_PATH,
    ObservatoryRpsBindingError,
    compose_v1_global_baseline_bound,
)
from genai_at_work.release_engine import (
    canonical_digest,
    load_json_object,
    sanitized_public_manifest,
    sha256_file,
    validate_release_manifest,
)
from genai_at_work.rps_refresh import RpsRefreshError, build_refresh_snapshot
from genai_at_work.rps_release import RpsReleaseError
from genai_at_work.rps_release_public import build_rps_observatory_release_candidate
from genai_at_work.sources.fred import FredClient, FredError

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ROOT = ROOT / "data" / "audit" / "private"
REGISTRY_DIR = ROOT / "data" / "registry"
DEFAULT_RELEASE_REGISTRY = REGISTRY_DIR / "observatory_release_registry.json"
DEFAULT_RELEASES_ROOT = ROOT / "data" / "releases"
MANIFEST_PATH = REGISTRY_DIR / "rps_source_series_manifest.json"
SCOPE_PATH = REGISTRY_DIR / "rps_provider_catalog_scope.json"
CLAIMS_PATH = REGISTRY_DIR / "longitudinal_claim_inventory.json"
PUBLIC_VIEW_CONTRACT_PATH = REGISTRY_DIR / "rps_public_observation_delivery_v1.json"
BASELINE_CONTRACT_PATH = REGISTRY_DIR / "observatory_v1_baseline_contract.json"
BINDINGS_PATH = ROOT / BINDINGS_REPOSITORY_PATH
RPS_SOURCE_ID = "rps-genai-tracker-fred-release-6"


class RehydrationError(RuntimeError):
    """Raised when a reviewed candidate cannot be reproduced exactly."""


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _assert_private_output_boundary(output_root: Path) -> None:
    resolved = output_root.resolve()
    root = ROOT.resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return
    try:
        resolved.relative_to(PRIVATE_ROOT.resolve())
    except ValueError as exc:
        raise RehydrationError(
            "Repository-local rehydration workspaces may only live under data/audit/private/."
        ) from exc


def _clean_head() -> str:
    try:
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except subprocess.CalledProcessError as exc:
        raise RehydrationError("Could not resolve a clean repository HEAD") from exc
    if status.strip():
        raise RehydrationError("Refusing exact rehydration from a dirty repository checkout")
    if len(head) not in {40, 64}:
        raise RehydrationError(f"Unexpected Git HEAD identity: {head!r}")
    return head.lower()


def _parse_timestamp(value: object) -> datetime:
    if not isinstance(value, str) or not value:
        raise RehydrationError("Reviewed candidate created_at must be a non-empty timestamp")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise RehydrationError(f"Invalid reviewed candidate created_at: {value!r}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise RehydrationError("Reviewed candidate created_at must be timezone-aware")
    return parsed.astimezone(UTC)


def _reviewed_source(manifest: dict[str, Any]) -> dict[str, Any]:
    sources = manifest.get("sources")
    if not isinstance(sources, list):
        raise RehydrationError("Reviewed candidate has no source list")
    matches = [
        row
        for row in sources
        if isinstance(row, dict) and row.get("source_id") == RPS_SOURCE_ID
    ]
    if len(matches) != 1:
        raise RehydrationError(
            f"Reviewed candidate must contain exactly one source {RPS_SOURCE_ID!r}"
        )
    return matches[0]


def _load_previous_release(
    registry_path: Path,
    releases_root: Path,
    reviewed_stage: dict[str, Any],
) -> dict[str, Any] | None:
    registry = load_json_object(registry_path)
    expected_id = reviewed_stage.get("registry_current_release_id")
    expected_sha = reviewed_stage.get("registry_current_manifest_sha256")
    if registry.get("current_release_id") != expected_id:
        raise RehydrationError(
            "Release registry advanced after review; a new candidate review is required"
        )
    if registry.get("current_release_manifest_sha256") != expected_sha:
        raise RehydrationError(
            "Release registry manifest identity changed after review; a new review is required"
        )
    if expected_id is None:
        return None
    if not isinstance(expected_id, str) or not expected_id:
        raise RehydrationError("Reviewed stage has an invalid current release ID")
    previous_path = releases_root / expected_id / "release_manifest.json"
    if not previous_path.is_file():
        raise RehydrationError(f"Reviewed previous release manifest is missing: {previous_path}")
    if not isinstance(expected_sha, str) or sha256_file(previous_path) != expected_sha:
        raise RehydrationError("Reviewed previous release manifest checksum mismatch")
    previous = load_json_object(previous_path)
    if previous.get("release_id") != expected_id:
        raise RehydrationError("Reviewed previous release manifest has the wrong release ID")
    return previous


def _review_file(review_root: Path, relative: str) -> Path:
    path = review_root / relative
    if not path.is_file():
        raise RehydrationError(f"Review package is missing {relative}")
    return path


def _assert_exact_json(observed: Path, reviewed: Path, label: str) -> None:
    if load_json_object(observed) != load_json_object(reviewed):
        raise RehydrationError(f"Rehydrated {label} differs from the reviewed {label}")


def _source_vintage_map(candidate: dict[str, Any]) -> dict[str, str]:
    sources = candidate.get("sources")
    if not isinstance(sources, list):
        raise RehydrationError("Rehydrated candidate has no source list")
    result: dict[str, str] = {}
    for row in sources:
        if not isinstance(row, dict):
            raise RehydrationError("Rehydrated candidate contains an invalid source row")
        source_id = row.get("source_id")
        vintage = row.get("source_vintage_id")
        if not isinstance(source_id, str) or not isinstance(vintage, str):
            raise RehydrationError("Rehydrated candidate source identity is incomplete")
        result[source_id] = vintage
    return result


def _artifact_hashes(candidate: dict[str, Any]) -> dict[str, str]:
    artifacts = candidate.get("artifacts")
    if not isinstance(artifacts, list):
        raise RehydrationError("Rehydrated candidate has no artifact list")
    result: dict[str, str] = {}
    for row in artifacts:
        if not isinstance(row, dict):
            raise RehydrationError("Rehydrated candidate contains an invalid artifact row")
        artifact_id = row.get("artifact_id")
        digest = row.get("sha256")
        if not isinstance(artifact_id, str) or not isinstance(digest, str):
            raise RehydrationError("Rehydrated artifact identity is incomplete")
        result[artifact_id] = digest
    return result


def rehydrate(args: argparse.Namespace) -> dict[str, Any]:
    review_root = args.review_package_dir.resolve()
    reviewed_manifest_path = _review_file(review_root, "sanitized-candidate-manifest.json")
    reviewed_stage_path = _review_file(review_root, "stage/stage_manifest.json")
    reviewed_diff_path = _review_file(review_root, "stage/release_diff.json")
    reviewed_review_path = _review_file(review_root, "stage/review_package.json")
    reviewed_gate_path = _review_file(review_root, "stage/publication_gate.json")

    reviewed_manifest = load_json_object(reviewed_manifest_path)
    reviewed_stage = load_json_object(reviewed_stage_path)
    reviewed_source = _reviewed_source(reviewed_manifest)
    reviewed_commit = reviewed_manifest.get("build", {}).get("builder_commit")
    head = _clean_head()
    if not isinstance(reviewed_commit, str) or reviewed_commit.lower() != head:
        raise RehydrationError(
            "Trusted rehydration must run on the exact reviewed candidate commit"
        )
    if reviewed_stage.get("candidate_release_id") != reviewed_manifest.get("release_id"):
        raise RehydrationError("Reviewed manifest and stage disagree on release_id")
    if reviewed_stage.get("candidate_manifest_digest") != canonical_digest(reviewed_manifest):
        # The reviewed file is sanitized, so its digest is intentionally distinct from the
        # private candidate digest. This check guards accidental misuse of the field.
        if reviewed_stage.get("candidate_manifest_digest") == canonical_digest(
            sanitized_public_manifest(reviewed_manifest)
        ):
            raise RehydrationError("Reviewed stage unexpectedly identifies a sanitized manifest")

    output_root = args.output_root.resolve()
    _assert_private_output_boundary(output_root)
    if output_root.exists():
        raise RehydrationError(f"Rehydration output root must be absent: {output_root}")
    output_root.mkdir(parents=True)

    previous = _load_previous_release(args.registry, args.releases_root, reviewed_stage)
    api_key = os.environ.get("FRED_API_KEY", "").strip()
    if not api_key:
        raise RehydrationError("FRED_API_KEY is required for trusted source rehydration")

    timestamp = _parse_timestamp(reviewed_manifest.get("created_at"))
    snapshot = build_refresh_snapshot(
        FredClient(api_key=api_key),
        load_json_object(MANIFEST_PATH),
        load_json_object(SCOPE_PATH),
        retrieved_at=timestamp,
    )
    reviewed_vintage = reviewed_source.get("source_vintage_id")
    observed_vintage = f"sha256:{snapshot['content_sha256']}"
    if reviewed_vintage != observed_vintage:
        raise RehydrationError(
            "Live RPS scientific source identity changed after review; a new candidate review is required"
        )

    snapshot_path = output_root / "source" / "rps_source_snapshot.json"
    _write_json(snapshot_path, snapshot)

    claims = load_json_object(CLAIMS_PATH)
    governed_claim_ids = claim_ids_from_inventory(claims)
    rps_root = output_root / "rps-candidate"
    rps_candidate = build_rps_observatory_release_candidate(
        snapshot,
        load_json_object(MANIFEST_PATH),
        load_json_object(SCOPE_PATH),
        claims,
        load_json_object(PUBLIC_VIEW_CONTRACT_PATH),
        output_dir=rps_root,
        release_id=f"rps-rehydrate-{str(reviewed_stage['stage_id'])[:24]}",
        builder_commit=head,
        previous_release=previous,
    )
    bind_claim_surfaces(rps_candidate, ROOT, expected_claim_ids=governed_claim_ids)
    validate_claim_surface_bindings(
        rps_candidate, ROOT, expected_claim_ids=governed_claim_ids
    )
    _write_json(rps_root / "release.json", rps_candidate)
    validate_release_manifest(rps_candidate, rps_root)

    global_root = output_root / "candidate"
    candidate = compose_v1_global_baseline_bound(
        rps_candidate_root=rps_root,
        output_dir=global_root,
        contract=load_json_object(BASELINE_CONTRACT_PATH),
        bindings=load_json_object(BINDINGS_PATH),
        repo_root=ROOT,
        release_id=str(reviewed_manifest["release_id"]),
        builder_commit=head,
        previous_release=previous,
    )
    validate_claim_surface_bindings(candidate, ROOT, expected_claim_ids=governed_claim_ids)
    validate_release_manifest(candidate, global_root)

    private_manifest_path = global_root / "release.json"
    if sha256_file(private_manifest_path) != reviewed_stage.get("candidate_manifest_sha256"):
        raise RehydrationError("Rehydrated private candidate manifest bytes differ from review")
    if canonical_digest(candidate) != reviewed_stage.get("candidate_manifest_digest"):
        raise RehydrationError("Rehydrated private candidate manifest digest differs from review")
    if sanitized_public_manifest(candidate) != reviewed_manifest:
        raise RehydrationError("Rehydrated sanitized candidate manifest differs from review")

    stage_root = output_root / "stage"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "observatory_release.py"),
            "stage",
            "--candidate-manifest",
            str(private_manifest_path),
            "--candidate-root",
            str(global_root),
            "--registry",
            str(args.registry),
            "--releases-root",
            str(args.releases_root),
            "--staging-dir",
            str(stage_root),
        ],
        cwd=ROOT,
        check=True,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )

    _assert_exact_json(stage_root / "stage_manifest.json", reviewed_stage_path, "stage manifest")
    _assert_exact_json(stage_root / "release_diff.json", reviewed_diff_path, "release diff")
    _assert_exact_json(stage_root / "review_package.json", reviewed_review_path, "review package")
    _assert_exact_json(stage_root / "publication_gate.json", reviewed_gate_path, "publication gate")

    identity = {
        "schema_version": 1,
        "status": "REHYDRATED_EXACT_CANDIDATE",
        "release_id": candidate["release_id"],
        "candidate_commit": head,
        "candidate_manifest_sha256": sha256_file(private_manifest_path),
        "candidate_manifest_digest": canonical_digest(candidate),
        "stage_id": load_json_object(stage_root / "stage_manifest.json")["stage_id"],
        "source_vintage_ids": _source_vintage_map(candidate),
        "artifact_sha256": _artifact_hashes(candidate),
        "source_input_bytes_included": False,
    }
    _write_json(output_root / "rehydration_identity.json", identity)
    return identity


def parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-package-dir", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument(
        "--registry", type=Path, default=DEFAULT_RELEASE_REGISTRY
    )
    parser.add_argument(
        "--releases-root", type=Path, default=DEFAULT_RELEASES_ROOT
    )
    return parser


def main() -> int:
    args = parser().parse_args()
    try:
        identity = rehydrate(args)
    except (
        ClaimSurfaceBindingError,
        FredError,
        ObservatoryBaselineError,
        ObservatoryRpsBindingError,
        RehydrationError,
        RpsRefreshError,
        RpsReleaseError,
        ValueError,
        subprocess.CalledProcessError,
    ) as exc:
        if args.output_root.exists():
            shutil.rmtree(args.output_root)
        raise SystemExit(f"Observatory rehydration blocked: {exc}") from exc
    print(json.dumps(identity, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
