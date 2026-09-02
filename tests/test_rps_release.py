from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from genai_at_work.release_engine import (
    candidate_gate_failures,
    diff_releases,
    gate_status,
    validate_release_manifest,
)
from genai_at_work.rps_release import (
    RpsReleaseError,
    build_rps_release_candidate,
    snapshot_content_sha256,
)

ROOT = Path(__file__).parents[1]
REGISTRY = ROOT / "data" / "registry"
BUILDER_COMMIT = "0123456789abcdef0123456789abcdef01234567"

_PERIOD_DATES = {
    "2026-Q1": "2026-02-01",
    "2026-Q2": "2026-05-01",
    "2026-Q3": "2026-08-01",
}


def _load(name: str) -> dict[str, Any]:
    value = json.loads((REGISTRY / name).read_text())
    assert isinstance(value, dict)
    return value


def _value(row: dict[str, Any], period_index: int) -> float:
    entity_index = int(row["entity_index"])
    metric = str(row["metric_id"])
    entity_type = str(row["entity_type"])
    if entity_type == "national":
        metric_offset = {
            "adoption_work": 0.0,
            "work_use_last_week": 3.0,
            "work_use_daily": 6.0,
            "assisted_hours_share": 9.0,
            "reported_time_savings_share": 12.0,
        }[metric]
        return 20.0 + metric_offset + period_index
    if metric == "adoption_work":
        return 10.0 + 1.1 * entity_index + 0.35 * (entity_index % 2) + 0.4 * period_index
    if metric == "assisted_hours_share":
        return 8.0 + 0.72 * entity_index + 1.3 * (entity_index % 3) + 0.3 * period_index
    if metric == "reported_time_savings_share":
        return 6.0 + 0.51 * entity_index + 1.05 * (entity_index % 5) + 0.5 * period_index
    raise AssertionError(f"Unexpected subgroup metric: {metric}")


