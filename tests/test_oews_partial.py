from __future__ import annotations

import math

from genai_at_work.oews import build_oews_composition
from genai_at_work.oews_partial import l1_identification_bounds


def _industries() -> list[dict[str, object]]:
    return [
        {
            "entity_index": 1,
            "entity_id": "industry-a",
            "entity_name": "Industry A",
            "oews_industry_code": "54--55",
            "comparability": "primary",
        }
    ]


def _occupations() -> list[dict[str, object]]:
    return [
        {
            "entity_index": 1,
            "entity_id": "occupation-a",
            "entity_name": "Occupation A",
            "oews_occupation_code": "110000",
        },
        {
            "entity_index": 2,
            "entity_id": "occupation-b",
            "entity_name": "Occupation B",
            "oews_occupation_code": "130000",
        },
        {
            "entity_index": 3,
            "entity_id": "occupation-c",
            "entity_name": "Occupation C",
            "oews_occupation_code": "150000",
        },
    ]


def _cps() -> list[dict[str, object]]:
    return [
        {
            "industry_id": "industry-a",
            "worker_weights": {
                "occupation-a": 0.55,
                "occupation-b": 0.25,
                "occupation-c": 0.20,
            },
        }
    ]


def test_complete_oews_vector_collapses_l1_interval() -> None:
    values = {
        "OEUN000000054--5500000001": 100.0,
        "OEUN000000054--5511000001": 60.0,
        "OEUN000000054--5513000001": 25.0,
        "OEUN000000054--5515000001": 15.0,
    }
    row = build_oews_composition(
        values,
        industry_entries=_industries(),
        occupation_entries=_occupations(),
    )[0]
    bound = l1_identification_bounds(
        [row],
        _cps(),
        occupation_ids=["occupation-a", "occupation-b", "occupation-c"],
    )[0]

    assert bound.bounds_supported is True
    assert bound.point_identified is True
    assert math.isclose(bound.l1_lower_bound or 0.0, 0.10)
    assert math.isclose(bound.l1_upper_bound or 0.0, 0.10)
    assert bound.l1_bound_width == 0.0


def test_missing_oews_cells_produce_sharp_allocation_bounds() -> None:
    values = {
        "OEUN000000054--5500000001": 100.0,
        "OEUN000000054--5511000001": 60.0,
        "OEUN000000054--5513000001": None,
        "OEUN000000054--5515000001": None,
    }
    row = build_oews_composition(
        values,
        industry_entries=_industries(),
        occupation_entries=_occupations(),
        coverage_gate=0.50,
    )[0]
    bound = l1_identification_bounds(
        [row],
        _cps(),
        occupation_ids=["occupation-a", "occupation-b", "occupation-c"],
    )[0]

    assert bound.bounds_supported is True
    assert bound.point_identified is False
    assert bound.missing_occupation_count == 2
    assert math.isclose(bound.residual_unpublished_mass_share or 0.0, 0.40)
    assert math.isclose(bound.cps_mass_in_missing_occupations or 0.0, 0.45)
    assert math.isclose(bound.l1_lower_bound or 0.0, 0.10)
    assert math.isclose(bound.l1_upper_bound or 0.0, 0.50)
    assert math.isclose(bound.l1_bound_width or 0.0, 0.40)


def test_missing_oews_bound_fails_closed_when_published_sum_exceeds_total() -> None:
    values = {
        "OEUN000000054--5500000001": 100.0,
        "OEUN000000054--5511000001": 101.0,
        "OEUN000000054--5513000001": None,
        "OEUN000000054--5515000001": None,
    }
    row = build_oews_composition(
        values,
        industry_entries=_industries(),
        occupation_entries=_occupations(),
        coverage_gate=0.98,
    )[0]
    bound = l1_identification_bounds(
        [row],
        _cps(),
        occupation_ids=["occupation-a", "occupation-b", "occupation-c"],
    )[0]

    assert bound.bounds_supported is False
    assert bound.l1_lower_bound is None
    assert bound.l1_upper_bound is None
    assert bound.unsupported_reason is not None
    assert "rounding model" in bound.unsupported_reason
