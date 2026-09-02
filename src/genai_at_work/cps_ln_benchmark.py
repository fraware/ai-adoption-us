"""Official BLS LN benchmark primitives for CPS uncertainty validation.

This module supports a deliberately narrow validation exercise for R1.1-G2b. It can
extract one published BLS standard-error aspect from either the LN flat-file format or
the Public Data API, parse the corresponding point estimate, and reconstruct the
published employment level from one official Basic Monthly CPS public-use file under
the BLS 16+ universe.

The benchmark does not estimate a CPS standard error from public-use microdata and it
must not be used to infer month-to-month, quarter-to-quarter, or year-over-year
covariance. The published LN standard error remains a BLS design-based output for a
single reference period.
"""

from __future__ import annotations

import csv
import gzip
import math
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from genai_at_work.cps import decode_fixed_width_record_2026, parse_final_weight

BLS_LN_ASPECT_URL = "https://download.bls.gov/pub/time.series/ln/ln.aspect"
BLS_PUBLIC_API_V2_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
MANAGEMENT_PROFESSIONAL_SERIES_ID = "LNU02032201"
STANDARD_ERROR_ASPECT_TYPE = "E"
STANDARD_ERROR_API_NAME = "Standard Error"
MANAGEMENT_PROFESSIONAL_OCCUPATION_CODES = frozenset(range(1, 11))
# Official 2026 record layout location 846-855, expressed as Python's zero-based slice.
PWCMPWGT_FIXED_WIDTH_2026 = (845, 855)

_MONTH_TO_PERIOD = {
    "jan": "M01",
    "feb": "M02",
    "mar": "M03",
    "apr": "M04",
    "may": "M05",
    "jun": "M06",
    "jul": "M07",
    "aug": "M08",
    "sep": "M09",
    "oct": "M10",
    "nov": "M11",
    "dec": "M12",
}


@dataclass(frozen=True)
class LNStandardError:
    """One published BLS LN standard-error aspect observation."""

    series_id: str
    year: int
    period: str
    aspect_type: str
    value: float
    footnote_code: str


@dataclass(frozen=True)
class CPSMonthlyBenchmark:
    """One reconstructed Basic Monthly CPS published-series level."""

    year: int
    month: str
    period: str
    rows_read: int
    employed_16_plus_rows: int
    benchmark_rows: int
    benchmark_weighted_persons: float
    benchmark_thousands: float


def month_period(month: str) -> str:
    """Return a BLS monthly period code (``M01`` ... ``M12``)."""

    normalized = month.strip().lower()
    try:
        return _MONTH_TO_PERIOD[normalized]
    except KeyError as exc:
        raise ValueError(f"unsupported month abbreviation: {month!r}") from exc


def _clean_row(row: Mapping[str | None, str | None]) -> dict[str, str]:
    cleaned: dict[str, str] = {}
    for raw_key, raw_value in row.items():
        if raw_key is None:
            continue
        key = raw_key.strip().lstrip("\ufeff")
        if not key:
            continue
        cleaned[key] = "" if raw_value is None else raw_value.strip()
    return cleaned


def _validated_positive_value(raw_value: object, *, label: str) -> float:
    try:
        value = float(str(raw_value).replace(",", ""))
    except ValueError as exc:
        raise ValueError(f"{label} is not numeric: {raw_value!r}") from exc
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{label} must be finite and positive: {value!r}")
    return value


