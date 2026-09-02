"""Independent OEWS-weighted RPS adoption counterfactual robustness.

May-2025 OEWS is an establishment-side occupation-composition robustness source.
It is not population-equivalent to CPS/RPS and must never be averaged with the
primary CPS worker-share composition estimate.

When OEWS omits one or more industry-by-occupation employment estimates, the
missing cells are unknown nonnegative employment mass. This module follows the
same partial-identification convention as :mod:`genai_at_work.oews_partial`:
complete OEWS vectors use the normalized published major-group composition;
incomplete vectors divide published occupation counts by the published
all-occupations total and allocate only the residual mass across missing
canonical occupations. No missing OEWS cell is imputed as zero.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from statistics import median
from typing import Any

from genai_at_work.longitudinal import AuditRecord
from genai_at_work.oews import OewsCompositionRow, spearman_rank_correlation

ADOPTION_METRIC = "adoption_work"


class OewsRpsError(ValueError):
    """Raised when OEWS/RPS counterfactual evidence violates its contract."""


@dataclass(frozen=True)
class OewsRpsAdoptionBoundRow:
    """OEWS-weighted adoption counterfactual/residual interval for one industry."""

    industry_index: int
    industry_id: str
    industry_name: str
    comparability: str
    period: str
    coverage: float
    supported: bool
    point_identified: bool
    missing_occupation_count: int
    missing_occupations: tuple[str, ...]
    residual_unpublished_employment: float | None
    residual_unpublished_mass_share: float | None
    observed_industry_adoption: float
    predicted_adoption_lower: float | None
    predicted_adoption_upper: float | None
    predicted_adoption_point: float | None
    residual_lower: float | None
    residual_upper: float | None
    residual_point: float | None
    residual_sign_identification: str | None
    unsupported_reason: str | None


@dataclass(frozen=True)
class CpsOewsAdoptionComparisonRow:
    """Comparison of CPS and independent OEWS occupation-adjusted adoption residuals."""

    industry_index: int
    industry_id: str
    comparability: str
    period: str
    cps_supported: bool
    oews_supported: bool
    cps_residual: float | None
    cps_residual_sign: str | None
    oews_point_identified: bool
    oews_residual_lower: float | None
    oews_residual_upper: float | None
    oews_residual_point: float | None
    oews_residual_sign_identification: str | None
    direction_agreement: bool | None
    cps_absolute_residual: float | None
    oews_absolute_residual_lower: float | None
    oews_absolute_residual_upper: float | None
    magnitude_relation: str | None
    cps_residual_inside_oews_interval: bool | None


def _finite_percent(value: object, *, context: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise OewsRpsError(f"{context} must be numeric")
    numeric = float(value)
    if not math.isfinite(numeric) or not 0.0 <= numeric <= 100.0:
        raise OewsRpsError(f"{context} must be a finite percentage in [0, 100]")
    return numeric


def _adoption_values(
    records: Sequence[AuditRecord],
    *,
    period: str,
    entity_type: str,
) -> dict[str, float]:
    values: dict[str, float] = {}
    for row in records:
        if (
            row.period != period
            or row.metric_id != ADOPTION_METRIC
            or row.entity_type != entity_type
        ):
            continue
        if row.entity_id in values:
            raise OewsRpsError(
                f"duplicate RPS {entity_type} adoption value for {row.entity_id}/{period}"
            )
        values[row.entity_id] = _finite_percent(
            row.value, context=f"RPS {entity_type} {row.entity_id}/{period}"
        )
    return values


def _sign(lower: float, upper: float, *, tolerance: float = 1e-12) -> str:
    if lower > tolerance:
        return "positive"
    if upper < -tolerance:
        return "negative"
    if abs(lower) <= tolerance and abs(upper) <= tolerance:
        return "zero"
    return "contains_zero"


def _unsupported(
    row: OewsCompositionRow,
    *,
    period: str,
    observed_industry_adoption: float,
    reason: str,
) -> OewsRpsAdoptionBoundRow:
    return OewsRpsAdoptionBoundRow(
        industry_index=row.industry_index,
        industry_id=row.industry_id,
        industry_name=row.industry_name,
        comparability=row.comparability,
        period=period,
        coverage=row.coverage,
        supported=False,
        point_identified=False,
        missing_occupation_count=len(row.missing_occupations),
        missing_occupations=row.missing_occupations,
        residual_unpublished_employment=None,
        residual_unpublished_mass_share=None,
        observed_industry_adoption=observed_industry_adoption,
        predicted_adoption_lower=None,
        predicted_adoption_upper=None,
        predicted_adoption_point=None,
        residual_lower=None,
        residual_upper=None,
        residual_point=None,
        residual_sign_identification=None,
        unsupported_reason=reason,
    )


def _complete_prediction(
    row: OewsCompositionRow,
    *,
    occupation_values: Mapping[str, float],
    occupation_ids: Sequence[str],
) -> float:
    if row.worker_weights is None:
        raise OewsRpsError("complete OEWS prediction requires a worker-weight vector")
    missing = [occupation_id for occupation_id in occupation_ids if occupation_id not in row.worker_weights]
    if missing:
        raise OewsRpsError("complete OEWS prediction received an incomplete worker-weight vector")
    weights = {occupation_id: float(row.worker_weights[occupation_id]) for occupation_id in occupation_ids}
    if any(not math.isfinite(weight) or weight < 0.0 for weight in weights.values()):
        raise OewsRpsError("OEWS worker weights must be finite and nonnegative")
    total = sum(weights.values())
    if not math.isclose(total, 1.0, abs_tol=1e-10):
        raise OewsRpsError(f"complete OEWS worker weights must sum to one, observed {total}")
    return sum(weights[occupation_id] * occupation_values[occupation_id] for occupation_id in occupation_ids)


def adoption_counterfactual_bounds(
    oews_rows: Sequence[OewsCompositionRow],
    rps_records: Sequence[AuditRecord],
    *,
    period: str,
    occupation_ids: Sequence[str],
) -> list[OewsRpsAdoptionBoundRow]:
    """Compute independent OEWS-weighted RPS adoption counterfactual bounds.

    For complete OEWS vectors the interval is a point estimate using the existing
    normalized OEWS worker weights. For incomplete vectors, published occupation
    employment is divided by the published all-occupations total. The remaining
    mass is allowed to occupy any missing canonical occupation. Because the
    counterfactual is linear, its extrema place all residual mass on the missing
    occupation with the minimum or maximum RPS adoption value.
    """

    if not occupation_ids or len(set(occupation_ids)) != len(occupation_ids):
        raise OewsRpsError("occupation_ids must be a non-empty unique sequence")
    occupation_values = _adoption_values(rps_records, period=period, entity_type="occupation")
    industry_values = _adoption_values(rps_records, period=period, entity_type="industry")
    missing_rps_occupations = sorted(set(occupation_ids) - set(occupation_values))
    unexpected_rps_occupations = sorted(set(occupation_values) - set(occupation_ids))
    if missing_rps_occupations or unexpected_rps_occupations:
        raise OewsRpsError(
            "RPS occupation adoption coverage does not match canonical occupation_ids: "
            f"missing={missing_rps_occupations!r}, unexpected={unexpected_rps_occupations!r}"
        )
    if len({row.industry_id for row in oews_rows}) != len(oews_rows):
        raise OewsRpsError("OEWS composition contains duplicate industry ids")
    missing_rps_industries = sorted({row.industry_id for row in oews_rows} - set(industry_values))
    if missing_rps_industries:
        raise OewsRpsError(
            f"RPS industry adoption is missing OEWS industries: {missing_rps_industries!r}"
        )

    results: list[OewsRpsAdoptionBoundRow] = []
    for row in sorted(oews_rows, key=lambda item: item.industry_index):
        observed = industry_values[row.industry_id]
        if not row.supported or row.worker_weights is None:
            results.append(
                _unsupported(
                    row,
                    period=period,
                    observed_industry_adoption=observed,
                    reason="OEWS composition does not pass the configured coverage gate",
                )
            )
            continue

        missing = tuple(
            occupation_id
            for occupation_id in occupation_ids
            if row.occupation_employment.get(occupation_id) is None
        )
        if not missing:
            predicted = _complete_prediction(
                row,
                occupation_values=occupation_values,
                occupation_ids=occupation_ids,
            )
            residual = observed - predicted
            results.append(
                OewsRpsAdoptionBoundRow(
                    industry_index=row.industry_index,
                    industry_id=row.industry_id,
                    industry_name=row.industry_name,
                    comparability=row.comparability,
                    period=period,
                    coverage=row.coverage,
                    supported=True,
                    point_identified=True,
                    missing_occupation_count=0,
                    missing_occupations=(),
                    residual_unpublished_employment=0.0,
                    residual_unpublished_mass_share=0.0,
                    observed_industry_adoption=observed,
                    predicted_adoption_lower=predicted,
                    predicted_adoption_upper=predicted,
                    predicted_adoption_point=predicted,
                    residual_lower=residual,
                    residual_upper=residual,
                    residual_point=residual,
                    residual_sign_identification=_sign(residual, residual),
                    unsupported_reason=None,
                )
            )
            continue

        total = row.total_employment
        if total is None or not math.isfinite(total) or total <= 0.0:
            results.append(
                _unsupported(
                    row,
                    period=period,
                    observed_industry_adoption=observed,
                    reason="published OEWS all-occupations employment is unavailable",
                )
            )
            continue
        if row.observed_major_group_employment > total + 1e-9:
            results.append(
                _unsupported(
                    row,
                    period=period,
                    observed_industry_adoption=observed,
                    reason=(
                        "published observed occupation employment exceeds the published "
                        "all-occupations total; counterfactual bounds would require an "
                        "explicit rounding model"
                    ),
                )
            )
            continue

        residual_employment = total - row.observed_major_group_employment
        residual_share = residual_employment / total
        missing_set = set(missing)
        known_prediction = 0.0
        for occupation_id in occupation_ids:
            if occupation_id in missing_set:
                continue
            employment = row.occupation_employment.get(occupation_id)
            if employment is None:
                raise OewsRpsError("OEWS missing-occupation bookkeeping is inconsistent")
            if not math.isfinite(employment) or employment < 0.0:
                raise OewsRpsError("OEWS occupation employment must be finite and nonnegative")
            known_prediction += (employment / total) * occupation_values[occupation_id]

        missing_values = [occupation_values[occupation_id] for occupation_id in missing]
        if not missing_values:
            raise OewsRpsError("positive incomplete-vector path requires missing occupations")
        lower_prediction = known_prediction + residual_share * min(missing_values)
        upper_prediction = known_prediction + residual_share * max(missing_values)
        if lower_prediction > upper_prediction + 1e-12:
            raise OewsRpsError("computed OEWS adoption counterfactual lower bound exceeds upper bound")
        residual_lower = observed - upper_prediction
        residual_upper = observed - lower_prediction
        point_identified = math.isclose(lower_prediction, upper_prediction, abs_tol=1e-12)
        predicted_point = lower_prediction if point_identified else None
        residual_point = residual_lower if point_identified else None
        results.append(
            OewsRpsAdoptionBoundRow(
                industry_index=row.industry_index,
                industry_id=row.industry_id,
                industry_name=row.industry_name,
                comparability=row.comparability,
                period=period,
                coverage=row.coverage,
                supported=True,
                point_identified=point_identified,
                missing_occupation_count=len(missing),
                missing_occupations=missing,
                residual_unpublished_employment=residual_employment,
                residual_unpublished_mass_share=residual_share,
                observed_industry_adoption=observed,
                predicted_adoption_lower=lower_prediction,
                predicted_adoption_upper=upper_prediction,
                predicted_adoption_point=predicted_point,
                residual_lower=residual_lower,
                residual_upper=residual_upper,
                residual_point=residual_point,
                residual_sign_identification=_sign(residual_lower, residual_upper),
                unsupported_reason=None,
            )
        )
    return results


def _absolute_interval(lower: float, upper: float) -> tuple[float, float]:
    if lower > upper:
        raise OewsRpsError("residual interval lower bound exceeds upper bound")
    if lower <= 0.0 <= upper:
        return 0.0, max(abs(lower), abs(upper))
    return min(abs(lower), abs(upper)), max(abs(lower), abs(upper))


def compare_cps_oews_adoption_residuals(
    cps_residual_rows: Sequence[Mapping[str, Any]],
    oews_rows: Sequence[OewsRpsAdoptionBoundRow],
    *,
    period: str,
) -> list[CpsOewsAdoptionComparisonRow]:
    """Compare CPS worker-share and independent OEWS adoption residual evidence."""

    cps_by_industry: dict[str, Mapping[str, Any]] = {}
    for raw in cps_residual_rows:
        if raw.get("period") != period or raw.get("metric_id") != ADOPTION_METRIC:
            continue
        industry_id = raw.get("industry_id")
        if not isinstance(industry_id, str) or not industry_id:
            raise OewsRpsError("CPS residual row has an invalid industry_id")
        if industry_id in cps_by_industry:
            raise OewsRpsError(f"duplicate CPS adoption residual for {industry_id}/{period}")
        cps_by_industry[industry_id] = raw

    results: list[CpsOewsAdoptionComparisonRow] = []
    for oews in sorted(oews_rows, key=lambda item: item.industry_index):
        cps = cps_by_industry.get(oews.industry_id)
        cps_supported = cps is not None and cps.get("suppressed") is False
        cps_residual: float | None = None
        cps_sign: str | None = None
        if cps_supported:
            assert cps is not None
            raw_residual = cps.get("occupation_adjusted_industry_context_residual")
            if isinstance(raw_residual, bool) or not isinstance(raw_residual, (int, float)):
                raise OewsRpsError(
                    f"supported CPS residual is nonnumeric for {oews.industry_id}/{period}"
                )
            cps_residual = float(raw_residual)
            if not math.isfinite(cps_residual):
                raise OewsRpsError("supported CPS residual must be finite")
            cps_sign = _sign(cps_residual, cps_residual)

        direction_agreement: bool | None = None
        cps_abs: float | None = abs(cps_residual) if cps_residual is not None else None
        oews_abs_lower: float | None = None
        oews_abs_upper: float | None = None
        magnitude_relation: str | None = None
        cps_inside: bool | None = None
        if (
            cps_residual is not None
            and oews.supported
            and oews.residual_lower is not None
            and oews.residual_upper is not None
        ):
            oews_abs_lower, oews_abs_upper = _absolute_interval(
                oews.residual_lower, oews.residual_upper
            )
            cps_inside = oews.residual_lower <= cps_residual <= oews.residual_upper
            if cps_sign in {"positive", "negative"} and oews.residual_sign_identification in {
                "positive",
                "negative",
            }:
                direction_agreement = cps_sign == oews.residual_sign_identification
            if cps_abs is not None:
                if oews_abs_upper < cps_abs - 1e-12:
                    magnitude_relation = "oews_smaller"
                elif oews_abs_lower > cps_abs + 1e-12:
                    magnitude_relation = "oews_larger"
                else:
                    magnitude_relation = "overlaps_cps_magnitude"

        results.append(
            CpsOewsAdoptionComparisonRow(
                industry_index=oews.industry_index,
                industry_id=oews.industry_id,
                comparability=oews.comparability,
                period=period,
                cps_supported=cps_supported,
                oews_supported=oews.supported,
                cps_residual=cps_residual,
                cps_residual_sign=cps_sign,
                oews_point_identified=oews.point_identified,
                oews_residual_lower=oews.residual_lower,
                oews_residual_upper=oews.residual_upper,
                oews_residual_point=oews.residual_point,
                oews_residual_sign_identification=oews.residual_sign_identification,
                direction_agreement=direction_agreement,
                cps_absolute_residual=cps_abs,
                oews_absolute_residual_lower=oews_abs_lower,
                oews_absolute_residual_upper=oews_abs_upper,
                magnitude_relation=magnitude_relation,
                cps_residual_inside_oews_interval=cps_inside,
            )
        )
    return results


def summarize_cps_oews_adoption_comparison(
    rows: Sequence[CpsOewsAdoptionComparisonRow],
    *,
    period: str,
) -> dict[str, Any]:
    """Summarize independent-source agreement without forcing partially identified points."""

    relevant = [row for row in rows if row.period == period and row.comparability == "primary"]
    supported = [row for row in relevant if row.cps_supported and row.oews_supported]
    point = [row for row in supported if row.oews_point_identified and row.oews_residual_point is not None]
    partial = [row for row in supported if not row.oews_point_identified]
    direction_resolved = [row for row in supported if row.direction_agreement is not None]
    exact_cps = [float(row.cps_residual) for row in point if row.cps_residual is not None]
    exact_oews = [float(row.oews_residual_point) for row in point if row.oews_residual_point is not None]
    absolute_point_differences = [
        abs(cps - oews) for cps, oews in zip(exact_cps, exact_oews, strict=True)
    ]
    partial_widths = [
        float(row.oews_residual_upper) - float(row.oews_residual_lower)
        for row in partial
        if row.oews_residual_lower is not None and row.oews_residual_upper is not None
    ]
    return {
        "period": period,
        "primary_industry_count": len(relevant),
        "supported_primary_count": len(supported),
        "point_identified_primary_count": len(point),
        "partially_identified_primary_count": len(partial),
        "direction_resolved_count": len(direction_resolved),
        "direction_agreement_count": sum(row.direction_agreement is True for row in supported),
        "direction_disagreement_count": sum(row.direction_agreement is False for row in supported),
        "direction_indeterminate_count": sum(row.direction_agreement is None for row in supported),
        "cps_residual_inside_oews_interval_count": sum(
            row.cps_residual_inside_oews_interval is True for row in supported
        ),
        "exact_residual_rank_spearman": (
            spearman_rank_correlation(exact_cps, exact_oews) if len(point) >= 2 else None
        ),
        "median_absolute_exact_residual_difference": (
            median(absolute_point_differences) if absolute_point_differences else None
        ),
        "maximum_partial_residual_interval_width": max(partial_widths, default=0.0),
        "interpretation": (
            "OEWS is an independent establishment-side composition robustness source. "
            "Partially identified rows remain intervals; CPS and OEWS are not averaged."
        ),
    }
