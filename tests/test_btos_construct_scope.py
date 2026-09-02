from __future__ import annotations

from json import loads
from pathlib import Path

REGISTRY = Path(__file__).parents[1] / "data" / "registry" / "btos_construct_scope_v1.json"


def _load_registry() -> dict[str, object]:
    return loads(REGISTRY.read_text())


def test_btos_core_wording_break_cannot_be_silently_spliced() -> None:
    core = _load_registry()["core_ai"]
    legacy = core["legacy_pre_change"]
    break_contract = core["wording_break"]

    assert legacy["comparable_as_single_continuous_series_with_post_change"] is False
    assert legacy["splice_permitted"] is False
    assert break_contract["collection_change_date"] == "2025-11-17"
    assert break_contract["first_new_series_release_date"] == "2025-12-04"
    assert "Never stitch" in break_contract["governance_rule"]


def test_post_change_core_is_business_level_not_worker_weighted() -> None:
    current = _load_registry()["core_ai"]["current_post_change"]

    assert current["reference_period"] == "last two weeks"
    assert current["question_object"] == "whether this business used AI in any of its business functions"
    assert current["measurement_unit"] == "business"
    assert current["worker_weighted"] is False
    assert current["employment_weighted"] is False
    assert "businesses responding" in current["estimator_denominator"]


def test_ai_supplement_is_pooled_business_snapshot_and_not_api_source() -> None:
    supplement = _load_registry()["ai_supplement_2025_2026"]

    assert supplement["collection_window"] == {
        "start": "2025-11-17",
        "end": "2026-02-08",
    }
    assert supplement["measurement_unit"] == "business"
    assert "all six biweekly panels" in supplement["panel_design"]
    assert supplement["api_available"] is False
    assert "official Census downloadable files" in supplement["canonical_acquisition_path"]


def test_task_change_items_are_not_productivity_measures() -> None:
    registry = _load_registry()
    questions = registry["ai_supplement_2025_2026"]["questions"]
    q26 = questions["Q26_replacement_intensity"]
    prohibited = set(registry["construct_contract"]["prohibited_collapses"])

    assert q26["continuous_task_count"] is False
    assert q26["response_categories"] == [
        "small number",
        "moderate number",
        "large number",
    ]
    assert "business-reported task replacement or enhancement is not measured productivity" in prohibited


def test_btos_and_rps_are_registered_as_distinct_measurement_units() -> None:
    registry = _load_registry()
    contract = registry["construct_contract"]
    alignment = registry["cross_source_alignment"]
    prohibited = set(contract["prohibited_collapses"])

    assert contract["B_core_current"].startswith("business-reported")
    assert contract["A_worker"].startswith("worker-reported")
    assert alignment["rps_direct_equivalence"] is False
    assert "business AI use is not worker adoption" in prohibited
    assert "sector-level BTOS/RPS association is not an organizational effect" in prohibited
    assert "BTOS and RPS measures must not be combined into a composite adoption score" in prohibited


def test_btos_empirical_analysis_remains_unexecuted() -> None:
    status = _load_registry()["empirical_status"]

    assert status["observation_values_included"] is False
    assert status["source_ingestion_status"] == "not-executed"
    assert status["construct_alignment_status"] == "ready-for-versioned-source-ingestion"
    assert status["public_analysis_status"] == "blocked-pending-versioned-ingestion-crosswalk-and-reproduction"
