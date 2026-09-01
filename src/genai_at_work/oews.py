"""OEWS occupation-composition ingestion and cross-source robustness diagnostics.

The module intentionally uses only public BLS OEWS aggregate employment series. It does
not treat OEWS as population-equivalent to CPS/RPS: OEWS excludes self-employed workers
and has additional industry-specific scope differences. The resulting comparison is an
independent-source composition robustness check, not a synchronized-survey validation.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import httpx

BLS_API_URL = "https://api.bls.gov/publicAPI/v1/timeseries/data/"
OEWS_EMPLOYMENT_DATATYPE = "01"
OEWS_ALL_OCCUPATIONS_CODE = "000000"


@dataclass(frozen=True)
class OewsCompositionRow:
    """One industry's OEWS employment composition over canonical occupations."""

    industry_index: int
    industry_id: str
    industry_name: str
    oews_industry_code: str
    comparability: str
    comparability_reason: str | None
    total_employment: float | None
    observed_major_group_employment: float
    raw_sum_to_total_ratio: float | None
    coverage: float
    supported: bool
    missing_occupations: tuple[str, ...]
    occupation_employment: dict[str, float | None]
    worker_weights: dict[str, float] | None


@dataclass(frozen=True)
class CompositionComparisonRow:
    """CPS-versus-OEWS worker-composition comparison for one industry."""

    industry_index: int
    industry_id: str
    industry_name: str
    comparability: str
    oews_supported: bool
    cps_supported: bool
    l1_distance: float | None
    cosine_similarity: float | None
    spearman_rank_correlation: float | None
    top_occupation_agreement: bool | None
    cps_top_occupation: str | None
    oews_top_occupation: str | None
    max_absolute_share_difference: float | None


def oews_series_id(
    industry_code: str,
    occupation_code: str,
    datatype: str = OEWS_EMPLOYMENT_DATATYPE,
) -> str:
    """Construct a national unadjusted OEWS series identifier.

    BLS OEWS national series use area type ``N`` and national area code ``0000000``.
    Industry and occupation components are both six characters, and employment is
    datatype ``01``.
    """

    if len(industry_code) != 6:
        raise ValueError(f"OEWS industry code must be 6 characters: {industry_code!r}")
    if len(occupation_code) != 6:
        raise ValueError(
            f"OEWS occupation code must be 6 characters: {occupation_code!r}"
        )
    if len(datatype) != 2:
        raise ValueError(f"OEWS datatype must be 2 characters: {datatype!r}")
    return f"OEUN0000000{industry_code}{occupation_code}{datatype}"


def chunked(values: Sequence[str], size: int) -> list[list[str]]:
    """Split a sequence into deterministic non-empty chunks."""

    if size <= 0:
        raise ValueError("chunk size must be positive")
    return [list(values[start : start + size]) for start in range(0, len(values), size)]


def parse_bls_series_response(
    payload: Mapping[str, Any],
    *,
    requested_series_ids: Sequence[str],
    year: int,
) -> dict[str, float | None]:
    """Parse one BLS API response into requested series values.

    Missing, suppressed, nonnumeric, wrong-year, and non-annual observations become
    ``None``. The returned mapping always contains every requested series ID.
    """

    values: dict[str, float | None] = {series_id: None for series_id in requested_series_ids}
    results = payload.get("Results", {})
    if not isinstance(results, Mapping):
        return values
    series_rows = results.get("series", [])
    if not isinstance(series_rows, list):
        return values

    for series in series_rows:
        if not isinstance(series, Mapping):
            continue
        series_id = series.get("seriesID")
        if not isinstance(series_id, str) or series_id not in values:
            continue
        data = series.get("data", [])
        if not isinstance(data, list):
            continue
        for observation in data:
            if not isinstance(observation, Mapping):
                continue
            if str(observation.get("year")) != str(year):
                continue
            if observation.get("period") != "A01":
                continue
            raw_value = observation.get("value")
            try:
                numeric = float(str(raw_value).replace(",", ""))
            except (TypeError, ValueError):
                continue
            if math.isfinite(numeric) and numeric >= 0:
                values[series_id] = numeric
                break
    return values


