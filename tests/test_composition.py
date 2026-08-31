from __future__ import annotations

import pytest

from genai_at_work.composition import composition_residuals
from genai_at_work.cps import IndustryComposition


def _composition(**overrides):
    values = dict(
        industry_id="information",
        industry_index=9,
        worker_coverage=1.0,
        actual_hours_valid_worker_coverage=1.0,
        actual_hours_mapping_coverage=1.0,
        usual_hours_valid_worker_coverage=1.0,
        usual_hours_mapping_coverage=1.0,
        worker_weights={"occ-a": 0.5, "occ-b": 0.5},
        actual_hour_weights={"occ-a": 0.25, "occ-b": 0.75},
        usual_hour_weights={"occ-a": 0.4, "occ-b": 0.6},
        worker_suppressed=False,
        actual_hours_suppressed=False,
        usual_hours_suppressed=False,
    )
    values.update(overrides)
    return IndustryComposition(**values)


def _records(metric: str, industry_value: float, occ_a: float, occ_b: float):
    return [
        {"entity_type": "industry", "entity_id": "information", "metric_id": metric, "period": "2026-Q2", "value": industry_value},
        {"entity_type": "occupation", "entity_id": "occ-a", "metric_id": metric, "period": "2026-Q2", "value": occ_a},
        {"entity_type": "occupation", "entity_id": "occ-b", "metric_id": metric, "period": "2026-Q2", "value": occ_b},
    ]


def test_adoption_uses_worker_weights():
    row = composition_residuals(
        [_composition()],
        _records("adoption_work", 60.0, 20.0, 40.0),
        period="2026-Q2",
        metric_id="adoption_work",
    )[0]
    assert row.weight_basis == "CPS worker share"
    assert row.predicted_from_occupation_mix == pytest.approx(30.0)
    assert row.occupation_adjusted_industry_context_residual == pytest.approx(30.0)


def test_hour_share_metrics_use_actual_hour_weights():
    row = composition_residuals(
        [_composition()],
        _records("assisted_hours_share", 35.0, 10.0, 30.0),
        period="2026-Q2",
        metric_id="assisted_hours_share",
    )[0]
    assert row.weight_basis == "CPS actual main-job hour share"
    assert row.predicted_from_occupation_mix == pytest.approx(25.0)
    assert row.occupation_adjusted_industry_context_residual == pytest.approx(10.0)


def test_usual_hours_are_explicit_sensitivity_only():
    row = composition_residuals(
        [_composition()],
        _records("reported_time_savings_share", 8.0, 2.0, 6.0),
        period="2026-Q2",
        metric_id="reported_time_savings_share",
        hours_basis="usual",
    )[0]
    assert "sensitivity" in row.weight_basis
    assert row.predicted_from_occupation_mix == pytest.approx(4.4)


def test_suppression_propagates_as_null_residual():
    comp = _composition(worker_weights=None, worker_suppressed=True, worker_coverage=0.95)
    row = composition_residuals(
        [comp],
        _records("adoption_work", 60.0, 20.0, 40.0),
        period="2026-Q2",
        metric_id="adoption_work",
    )[0]
    assert row.suppressed is True
    assert row.predicted_from_occupation_mix is None
    assert row.occupation_adjusted_industry_context_residual is None
    assert row.coverage == pytest.approx(0.95)


def test_missing_occupation_value_fails_closed():
    records = _records("adoption_work", 60.0, 20.0, 40.0)[:-1]
    with pytest.raises(ValueError, match="missing occupation RPS values"):
        composition_residuals(
            [_composition()],
            records,
            period="2026-Q2",
            metric_id="adoption_work",
        )


def test_unsupported_metric_is_rejected():
    with pytest.raises(ValueError, match="unsupported composition metric"):
        composition_residuals([], [], period="2026-Q2", metric_id="productivity")
