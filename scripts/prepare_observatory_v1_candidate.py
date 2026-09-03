#!/usr/bin/env python3
"""Prepare a complete private Observatory v1 global-baseline candidate.

The input RPS component and resulting global candidate contain authorized RPS
source-observation bytes under ``inputs/``. Repository-local output is therefore
restricted to ``data/audit/private/``. External private paths are also allowed.

This command composes and validates a candidate only. It never stages, reviews,
or promotes a release.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from genai_at_work.observatory_baseline import (
    ObservatoryBaselineError,
    compose_v1_global_baseline,
)
from genai_at_work.release_engine import load_json_object

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ROOT = ROOT / "data" / "audit" / "private"
DEFAULT_CONTRACT = ROOT / "data" / "registry" / "observatory_v1_baseline_contract.json"


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
            "Repository-local global release candidates may only be written under "
            "data/audit/private/. Use an external private directory otherwise."
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
                "Refusing to compose a release candidate from a dirty Git working tree."
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


def _previous_release(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    return load_json_object(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rps-candidate-root",
        type=Path,
        required=True,
        help="Private RPS complete-history candidate directory containing release.json.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help=(
            "New global candidate directory. Repository-local paths must be under "
            "data/audit/private/; external private paths are allowed."
        ),
    )
    parser.add_argument(
        "--release-id",
        required=True,
        help="Lowercase immutable global release-candidate slug.",
    )
    parser.add_argument(
        "--contract",
        type=Path,
        default=DEFAULT_CONTRACT,
        help="Pinned Observatory v1 baseline composition contract.",
    )
    parser.add_argument(
        "--previous-release-manifest",
        type=Path,
        help="Previously promoted global release manifest, when preparing an update.",
    )
    args = parser.parse_args()

    _assert_output_boundary(args.output_dir)
    if args.output_dir.exists():
        raise SystemExit(f"Output directory must be new and absent: {args.output_dir}")

    contract = load_json_object(args.contract)
    previous = _previous_release(args.previous_release_manifest)
    commit = _builder_commit()

    try:
        candidate = compose_v1_global_baseline(
            rps_candidate_root=args.rps_candidate_root,
            output_dir=args.output_dir,
            contract=contract,
            repo_root=ROOT,
            release_id=args.release_id,
            builder_commit=commit,
            previous_release=previous,
        )
    except (ObservatoryBaselineError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc

    summary = {
        "release_id": candidate["release_id"],
        "release_type": candidate["release_type"],
        "data_mode": candidate["data_mode"],
        "builder_commit": candidate["build"]["builder_commit"],
        "baseline_contract_id": candidate["baseline_contract_id"],
        "source_ids": [row["source_id"] for row in candidate["sources"]],
        "artifact_count": len(candidate["artifacts"]),
        "diagnostic_count": len(candidate["diagnostics"]),
        "claim_count": len(candidate["claims"]),
        "candidate_manifest": str((args.output_dir / "release.json").resolve()),
        "source_input_bytes_publication": False,
        "staging_performed": False,
        "promotion_performed": False,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
