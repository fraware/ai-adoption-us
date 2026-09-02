#!/usr/bin/env python3
"""Report rights-safe RPS series-period topology from a validated private snapshot.

This diagnostic emits metadata only: series IDs, metric/entity classes, and period
labels. It never emits observation values, realtime fields, notes, or source bytes.
It exists to distinguish staggered source-history coverage from an actual missing
analytical cell before the release adapter chooses any common period window.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from genai_at_work.rps_release import _validate_registered_scope

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "registry" / "rps_source_series_manifest.json"
SCOPE_PATH = ROOT / "data" / "registry" / "rps_provider_catalog_scope.json"
SUBGROUP_ENTITY_TYPES = {"industry", "occupation"}
SUBGROUP_METRICS = {
    "adoption_work",
    "assisted_hours_share",
    "reported_time_savings_share",
}


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise SystemExit(f"Expected JSON object at {path}")
    return {str(key): item for key, item in value.items()}


def _periods(series: dict[str, Any]) -> tuple[str, ...]:
    observations = series.get("observations")
    if not isinstance(observations, list):
        raise SystemExit(f"Invalid observations for {series.get('series_id')}")
    periods: list[str] = []
    for row in observations:
        if not isinstance(row, dict):
            raise SystemExit(f"Invalid observation row for {series.get('series_id')}")
        period = row.get("period")
        if not isinstance(period, str) or not period:
            raise SystemExit(f"Invalid period for {series.get('series_id')}")
        periods.append(period)
    if len(periods) != len(set(periods)):
        raise SystemExit(f"Duplicate periods for {series.get('series_id')}")
    return tuple(periods)


def _shape_summary(series: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in series:
        grouped[_periods(row)].append(row)

    output: list[dict[str, Any]] = []
    for periods, rows in sorted(grouped.items(), key=lambda item: (item[0], len(item[1]))):
        metric_counts = Counter(str(row.get("metric_id")) for row in rows)
        entity_type_counts = Counter(str(row.get("entity_type")) for row in rows)
        output.append(
            {
                "periods": list(periods),
                "series_count": len(rows),
                "metric_counts": dict(sorted(metric_counts.items())),
                "entity_type_counts": dict(sorted(entity_type_counts.items())),
                "series_ids": sorted(str(row.get("series_id")) for row in rows),
            }
        )
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-snapshot", type=Path, required=True)
    args = parser.parse_args()

    snapshot = _load_object(args.source_snapshot)
    manifest = _load_object(MANIFEST_PATH)
    scope = _load_object(SCOPE_PATH)
    _, series, _ = _validate_registered_scope(snapshot, manifest, scope)

    subgroup = [
        row
        for row in series
        if row.get("entity_type") in SUBGROUP_ENTITY_TYPES
        and row.get("metric_id") in SUBGROUP_METRICS
    ]
    national = [row for row in series if row.get("entity_type") == "national"]
    if len(subgroup) != 126 or len(national) != 5:
        raise SystemExit(
            f"Unexpected registered topology: subgroup={len(subgroup)}, national={len(national)}"
        )

    subgroup_sets = [set(_periods(row)) for row in subgroup]
    common = set.intersection(*subgroup_sets)
    union = set.union(*subgroup_sets)
    period_counts = Counter(period for row in subgroup for period in _periods(row))

    result = {
        "schema_version": 1,
        "diagnostic_type": "rps_series_period_topology_metadata_only",
        "source_content_sha256": snapshot.get("content_sha256"),
        "raw_observation_values_included": False,
        "subgroup_series_count": len(subgroup),
        "national_series_count": len(national),
        "subgroup_common_periods": sorted(common),
        "subgroup_union_periods": sorted(union),
        "subgroup_series_count_by_period": {
            period: period_counts[period] for period in sorted(period_counts)
        },
        "subgroup_period_shapes": _shape_summary(subgroup),
        "national_period_shapes": _shape_summary(national),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
