from __future__ import annotations

from json import loads
from pathlib import Path

ROOT = Path(__file__).parents[1]
REGISTRY = ROOT / "data" / "registry"
DERIVED = ROOT / "data" / "derived" / "btos"
SOURCE = REGISTRY / "btos_core_ai_202611_source_v1.json"
CHECKPOINT = DERIVED / "btos_core_ai_202611.json"
PROTOCOL = REGISTRY / "btos_rps_comparison_protocol_v1.json"
EXECUTION = REGISTRY / "btos_rps_comparison_execution_state_v1.json"
BASELINE_SOURCE = REGISTRY / "btos_core_ai_202617_source_v1.json"


def _load(path: Path) -> dict[str, object]:
    return loads(path.read_text())


def test_202611_was_selected_under_canonical_preregistration_before_outcomes() -> None:
    source = _load(SOURCE)
    selection = source["period_selection_provenance"]

    assert source["cycle"] == "202611"
    assert selection["protocol"] == "data/registry/btos_rps_comparison_protocol_v1.json"
    assert selection["protocol_canonical_commit"] == "854db8d637e5f7896ef2f779692d9451d8971e55"
    assert selection["protocol_status_before_outcome_inspection"] == "preregistered-not-executed"
    assert selection["authoritative_exact_rps_fieldwork_dates_resolution"].startswith("not-resolved")
    assert selection["rule_invoked"] == "registered May-midpoint fallback"
    assert selection["fallback_anchor"] == "2026-05-16"
    assert selection["selected_cycle"] == "202611"
    assert "selected before inspecting" in selection["selection_basis"]
    assert "only after the protocol was merged" in selection["outcome_inspection_ordering"]


def test_202611_dates_match_registered_fallback_cycle() -> None:
    source = _load(SOURCE)

    assert source["dates"] == {
        "collection_start": "2026-05-18",
        "collection_end": "2026-05-31",
        "reference_start": "2026-05-04",
        "reference_end": "2026-05-17",
        "publication_date": "2026-06-04",
    }


def test_202611_uses_same_pinned_census_bytes_as_baseline_checkpoint() -> None:
    source = _load(SOURCE)["source_files"]
    baseline = _load(BASELINE_SOURCE)["source_files"]

    for key in ("national", "sector"):
        assert source[key]["url"] == baseline[key]["url"]
        assert source[key]["filename"] == baseline[key]["filename"]
        assert source[key]["byte_size"] == baseline[key]["byte_size"]
        assert source[key]["sha256"] == baseline[key]["sha256"]


def test_national_checkpoint_preserves_published_rounding_residual() -> None:
    source = _load(SOURCE)
    checkpoint = _load(CHECKPOINT)
    distribution = source["national_response_distribution"]

    assert checkpoint["national"] == {
        "estimate_pct": 20.6,
        "standard_error_pp": 0.29,
        "suppression_code": None,
    }
    assert distribution["answer_1_yes_pct"] == 20.6
    assert distribution["answer_2_no_pct"] == 69.6
    assert distribution["answer_3_do_not_know_pct"] == 9.9
    assert distribution["published_total_pct"] == 100.1
    assert "no component is renormalized or altered" in distribution["rounding_note"]


def test_202611_sector_suppression_is_source_native_and_fail_closed() -> None:
    checkpoint = _load(CHECKPOINT)
    sectors = checkpoint["sectors"]
    suppressed = {
        row["btos_sector_code"]: row
        for row in sectors
        if row["suppression_code"] == "S"
    }

    assert len(sectors) == 20
    assert set(suppressed) == {"11", "55"}
    for row in suppressed.values():
        assert row["estimate_pct"] is None
        assert row["standard_error_pp"] is None

    xx = next(row for row in sectors if row["btos_sector_code"] == "XX")
    assert xx["entity_id"] is None
    assert xx["comparability"] == "unclassified"
    assert xx["estimate_pct"] == 30.7
    assert xx["standard_error_pp"] == 1.91


def test_202611_btos_only_readiness_matches_preregistered_tiers() -> None:
    checkpoint = _load(CHECKPOINT)
    readiness = checkpoint["analysis_readiness"]

    assert readiness == {
        "primary_crosswalk_sectors": 15,
        "primary_btos_published_non_suppressed": 14,
        "primary_btos_suppressed_source_keys": ["55"],
        "limited_crosswalk_sectors": 4,
        "limited_btos_published_non_suppressed": 3,
        "limited_btos_suppressed_source_keys": ["11"],
        "rps_eligibility_not_evaluated": True,
    }


def test_execution_state_advances_without_overwriting_protocol_history() -> None:
    protocol = _load(PROTOCOL)
    execution = _load(EXECUTION)

    assert protocol["status"] == "preregistered-not-executed"
    assert protocol["execution_gate"]["btos_selected_cycle_observation_values_examined"] is False
    assert execution["protocol_canonical_commit"] == "854db8d637e5f7896ef2f779692d9451d8971e55"
    assert execution["status"] == "btos-selected-cycle-reproduced-rps-blocked"
    assert execution["period_resolution"]["selection_was_value_independent"] is True
    assert execution["btos_execution"]["selected_cycle_observation_values_examined"] is True
    assert execution["rps_execution"]["industry_observation_vector_retrieved"] is False
    assert execution["rps_execution"]["rights_gate_blocks_execution"] is True
    assert execution["cross_source_execution"]["statistics_computed"] is False
    assert execution["governance"]["protocol_v1_modified_after_outcome_inspection"] is False


def test_202611_checkpoint_contains_no_rps_or_cross_source_result() -> None:
    source = _load(SOURCE)
    checkpoint = _load(CHECKPOINT)
    execution = _load(EXECUTION)

    assert source["rps_values_included"] is False
    assert source["cross_source_statistics_included"] is False
    assert checkpoint["rps_values_included"] is False
    assert checkpoint["cross_source_statistics_included"] is False
    assert execution["rps_execution"]["industry_observation_vector_retrieved"] is False
    assert execution["cross_source_execution"]["sector_pairs_assembled"] is False
    assert execution["cross_source_execution"]["leaderboard_created"] is False
