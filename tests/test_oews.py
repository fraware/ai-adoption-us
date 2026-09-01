from __future__ import annotations

import math

from genai_at_work.oews import (
    build_oews_composition,
    compare_cps_oews_worker_composition,
    cosine_similarity,
    oews_series_id,
    parse_bls_series_response,
    required_series_ids,
    spearman_rank_correlation,
)


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
    ]


def test_oews_series_id_matches_validated_bls_shape() -> None:
    assert oews_series_id("56--57", "110000") == "OEUN000000056--5711000001"


def test_required_series_ids_includes_total_and_each_occupation() -> None:
    assert required_series_ids(_industries(), _occupations()) == [
        "OEUN000000054--5500000001",
        "OEUN000000054--5511000001",
        "OEUN000000054--5513000001",
    ]


def test_parse_bls_series_response_preserves_missing_series() -> None:
    requested = ["series-a", "series-b"]
    payload = {
        "Results": {
            "series": [
                {
                    "seriesID": "series-a",
                    "data": [
                        {
                            "year": "2025",
                            "period": "A01",
                            "value": "1234",
                        }
                    ],
                },
                {"seriesID": "series-b", "data": []},
            ]
        }
    }
    assert parse_bls_series_response(
        payload, requested_series_ids=requested, year=2025
    ) == {"series-a": 1234.0, "series-b": None}


def test_build_oews_composition_normalizes_supported_vector() -> None:
    values = {
        "OEUN000000054--5500000001": 100.0,
        "OEUN000000054--5511000001": 60.0,
        "OEUN000000054--5513000001": 40.0,
    }
    row = build_oews_composition(
        values,
        industry_entries=_industries(),
        occupation_entries=_occupations(),
    )[0]
    assert row.supported is True
    assert row.coverage == 1.0
    assert row.worker_weights == {"occupation-a": 0.6, "occupation-b": 0.4}
    assert math.isclose(sum(row.worker_weights.values()), 1.0)


def test_build_oews_composition_suppresses_below_coverage_gate() -> None:
    values = {
        "OEUN000000054--5500000001": 100.0,
        "OEUN000000054--5511000001": 90.0,
        "OEUN000000054--5513000001": None,
    }
    row = build_oews_composition(
        values,
        industry_entries=_industries(),
        occupation_entries=_occupations(),
        coverage_gate=0.98,
    )[0]
    assert row.supported is False
    assert row.coverage == 0.9
    assert row.worker_weights is None
    assert row.missing_occupations == ("occupation-b",)


def test_rounded_major_groups_can_slightly_exceed_total() -> None:
    values = {
        "OEUN000000054--5500000001": 99.0,
        "OEUN000000054--5511000001": 60.0,
        "OEUN000000054--5513000001": 40.0,
    }
    row = build_oews_composition(
        values,
        industry_entries=_industries(),
        occupation_entries=_occupations(),
    )[0]
    assert row.raw_sum_to_total_ratio is not None
    assert row.raw_sum_to_total_ratio > 1.0
    assert row.coverage == 1.0
    assert row.supported is True


def test_rank_and_cosine_metrics() -> None:
    assert math.isclose(spearman_rank_correlation([1, 2, 3], [2, 4, 6]) or 0, 1.0)
    assert math.isclose(cosine_similarity([1, 0], [1, 0]) or 0, 1.0)


def test_compare_cps_oews_worker_composition() -> None:
    values = {
        "OEUN000000054--5500000001": 100.0,
        "OEUN000000054--5511000001": 60.0,
        "OEUN000000054--5513000001": 40.0,
    }
    oews_row = build_oews_composition(
        values,
        industry_entries=_industries(),
        occupation_entries=_occupations(),
    )[0]
    cps = [
        {
            "industry_id": "industry-a",
            "worker_weights": {"occupation-a": 0.55, "occupation-b": 0.45},
        }
    ]
    comparison = compare_cps_oews_worker_composition(
        [oews_row], cps, occupation_ids=["occupation-a", "occupation-b"]
    )[0]
    assert math.isclose(comparison.l1_distance or 0, 0.1)
    assert comparison.top_occupation_agreement is True
    assert comparison.cps_top_occupation == "occupation-a"
    assert comparison.oews_top_occupation == "occupation-a"
