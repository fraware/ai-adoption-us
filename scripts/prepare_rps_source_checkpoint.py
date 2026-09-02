#!/usr/bin/env python3
"""Prepare a rights-safe RPS source-checkpoint candidate from live-validation outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from genai_at_work.rps_checkpoint import RpsCheckpointError, build_public_rps_source_checkpoint


def _load_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise RpsCheckpointError(f"Could not read {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RpsCheckpointError(f"{label} must contain a JSON object: {path}")
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-summary", type=Path, required=True)
    parser.add_argument("--release-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--validation-run-id", required=True)
    parser.add_argument("--validation-commit", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output: Path = args.output
    if output.exists():
        raise SystemExit(f"Checkpoint output already exists; refusing overwrite: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)

    try:
        checkpoint = build_public_rps_source_checkpoint(
            _load_object(args.source_summary, label="source summary"),
            _load_object(args.release_manifest, label="release manifest"),
            validation_run_id=str(args.validation_run_id),
            validation_commit=str(args.validation_commit),
        )
    except RpsCheckpointError as exc:
        raise SystemExit(str(exc)) from exc

    output.write_text(json.dumps(checkpoint, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "checkpoint_state": checkpoint["checkpoint_state"],
                "source_content_sha256": checkpoint["source_content_sha256"],
                "source_snapshot_file_sha256": checkpoint["source_snapshot_file_sha256"],
                "source_reference_periods": checkpoint["source_reference_periods"],
                "analysis_reference_periods": checkpoint["analysis_reference_periods"],
                "analysis_metric_reference_periods": checkpoint[
                    "analysis_metric_reference_periods"
                ],
                "source_object_count": len(checkpoint["source_objects"]),
                "observation_count": checkpoint["observation_count"],
                "requires_human_acceptance": checkpoint["requires_human_acceptance"],
                "durable_private_raw_archive_attested": checkpoint["rights_boundary"][
                    "durable_private_raw_archive_attested"
                ],
                "promotion_performed": checkpoint["promotion_performed"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
