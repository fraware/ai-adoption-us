from __future__ import annotations

import math

from genai_at_work.cps import CPSPerson
from genai_at_work.cps_domain_diagnostics import (
    build_cps_domain_diagnostics,
)


def _person(
    *,
    month: str,
    industry_id: str,
    industry_index: int,
    occupation_id: str,
    occupation_index: int,
    weight: float,
) -> CPSPerson:
    return CPSPerson(
        month=month,
        industry_id=industry_id,
        industry_index=industry_index,
        occupation_id=occupation_id,
        occupation_index=occupation_index,
        worker_weight=weight,
        actual_hours=40.0,
        usual_hours=40.0,
    )


def test_domain_diagnostics_capture_monthly_instability_and_weight_dispersion() -> None:
    people: list[CPSPerson] = []
    for month in ("apr", "may", "jun"):
        if month == "apr":
            people.extend(
                [
                    _person(
                        month=month,
                        industry_id="industry-a",
                        industry_index=1,
                        occupation_id="occupation-a",
                        occupation_index=1,
                        weight=1.0,
                    ),
                    _person(
                        month=month,
                        industry_id="industry-a",
                        industry_index=1,
                        occupation_id="occupation-a",
                        occupation_index=1,
                        weight=1.0,
                    ),
                ]
            )
        else:
            people.extend(
                [
                    _person(
                        month=month,
                        industry_id="industry-a",
                        industry_index=1,
                        occupation_id="occupation-b",
                        occupation_index=2,
                        weight=1.0,
                    ),
                    _person(
                        month=month,
                        industry_id="industry-a",
                        industry_index=1,
                        occupation_id="occupation-b",
                        occupation_index=2,
                        weight=1.0,
                    ),
                ]
            )

    row = build_cps_domain_diagnostics(
        people,
        occupation_ids=("occupation-a", "occupation-b"),
    )[0]

    assert row.person_month_count == 6
    assert row.minimum_month_person_count == 2
    assert row.maximum_month_person_count == 2
    assert row.monthly_person_counts == {"apr": 2, "jun": 2, "may": 2}
    assert math.isclose(row.kish_effective_person_months, 6.0)
    assert math.isclose(row.kish_fraction_of_person_months, 1.0)
    assert math.isclose(row.maximum_person_month_weight_share, 1 / 6)
    assert row.monthly_top_occupation_agreement is False
    assert math.isclose(row.maximum_pairwise_month_l1 or 0.0, 2.0)
    assert math.isclose(row.maximum_month_to_pooled_l1 or 0.0, 4 / 3)


def test_domain_diagnostics_detect_weight_concentration() -> None:
    people = [
        _person(
            month="apr",
            industry_id="industry-a",
            industry_index=1,
            occupation_id="occupation-a",
            occupation_index=1,
            weight=9.0,
        ),
        _person(
            month="apr",
            industry_id="industry-a",
            industry_index=1,
            occupation_id="occupation-a",
            occupation_index=1,
            weight=1.0,
        ),
    ]
    row = build_cps_domain_diagnostics(
        people,
        occupation_ids=("occupation-a",),
    )[0]

    assert math.isclose(row.kish_effective_person_months, 100 / 82)
    assert math.isclose(row.maximum_person_month_weight_share, 0.9)
