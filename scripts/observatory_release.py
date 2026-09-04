#!/usr/bin/env python3
"""Stage Observatory candidates and execute the internal reviewed promotion kernel.

The CLI may stage candidates and may exercise promotion against isolated test or
scratch registries. Promotion of the canonical repository registry/release tree
is fail-closed unless invoked by the exact-rehydration wrapper after it has
verified the reviewed candidate, source vintage, artifacts, and rehydration
identity.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from genai_at_work.github_ci import (
    GithubCiVerificationError,
    fetch_and_verify_github_ci,
)
from genai_at_work.release_engine import (
    candidate_gate_failures,
    canonical_digest,
    diff_releases,
    gate_status,
    load_json_object,
    review_package,
    sanitized_public_manifest,
    sha256_file,
    stage_fingerprint,
    validate_release_manifest,
    validate_review_attestation,
)

ROOT = Path(__file__).parents[1]
CI_POLICY = ROOT / "data/registry/observatory_release_ci_policy.json"
CANONICAL_REGISTRY = ROOT / "data/registry/observatory_release_registry.json"
CANONICAL_RELEASES_ROOT = ROOT / "data/releases"
RELEASE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")


def _safe_release_id(value: object, *, context: str) -> str:
    if not isinstance(value, str) or RELEASE_ID_RE.fullmatch(value) is None:
        raise SystemExit(
            f"{context} must be a lowercase ASCII release slug using only a-z, 0-9, '.', '_' or '-'"
        )
    return value


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(temp, path)


def _current_id(registry: dict[str, Any]) -> str | None:
    value = registry.get("current_release_id")
    if value is None:
        return None
    return _safe_release_id(value, context="Release registry current_release_id")


def _load_previous(
    registry: dict[str, Any], releases_root: Path
) -> dict[str, Any] | None:
    current = _current_id(registry)
    if current is None:
        return None
    path = releases_root / current / "release_manifest.json"
    if not path.is_file():
        raise SystemExit(f"Registered current release manifest is missing: {path}")
    expected = registry.get("current_release_manifest_sha256")
    actual = sha256_file(path)
    if not isinstance(expected, str) or actual != expected:
        raise SystemExit("Registered current release manifest checksum mismatch")
    previous = load_json_object(path)
    if previous.get("release_id") != current:
        raise SystemExit("Registered current release ID does not match its manifest")
    return previous


def _validate_supersession(candidate: dict[str, Any], registry: dict[str, Any]) -> None:
    current = _current_id(registry)
    release_id = _safe_release_id(
        candidate.get("release_id"), context="Candidate release_id"
    )
    supersedes = candidate.get("supersedes_release_id")
    if supersedes is not None:
        _safe_release_id(supersedes, context="Candidate supersedes_release_id")
    if current is None and supersedes is not None:
        raise SystemExit("First promoted release must use supersedes_release_id=null")
    if current is not None and supersedes != current:
        raise SystemExit(f"Candidate must explicitly supersede current release {current!r}")
    releases = registry.get("releases")
    if not isinstance(releases, list):
        raise SystemExit("Release registry releases must be a list")
    known = {
        _safe_release_id(row.get("release_id"), context="Registered release_id")
        for row in releases
        if isinstance(row, dict)
    }
    if release_id == current or release_id in known:
        raise SystemExit(f"Release ID is already frozen and cannot be reused: {release_id}")


def _has_changes(diff: dict[str, Any]) -> bool:
    return any(
        bool(diff.get(key))
        for key in (
            "source_changes",
            "artifact_changes",
            "diagnostic_changes",
            "claim_changes",
        )
    )


def _stage_payload(
    registry: dict[str, Any],
    candidate_manifest: Path,
    candidate: dict[str, Any],
    release_diff: dict[str, Any],
    review: dict[str, Any],
    status: str,
) -> dict[str, Any]:
    """Build the portable immutable identity of one staged candidate."""

    payload: dict[str, Any] = {
        "schema_version": 2,
        "registry_current_release_id": _current_id(registry),
        "registry_current_manifest_sha256": registry.get(
            "current_release_manifest_sha256"
        ),
        "candidate_release_id": candidate["release_id"],
        "candidate_data_mode": candidate["data_mode"],
        "candidate_manifest_sha256": sha256_file(candidate_manifest),
        "candidate_manifest_digest": canonical_digest(candidate),
        "release_diff_digest": canonical_digest(release_diff),
        "review_package_digest": canonical_digest(review),
        "gate_status": status,
    }
    payload["stage_id"] = stage_fingerprint(payload)
    return payload


def _gate_payload(
    stage_id: str, status: str, failures: list[dict[str, str]]
) -> dict[str, Any]:
    return {
        "stage_id": stage_id,
        "status": status,
        "failures": failures,
        "promotion_requires_review": status == "BLOCKED_REVIEW_REQUIRED",
        "source_input_bytes_publishable_by_this_engine": False,
    }


def _promotion_timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _verify_ci_evidence(attestation: dict[str, Any]) -> dict[str, Any]:
    """Resolve attested run IDs and prove they passed for the exact candidate commit."""

    policy = load_json_object(CI_POLICY)
    repository = os.environ.get("GITHUB_REPOSITORY", "").strip()
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com").strip()
    raw_run_ids = attestation.get("ci_run_ids")
    if not isinstance(raw_run_ids, list) or not all(
        isinstance(value, int) and not isinstance(value, bool) and value > 0
        for value in raw_run_ids
    ):
        raise SystemExit("Review attestation contains invalid ci_run_ids")
    candidate_commit = attestation.get("candidate_commit")
    if not isinstance(candidate_commit, str):
        raise SystemExit("Review attestation candidate_commit is invalid")
    if not repository:
        raise SystemExit("GITHUB_REPOSITORY is required for promotion CI verification")
    if not token:
        raise SystemExit("GITHUB_TOKEN is required for promotion CI verification")

    try:
        return fetch_and_verify_github_ci(
            repository=repository,
            run_ids=raw_run_ids,
            candidate_commit=candidate_commit,
            token=token,
            policy=policy,
            api_url=api_url,
        )
    except GithubCiVerificationError as exc:
        raise SystemExit(f"Promotion CI verification failed: {exc}") from exc


def stage(args: argparse.Namespace) -> int:
    if args.staging_dir.exists():
        raise SystemExit(
            f"Staging directory already exists; use a new immutable path: {args.staging_dir}"
        )
    registry = load_json_object(args.registry)
    candidate = load_json_object(args.candidate_manifest)
    validate_release_manifest(candidate, args.candidate_root)
    _validate_supersession(candidate, registry)
    previous = _load_previous(registry, args.releases_root)
    release_diff = diff_releases(previous, candidate)
    failures = candidate_gate_failures(candidate, release_diff)
    status = gate_status(failures, _has_changes(release_diff))
    review = review_package(candidate, release_diff)
    stage_manifest = _stage_payload(
        registry,
        args.candidate_manifest,
        candidate,
        release_diff,
        review,
        status,
    )
    gate = _gate_payload(str(stage_manifest["stage_id"]), status, failures)

    args.staging_dir.mkdir(parents=True)
    _write_json(args.staging_dir / "stage_manifest.json", stage_manifest)
    _write_json(args.staging_dir / "release_diff.json", release_diff)
    _write_json(args.staging_dir / "review_package.json", review)
    _write_json(args.staging_dir / "publication_gate.json", gate)
    print(
        json.dumps(
            {"stage_id": stage_manifest["stage_id"], "status": status},
            indent=2,
        )
    )
    return 0


def _copy_artifacts(
    candidate: dict[str, Any], candidate_root: Path, release_dir: Path
) -> dict[str, Any]:
    public = sanitized_public_manifest(candidate)
    candidate_artifacts = candidate.get("artifacts")
    if not isinstance(candidate_artifacts, list):
        raise SystemExit("Invalid artifact manifest during promotion")
    for artifact in candidate_artifacts:
        if not isinstance(artifact, dict):
            raise SystemExit("Invalid artifact entry during promotion")
        relative = Path(str(artifact["path"]))
        source = candidate_root / relative
        destination = release_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        if sha256_file(destination) != str(artifact["sha256"]):
            raise SystemExit(
                f"Copied release artifact checksum mismatch: {artifact['artifact_id']}"
            )
    return public


def _require_rehydrated_canonical_promotion(args: argparse.Namespace) -> None:
    targets_canonical_state = (
        args.registry.resolve() == CANONICAL_REGISTRY.resolve()
        or args.releases_root.resolve() == CANONICAL_RELEASES_ROOT.resolve()
    )
    if targets_canonical_state and getattr(args, "_rehydration_verified", False) is not True:
        raise SystemExit(
            "Direct canonical Observatory promotion is disabled. Use "
            "scripts/promote_rehydrated_observatory_v1.py after exact rehydration."
        )


def promote(args: argparse.Namespace) -> int:
    """Promotion kernel; canonical state requires the exact-rehydration capability."""

    _require_rehydrated_canonical_promotion(args)

    registry = load_json_object(args.registry)
    candidate = load_json_object(args.candidate_manifest)
    validate_release_manifest(candidate, args.candidate_root)
    _validate_supersession(candidate, registry)
    previous = _load_previous(registry, args.releases_root)
    release_diff = diff_releases(previous, candidate)
    failures = candidate_gate_failures(candidate, release_diff)
    status = gate_status(failures, _has_changes(release_diff))
    if status != "BLOCKED_REVIEW_REQUIRED":
        raise SystemExit(
            f"Promotion requires a valid changed release awaiting review; found {status}"
        )

    staged_manifest = load_json_object(args.staging_dir / "stage_manifest.json")
    staged_diff = load_json_object(args.staging_dir / "release_diff.json")
    staged_review = load_json_object(args.staging_dir / "review_package.json")
    staged_gate = load_json_object(args.staging_dir / "publication_gate.json")
    expected_review = review_package(candidate, release_diff)
    recomputed = _stage_payload(
        registry,
        args.candidate_manifest,
        candidate,
        release_diff,
        expected_review,
        status,
    )
    if recomputed != staged_manifest:
        raise SystemExit(
            "Release candidate, registry, or stage fingerprint changed after staging"
        )
    if staged_diff != release_diff:
        raise SystemExit("Release diff changed after staging")
    if staged_review != expected_review:
        raise SystemExit("Review package changed after staging")
    expected_gate = _gate_payload(str(recomputed["stage_id"]), status, failures)
    if staged_gate != expected_gate:
        raise SystemExit("Publication gate changed after staging")

    attestation = load_json_object(args.attestation)
    validate_review_attestation(
        attestation,
        stage_id=str(staged_manifest["stage_id"]),
        candidate_manifest_sha256=sha256_file(args.candidate_manifest),
        candidate=candidate,
        release_diff=release_diff,
    )
    ci_evidence = _verify_ci_evidence(attestation)

    release_id = _safe_release_id(
        candidate["release_id"], context="Candidate release_id"
    )
    target = args.releases_root / release_id
    temporary = args.releases_root / f".{release_id}.tmp"
    if target.exists():
        raise SystemExit(f"Immutable release directory already exists: {target}")
    if temporary.exists():
        raise SystemExit(f"Temporary release directory already exists: {temporary}")
    promotion_time = _promotion_timestamp()
    temporary.mkdir(parents=True)
    try:
        public_manifest = _copy_artifacts(
            candidate, args.candidate_root, temporary
        )
        public_manifest["release_status"] = "PROMOTED_AFTER_EXPLICIT_REVIEW"
        public_manifest["reviewed_at"] = attestation["reviewed_at"]
        public_manifest["promoted_at"] = promotion_time
        public_manifest["reviewer"] = attestation["reviewer"]
        _write_json(temporary / "release_manifest.json", public_manifest)
        _write_json(temporary / "release_diff.json", release_diff)
        _write_json(
            temporary / "review_record.json",
            {
                "stage_id": staged_manifest["stage_id"],
                "release_id": release_id,
                "data_mode": candidate["data_mode"],
                "candidate_manifest_sha256": staged_manifest[
                    "candidate_manifest_sha256"
                ],
                "candidate_manifest_digest": staged_manifest[
                    "candidate_manifest_digest"
                ],
                "release_diff_digest": staged_manifest["release_diff_digest"],
                "review_package_digest": staged_manifest[
                    "review_package_digest"
                ],
                "reviewer": attestation["reviewer"],
                "reviewed_at": attestation["reviewed_at"],
                "promoted_at": promotion_time,
                "scientific_reviewed": True,
                "editorial_reviewed": True,
                "source_rights_reviewed": True,
                "ci_passed_attested": True,
                "ci_evidence_verified_by_release_engine": True,
                "ci_evidence_policy_id": ci_evidence["policy_id"],
                "ci_evidence_digest": ci_evidence["evidence_digest"],
                "ci_verified_runs": ci_evidence["runs"],
                "candidate_commit": attestation["candidate_commit"],
                "ci_run_ids": attestation["ci_run_ids"],
                "artifact_sha256": attestation["artifact_sha256"],
                "reviewed_source_ids": attestation["reviewed_source_ids"],
                "reviewed_artifact_ids": attestation[
                    "reviewed_artifact_ids"
                ],
                "reviewed_diagnostic_ids": attestation[
                    "reviewed_diagnostic_ids"
                ],
                "reviewed_claim_ids": attestation["reviewed_claim_ids"],
                "source_input_bytes_included": False,
            },
        )
        os.replace(temporary, target)
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise

    manifest_path = target / "release_manifest.json"
    manifest_sha = sha256_file(manifest_path)
    releases = registry.get("releases")
    if not isinstance(releases, list):
        shutil.rmtree(target)
        raise SystemExit("Release registry releases must be a list")
    updated = dict(registry)
    updated["current_release_id"] = release_id
    updated["current_release_manifest_sha256"] = manifest_sha
    updated["status"] = "CURRENT_RELEASE_PROMOTED"
    updated["releases"] = [
        *releases,
        {
            "release_id": release_id,
            "manifest_sha256": manifest_sha,
            "promoted_at": promotion_time,
            "supersedes_release_id": candidate.get("supersedes_release_id"),
            "data_mode": candidate["data_mode"],
            "candidate_commit": attestation["candidate_commit"],
            "ci_run_ids": attestation["ci_run_ids"],
            "ci_evidence_policy_id": ci_evidence["policy_id"],
            "ci_evidence_digest": ci_evidence["evidence_digest"],
        },
    ]
    try:
        _write_json(args.registry, updated)
    except Exception:
        shutil.rmtree(target)
        raise
    print(
        json.dumps(
            {
                "release_id": release_id,
                "release_manifest_sha256": manifest_sha,
                "release_directory": str(target),
                "promoted_at": promotion_time,
                "ci_evidence_verified_by_release_engine": True,
                "source_input_bytes_included": False,
                "status": "PROMOTED_AFTER_EXPLICIT_REVIEW",
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Stage immutable Observatory candidates and exercise isolated release-engine promotion"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--candidate-manifest", type=Path, required=True)
    common.add_argument("--candidate-root", type=Path, required=True)
    common.add_argument(
        "--registry",
        type=Path,
        default=CANONICAL_REGISTRY,
    )
    common.add_argument(
        "--releases-root", type=Path, default=CANONICAL_RELEASES_ROOT
    )
    common.add_argument("--staging-dir", type=Path, required=True)
    sub.add_parser("stage", parents=[common])
    promote_parser = sub.add_parser(
        "promote",
        parents=[common],
        help="Canonical state is fail-closed; isolated test/scratch registries remain supported",
    )
    promote_parser.add_argument("--attestation", type=Path, required=True)
    return parser


def main() -> int:
    args = parser().parse_args()
    return stage(args) if args.command == "stage" else promote(args)


if __name__ == "__main__":
    raise SystemExit(main())
