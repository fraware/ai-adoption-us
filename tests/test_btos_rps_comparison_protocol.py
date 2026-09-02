from __future__ import annotations

from json import loads
from pathlib import Path

ROOT = Path(__file__).parents[1]
REGISTRY = ROOT / "data" / "registry"
PROTOCOL = REGISTRY / "btos_rps_comparison_protocol_v1.json"
CROSSWALK = REGISTRY / "btos_rps_industry_crosswalk_v1.json"
RPS_SCOPE = REGISTRY / "rps_provider_catalog_scope.json"


def _load(path: Path) -> dict[str, object]:
    return loads(path.read_text())


def test_protocol_is_preregistered_and_empirically_unexecuted() -> None:
    protocol = _load(PROTOCOL)
    gate = protocol["execution_gate"]

    assert protocol["protocol_id"] == "btos-rps-industry-triangulation-v1"
    assert protocol["status"] == "preregistered-not-executed"
    assert gate["rps_observation_values_included"] is False
    assert gate["btos_selected_cycle_observation_values_examined"] is False
    assert gate["cross_source_statistics_included"] is False


def test_protocol_preserves_preregistration_rights_state_after_permission_change() -> None:
    protocol = _load(PROTOCOL)
    rps_scope = _load(RPS_SCOPE)
    gate = protocol["execution_gate"]

    assert (
        rps_scope["source_owner_permission_status"]
        == "granted_for_published_aggregate_project_use"
    )
    assert gate["current_rps_source_owner_permission_status"] == "unresolved"
    requirements = " ".join(gate["required_before_execution"])
    assert "unresolved permission state blocks execution" in requirements
    assert "transformed cross-source result" in requirements


def test_protocol_fixes_the_closest_construct_pair_without_collapse() -> None:
    protocol = _load(PROTOCOL)
    constructs = protocol["constructs"]
    btos = constructs["btos"]
    rps = constructs["rps"]
    boundaries = " ".join(constructs["non_equivalence"])

    assert (btos["question_id"], btos["answer_id"], btos["answer"]) == (7, 1, "Yes")
    assert btos["measurement_unit"] == "employer business"
    assert btos["technology_scope"] == "Artificial Intelligence as defined by BTOS"
    assert rps["metric_id"] == "adoption_work"
    assert rps["measurement_unit"] == "employed adult age 18-64"
    assert rps["technology_scope"] == "Generative AI"
    assert "do not substitute assisted-hours or reported-time-savings metrics" in rps[
        "series_selection_rule"
    ]
    assert "not a validation of a common adoption rate" in boundaries


def test_period_selection_is_mechanical_and_value_independent() -> None:
    period = _load(PROTOCOL)["period_selection"]
    fallback = period["fallback_selected_btos_cycle"]

    assert period["rps_target_period"] == "Q2 2026"
    assert period["rps_named_wave_month"] == "2026-05"
    assert "smallest absolute distance" in period["primary_rule"]
    assert "Ties select the earlier BTOS cycle" in period["primary_rule"]
    assert "Do not choose a cycle based on estimates" in period["primary_rule"]
    assert period["fallback_rule"].startswith(
        "If authoritative exact RPS Q2 2026 fieldwork dates remain unavailable"
    )
    assert fallback == {
        "cycle": "202611",
        "reference_start": "2026-05-04",
        "reference_end": "2026-05-17",
        "collection_start": "2026-05-18",
        "collection_end": "2026-05-31",
        "publication_date": "2026-06-04",
        "selection_basis": "date metadata only from the pinned National.xlsx workbook; Question 7 / Answer 1 sector values for this cycle were not inspected when v1 was registered",
    }
    assert "Do not use the already reproduced cycle 202617" in period["explicit_non_selection"]