def _snapshot(periods: tuple[str, ...] = ("2026-Q1", "2026-Q2")) -> dict[str, Any]:
    manifest = _load("rps_source_series_manifest.json")
    scope = _load("rps_provider_catalog_scope.json")
    raw_series = manifest["series"]
    assert isinstance(raw_series, list)

    series: list[dict[str, Any]] = []
    for raw in raw_series:
        assert isinstance(raw, dict)
        series_id = str(raw["series_id"])
        observations = [
            {
                "date": _PERIOD_DATES[period],
                "period": period,
                "value": _value(raw, index),
                "unit": "Percent",
                "realtime_start": "2026-09-02",
                "realtime_end": "2026-09-02",
                "source_last_updated": "2026-09-01 00:00:00+00",
            }
            for index, period in enumerate(periods)
        ]
        series.append(
            {
                "series_id": series_id,
                "title": f"Synthetic release-contract series {series_id}",
                "metric_id": raw["metric_id"],
                "entity_id": raw["entity_id"],
                "entity_type": raw["entity_type"],
                "entity_name": raw["entity_name"],
                "frequency": "Quarterly",
                "unit": "Percent",
                "seasonal_adjustment": "Not Seasonally Adjusted",
                "observation_start": _PERIOD_DATES[periods[0]],
                "observation_end": _PERIOD_DATES[periods[-1]],
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
        "observation_count": len(series) * len(periods),
        "series": series,
        "excluded_series": excluded,
    }
    snapshot["content_sha256"] = snapshot_content_sha256(snapshot)
    return snapshot


def _build(
    tmp_path: Path,
    snapshot: dict[str, Any],
    *,
    release_id: str = "rps-baseline-test",
    previous_release: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return build_rps_release_candidate(
        snapshot,
        _load("rps_source_series_manifest.json"),
        _load("rps_provider_catalog_scope.json"),
        _load("longitudinal_claim_inventory.json"),
        output_dir=tmp_path,
        release_id=release_id,
        builder_commit=BUILDER_COMMIT,
        previous_release=previous_release,
    )


def test_baseline_candidate_is_release_engine_valid_and_derived_only(tmp_path: Path) -> None:
    candidate = _build(tmp_path, _snapshot())
    validate_release_manifest(candidate, tmp_path)

    source = candidate["sources"][0]
    assert candidate["release_type"] == "baseline"
    assert candidate["data_mode"] == "derived_only"
    assert source["revision_status"] == "new_wave"
    assert source["rights"] == {
        "status": "approved",
        "storage_scope": "private",
        "publication_scope": "derived_only",
        "redistribution_scope": "derived_only",
    }
    assert source["reference_periods"] == ["2026-Q1", "2026-Q2"]
    assert [row["object_id"] for row in source["objects"]] == ["2026-q1", "2026-q2"]
    assert all(str(row["local_path"]).startswith("inputs/rps/") for row in source["objects"])
    assert all(str(row["path"]).startswith("artifacts/longitudinal/") for row in candidate["artifacts"])
    assert not any("observation" in str(row["path"]).lower() for row in candidate["artifacts"])
    assert all(row["status"] == "pass" for row in candidate["diagnostics"])
    assert candidate["source_input_bytes_publication"] is False
    assert "RPS longitudinal component only" in candidate["candidate_scope"]

    expected_claims = {
        row["claim_id"] for row in _load("longitudinal_claim_inventory.json")["claims"]
    }
    assert {row["claim_id"] for row in candidate["claims"]} == expected_claims
    assert all(
        set(row["artifact_ids"]) == {artifact["artifact_id"] for artifact in candidate["artifacts"]}
        for row in candidate["claims"]
    )

    diff = diff_releases(None, candidate)
    assert diff["contract_failures"] == []
    assert gate_status(candidate_gate_failures(candidate, diff), True) == "BLOCKED_REVIEW_REQUIRED"


def test_new_wave_adds_period_object_without_rewriting_frozen_history(tmp_path: Path) -> None:
    baseline_dir = tmp_path / "baseline"
    baseline = _build(baseline_dir, _snapshot())

    new_dir = tmp_path / "new-wave"
    current = _build(
        new_dir,
        _snapshot(("2026-Q1", "2026-Q2", "2026-Q3")),
        release_id="rps-new-wave-test",
        previous_release=baseline,
    )
    validate_release_manifest(current, new_dir)

    old_objects = {row["object_id"]: row["sha256"] for row in baseline["sources"][0]["objects"]}
    new_objects = {row["object_id"]: row["sha256"] for row in current["sources"][0]["objects"]}
    assert new_objects["2026-q1"] == old_objects["2026-q1"]
    assert new_objects["2026-q2"] == old_objects["2026-q2"]
    assert "2026-q3" not in old_objects
    assert current["sources"][0]["revision_status"] == "new_wave"
    assert current["release_type"] == "new_wave"

    diff = diff_releases(baseline, current)
    assert diff["contract_failures"] == []
    source_change = diff["source_changes"][0]
    assert source_change["added_periods"] == ["2026-Q3"]
    assert source_change["modified_objects"] == []
    assert source_change["added_objects"] == ["2026-q3"]


def test_historical_value_change_is_revision_and_changes_only_that_period_object(
    tmp_path: Path,
) -> None:
    baseline = _build(tmp_path / "baseline", _snapshot())
    revised_snapshot = _snapshot()
    target = revised_snapshot["series"][10]["observations"][0]
    target["value"] = float(target["value"]) + 0.25
    revised_snapshot["content_sha256"] = snapshot_content_sha256(revised_snapshot)

    current = _build(
        tmp_path / "revision",
        revised_snapshot,
        release_id="rps-revision-test",
        previous_release=baseline,
    )
    old_objects = {row["object_id"]: row["sha256"] for row in baseline["sources"][0]["objects"]}
    new_objects = {row["object_id"]: row["sha256"] for row in current["sources"][0]["objects"]}

    assert current["sources"][0]["revision_status"] == "revision"
    assert current["release_type"] == "revision"
    assert new_objects["2026-q1"] != old_objects["2026-q1"]
    assert new_objects["2026-q2"] == old_objects["2026-q2"]
    diff = diff_releases(baseline, current)
    assert diff["contract_failures"] == []
    assert diff["source_changes"][0]["modified_objects"] == ["2026-q1"]


def test_new_wave_plus_historical_change_is_mixed(tmp_path: Path) -> None:
    baseline = _build(tmp_path / "baseline", _snapshot())
    mixed_snapshot = _snapshot(("2026-Q1", "2026-Q2", "2026-Q3"))
    target = mixed_snapshot["series"][12]["observations"][0]
    target["value"] = float(target["value"]) + 0.5
    mixed_snapshot["content_sha256"] = snapshot_content_sha256(mixed_snapshot)

    current = _build(
        tmp_path / "mixed",
        mixed_snapshot,
        release_id="rps-mixed-test",
        previous_release=baseline,
    )
    assert current["sources"][0]["revision_status"] == "mixed"
    assert current["release_type"] == "mixed"
    diff = diff_releases(baseline, current)
    assert diff["contract_failures"] == []


def test_snapshot_tampering_and_missing_series_period_fail_closed(tmp_path: Path) -> None:
    tampered = _snapshot()
    tampered["series"][0]["observations"][0]["value"] += 1.0
    with pytest.raises(RpsReleaseError, match="scientific content hash mismatch"):
        _build(tmp_path / "tampered", tampered)

    incomplete = _snapshot()
    incomplete["series"][0]["observations"].pop()
    incomplete["observation_count"] -= 1
    incomplete["content_sha256"] = snapshot_content_sha256(incomplete)
    with pytest.raises(RpsReleaseError, match="do not share one complete quarterly period set"):
        _build(tmp_path / "incomplete", incomplete)


def test_retrieval_envelope_does_not_change_candidate_input_or_artifact_hashes(
    tmp_path: Path,
) -> None:
    first_snapshot = _snapshot()
    second_snapshot = copy.deepcopy(first_snapshot)
    second_snapshot["retrieved_at"] = "2026-09-03T12:00:00Z"
    for series in second_snapshot["series"]:
        for observation in series["observations"]:
            observation["realtime_start"] = "2026-09-03"
            observation["realtime_end"] = "2026-09-03"
    assert snapshot_content_sha256(second_snapshot) == first_snapshot["content_sha256"]

    first = _build(tmp_path / "first", first_snapshot)
    second = _build(tmp_path / "second", second_snapshot, release_id="rps-second-test")

    assert first["build"]["input_sha256"] == second["build"]["input_sha256"]
    assert first["build"]["output_sha256"] == second["build"]["output_sha256"]
    assert first["sources"][0]["source_vintage_id"] == second["sources"][0]["source_vintage_id"]
    assert first["sources"][0]["retrieved_at"] != second["sources"][0]["retrieved_at"]
