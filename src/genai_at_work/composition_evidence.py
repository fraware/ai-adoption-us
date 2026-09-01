"""Evidence-tier classification for CPS occupation-composition inputs.

This module turns versioned empirical reliability diagnostics into an explicit evidence tier.
It does not perform statistical inference. A project governance rule can demote a definitionally
comparable industry to sensitivity-only when its pooled CPS composition is too sensitive to the
constituent months.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CompositionEvidenceTierRow:
    """Evidence-tier decision for one industry."""

    industry_index: int
    industry_id: str
    industry_name: str
    source_comparability: str
    evidence_tier: str
    required_periods: tuple[str, ...]
    maximum_leave_one_month_out_l1_by_period: dict[str, float]
    maximum_leave_one_month_out_l1_across_required_periods: float | None
    stability_threshold_l1: float
    passes_stability_rule: bool | None
    reason: str


def classify_composition_evidence(
    period_rows: Sequence[Mapping[str, Any]],
    *,
    required_periods: Sequence[str],
    threshold_l1: float,
) -> list[CompositionEvidenceTierRow]:
    """Classify industry composition evidence using a versioned stability policy.

    ``period_rows`` must contain one row per industry-period with the fields produced by
    ``period_reliability.csv``. Definitionally limited/excluded source categories retain those
    tiers. Only ``primary`` rows are eligible for ``primary_stable``.
    """

    if not 0 <= threshold_l1 <= 2:
        raise ValueError("L1 stability threshold must be between 0 and 2")
    periods = tuple(str(period) for period in required_periods)
    if not periods or len(set(periods)) != len(periods):
        raise ValueError("required periods must be a non-empty unique sequence")

    by_industry: dict[str, dict[str, Mapping[str, Any]]] = {}
    metadata: dict[str, tuple[int, str, str]] = {}
    for row in period_rows:
        industry_id = str(row["industry_id"])
        period = str(row["period"])
        index = int(row["industry_index"])
        name = str(row["industry_name"])
        comparability = str(row["comparability"])
        previous = metadata.setdefault(industry_id, (index, name, comparability))
        if previous != (index, name, comparability):
            raise ValueError(f"inconsistent industry metadata for {industry_id}")
        industry_periods = by_industry.setdefault(industry_id, {})
        if period in industry_periods:
            raise ValueError(f"duplicate reliability row for {industry_id} {period}")
        industry_periods[period] = row

    output: list[CompositionEvidenceTierRow] = []
    for industry_id, (index, name, comparability) in metadata.items():
        period_map = by_industry[industry_id]
        missing = [period for period in periods if period not in period_map]
        if missing:
            raise ValueError(f"missing required reliability periods for {industry_id}: {missing}")
        diagnostics = {
            period: float(period_map[period]["maximum_leave_one_month_out_l1_to_quarter"])
            for period in periods
        }
        if comparability == "primary":
            maximum = max(diagnostics.values())
            stable = all(value <= threshold_l1 for value in diagnostics.values())
            tier = "primary_stable" if stable else "sensitivity_unstable"
            reason = (
                "passes the versioned leave-one-month-out stability rule in every required period"
                if stable
                else "fails the versioned leave-one-month-out stability rule in at least one required period"
            )
        elif comparability == "limited":
            maximum = max(diagnostics.values())
            stable = None
            tier = "limited"
            reason = "source-universe comparability is limited under the OEWS crosswalk"
        elif comparability == "excluded":
            maximum = max(diagnostics.values())
            stable = None
            tier = "excluded"
            reason = "source-universe definitions are excluded from the primary OEWS-CPS comparison"
        else:
            raise ValueError(f"unknown source comparability category: {comparability}")

        output.append(
            CompositionEvidenceTierRow(
                industry_index=index,
                industry_id=industry_id,
                industry_name=name,
                source_comparability=comparability,
                evidence_tier=tier,
                required_periods=periods,
                maximum_leave_one_month_out_l1_by_period=diagnostics,
                maximum_leave_one_month_out_l1_across_required_periods=maximum,
                stability_threshold_l1=threshold_l1,
                passes_stability_rule=stable,
                reason=reason,
            )
        )
    return sorted(output, key=lambda row: row.industry_index)