def test_primary_sector_pool_is_exactly_the_primary_crosswalk_tier() -> None:
    protocol = _load(PROTOCOL)
    crosswalk = _load(CROSSWALK)
    eligibility = protocol["sector_eligibility"]
    primary = eligibility["primary"]

    primary_rows = [
        row
        for row in crosswalk["entries"]
        if row["mapping_status"] == "mapped" and row["comparability"] == "primary"
    ]
    limited_keys = {
        row["btos_sector_code"]
        for row in crosswalk["entries"]
        if row["mapping_status"] == "mapped" and row["comparability"] == "limited"
    }

    assert len(primary_rows) == 15
    assert primary["expected_crosswalk_pool_before_missingness_or_suppression"] == 15
    assert primary["minimum_analysis_n"] == 10
    assert primary["weighting"] == "unweighted across eligible industry categories"
    assert set(eligibility["limited_comparability_sensitivity"]["source_keys"]) == limited_keys
    assert limited_keys == {"11", "48", "52", "81"}


def test_suppression_and_unsupported_categories_fail_closed() -> None:
    eligibility = _load(PROTOCOL)["sector_eligibility"]
    exclusions = {row["source_or_target"]: row["reason"] for row in eligibility["always_excluded"]}

    assert set(exclusions) == {"XX", "public-administration"}
    assert "may not be redistributed" in exclusions["XX"]
    assert "no BTOS counterpart" in exclusions["public-administration"]
    assert "Never infer, complement, interpolate, or model" in eligibility["suppression_rule"]
    assert "never switch cycles" in eligibility["suppression_rule"]
    assert "do not substitute another RPS quarter or metric" in eligibility["missingness_rule"]


def test_statistics_are_fixed_descriptive_and_noncausal() -> None:
    protocol = _load(PROTOCOL)
    analysis = protocol["analysis"]
    uncertainty = protocol["uncertainty"]
    forbidden = set(analysis["forbidden_statistics_or_transformations_v1"])

    assert analysis["primary_statistic"]["name"] == "Spearman rank correlation"
    assert analysis["primary_statistic"]["tie_method"] == "average ranks"
    assert analysis["primary_statistic"]["weights"] == "none"
    assert analysis["secondary_statistic"]["name"] == "Pearson correlation"
    assert analysis["secondary_statistic"]["weights"] == "none"
    assert "percentage-point BTOS-minus-RPS adoption gaps" in forbidden
    assert "employment-weighted correlation" in forbidden
    assert "causal coefficients" in forbidden
    assert "composite BTOS-RPS adoption scores" in forbidden
    assert "Do not report p-values or confidence intervals" in uncertainty[
        "cross_source_inference_v1"
    ]


def test_limited_preanalysis_exposure_is_disclosed_without_posthoc_exclusion() -> None:
    exposure = _load(PROTOCOL)["pre_analysis_exposure"]

    assert exposure["fully_blinded"] is False
    assert set(exposure["exposed_rps_industries"]) == {
        "information",
        "management-of-companies-and-enterprises",
    }
    assert "No complete RPS industry vector was assembled" in exposure["disclosure"]
    assert "Do not exclude or specially treat" in exposure["governance_rule"]
    assert "not as fully blinded" in exposure["governance_rule"]


def test_protocol_cannot_publish_a_leaderboard_or_overclaim() -> None:
    reporting = _load(PROTOCOL)["reporting"]
    required = " ".join(reporting["required_outputs"])

    assert "no identity line" in required
    assert "business-versus-worker" in required
    assert "AI-versus-GenAI" in required
    assert "not publish a one-cycle industry leaderboard" in reporting["ranking_rule"]
    assert "Do not interpret agreement as validation or causality" in reporting[
        "interpretation_rule"
    ]


def test_v1_becomes_immutable_after_outcome_inspection() -> None:
    versioning = _load(PROTOCOL)["versioning"]

    assert "require a new protocol version" in versioning["immutable_after_values_rule"]
    assert "Do not overwrite v1" in versioning["immutable_after_values_rule"]
    assert (
        versioning["execution_status_after_registration"]
        == "blocked-pending-rps-rights-and-selected-cycle-btos-reproduction"
    )