def fetch_oews_series_values(
    series_ids: Sequence[str],
    *,
    year: int,
    client: httpx.Client,
    batch_size: int = 25,
) -> tuple[dict[str, float | None], list[dict[str, Any]]]:
    """Fetch OEWS values through the sanctioned BLS public API.

    ``batch_size`` defaults to the unregistered BLS limit of 25 series per request.
    Request provenance is returned without storing entire source response bodies.
    """

    if len(set(series_ids)) != len(series_ids):
        raise ValueError("OEWS series list contains duplicate identifiers")
    values: dict[str, float | None] = {}
    request_manifest: list[dict[str, Any]] = []

    for batch_index, batch in enumerate(chunked(series_ids, batch_size), start=1):
        response = client.post(
            BLS_API_URL,
            json={
                "seriesid": batch,
                "startyear": str(year),
                "endyear": str(year),
            },
        )
        response.raise_for_status()
        payload = response.json()
        status = payload.get("status") if isinstance(payload, Mapping) else None
        if status != "REQUEST_SUCCEEDED":
            raise ValueError(f"BLS API request failed: status={status!r}")
        parsed = parse_bls_series_response(
            payload,
            requested_series_ids=batch,
            year=year,
        )
        values.update(parsed)
        messages = payload.get("message", []) if isinstance(payload, Mapping) else []
        request_manifest.append(
            {
                "batch_index": batch_index,
                "series_count": len(batch),
                "first_series_id": batch[0],
                "last_series_id": batch[-1],
                "http_status": response.status_code,
                "api_status": status,
                "messages": messages if isinstance(messages, list) else [],
            }
        )

    return values, request_manifest


def required_series_ids(
    industry_entries: Sequence[Mapping[str, Any]],
    occupation_entries: Sequence[Mapping[str, Any]],
) -> list[str]:
    """Return the deterministic OEWS series set needed for composition analysis."""

    series_ids: list[str] = []
    for industry in industry_entries:
        industry_code = str(industry["oews_industry_code"])
        series_ids.append(oews_series_id(industry_code, OEWS_ALL_OCCUPATIONS_CODE))
        for occupation in occupation_entries:
            series_ids.append(
                oews_series_id(industry_code, str(occupation["oews_occupation_code"]))
            )
    return series_ids


def build_oews_composition(
    values: Mapping[str, float | None],
    *,
    industry_entries: Sequence[Mapping[str, Any]],
    occupation_entries: Sequence[Mapping[str, Any]],
    coverage_gate: float = 0.98,
) -> list[OewsCompositionRow]:
    """Build normalized employee-share occupation vectors by industry.

    Coverage is the observed major-group employment sum divided by the BLS published
    all-occupations employment total, capped at one for the gate because independent
    rounded major-group estimates can sum slightly above the rounded total. Supported
    vectors are normalized by the observed major-group sum itself.
    """

    if not 0 < coverage_gate <= 1:
        raise ValueError("coverage gate must be in (0, 1]")

    rows: list[OewsCompositionRow] = []
    for industry in industry_entries:
        industry_code = str(industry["oews_industry_code"])
        total_series = oews_series_id(industry_code, OEWS_ALL_OCCUPATIONS_CODE)
        total = values.get(total_series)

        occupation_employment: dict[str, float | None] = {}
        missing: list[str] = []
        observed_sum = 0.0
        for occupation in occupation_entries:
            entity_id = str(occupation["entity_id"])
            series = oews_series_id(
                industry_code, str(occupation["oews_occupation_code"])
            )
            employment = values.get(series)
            occupation_employment[entity_id] = employment
            if employment is None:
                missing.append(entity_id)
            else:
                observed_sum += employment

        raw_ratio = (
            observed_sum / total
            if total is not None and total > 0 and math.isfinite(total)
            else None
        )
        coverage = min(1.0, raw_ratio) if raw_ratio is not None else 0.0
        supported = coverage >= coverage_gate and observed_sum > 0
        weights = (
            {
                entity_id: employment / observed_sum
                for entity_id, employment in occupation_employment.items()
                if employment is not None
            }
            if supported
            else None
        )

        rows.append(
            OewsCompositionRow(
                industry_index=int(industry["entity_index"]),
                industry_id=str(industry["entity_id"]),
                industry_name=str(industry["entity_name"]),
                oews_industry_code=industry_code,
                comparability=str(industry["comparability"]),
                comparability_reason=(
                    str(industry["reason"]) if industry.get("reason") else None
                ),
                total_employment=total,
                observed_major_group_employment=observed_sum,
                raw_sum_to_total_ratio=raw_ratio,
                coverage=coverage,
                supported=supported,
                missing_occupations=tuple(missing),
                occupation_employment=occupation_employment,
                worker_weights=weights,
            )
        )
    return rows


def _average_ranks(values: Sequence[float]) -> list[float]:
    """Return average ranks with deterministic tie handling."""

    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    start = 0
    while start < len(indexed):
        end = start + 1
        while end < len(indexed) and indexed[end][1] == indexed[start][1]:
            end += 1
        average_rank = (start + 1 + end) / 2.0
        for position in range(start, end):
            ranks[indexed[position][0]] = average_rank
        start = end
    return ranks


