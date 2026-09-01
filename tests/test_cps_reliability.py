from __future__ import annotations

import math

from genai_at_work.cps import CPSPerson
from genai_at_work.cps_reliability import (
    build_period_reliability,
    compare_period_reliability,
    kish_weight_dispersion_effective_n,
    l1_distance,
    verify_reference_vectors,
)


def _person(month: str, occupation: str, weight: float = 1.0) -> CPSPerson:
    return CPSPerson(
        month=month,
        industry_id="industry-a",
        industry_index=1,
        occupation_id=occupation,
        occupation_index=1 if occupation == "occupation-a" else 2,
        worker_weight=weight,
        actual_hours=40.0,
        usual_hours=40.0,
    )


def test_kish_weight_dispersion_effective_n() -> None:
    assert math.isclose(kish_weight_dispersion_effective_n([1.0, 1.0, 1.0]), 3.0)
    assert kish_weight_dispersion_effective_n([]) == 0.0
    assert kish_weight_dispersion_effective_n([1.0, 10.0]) < 2.0


def test_l1_sparse_vectors() -> None:
    assert math.isclose(
        l1_distance({"a": 0.6, "b": 0.4}, {"a": 0.5, "c": 0.5}),
        1.0,
    )


def test_build_period_reliability_tracks_month_sensitivity() -> None:
    people = [
        _person("apr", "occupation-a"),
        _person("apr", "occupation-a"),
        _person("may", "occupation-a"),
        _person("may", "occupation-b"),
        _person("jun", "occupation-b"),
        _person("jun", "occupation-b"),
    ]
    row = build_period_reliability(people, months=("apr", "may", "jun"))[0]
    assert row.person_month_count == 6
    assert math.isclose(row.kish_weight_dispersion_effective_n, 6.0)
    assert row.monthly_person_month_counts == {"apr": 2, "may": 2, "jun": 2}
    assert math.isclose(row.maximum_pairwise_month_l1, 2.0)
    assert math.isclose(row.maximum_monthly_l1_to_quarter, 1.0)
    assert math.isclose(row.maximum_leave_one_month_out_l1_to_quarter, 0.5)
    assert row.all_monthly_tops_match_quarter is False


def test_compare_period_reliability_uses_within_quarter_envelope() -> None:
    period = build_period_reliability(
        [
            _person("apr", "occupation-a"),
            _person("may", "occupation-a"),
            _person("jun", "occupation-b"),
        ],
        months=("apr", "may", "jun"),
    )
    result = compare_period_reliability(
        period,
        period,
        quarter_weights_2025={"industry-a": {"occupation-a": 2 / 3, "occupation-b": 1 / 3}},
        quarter_weights_2026={"industry-a": {"occupation-a": 2 / 3, "occupation-b": 1 / 3}},
    )[0]
    assert result.l1_q2_2025_to_q2_2026 == 0.0
    assert result.year_over_year_exceeds_within_quarter_envelope is False
    assert result.tops_match_across_quarters is True


def test_verify_reference_vectors_accepts_sparse_zero_equivalence() -> None:
    verify_reference_vectors(
        {"industry-a": {"occupation-a": 1.0}},
        [{"industry_id": "industry-a", "worker_weights": {"occupation-a": 1.0}}],
    )