def extract_ln_standard_error(
    aspect_path: Path,
    *,
    series_id: str,
    year: int,
    period: str,
) -> LNStandardError:
    """Extract exactly one ``E`` aspect row from the tab-delimited LN flat file."""

    if year < 1900:
        raise ValueError("year is implausible")
    if not series_id.strip():
        raise ValueError("series_id must be non-empty")
    if not period.startswith("M") or len(period) != 3:
        raise ValueError(f"period must be a monthly BLS code, got {period!r}")

    matching_period_rows: list[dict[str, str]] = []
    with aspect_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = {str(name).strip().lstrip("\ufeff") for name in (reader.fieldnames or [])}
        required = {"series_id", "year", "period", "aspect_type", "value"}
        missing = required - fieldnames
        if missing:
            raise ValueError(f"BLS LN aspect file is missing columns: {sorted(missing)}")

        for raw_row in reader:
            row = _clean_row(raw_row)
            if row.get("series_id") != series_id:
                continue
            if row.get("year") != str(year) or row.get("period") != period:
                continue
            matching_period_rows.append(row)

    if not matching_period_rows:
        raise ValueError(f"no BLS LN aspect rows for {series_id} {year} {period}")

    standard_error_rows = [
        row for row in matching_period_rows if row.get("aspect_type") == STANDARD_ERROR_ASPECT_TYPE
    ]
    if len(standard_error_rows) != 1:
        observed_types = sorted({row.get("aspect_type", "") for row in matching_period_rows})
        raise ValueError(
            "expected exactly one standard-error aspect row for "
            f"{series_id} {year} {period}; found {len(standard_error_rows)}; "
            f"observed aspect types={observed_types}"
        )

    row = standard_error_rows[0]
    footnote = row.get("footnote_codes", row.get("footnote_code", ""))
    return LNStandardError(
        series_id=series_id,
        year=year,
        period=period,
        aspect_type=STANDARD_ERROR_ASPECT_TYPE,
        value=_validated_positive_value(row["value"], label="standard-error aspect value"),
        footnote_code=footnote,
    )


def _bls_api_observation(
    payload: Mapping[str, object],
    *,
    series_id: str,
    year: int,
    period: str,
) -> dict[str, object]:
    if payload.get("status") != "REQUEST_SUCCEEDED":
        raise ValueError(
            f"BLS API request did not succeed: {payload.get('status')!r}; "
            f"message={payload.get('message')!r}"
        )
    results = payload.get("Results")
    if not isinstance(results, dict):
        raise ValueError("BLS API response lacks Results object")
    raw_series = results.get("series")
    if not isinstance(raw_series, list):
        raise ValueError("BLS API response lacks series array")
    candidates = [row for row in raw_series if isinstance(row, dict) and row.get("seriesID") == series_id]
    if len(candidates) != 1:
        raise ValueError(f"expected exactly one BLS API series {series_id}; found {len(candidates)}")
    data = candidates[0].get("data")
    if not isinstance(data, list):
        raise ValueError("BLS API series lacks data array")
    matches = [
        row
        for row in data
        if isinstance(row, dict)
        and row.get("year") == str(year)
        and row.get("period") == period
    ]
    if len(matches) != 1:
        raise ValueError(
            f"expected exactly one BLS API observation for {series_id} {year} {period}; "
            f"found {len(matches)}"
        )
    return {str(key): value for key, value in matches[0].items()}


def parse_bls_api_month_value(
    payload: Mapping[str, object],
    *,
    series_id: str,
    year: int,
    period: str,
) -> float:
    """Parse one point estimate from a BLS Public Data API response."""

    observation = _bls_api_observation(
        payload,
        series_id=series_id,
        year=year,
        period=period,
    )
    raw_value = observation.get("value")
    try:
        value = float(str(raw_value).replace(",", ""))
    except ValueError as exc:
        raise ValueError(f"BLS API observation is not numeric: {raw_value!r}") from exc
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"BLS API observation must be finite and nonnegative: {value!r}")
    return value


