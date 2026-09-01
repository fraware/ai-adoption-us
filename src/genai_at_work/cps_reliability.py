"""Empirical reliability diagnostics for pooled CPS occupation-composition estimates.

These diagnostics are deliberately descriptive. They quantify weight concentration and
within-quarter instability of worker-share occupation vectors without pretending to be
CPS design-based standard errors. In particular, Kish weight-dispersion effective sample
size does not account for CPS clustering, stratification, or rotation-group dependence and
must not be interpreted as an inferential effective sample size.
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

from genai_at_work.cps import CPSPerson, build_composition


@dataclass(frozen=True)
class CPSIndustryReliabilityRow:
    """One period-industry diagnostic record."""

    industry_id: str
    industry_index: int
    person_month_count: int
    weighted_worker_population: float
    kish_weight_dispersion_effective_n: float
    monthly_person_month_counts: dict[str, int]
    monthly_kish_weight_dispersion_effective_n: dict[str, float]
    monthly_l1_to_quarter: dict[str, float]
    leave_one_month_out_l1_to_quarter: dict[str, float]
    maximum_pairwise_month_l1: float
    maximum_monthly_l1_to_quarter: float
    maximum_leave_one_month_out_l1_to_quarter: float
    quarter_top_occupation: str
    monthly_top_occupations: dict[str, str]
    all_monthly_tops_match_quarter: bool


@dataclass(frozen=True)
class CPSCrossVintageReliabilityRow:
    """Cross-vintage stability diagnostic for one industry."""

    industry_id: str
    industry_index: int
    l1_q2_2025_to_q2_2026: float
    within_quarter_l1_envelope: float
    year_over_year_to_within_quarter_ratio: float | None
    year_over_year_exceeds_within_quarter_envelope: bool
    minimum_kish_weight_dispersion_effective_n: float
    maximum_leave_one_month_out_l1: float
    tops_match_across_quarters: bool


def l1_distance(left: Mapping[str, float], right: Mapping[str, float]) -> float:
    """Return L1 distance between sparse probability vectors."""

    keys = set(left) | set(right)
    return sum(abs(float(left.get(key, 0.0)) - float(right.get(key, 0.0))) for key in keys)


def kish_weight_dispersion_effective_n(weights: Iterable[float]) -> float:
    """Return Kish's weight-dispersion diagnostic effective n.

    This quantity only measures unequal weighting: ``(sum w)^2 / sum(w^2)``. It is not a
    CPS design-based effective sample size because it omits clustering, stratification,
    and rotation-group covariance.
    """

    materialized = [float(weight) for weight in weights if float(weight) > 0]
    if not materialized:
        return 0.0
    numerator = sum(materialized) ** 2
    denominator = sum(weight * weight for weight in materialized)
    return numerator / denominator if denominator > 0 else 0.0


def _worker_vectors(people: Sequence[CPSPerson]) -> dict[str, dict[str, float]]:
    rows = build_composition(people, coverage_gate=0.98)
    vectors: dict[str, dict[str, float]] = {}
    for row in rows:
        if row.worker_suppressed or row.worker_weights is None:
            raise ValueError(f"worker composition unexpectedly unsupported: {row.industry_id}")
        vectors[row.industry_id] = dict(row.worker_weights)
    return vectors


def _top_occupation(weights: Mapping[str, float]) -> str:
    if not weights:
        raise ValueError("cannot select top occupation from empty composition")
    return max(weights, key=weights.__getitem__)


def build_period_reliability(
    people: Sequence[CPSPerson],
    *,
    months: Sequence[str],
) -> list[CPSIndustryReliabilityRow]:
    """Compute within-quarter reliability diagnostics by industry.

    The quarter vector is compared with each single-month vector and each leave-one-month-out
    vector. These are empirical perturbation diagnostics, not statistical significance tests.
    """

    if len(months) != 3 or len(set(months)) != 3:
        raise ValueError("reliability diagnostics require exactly three distinct quarter months")
    month_set = set(months)
    observed_months = {person.month for person in people}
    if not observed_months <= month_set:
        raise ValueError(f"people contain unexpected months: {sorted(observed_months - month_set)}")

    quarter_vectors = _worker_vectors(people)
    by_industry: dict[str, list[CPSPerson]] = defaultdict(list)
    industry_index: dict[str, int] = {}
    for person in people:
        by_industry[person.industry_id].append(person)
        previous = industry_index.setdefault(person.industry_id, person.industry_index)
        if previous != person.industry_index:
            raise ValueError(f"conflicting industry index for {person.industry_id}")

    rows: list[CPSIndustryReliabilityRow] = []
    for industry_id, industry_people in by_industry.items():
        quarter = quarter_vectors[industry_id]
        monthly_vectors: dict[str, dict[str, float]] = {}
        monthly_counts: dict[str, int] = {}
        monthly_ess: dict[str, float] = {}
        monthly_l1: dict[str, float] = {}
        monthly_tops: dict[str, str] = {}

        for month in months:
            month_people = [person for person in industry_people if person.month == month]
            if not month_people:
                raise ValueError(f"industry {industry_id} has no observations in {month}")
            vector = _worker_vectors(month_people).get(industry_id)
            if vector is None:
                raise ValueError(f"industry {industry_id} lacks supported monthly vector in {month}")
            monthly_vectors[month] = vector
            monthly_counts[month] = len(month_people)
            monthly_ess[month] = kish_weight_dispersion_effective_n(
                person.worker_weight for person in month_people
            )
            monthly_l1[month] = l1_distance(vector, quarter)
            monthly_tops[month] = _top_occupation(vector)

        leave_one_out_l1: dict[str, float] = {}
        for omitted_month in months:
            retained = [person for person in industry_people if person.month != omitted_month]
            vector = _worker_vectors(retained).get(industry_id)
            if vector is None:
                raise ValueError(
                    f"industry {industry_id} lacks leave-one-month-out vector for {omitted_month}"
                )
            leave_one_out_l1[omitted_month] = l1_distance(vector, quarter)

        pairwise = [
            l1_distance(monthly_vectors[left], monthly_vectors[right])
            for index, left in enumerate(months)
            for right in months[index + 1 :]
        ]
        quarter_top = _top_occupation(quarter)
        rows.append(
            CPSIndustryReliabilityRow(
                industry_id=industry_id,
                industry_index=industry_index[industry_id],
                person_month_count=len(industry_people),
                weighted_worker_population=sum(
                    person.worker_weight for person in industry_people
                ),
                kish_weight_dispersion_effective_n=kish_weight_dispersion_effective_n(
                    person.worker_weight for person in industry_people
                ),
                monthly_person_month_counts=monthly_counts,
                monthly_kish_weight_dispersion_effective_n=monthly_ess,
                monthly_l1_to_quarter=monthly_l1,
                leave_one_month_out_l1_to_quarter=leave_one_out_l1,
                maximum_pairwise_month_l1=max(pairwise),
                maximum_monthly_l1_to_quarter=max(monthly_l1.values()),
                maximum_leave_one_month_out_l1_to_quarter=max(leave_one_out_l1.values()),
                quarter_top_occupation=quarter_top,
                monthly_top_occupations=monthly_tops,
                all_monthly_tops_match_quarter=all(
                    top == quarter_top for top in monthly_tops.values()
                ),
            )
        )
    return sorted(rows, key=lambda row: row.industry_index)


def compare_period_reliability(
    period_2025: Sequence[CPSIndustryReliabilityRow],
    period_2026: Sequence[CPSIndustryReliabilityRow],
    *,
    quarter_weights_2025: Mapping[str, Mapping[str, float]],
    quarter_weights_2026: Mapping[str, Mapping[str, float]],
) -> list[CPSCrossVintageReliabilityRow]:
    """Compare Q2 worker-composition stability without treating it as a significance test."""

    by_2025 = {row.industry_id: row for row in period_2025}
    by_2026 = {row.industry_id: row for row in period_2026}
    if set(by_2025) != set(by_2026):
        raise ValueError("period reliability industry universes do not match")

    rows: list[CPSCrossVintageReliabilityRow] = []
    for industry_id in by_2025:
        left = by_2025[industry_id]
        right = by_2026[industry_id]
        if left.industry_index != right.industry_index:
            raise ValueError(f"industry index mismatch for {industry_id}")
        weights_2025 = quarter_weights_2025.get(industry_id)
        weights_2026 = quarter_weights_2026.get(industry_id)
        if weights_2025 is None or weights_2026 is None:
            raise ValueError(f"missing quarter weights for {industry_id}")
        year_l1 = l1_distance(weights_2025, weights_2026)
        envelope = max(left.maximum_pairwise_month_l1, right.maximum_pairwise_month_l1)
        ratio = year_l1 / envelope if envelope > 0 else None
        rows.append(
            CPSCrossVintageReliabilityRow(
                industry_id=industry_id,
                industry_index=left.industry_index,
                l1_q2_2025_to_q2_2026=year_l1,
                within_quarter_l1_envelope=envelope,
                year_over_year_to_within_quarter_ratio=ratio,
                year_over_year_exceeds_within_quarter_envelope=year_l1 > envelope,
                minimum_kish_weight_dispersion_effective_n=min(
                    left.kish_weight_dispersion_effective_n,
                    right.kish_weight_dispersion_effective_n,
                ),
                maximum_leave_one_month_out_l1=max(
                    left.maximum_leave_one_month_out_l1_to_quarter,
                    right.maximum_leave_one_month_out_l1_to_quarter,
                ),
                tops_match_across_quarters=(
                    left.quarter_top_occupation == right.quarter_top_occupation
                ),
            )
        )
    return sorted(rows, key=lambda row: row.industry_index)


def verify_reference_vectors(
    computed: Mapping[str, Mapping[str, float]],
    reference: Sequence[Mapping[str, object]],
    *,
    tolerance: float = 1e-10,
) -> None:
    """Assert that recomputed worker vectors reproduce a committed reference artifact."""

    reference_by_id = {str(row["industry_id"]): row for row in reference}
    if set(computed) != set(reference_by_id):
        raise ValueError("computed/reference industry universes differ")
    for industry_id, weights in computed.items():
        raw_reference = reference_by_id[industry_id].get("worker_weights")
        if not isinstance(raw_reference, Mapping):
            raise ValueError(f"reference worker weights unavailable for {industry_id}")
        reference_weights = {str(key): float(value) for key, value in raw_reference.items()}
        distance = l1_distance(weights, reference_weights)
        if not math.isclose(distance, 0.0, abs_tol=tolerance):
            raise ValueError(
                f"recomputed worker composition disagrees with reference for {industry_id}: "
                f"L1={distance}"
            )
