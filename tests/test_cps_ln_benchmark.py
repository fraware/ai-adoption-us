from __future__ import annotations

import gzip
from pathlib import Path

import pytest

from genai_at_work.cps import FIXED_WIDTH_FIELDS_2026
from genai_at_work.cps_ln_benchmark import (
    MANAGEMENT_PROFESSIONAL_SERIES_ID,
    PWCMPWGT_FIXED_WIDTH_2026,
    extract_bls_api_standard_error,
    extract_ln_standard_error,
    month_period,
    parse_bls_api_month_value,
    published_rounding_matches,
    reconstruct_management_professional_employment,
)


def _fixed_width_record(**values: str) -> str:
    width = max(
        max(end for _, end in FIXED_WIDTH_FIELDS_2026.values()),
        PWCMPWGT_FIXED_WIDTH_2026[1],
    )
    chars = [" "] * width
    for field, value in values.items():
        if field == "PWCMPWGT":
            start, end = PWCMPWGT_FIXED_WIDTH_2026
        else:
            start, end = FIXED_WIDTH_FIELDS_2026[field]
        if len(value) > end - start:
            raise ValueError(f"fixture value too wide for {field}")
        chars[start:end] = list(value.rjust(end - start))
    return "".join(chars) + "\n"


def _raw_weight(persons: float) -> str:
    return str(round(persons * 10_000)).rjust(10, "0")


def _api_payload(*, with_aspects: bool = True) -> dict[str, object]:
    observation: dict[str, object] = {
        "year": "2026",
        "period": "M07",
        "value": "69,913",
    }
    if with_aspects:
        observation["aspects"] = [
            {
                "name": "Standard Error",
                "value": "447.5",
                "footnotes": [{"code": "P", "text": "Preliminary."}],
            }
        ]
    return {
        "status": "REQUEST_SUCCEEDED",
        "message": [],
        "Results": {
            "series": [
                {
                    "seriesID": "LNU02032201",
                    "data": [
                        observation,
                        {"year": "2026", "period": "M06", "value": "70366"},
                    ],
                }
            ]
        },
    }


def test_month_period_maps_month_abbreviations() -> None:
    assert month_period("jul") == "M07"
    assert month_period(" JUL ") == "M07"
    with pytest.raises(ValueError, match="unsupported month"):
        month_period("jly")


def test_extract_ln_standard_error_filters_exact_series_period(tmp_path: Path) -> None:
    path = tmp_path / "ln.aspect"
    path.write_text(
        "series_id\tyear\tperiod\taspect_type\tvalue\tfootnote_codes\n"
        "LNU02032201\t2026\tM06\tE\t451.2\t\n"
        "LNU02032201\t2026\tM07\tE\t447.5\tP\n"
        "LNU02032204\t2026\tM07\tE\t300.0\t\n"
    )
    result = extract_ln_standard_error(
        path,
        series_id=MANAGEMENT_PROFESSIONAL_SERIES_ID,
        year=2026,
        period="M07",
    )
    assert result.value == 447.5
    assert result.aspect_type == "E"
    assert result.footnote_code == "P"


def test_extract_ln_standard_error_fails_closed_on_duplicate_rows(tmp_path: Path) -> None:
    path = tmp_path / "ln.aspect"
    path.write_text(
        "series_id\tyear\tperiod\taspect_type\tvalue\n"
        "LNU02032201\t2026\tM07\tE\t447.5\n"
        "LNU02032201\t2026\tM07\tE\t448.0\n"
    )
    with pytest.raises(ValueError, match="exactly one standard-error"):
        extract_ln_standard_error(
            path,
            series_id=MANAGEMENT_PROFESSIONAL_SERIES_ID,
            year=2026,
            period="M07",
        )


def test_parse_bls_api_month_value_requires_exact_observation() -> None:
    assert (
        parse_bls_api_month_value(
            _api_payload(),
            series_id=MANAGEMENT_PROFESSIONAL_SERIES_ID,
            year=2026,
            period="M07",
        )
        == 69_913.0
    )


def test_extract_bls_api_standard_error_requires_named_aspect() -> None:
    result = extract_bls_api_standard_error(
        _api_payload(),
        series_id=MANAGEMENT_PROFESSIONAL_SERIES_ID,
        year=2026,
        period="M07",
    )
    assert result.value == 447.5
    assert result.aspect_type == "Standard Error"
    assert result.footnote_code == "P"


def test_extract_bls_api_standard_error_fails_when_keyless_path_omits_aspects() -> None:
    with pytest.raises(ValueError, match="did not include an aspects array"):
        extract_bls_api_standard_error(
            _api_payload(with_aspects=False),
            series_id=MANAGEMENT_PROFESSIONAL_SERIES_ID,
            year=2026,
            period="M07",
        )


def test_reconstruct_management_professional_employment_uses_composited_weight(
    tmp_path: Path,
) -> None:
    path = tmp_path / "jul26pub.dat.gz"
    rows = [
        _fixed_width_record(
            PRTAGE="16",
            PREMPNOT="1",
            PRDTOCC1="1",
            PWSSWGT=_raw_weight(9000.0),
            PWCMPWGT=_raw_weight(1000.4),
        ),
        _fixed_width_record(
            PRTAGE="70",
            PREMPNOT="1",
            PRDTOCC1="10",
            PWSSWGT=_raw_weight(8000.0),
            PWCMPWGT=_raw_weight(2000.2),
        ),
        _fixed_width_record(
            PRTAGE="45",
            PREMPNOT="1",
            PRDTOCC1="11",
            PWSSWGT=_raw_weight(5000.0),
            PWCMPWGT=_raw_weight(5000.0),
        ),
        _fixed_width_record(
            PRTAGE="15",
            PREMPNOT="1",
            PRDTOCC1="2",
            PWSSWGT=_raw_weight(7000.0),
            PWCMPWGT=_raw_weight(7000.0),
        ),
        _fixed_width_record(
            PRTAGE="50",
            PREMPNOT="2",
            PRDTOCC1="3",
            PWSSWGT=_raw_weight(9000.0),
            PWCMPWGT=_raw_weight(9000.0),
        ),
    ]
    with gzip.open(path, mode="wt", encoding="ascii") as handle:
        handle.writelines(rows)

    result = reconstruct_management_professional_employment(path, year=2026, month="jul")
    assert result.rows_read == 5
    assert result.employed_16_plus_rows == 3
    assert result.benchmark_rows == 2
    assert result.benchmark_weighted_persons == pytest.approx(3000.6)
    assert result.benchmark_thousands == pytest.approx(3.0006)


def test_published_rounding_match_is_explicit() -> None:
    assert published_rounding_matches(69_912.51, 69_913.0)
    assert not published_rounding_matches(69_912.49, 69_913.0)
