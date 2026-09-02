from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from genai_at_work.release_engine import diff_releases, validate_release_manifest
from genai_at_work.rps_release import RpsReleaseError, snapshot_content_sha256
from genai_at_work.rps_release_complete import (
    build_rps_release_candidate_complete_history,
    prepare_rps_source_history,
)

ROOT = Path(__file__).parents[1]
REGISTRY = ROOT / "data" / "registry"
BUILDER_COMMIT = "0123456789abcdef0123456789abcdef01234567"

DATES = {
    "2024-Q3": "2024-08-01",
    "2024-Q4": "2024-11-01",
    "2025-Q1": "2025-02-01",
    "2025-Q2": "2025-05-01",
    "2026-Q2": "2026-05-01",
    "2026-Q3": "2026-08-01",
}
NATIONAL_PERIODS = ("2024-Q3", "2024-Q4", "2025-Q1", "2025-Q2", "2026-Q2")
SUBGROUP_PERIODS = ("2025-Q2", "2026-Q2")


def _load(name: str) -> dict[str, Any]:
    value = json.loads((REGISTRY / name).read_text())
    assert isinstance(value, dict)
    return value


def _value(row: dict[str, Any], period_index: int) -> float:
    entity_index = int(row["entity_index"])
    metric = str(row["metric_id"])
    if row["entity_type"] == "national":
        metric_index = (
            "adoption_work",
            "work_use_last_week",
            "work_use_daily",
            "assisted_hours_share",
            "reported_time_savings_share",
        ).index(metric)
        return 20.0 + metric_index * 3.0 + period_index * 0.2
    if metric == "adoption_work":
        return 10.0 + 0.82 * entity_index + 0.65 * (entity_index % 2) + period_index * 0.4
    if metric == "assisted_hours_share":
        return 7.0 + 0.49 * entity_index + 1.15 * (entity_index % 3) + period_index * 0.25
    if metric == "reported_time_savings_share":
        return 5.0 + 0.36 * entity_index + 0.85 * (entity_index % 5) + period_index * 0.45
    raise AssertionError(f"Unexpected subgroup metric: {metric}")


def _snapshot(
    *,
    national_periods: tuple[str, ...] = NATIONAL_PERIODS,
    subgroup_periods: tuple[str, ...] = SUBGROUP_PERIODS,
) -> dict[str, Any]:
    manifest = _load("rps_source_series_manifest.json")
    scope = _load("rps_provider_catalog_scope.json")
    raw_series = manifest["series"]
    assert isinstance(raw_series, list)
    series: list[dict[str, Any]] = []
    observation_count = 0
    for raw in raw_series:
        assert isinstance(raw, dict)
        periods = national_periods if raw["entity_type"] == "national" else subgroup_periods
        observations = [
            {
                "date": DATES[period],
                "period": period,
                "value": _value(raw, index),
                "unit": "Percent",
                "realtime_start": "2026-09-02",
                "realtime_end": "2026-09-02",
                "source_last_updated": "2026-09-01 00:00:00+00",
            }
            for index, period in enumerate(periods)
        ]
        observation_count += len(observations)
        series_id = str(raw["series_id"])
        series.append(
            {
                "series_id": series_id,
                "title": f"Synthetic mixed-history series {series_id}",
                "metric_id": raw["metric_id"],
                "entity_id": raw["entity_id"],
                "entity_type": raw["entity_type"],
                "entity_name": raw["entity_name"],
                "frequency": "Quarterly",
                "unit": "Percent",
                "seasonal_adjustment": "Not Seasonally Adjusted",
                "observation_start": DATES[periods[0]],
                "observation_end": DATES[periods[-1]],
                "last_updated": "2026-09-01 00:00:00+00",
                "notes_hash": (series_id.encode().hex() + "0" * 64)[:64],
                "source_url": f"https://fred.stlouisfed.org/series/{series_id}",
                "copyright_status": "Copyrighted: Citation Required",
                "citation_text": f"Synthetic test citation for {series_id}.",
                "observations": observations,
            }
        )

    excluded_raw = scope["intentionally_excluded_national_series"]
    assert isinstance(excluded_raw, list)
    excluded = [
        {
            "series_id": row["series_id"],
            "title": f"Synthetic excluded {row['series_id']}",
            "construct": row["construct"],
            "reason": row["reason"],
            "observations_retrieved": False,
        }
        for row in excluded_raw
        if isinstance(row, dict)
    ]
    snapshot: dict[str, Any] = {
        "schema_version": 1,
        "snapshot_type": "rps_published_aggregate_refresh",
        "source_id": "rps-genai-tracker-fred-release-6",
        "provider": "FRED/ALFRED distribution of the RPS GenAI Adoption Tracker",
        "provider_release_id": 6,
        "retrieved_at": "2026-09-02T12:00:00Z",
        "rights": {
            "status": "approved",
            "scope": "published aggregate project use",
            "decision_ref": "docs/source-rights/RPS_SOURCE_DECISION.md",
            "public_bulk_redistribution_approved": False,
        },
        "inventory": {
            "provider_series_count": scope["provider_release_series_count"],
            "observatory_series_count": scope["observatory_registry_series_count"],
            "excluded_series_count": len(excluded),
            "provider_inventory_status": "pass",
        },
        "observation_count": observation_count,
        "series": series,
        "excluded_series": excluded,
    }
    snapshot["content_sha256"] = snapshot_content_sha256(snapshot)
    return snapshot


