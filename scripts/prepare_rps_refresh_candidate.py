#!/usr/bin/env python3
"""Build a private RPS aggregate refresh source candidate.

The command retrieves the rights-cleared published aggregate Tracker series,
validates the provider inventory, writes the source snapshot and detailed diff
only to a private/external candidate directory, and emits a review-safe summary.
It never writes raw RPS observations into the public web tree or promotes a
release automatically.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from genai_at_work.rps_refresh import (
    build_refresh_snapshot,
    compare_refresh_snapshots,
    summarize_refresh_candidate,
)
from genai_at_work.sources.fred import FredClient

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "registry" / "rps_source_series_manifest.json"
SCOPE_PATH = ROOT / "data" / "registry" / "rps_provider_catalog_scope.json"
PRIVATE_ROOT = ROOT / "data" / "audit" / "private"


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise SystemExit(f"Expected a JSON object at {path}")
    return {str(key): item for key, item in value.items()}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_timestamp(value: str | None) -> datetime | None:
    if value is None:
        return None
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise SystemExit(f"Invalid --retrieved-at timestamp: {value!r}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise SystemExit("--retrieved-at must include a timezone offset or Z")
    return parsed.astimezone(UTC)


def _assert_output_boundary(output_dir: Path) -> None:
    """Require repository-local source snapshots to live under the private audit root."""

    resolved = output_dir.resolve()
    root = ROOT.resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return

    private = PRIVATE_ROOT.resolve()
    try:
        resolved.relative_to(private)
    except ValueError as exc:
        raise SystemExit(
            "Repository-local RPS refresh outputs may only be written under "
            "data/audit/private/. Use an external directory for transient source candidates."
        ) from exc


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _baseline_diff(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "source_id": snapshot["source_id"],
        "previous_content_sha256": None,
        "current_content_sha256": snapshot["content_sha256"],
        "revision_status": "baseline",
        "requires_release_review": True,
        "counts": {
            "new_observations": snapshot["observation_count"],
            "revised_observations": 0,
            "removed_observations": 0,
            "definition_changes": 0,
        },
        "new_observations": [],
        "revised_observations": [],
        "removed_observations": [],
        "definition_changes": [],
        "note": "Baseline candidate; no prior private snapshot was supplied for cell-level comparison.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help=(
            "New or empty candidate directory. Repository-local paths must be under "
            "data/audit/private/. External transient directories are also allowed."
        ),
    )
    parser.add_argument(
        "--previous-snapshot",
        type=Path,
        help="Optional previous private rps_source_snapshot.json used for revision classification.",
    )
    parser.add_argument(
        "--retrieved-at",
        help="Optional timezone-aware ISO-8601 timestamp, primarily for reproducible audits/tests.",
    )
    args = parser.parse_args()

    output_dir = args.output_dir
    _assert_output_boundary(output_dir)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise SystemExit(f"Output directory must be new or empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    previous: dict[str, Any] | None = None
    if args.previous_snapshot is not None:
        if not args.previous_snapshot.is_file():
            raise SystemExit(f"Previous snapshot does not exist: {args.previous_snapshot}")
        previous = _load_json(args.previous_snapshot)

    load_dotenv(ROOT / ".env")
    api_key = os.environ.get("FRED_API_KEY", "").strip()
    if not api_key:
        raise SystemExit(
            "FRED_API_KEY is required for the official API distribution path. "
            "HTML scraping and manual-copy substitution are intentionally unsupported."
        )

    manifest = _load_json(MANIFEST_PATH)
    scope = _load_json(SCOPE_PATH)
    retrieved_at = _parse_timestamp(args.retrieved_at)
    snapshot = build_refresh_snapshot(
        FredClient(api_key=api_key),
        manifest,
        scope,
        retrieved_at=retrieved_at,
    )

    snapshot_path = output_dir / "rps_source_snapshot.json"
    _write_json(snapshot_path, snapshot)
    snapshot_file_sha256 = _sha256_file(snapshot_path)

    diff = compare_refresh_snapshots(previous, snapshot) if previous else _baseline_diff(snapshot)
    diff_path = output_dir / "rps_refresh_diff.json"
    _write_json(diff_path, diff)

    candidate = summarize_refresh_candidate(
        snapshot,
        previous_snapshot=previous,
        snapshot_file_sha256=snapshot_file_sha256,
    )
    candidate["private_snapshot_file"] = snapshot_path.name
    candidate["private_snapshot_file_sha256"] = snapshot_file_sha256
    candidate["private_diff_file"] = diff_path.name
    candidate["private_diff_file_sha256"] = _sha256_file(diff_path)
    summary_path = output_dir / "rps_refresh_candidate.json"
    _write_json(summary_path, candidate)

    print(json.dumps(candidate, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