def extract_bls_api_standard_error(
    payload: Mapping[str, object],
    *,
    series_id: str,
    year: int,
    period: str,
) -> LNStandardError:
    """Extract exactly one ``Standard Error`` aspect from one BLS API observation."""

    observation = _bls_api_observation(
        payload,
        series_id=series_id,
        year=year,
        period=period,
    )
    aspects = observation.get("aspects")
    if not isinstance(aspects, list):
        raise ValueError(
            "BLS API observation did not include an aspects array; the keyless "
            "single-series aspects path is unavailable for this request"
        )
    matches = [
        aspect
        for aspect in aspects
        if isinstance(aspect, dict)
        and str(aspect.get("name", "")).strip().casefold() == STANDARD_ERROR_API_NAME.casefold()
    ]
    if len(matches) != 1:
        observed_names = sorted(
            str(aspect.get("name", "")) for aspect in aspects if isinstance(aspect, dict)
        )
        raise ValueError(
            "expected exactly one BLS API Standard Error aspect for "
            f"{series_id} {year} {period}; found {len(matches)}; "
            f"observed aspect names={observed_names}"
        )
    aspect = matches[0]
    footnotes = aspect.get("footnotes")
    codes: list[str] = []
    if isinstance(footnotes, list):
        for item in footnotes:
            if isinstance(item, dict) and item.get("code"):
                codes.append(str(item["code"]))
    return LNStandardError(
        series_id=series_id,
        year=year,
        period=period,
        aspect_type=STANDARD_ERROR_API_NAME,
        value=_validated_positive_value(aspect.get("value"), label="BLS API Standard Error"),
        footnote_code=",".join(codes),
    )


def reconstruct_management_professional_employment(
    cps_path: Path,
    *,
    year: int,
    month: str,
) -> CPSMonthlyBenchmark:
    """Reconstruct published ``LNU02032201`` from one official 2026 CPS file.

    The BLS published-labor-force universe uses the composited final weight
    ``PWCMPWGT`` for civilian people age 16 and over. The broad Management,
    Professional, and Related group corresponds to ``PRDTOCC1`` recodes 1 through 10.
    ``PWCMPWGT`` has four implied decimal places and occupies record positions 846-855
    in the official 2026 fixed-width layout.
    """

    if year != 2026:
        raise ValueError("benchmark fixed-width reconstruction is pinned to the audited 2026 layout")
    period = month_period(month)
    rows_read = 0
    employed_16_plus_rows = 0
    benchmark_rows = 0
    weighted_persons = 0.0
    weight_start, weight_end = PWCMPWGT_FIXED_WIDTH_2026

    with gzip.open(cps_path, mode="rt", encoding="ascii", newline="") as handle:
        for line in handle:
            rows_read += 1
            row = decode_fixed_width_record_2026(line)
            try:
                age = int(row["PRTAGE"].strip())
                employment_status = int(row["PREMPNOT"].strip())
                occupation_code = int(row["PRDTOCC1"].strip())
            except ValueError:
                continue
            if age < 16 or employment_status != 1:
                continue
            employed_16_plus_rows += 1
            if occupation_code not in MANAGEMENT_PROFESSIONAL_OCCUPATION_CODES:
                continue
            weight = parse_final_weight(line[weight_start:weight_end])
            if weight is None:
                raise ValueError(
                    f"benchmark row {rows_read} has invalid PWCMPWGT despite published-series scope"
                )
            benchmark_rows += 1
            weighted_persons += weight

    if rows_read == 0:
        raise ValueError("CPS benchmark file is empty")
    if benchmark_rows == 0 or weighted_persons <= 0:
        raise ValueError("CPS benchmark produced no weighted observations")
    return CPSMonthlyBenchmark(
        year=year,
        month=month.strip().lower(),
        period=period,
        rows_read=rows_read,
        employed_16_plus_rows=employed_16_plus_rows,
        benchmark_rows=benchmark_rows,
        benchmark_weighted_persons=weighted_persons,
        benchmark_thousands=weighted_persons / 1000.0,
    )


def published_rounding_matches(reconstructed_thousands: float, published_thousands: float) -> bool:
    """Return whether a full-precision reconstruction rounds to the published thousand."""

    if not math.isfinite(reconstructed_thousands) or not math.isfinite(published_thousands):
        return False
    if reconstructed_thousands < 0 or published_thousands < 0:
        return False
    published_integer = math.floor(published_thousands + 0.5)
    reconstructed_integer = math.floor(reconstructed_thousands + 0.5)
    return published_integer == reconstructed_integer
