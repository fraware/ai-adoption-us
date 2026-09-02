from __future__ import annotations

import json
from pathlib import Path

import pytest

from genai_at_work.cps_design_variance import (
    composition_covariance_identifiability,
    validate_public_design_variance_decision,
)

ROOT = Path(__file__).resolve().parents[1]
DECISION_PATH = ROOT / "data" / "registry" / "cps_design_variance_decision.json"


def _decision() -> dict[str, object]:
    payload = json.loads(DECISION_PATH.read_text())
    assert isinstance(payload, dict)
    return payload


def test_22_part_composition_marginals_leave_209_covariance_parameters_unidentified() -> None:
    result = composition_covariance_identifiability(22)
    assert result.symmetric_parameter_count == 253
    assert result.simplex_constraint_count == 22
    assert result.parameters_after_simplex_constraint == 231
    assert result.marginal_variance_count == 22
    assert result.unidentified_parameters_after_marginals == 209


def test_identifiability_contract_rejects_too_small_dimension() -> None:
    with pytest.raises(ValueError, match="dimension >= 3"):
        composition_covariance_identifiability(2)


def test_public_design_variance_registry_fails_closed_for_full_covariance() -> None:
    decision = _decision()
    validate_public_design_variance_decision(decision)

    public_path = decision["public_variance_path"]
    publication = decision["publication"]
    quarter = decision["quarter_pooling"]
    assert isinstance(public_path, dict)
    assert isinstance(publication, dict)
    assert isinstance(quarter, dict)

    assert public_path["basic_monthly_public_replicate_system_identified"] is False
    assert public_path["gvf_scalar_or_marginal_approximation_available"] is True
    assert public_path["gvf_full_composition_covariance_identified"] is False
    assert publication["design_based_composition_interval_allowed"] is False
    assert publication["pooled_quarter_design_based_interval_allowed"] is False
    assert publication["occupation_adjusted_rps_residual_interval_allowed"] is False
    assert publication["gvf_marginal_benchmark_allowed"] is True
    assert quarter["required_month_level_dimension"] == 66
    assert quarter["requires_cross_month_covariance_blocks"] is True
    assert quarter["independent_month_assumption_allowed"] is False


def test_registry_pins_internal_sdr_and_rotation_overlap_evidence() -> None:
    decision = _decision()
    evidence = decision["official_method_evidence"]
    assert isinstance(evidence, dict)
    direct = evidence["direct_variance_method"]
    rotation = evidence["rotation_overlap"]
    gvf = evidence["gvf"]
    assert isinstance(direct, dict)
    assert isinstance(rotation, dict)
    assert isinstance(gvf, dict)

    assert direct["method"] == "successive-difference replication"
    assert direct["replicate_count"] == 160
    assert direct["rotation_group_in_replication_sort"] is True
    assert direct["rotation_group_variance_and_covariance_supported_in_internal_method"] is True
    assert rotation["pattern"] == "4-8-4"
    assert rotation["consecutive_month_sample_unit_overlap_fraction"] == 0.75
    assert rotation["same_month_consecutive_year_sample_unit_overlap_fraction"] == 0.5
    assert gvf["period_and_change_factors_available"] is True
    assert gvf["period_factor_basis"] == (
        "historical correlations with an equal-monthly-variance approximation"
    )
    assert gvf["borrowing_requires_approximately_similar_design_effects"] is True


def test_validator_rejects_silent_promotion_to_design_based_publication() -> None:
    decision = _decision()
    publication = decision["publication"]
    assert isinstance(publication, dict)
    publication["pooled_quarter_design_based_interval_allowed"] = True
    with pytest.raises(ValueError, match="must remain false"):
        validate_public_design_variance_decision(decision)


def test_validator_rejects_claim_that_gvf_identifies_full_covariance() -> None:
    decision = _decision()
    public_path = decision["public_variance_path"]
    assert isinstance(public_path, dict)
    public_path["gvf_full_composition_covariance_identified"] = True
    with pytest.raises(ValueError, match="GVF must not"):
        validate_public_design_variance_decision(decision)