def _build(
    tmp_path: Path,
    snapshot: dict[str, Any],
    *,
    release_id: str = "rps-complete-history-baseline",
    previous_release: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return build_rps_release_candidate_complete_history(
        snapshot,
        _load("rps_source_series_manifest.json"),
        _load("rps_provider_catalog_scope.json"),
        _load("longitudinal_claim_inventory.json"),
        output_dir=tmp_path,
        release_id=release_id,
        builder_commit=BUILDER_COMMIT,
        previous_release=previous_release,
    )


def test_longer_national_history_is_preserved_while_subgroup_window_is_complete() -> None:
    snapshot = _snapshot()
    prepared = prepare_rps_source_history(
        snapshot,
        _load("rps_source_series_manifest.json"),
        _load("rps_provider_catalog_scope.json"),
    )
    panel = prepared.analysis_panel
    assert prepared.source_periods == NATIONAL_PERIODS
    assert panel.periods == SUBGROUP_PERIODS
    assert prepared.subgroup_series_count == 126
    assert prepared.national_series_count == 5
    assert len(panel.period_rows["2024-Q3"]) == 5
    assert len(panel.period_rows["2025-Q2"]) == 131
    assert len(panel.period_rows["2026-Q2"]) == 131
    assert panel.observation_count == 5 * len(NATIONAL_PERIODS) + 126 * len(SUBGROUP_PERIODS)
    assert len(panel.subgroup_records) == 126 * len(SUBGROUP_PERIODS)


def test_complete_history_candidate_hash_binds_national_only_periods(tmp_path: Path) -> None:
    candidate = _build(tmp_path, _snapshot())
    validate_release_manifest(candidate, tmp_path)
    source = candidate["sources"][0]
    assert candidate["release_type"] == "baseline"
    assert source["reference_periods"] == list(NATIONAL_PERIODS)
    assert source["analysis_reference_periods"] == list(SUBGROUP_PERIODS)
    assert [row["object_id"] for row in source["objects"]] == [
        period.lower() for period in NATIONAL_PERIODS
    ]
    assert source["coverage"]["required_units"] == 131 * len(SUBGROUP_PERIODS)
    assert source["coverage"]["observed_units"] == 131 * len(SUBGROUP_PERIODS)
    assert source["coverage"]["full_source_observed_units"] == (
        5 * len(NATIONAL_PERIODS) + 126 * len(SUBGROUP_PERIODS)
    )
    assert candidate["source_input_bytes_publication"] is False


def test_subgroup_new_wave_adds_one_object_and_preserves_old_history(tmp_path: Path) -> None:
    baseline = _build(tmp_path / "baseline", _snapshot())
    current = _build(
        tmp_path / "new",
        _snapshot(
            national_periods=(*NATIONAL_PERIODS, "2026-Q3"),
            subgroup_periods=(*SUBGROUP_PERIODS, "2026-Q3"),
        ),
        release_id="rps-complete-history-new-wave",
        previous_release=baseline,
    )
    validate_release_manifest(current, tmp_path / "new")
    old_objects = {
        row["object_id"]: row["sha256"] for row in baseline["sources"][0]["objects"]
    }
    new_objects = {
        row["object_id"]: row["sha256"] for row in current["sources"][0]["objects"]
    }
    for period in NATIONAL_PERIODS:
        assert new_objects[period.lower()] == old_objects[period.lower()]
    assert "2026-q3" in new_objects
    assert current["sources"][0]["revision_status"] == "new_wave"
    assert current["sources"][0]["analysis_reference_periods"][-1] == "2026-Q3"


def test_national_only_history_revision_is_detected_even_when_analytics_are_unchanged(
    tmp_path: Path,
) -> None:
    baseline = _build(tmp_path / "baseline", _snapshot())
    revised = _snapshot()
    national = next(row for row in revised["series"] if row["entity_type"] == "national")
    national["observations"][0]["value"] = float(national["observations"][0]["value"]) + 0.25
    revised["content_sha256"] = snapshot_content_sha256(revised)
    current = _build(
        tmp_path / "revision",
        revised,
        release_id="rps-complete-history-national-revision",
        previous_release=baseline,
    )
    assert current["sources"][0]["revision_status"] == "revision"
    assert current["release_type"] == "revision"
    assert current["sources"][0]["analysis_reference_periods"] == list(SUBGROUP_PERIODS)
    diff = diff_releases(baseline, current)
    assert diff["contract_failures"] == []
    assert diff["source_changes"][0]["modified_objects"] == ["2024-q3"]


def test_inconsistent_subgroup_period_sets_fail_closed() -> None:
    snapshot = _snapshot()
    subgroup = next(row for row in snapshot["series"] if row["entity_type"] == "occupation")
    subgroup["observations"] = subgroup["observations"][:-1]
    snapshot["observation_count"] -= 1
    snapshot["content_sha256"] = snapshot_content_sha256(snapshot)
    with pytest.raises(RpsReleaseError, match="subgroup series do not share"):
        prepare_rps_source_history(
            snapshot,
            _load("rps_source_series_manifest.json"),
            _load("rps_provider_catalog_scope.json"),
        )
