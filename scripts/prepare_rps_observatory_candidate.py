#!/usr/bin/env python3
"""Build a private RPS observatory candidate component from a source snapshot.

This command performs no network access and no release promotion. The supplied
snapshot must already have been acquired through the authorized RPS refresh
pipeline. Repository-local candidate packages are restricted to
``data/audit/private/`` because their ``inputs/`` directory contains source
observation bytes.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from genai_at_work.rps_release import RpsReleaseError
from genai_at_work.rps_release_public import build_rps_observatory_release_candidate

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ROOT = ROOT / "data" / "audit" / "private"
MANIFEST_PATH = ROOT / "data" / "registry" / "rps_source_series_manifest.json"
SCOPE_PATH = ROOT / "data" / "registry" / "rps_provider_catalog_scope.json"
CLAIMS_PATH = ROOT / "data" / "registry" / "longitudinal_claim_inventory.json"
PUBLIC_VIEW_CONTRACT_PATH = (
    ROOT / "data" / "registry" / "rps_public_observation_delivery_v1.json"
)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SystemExit(f"Required JSON file does not exist: {path}")
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise SystemExit(f"Expected a JSON object at {path}")
    return {str(key): item for key, item in value.items()}


def _assert_output_boundary(output_dir: Path) -> None:
    resolved = output_dir.resolve()
    root = ROOT.resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return
    try:
        resolved.relative_to(PRIVATE_ROOT.resolve())
    except ValueError as exc:
        raise SystemExit(
            "Repository-local RPS release candidates may only be written under "
            "data/audit/private/. Use an external directory for transient candidates."
        ) from exc


def _builder_commit() -> str:
    try:
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        if status.strip():
            raise SystemExit(
                "Refusing to build a release candidate from a dirty Git working tree. "
                "Commit or remove all changes first."
            )
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except subprocess.CalledProcessError as exc:
        raise SystemExit("Could not resolve a clean Git builder commit") from exc
    if len(commit) not in {40, 64}:
        raise SystemExit(f"Unexpected Git commit identity: {commit!r}")
    return commit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-snapshot",
        type=Path,
        required=True,
        help="Private rps_source_snapshot.json produced by the authorized refresh pipeline.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help=(
            "New or empty candidate directory. Repository-local paths must be beneath "
            "data/audit/private/; external transient directories are allowed."
        ),
    )
    parser.add_argument(
        "--release-id",
        required=True,
        help="Lowercase immutable release-candidate slug.",
    )
    parser.add_argument(
        "--previous-release-manifest",
        type=Path,
        help=(
            "Optional previously frozen release manifest for new-wave/revision classification. "
            "Omit only when preparing the first baseline component."
        ),
    )
    args = parser.parse_args()

    _assert_output_boundary(args.output_dir)
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise SystemExit(f"Output directory must be new or empty: {args.output_dir}")

    snapshot = _load_json(args.source_snapshot)
    manifest = _load_json(MANIFEST_PATH)
    scope = _load_json(SCOPE_PATH)
    claims = _load_json(CLAIMS_PATH)
    public_view_contract = _load_json(PUBLIC_VIEW_CONTRACT_PATH)
    previous = (
        _load_json(args.previous_release_manifest)
        if args.previous_release_manifest is not None
        else None
    )
    commit = _builder_commit()

    try:
        candidate = build_rps_observatory_release_candidate(
            snapshot,
            manifest,
            scope,
            claims,
            public_view_contract,
            output_dir=args.output_dir,
            release_id=args.release_id,
            builder_commit=commit,
            previous_release=previous,
        )
    except (RpsReleaseError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc

    source = candidate["sources"][0]
    artifact_ids = [row["artifact_id"] for row in candidate["artifacts"]]
    summary = {
        "release_id": candidate["release_id"],
        "release_type": candidate["release_type"],
        "data_mode": candidate["data_mode"],
        "builder_id": candidate["build"]["builder_id"],
        "builder_commit": candidate["build"]["builder_commit"],
        "source_id": source["source_id"],
        "source_vintage_id": source["source_vintage_id"],
        "source_revision_status": source["revision_status"],
        "reference_periods": source["reference_periods"],
        "analysis_reference_periods": source["analysis_reference_periods"],
        "source_objects": len(source["objects"]),
        "full_source_observed_units": source["coverage"]["full_source_observed_units"],
        "derived_artifacts": len(candidate["artifacts"]),
        "public_observation_view_included": "rps-public-observation-view" in artifact_ids,
        "diagnostics": {
            row["diagnostic_id"]: row["status"] for row in candidate["diagnostics"]
        },
        "claims_requiring_release_traceability": len(candidate["claims"]),
        "candidate_manifest": str((args.output_dir / "release.json").resolve()),
        "source_input_bytes_publication": False,
        "promotion_performed": False,
        "global_baseline_warning": (
            "This is the RPS observatory component. Do not promote it as the first global "
            "observatory baseline unless the complete observatory release composition is reviewed."
        ),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