def _pearson(left: Sequence[float], right: Sequence[float]) -> float | None:
    if len(left) != len(right) or len(left) < 2:
        return None
    left_mean = sum(left) / len(left)
    right_mean = sum(right) / len(right)
    numerator = sum(
        (left_value - left_mean) * (right_value - right_mean)
        for left_value, right_value in zip(left, right, strict=True)
    )
    left_ss = sum((value - left_mean) ** 2 for value in left)
    right_ss = sum((value - right_mean) ** 2 for value in right)
    denominator = math.sqrt(left_ss * right_ss)
    return numerator / denominator if denominator > 0 else None


def spearman_rank_correlation(
    left: Sequence[float], right: Sequence[float]
) -> float | None:
    """Compute Spearman correlation as Pearson correlation of average ranks."""

    if len(left) != len(right):
        raise ValueError("Spearman vectors must have the same length")
    return _pearson(_average_ranks(left), _average_ranks(right))


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float | None:
    """Compute cosine similarity for nonzero equal-length vectors."""

    if len(left) != len(right):
        raise ValueError("cosine vectors must have the same length")
    numerator = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    denominator = left_norm * right_norm
    return numerator / denominator if denominator > 0 else None


def compare_cps_oews_worker_composition(
    oews_rows: Sequence[OewsCompositionRow],
    cps_industries: Sequence[Mapping[str, Any]],
    *,
    occupation_ids: Sequence[str],
) -> list[CompositionComparisonRow]:
    """Compare OEWS employee shares with CPS worker shares by industry."""

    cps_by_id = {str(row["industry_id"]): row for row in cps_industries}
    comparisons: list[CompositionComparisonRow] = []

    for oews_row in oews_rows:
        cps = cps_by_id.get(oews_row.industry_id)
        cps_weights_raw = cps.get("worker_weights") if cps is not None else None
        cps_supported = isinstance(cps_weights_raw, Mapping)
        if not oews_row.supported or oews_row.worker_weights is None or not cps_supported:
            comparisons.append(
                CompositionComparisonRow(
                    industry_index=oews_row.industry_index,
                    industry_id=oews_row.industry_id,
                    industry_name=oews_row.industry_name,
                    comparability=oews_row.comparability,
                    oews_supported=oews_row.supported,
                    cps_supported=cps_supported,
                    l1_distance=None,
                    cosine_similarity=None,
                    spearman_rank_correlation=None,
                    top_occupation_agreement=None,
                    cps_top_occupation=None,
                    oews_top_occupation=None,
                    max_absolute_share_difference=None,
                )
            )
            continue

        cps_weights = {str(key): float(value) for key, value in cps_weights_raw.items()}
        oews_weights = oews_row.worker_weights
        missing_ids = [
            occupation_id
            for occupation_id in occupation_ids
            if occupation_id not in cps_weights or occupation_id not in oews_weights
        ]
        if missing_ids:
            raise ValueError(
                f"supported composition missing canonical occupations: {missing_ids}"
            )

        cps_vector = [cps_weights[occupation_id] for occupation_id in occupation_ids]
        oews_vector = [oews_weights[occupation_id] for occupation_id in occupation_ids]
        absolute_differences = [
            abs(cps_value - oews_value)
            for cps_value, oews_value in zip(cps_vector, oews_vector, strict=True)
        ]
        cps_top = max(occupation_ids, key=cps_weights.__getitem__)
        oews_top = max(occupation_ids, key=oews_weights.__getitem__)

        comparisons.append(
            CompositionComparisonRow(
                industry_index=oews_row.industry_index,
                industry_id=oews_row.industry_id,
                industry_name=oews_row.industry_name,
                comparability=oews_row.comparability,
                oews_supported=True,
                cps_supported=True,
                l1_distance=sum(absolute_differences),
                cosine_similarity=cosine_similarity(cps_vector, oews_vector),
                spearman_rank_correlation=spearman_rank_correlation(
                    cps_vector, oews_vector
                ),
                top_occupation_agreement=cps_top == oews_top,
                cps_top_occupation=cps_top,
                oews_top_occupation=oews_top,
                max_absolute_share_difference=max(absolute_differences),
            )
        )

    return comparisons


def median(values: Iterable[float]) -> float | None:
    """Return a deterministic median without an additional statistics dependency."""

    ordered = sorted(values)
    if not ordered:
        return None
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2.0
