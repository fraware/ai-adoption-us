#!/usr/bin/env python3
"""Probe the authorized RPS aggregate distribution and emit non-canonical review evidence."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from genai_at_work.rps_refresh import build_refresh_candidate
from genai_at_work.sources.fred import FredClient

ROOT = Path(__file__).parents[1].resolve()
MANIFEST = ROOT / "data" / "registry" / "rps_source_series_manifest.json"
PROVIDER_SCOPE = ROOT / "data" / "registry" / "rps_provider_catalog_scope.json"
CANONICAL_CHECKPOINT = ROOT / "data" / "registry" / "rps_industry_adoption_q2_2026_v1.json"


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise SystemExit(f"Expected JSON object at {path}")
    return value


def _assert_review_output(path: Path) -> None:
    resolved = path.resolve()
    forbidden = (
        ROOT / "data" / "registry",
        ROOT / "data" / "derived",
        ROOT / "apps" / "web" / "public",
    )
    for root in forbidden:
        try:
            resolved.relative_to(root)
        except ValueError:
            continue
        raise SystemExit(
            f"Refusing to write source-watch evidence into canonical/public data tree: {resolved}"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    _assert_review_output(args.output)

    api_key = os.environ.get("FRED_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("FRED_API_KEY is required for the documented FRED API source watch")

    manifest = _load(MANIFEST)
    provider_scope = _load(PROVIDER_SCOPE)
    checkpoint = _load(CANONICAL_CHECKPOINT)
    release_id = provider_scope.get("provider_release_id")
    if not isinstance(release_id, int):
        raise SystemExit("provider_release_id must be an integer")

    series = manifest.get("series")
    if not isinstance(series, list):
        raise SystemExit("RPS source series manifest is invalid")
    series_ids: list[str] = []
    for row in series:
        if not isinstance(row, dict) or not isinstance(row.get("series_id"), str):
            raise SystemExit("RPS source series manifest contains an invalid series row")
        series_ids.append(row["series_id"])

    client = FredClient(api_key=api_key)
    release_rows = list(client.iter_release_series(release_id))
    observations_by_series: dict[str, list[dict[str, object]]] = {}
    for index, series_id in enumerate(series_ids, start=1):
        observations = client.series_observations(series_id)
        observations_by_series[series_id] = [dict(row) for row in observations]
        if index % 20 == 0 or index == len(series_ids):
            print(f"Fetched RPS observations for {index}/{len(series_ids)} supported series", file=sys.stderr)

    candidate = build_refresh_candidate(
        manifest=manifest,
        provider_scope=provider_scope,
        canonical_checkpoint=checkpoint,
        release_rows=release_rows,
        observations_by_series=observations_by_series,
        retrieved_at=datetime.now(timezone.utc).isoformat(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(candidate, indent=2, sort_keys=False) + "\n")
    print(json.dumps(candidate["catalog"], sort_keys=True))
    print(f"RPS source-watch status: {candidate['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
