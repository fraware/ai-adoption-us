"""Descriptive stability diagnostics for CPS occupation-composition domains.

These diagnostics are intentionally not design-based standard errors. Basic Monthly CPS
uses a complex rotating-panel design, and the public-use final weights alone do not encode
the replicate structure needed for direct replication variance estimates. The measures here
flag thin or unstable industry domains using unweighted person-month counts, final-weight
dispersion, and within-quarter composition movement.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import combinations
from statistics import median

from genai_at_work.cps import CPSPerson, IndustryComposition, build_composition


@dataclass(frozen=True)
class CpsDomainDiagnostic:
    """Non-inferential reliability diagnostics for one CPS industry domain."""

    industry_index: int
    industry_id: str
    person_month_count: int
    minimum_month_person_count: int
    maximum_month_person_count: int
    monthly_person_counts: dict[str, int]
    pooled_weighted_population: float
    kish_effective_person_months: float
    kish_fraction_of_person_months: float
    maximum_person_month_weight_share: float
    pooled_top_occupation: str | None
    pooled_top_occupation_share: float | None
    pooled_top_two_margin: float | None
    monthly_top_occupations: dict[str, str | None]
    monthly_top_occupation_agreement: bool
    median_pairwise_month_l1: float | None
    maximum_pairwise_month_l1: float | None
    maximum_month_to_pooled_l1: float | None


def _canonical_weights(
    composition: IndustryComposition,
    occupation_ids: tuple[str, ...],
) -> dict[str, float] | None:
    if composition.worker_weights is None:
        return None
    return {
        occupation_id: composition.worker_weights.get(occupation_id, 0.0)
        for occupation_id in occupation_ids
    }


def _l1(left: dict[str, float], right: dict[str, float]) -> float:
    if set(left) != set(right):
        raise ValueError("composition vectors must have identical canonical keys")
    return sum(abs(left[key] - right[key]) for key in left)


def _top_summary(weights: dict[str, float] | None) -> tuple[str | None, float | None, float | None]:
    if not weights:
        return None, None, None
    ranked = sorted(weights.items(), key=lambda item: (-item[1], item[0]))
    top_id, top_share = ranked[0]
    second_share = ranked[1][1] if len(ranked) > 1 else 0.0
    return top_id, top_share, top_share - second_share


def build_cps_domain_diagnostics(
    people: list[CPSPerson],
    *,
    occupation_ids: tuple[str, ...],
    coverage_gate: float = 0.98,
) -> list[CpsDomainDiagnostic]:
    """Compute descriptive domain stability measures from one pooled CPS quarter.

    The Kish quantity is reported as an effective *person-month* count induced only by
    final-weight dispersion. It does not account for CPS clustering, stratification, the
    4-8-4 rotation pattern, or repeat observations across months, and must not be used as a
    design-based effective sample size or standard-error substitute.
    """

    if not people:
        raise ValueError("CPS domain diagnostics require at least one in-scope person")
    months = tuple(sorted({person.month for person in people}))
    if not months:
        raise ValueError("CPS domain diagnostics could not resolve months")

    pooled = {
        row.industry_id: row
        for row in build_composition(people, coverage_gate=coverage_gate)
    }
    monthly: dict[str, dict[str, IndustryComposition]] = {}
    for month in months:
        month_people = [person for person in people if person.month == month]
        monthly[month] = {
            row.industry_id: row
            for row in build_composition(month_people, coverage_gate=coverage_gate)
        }

    people_by_industry: dict[str, list[CPSPerson]] = {}
    for person in people:
        people_by_industry.setdefault(person.industry_id, []).append(person)

    diagnostics: list[CpsDomainDiagnostic] = []
    for industry_id, industry_people in people_by_industry.items():
        pooled_row = pooled[industry_id]
        pooled_weights = _canonical_weights(pooled_row, occupation_ids)
        month_counts = {
            month: sum(person.month == month for person in industry_people)
            for month in months
        }
        weights = [person.worker_weight for person in industry_people]
        weight_sum = sum(weights)
        weight_square_sum = sum(weight * weight for weight in weights)
        kish = weight_sum * weight_sum / weight_square_sum if weight_square_sum > 0 else 0.0
        maximum_weight_share = max(weights) / weight_sum if weight_sum > 0 else 0.0

        monthly_weights: dict[str, dict[str, float] | None] = {}
        monthly_tops: dict[str, str | None] = {}
        for month in months:
            month_row = monthly[month].get(industry_id)
            canonical = (
                _canonical_weights(month_row, occupation_ids)
                if month_row is not None
                else None
            )
            monthly_weights[month] = canonical
            monthly_tops[month] = _top_summary(canonical)[0]

        pairwise_l1 = [
            _l1(left, right)
            for first, second in combinations(months, 2)
            if (left := monthly_weights[first]) is not None
            and (right := monthly_weights[second]) is not None
        ]
        month_to_pooled_l1 = [
            _l1(month_weights, pooled_weights)
            for month_weights in monthly_weights.values()
            if month_weights is not None and pooled_weights is not None
        ]
        top_id, top_share, top_margin = _top_summary(pooled_weights)
        observed_month_tops = [value for value in monthly_tops.values() if value is not None]
        monthly_top_agreement = (
            len(observed_month_tops) == len(months)
            and len(set(observed_month_tops)) == 1
        )

        diagnostics.append(
            CpsDomainDiagnostic(
                industry_index=pooled_row.industry_index,
                industry_id=industry_id,
                person_month_count=len(industry_people),
                minimum_month_person_count=min(month_counts.values()),
                maximum_month_person_count=max(month_counts.values()),
                monthly_person_counts=month_counts,
                pooled_weighted_population=weight_sum,
                kish_effective_person_months=kish,
                kish_fraction_of_person_months=(
                    kish / len(industry_people) if industry_people else 0.0
                ),
                maximum_person_month_weight_share=maximum_weight_share,
                pooled_top_occupation=top_id,
                pooled_top_occupation_share=top_share,
                pooled_top_two_margin=top_margin,
                monthly_top_occupations=monthly_tops,
                monthly_top_occupation_agreement=monthly_top_agreement,
                median_pairwise_month_l1=(median(pairwise_l1) if pairwise_l1 else None),
                maximum_pairwise_month_l1=(max(pairwise_l1) if pairwise_l1 else None),
                maximum_month_to_pooled_l1=(
                    max(month_to_pooled_l1) if month_to_pooled_l1 else None
                ),
            )
        )

    return sorted(diagnostics, key=lambda row: row.industry_index)


def validate_domain_diagnostics(rows: list[CpsDomainDiagnostic]) -> None:
    """Fail closed on internally inconsistent diagnostic output."""

    if len(rows) != 20:
        raise ValueError(f"expected 20 CPS industry diagnostics, found {len(rows)}")
    for row in rows:
        if row.person_month_count <= 0:
            raise ValueError(f"empty CPS domain: {row.industry_id}")
        if not 0 < row.kish_effective_person_months <= row.person_month_count + 1e-9:
            raise ValueError(f"invalid Kish diagnostic for {row.industry_id}")
        if not 0 < row.kish_fraction_of_person_months <= 1 + 1e-12:
            raise ValueError(f"invalid Kish fraction for {row.industry_id}")
        if not 0 < row.maximum_person_month_weight_share <= 1:
            raise ValueError(f"invalid maximum weight share for {row.industry_id}")
        for metric in (
            row.median_pairwise_month_l1,
            row.maximum_pairwise_month_l1,
            row.maximum_month_to_pooled_l1,
        ):
            if metric is not None and (not math.isfinite(metric) or not 0 <= metric <= 2):
                raise ValueError(f"invalid L1 diagnostic for {row.industry_id}: {metric}")
