from __future__ import annotations

from genai_at_work.longitudinal import AuditRecord
from genai_at_work.oews import OewsCompositionRow
from genai_at_work.oews_rps import (
    adoption_counterfactual_bounds,
    compare_cps_oews_adoption_residuals,
    summarize_cps_oews_adoption_comparison,
)

PERIOD = "2025-Q2"


def _record(entity_type: str, entity_id: str, entity_index: int, value: float) -> AuditRecord:
    return AuditRecord(
        entity_type=entity_type,
        entity_id=entity_id,
        entity_index=entity_index,
        metric_id="adoption_work",
        period=PERIOD,
        value=value,
        series_id=f"series-{entity_type}-{entity_id}",
        audit_scope="synthetic_test",
        rights_status="synthetic",
    )


def _oews(
    *,
    occupation_employment: dict[str, float | None],
    total: float,
    worker_weights: dict[str, float] | None,
    observed_sum: float | None = None,
    comparability: str = "primary",
) -> OewsCompositionRow:
    missing = tuple(key for key, value in occupation_employment.items() if value is None)
    observed = (
        observed_sum
        if observed_sum is not None
        else sum(value for value in occupation_employment.values() if value is not None)
    )
    return OewsCompositionRow(
        industry_index=1,
        industry_id="industry-1",
        industry_name="Industry 1",
        oews_industry_code="000001",
        comparability=comparability,
        comparability_reason=None,
        total_employment=total,
        observed_major_group_employment=observed,
        raw_sum_to_total_ratio=observed / total,
        coverage=min(1.0, observed / total),
        supported=True,
        missing_occupations=missing,
        occupation_employment=occupation_employment,
        worker_weights=worker_weights,
    )


def test_complete_oews_vector_produces_exact_counterfactual() -> None:
    occupation_ids = ["a", "b"]
    records = [
        _record("industry", "industry-1", 1, 60.0),
        _record("occupation", "a", 1, 10.0),
        _record("occupation", "b", 2, 50.0),
    ]
    row = _oews(
        occupation_employment={"a": 40.0, "b": 60.0},
        total=100.0,
        worker_weights={"a": 0.4, "b": 0.6},
    )
    result = adoption_counterfactual_bounds(
        [row], records, period=PERIOD, occupation_ids=occupation_ids
    )[0]
    assert result.supported is True
    assert result.point_identified is True
    assert result.predicted_adoption_point == 34.0
    assert result.residual_point == 26.0
    assert result.residual_sign_identification == "positive"


def test_multiple_unpublished_cells_produce_linear_functional_interval() -> None:
    occupation_ids = ["a", "b", "c", "d"]
    records = [
        _record("industry", "industry-1", 1, 50.0),
        _record("occupation", "a", 1, 10.0),
        _record("occupation", "b", 2, 20.0),
        _record("occupation", "c", 3, 80.0),
        _record("occupation", "d", 4, 90.0),
    ]
    row = _oews(
        occupation_employment={"a": 40.0, "b": None, "c": None, "d": 40.0},
        total=100.0,
        worker_weights={"a": 0.5, "d": 0.5},
    )
    result = adoption_counterfactual_bounds(
        [row], records, period=PERIOD, occupation_ids=occupation_ids
    )[0]
    assert result.supported is True
    assert result.point_identified is False
    assert result.residual_unpublished_mass_share == 0.2
    assert result.predicted_adoption_lower == 44.0
    assert result.predicted_adoption_upper == 56.0
    assert result.predicted_adoption_point is None
    assert result.residual_lower == -6.0
    assert result.residual_upper == 6.0
    assert result.residual_sign_identification == "contains_zero"


def test_single_unpublished_cell_is_point_identified_by_published_total() -> None:
    occupation_ids = ["a", "b", "c"]
    records = [
        _record("industry", "industry-1", 1, 50.0),
        _record("occupation", "a", 1, 10.0),
        _record("occupation", "b", 2, 50.0),
        _record("occupation", "c", 3, 90.0),
    ]
    row = _oews(
        occupation_employment={"a": 40.0, "b": None, "c": 40.0},
        total=100.0,
        worker_weights={"a": 0.5, "c": 0.5},
    )
    result = adoption_counterfactual_bounds(
        [row], records, period=PERIOD, occupation_ids=occupation_ids
    )[0]
    assert result.point_identified is True
    assert result.predicted_adoption_lower == 50.0
    assert result.predicted_adoption_upper == 50.0
    assert result.predicted_adoption_point == 50.0
    assert result.residual_point == 0.0


def test_incoherent_rounding_case_fails_closed_as_unsupported() -> None:
    occupation_ids = ["a", "b"]
    records = [
        _record("industry", "industry-1", 1, 50.0),
        _record("occupation", "a", 1, 10.0),
        _record("occupation", "b", 2, 50.0),
    ]
    row = _oews(
        occupation_employment={"a": 101.0, "b": None},
        total=100.0,
        worker_weights={"a": 1.0},
        observed_sum=101.0,
    )
    result = adoption_counterfactual_bounds(
        [row], records, period=PERIOD, occupation_ids=occupation_ids
    )[0]
    assert result.supported is False
    assert result.predicted_adoption_point is None
    assert result.unsupported_reason is not None
    assert "rounding model" in result.unsupported_reason


def test_cps_oews_comparison_preserves_partial_identification() -> None:
    occupation_ids = ["a", "b", "c", "d"]
    records = [
        _record("industry", "industry-1", 1, 50.0),
        _record("occupation", "a", 1, 10.0),
        _record("occupation", "b", 2, 20.0),
        _record("occupation", "c", 3, 80.0),
        _record("occupation", "d", 4, 90.0),
    ]
    row = _oews(
        occupation_employment={"a": 40.0, "b": None, "c": None, "d": 40.0},
        total=100.0,
        worker_weights={"a": 0.5, "d": 0.5},
    )
    bounds = adoption_counterfactual_bounds(
        [row], records, period=PERIOD, occupation_ids=occupation_ids
    )
    cps = [
        {
            "industry_id": "industry-1",
            "period": PERIOD,
            "metric_id": "adoption_work",
            "suppressed": False,
            "occupation_adjusted_industry_context_residual": 5.0,
        }
    ]
    comparison = compare_cps_oews_adoption_residuals(cps, bounds, period=PERIOD)[0]
    assert comparison.cps_residual == 5.0
    assert comparison.oews_residual_lower == -6.0
    assert comparison.oews_residual_upper == 6.0
    assert comparison.direction_agreement is None
    assert comparison.magnitude_relation == "overlaps_cps_magnitude"
    assert comparison.cps_residual_inside_oews_interval is True

    summary = summarize_cps_oews_adoption_comparison([comparison], period=PERIOD)
    assert summary["primary_industry_count"] == 1
    assert summary["partially_identified_primary_count"] == 1
    assert summary["direction_indeterminate_count"] == 1
    assert summary["cps_residual_inside_oews_interval_count"] == 1
