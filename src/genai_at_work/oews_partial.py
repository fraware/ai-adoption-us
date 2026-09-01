"""Partial-identification diagnostics for CPS-versus-OEWS composition comparisons.

OEWS can omit an industry-by-occupation estimate even when the sum of published major
occupation groups covers nearly all published industry employment. Missing OEWS cells
are therefore treated as unknown nonnegative employment mass, not as zero. This module
bounds the L1 distance to a CPS worker-share vector conditional on the published OEWS
industry total and published occupation counts.

These bounds address unpublished-cell allocation only. They do not incorporate OEWS
sampling/model uncertainty, CPS sampling uncertainty, or rounding uncertainty in the
published point estimates.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from genai_at_work.oews import OewsCompositionRow


@dataclass(frozen=True)
class L1IdentificationBoundRow:
    """Identification interval for one CPS-versus-OEWS industry L1 distance."""

    industry_index: int
    industry_id: str
    industry_name: str
    comparability: str
    coverage: float
    cps_supported: bool
    bounds_supported: bool
    point_identified: bool
    missing_occupation_count: int
    missing_occupations: tuple[str, ...]
    residual_unpublished_employment: float | None
    residual_unpublished_mass_share: float | None
    cps_mass_in_missing_occupations: float | None
    l1_lower_bound: float | None
    l1_upper_bound: float | None
    l1_bound_width: float | None
    unsupported_reason: str | None


def _canonical_cps_weights(
    raw: object,
    occupation_ids: Sequence[str],
) -> dict[str, float] | None:
    if not isinstance(raw, Mapping):
        return None
    weights = {str(key): float(value) for key, value in raw.items()}
    canonical = {occupation_id: weights.get(occupation_id, 0.0) for occupation_id in occupation_ids}
    if any(not math.isfinite(value) or value < 0 for value in canonical.values()):
        raise ValueError("CPS worker weights must be finite and nonnegative")
    total = sum(canonical.values())
    if not math.isclose(total, 1.0, abs_tol=1e-10):
        raise ValueError(f"CPS canonical worker weights must sum to one, got {total}")
    return canonical


def _unsupported(
    row: OewsCompositionRow,
    *,
    cps_supported: bool,
    reason: str,
) -> L1IdentificationBoundRow:
    return L1IdentificationBoundRow(
        industry_index=row.industry_index,
        industry_id=row.industry_id,
        industry_name=row.industry_name,
        comparability=row.comparability,
        coverage=row.coverage,
        cps_supported=cps_supported,
        bounds_supported=False,
        point_identified=False,
        missing_occupation_count=len(row.missing_occupations),
        missing_occupations=row.missing_occupations,
        residual_unpublished_employment=None,
        residual_unpublished_mass_share=None,
        cps_mass_in_missing_occupations=None,
        l1_lower_bound=None,
        l1_upper_bound=None,
        l1_bound_width=None,
        unsupported_reason=reason,
    )


def _point_identified_bounds(
    row: OewsCompositionRow,
    *,
    cps_weights: Mapping[str, float],
    occupation_ids: Sequence[str],
) -> L1IdentificationBoundRow:
    if row.worker_weights is None:
        return _unsupported(
            row,
            cps_supported=True,
            reason="OEWS composition vector is unavailable under the coverage gate",
        )
    missing = [
        occupation_id
        for occupation_id in occupation_ids
        if occupation_id not in row.worker_weights
    ]
    if missing:
        raise ValueError("point-identification helper received an incomplete OEWS vector")
    l1 = sum(
        abs(cps_weights[occupation_id] - row.worker_weights[occupation_id])
        for occupation_id in occupation_ids
    )
    return L1IdentificationBoundRow(
        industry_index=row.industry_index,
        industry_id=row.industry_id,
        industry_name=row.industry_name,
        comparability=row.comparability,
        coverage=row.coverage,
        cps_supported=True,
        bounds_supported=True,
        point_identified=True,
        missing_occupation_count=0,
        missing_occupations=(),
        residual_unpublished_employment=0.0,
        residual_unpublished_mass_share=0.0,
        cps_mass_in_missing_occupations=0.0,
        l1_lower_bound=l1,
        l1_upper_bound=l1,
        l1_bound_width=0.0,
        unsupported_reason=None,
    )


def _missing_block_l1_extrema(
    cps_missing_weights: Sequence[float],
    residual_mass_share: float,
) -> tuple[float, float]:
    """Return min/max L1 contribution over a simplex of missing OEWS mass.

    The lower bound follows from the triangle inequality and is attainable because mass
    can be distributed across missing coordinates. The upper bound of the convex L1
    objective over the simplex occurs at a vertex, so it is the largest value obtained by
    assigning all residual OEWS mass to one missing occupation.
    """

    if not cps_missing_weights:
        if residual_mass_share > 1e-12:
            raise ValueError("positive residual mass requires at least one missing occupation")
        return 0.0, 0.0
    cps_missing_mass = sum(cps_missing_weights)
    lower = abs(cps_missing_mass - residual_mass_share)
    upper = max(
        abs(cps_weight - residual_mass_share)
        + cps_missing_mass
        - cps_weight
        for cps_weight in cps_missing_weights
    )
    return lower, upper


def l1_identification_bounds(
    oews_rows: Sequence[OewsCompositionRow],
    cps_industries: Sequence[Mapping[str, Any]],
    *,
    occupation_ids: Sequence[str],
) -> list[L1IdentificationBoundRow]:
    """Bound industry-level CPS-versus-OEWS L1 distances.

    For complete OEWS vectors, the interval collapses to the existing exact L1 distance.
    For incomplete vectors, published occupation counts are divided by the published
    all-occupations total and the remaining published-total mass is allowed to occupy any
    missing canonical occupation. If published observed occupation employment exceeds the
    published all-occupations total, a coherent residual-mass simplex cannot be formed and
    the bound fails closed instead of applying a rounding correction implicitly.
    """

    cps_by_id = {str(row["industry_id"]): row for row in cps_industries}
    results: list[L1IdentificationBoundRow] = []

    for row in oews_rows:
        cps = cps_by_id.get(row.industry_id)
        cps_raw = cps.get("worker_weights") if cps is not None else None
        cps_weights = _canonical_cps_weights(cps_raw, occupation_ids)
        if cps_weights is None:
            results.append(
                _unsupported(
                    row,
                    cps_supported=False,
                    reason="CPS worker-share vector is unavailable",
                )
            )
            continue
        if not row.supported or row.worker_weights is None:
            results.append(
                _unsupported(
                    row,
                    cps_supported=True,
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
            results.append(
                _point_identified_bounds(
                    row,
                    cps_weights=cps_weights,
                    occupation_ids=occupation_ids,
                )
            )
            continue

        total = row.total_employment
        if total is None or not math.isfinite(total) or total <= 0:
            results.append(
                _unsupported(
                    row,
                    cps_supported=True,
                    reason="published OEWS all-occupations employment is unavailable",
                )
            )
            continue
        if row.observed_major_group_employment > total + 1e-9:
            results.append(
                _unsupported(
                    row,
                    cps_supported=True,
                    reason=(
                        "published observed occupation employment exceeds the published "
                        "all-occupations total; unpublished-cell bounds would require an "
                        "explicit rounding model"
                    ),
                )
            )
            continue

        residual_employment = total - row.observed_major_group_employment
        residual_share = residual_employment / total
        missing_set = set(missing)
        observed_l1 = 0.0
        for occupation_id in occupation_ids:
            if occupation_id in missing_set:
                continue
            employment = row.occupation_employment.get(occupation_id)
            if employment is None:
                raise AssertionError("missing occupation bookkeeping is inconsistent")
            observed_share = employment / total
            observed_l1 += abs(cps_weights[occupation_id] - observed_share)

        cps_missing_weights = [cps_weights[occupation_id] for occupation_id in missing]
        cps_missing_mass = sum(cps_missing_weights)
        missing_lower, missing_upper = _missing_block_l1_extrema(
            cps_missing_weights,
            residual_share,
        )
        lower = observed_l1 + missing_lower
        upper = observed_l1 + missing_upper
        if lower > upper + 1e-12:
            raise AssertionError("computed L1 lower bound exceeds upper bound")

        results.append(
            L1IdentificationBoundRow(
                industry_index=row.industry_index,
                industry_id=row.industry_id,
                industry_name=row.industry_name,
                comparability=row.comparability,
                coverage=row.coverage,
                cps_supported=True,
                bounds_supported=True,
                point_identified=False,
                missing_occupation_count=len(missing),
                missing_occupations=missing,
                residual_unpublished_employment=residual_employment,
                residual_unpublished_mass_share=residual_share,
                cps_mass_in_missing_occupations=cps_missing_mass,
                l1_lower_bound=lower,
                l1_upper_bound=upper,
                l1_bound_width=upper - lower,
                unsupported_reason=None,
            )
        )

    return results
