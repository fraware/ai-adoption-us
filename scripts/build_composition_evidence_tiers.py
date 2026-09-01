#!/usr/bin/env python3
"""Apply the versioned CPS composition evidence policy to frozen robustness artifacts.

This is an offline governance step. It does not fetch CPS, OEWS, or RPS data. The full
unfiltered robustness results remain untouched; this script adds a stability-qualified summary
for primary-evidence use and retains unstable primary industries as sensitivity evidence.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from genai_at_work.composition_evidence import classify_composition_evidence


def _load_json(path: Path) -> dict[str, Any]:
    raw: object = json.loads(path.read_text())
    if not isinstance(raw, dict):
        raise ValueError(f"expected JSON object in {path}")
    return {str(key): value for key, value in raw.items()}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"cannot write empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _float(row: dict[str, str], key: str) -> float | None:
    value = row.get(key, "")
    return float(value) if value not in (None, "") else None


def _bool(row: dict[str, str], key: str) -> bool | None:
    value = row.get(key, "")
    if value == "True":
        return True
    if value == "False":
        return False
    return None


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2.0


def _exact_summary(
    rows: list[dict[str, str]],
    *,
    stable_ids: set[str] | None,
) -> dict[str, object]:
    selected = [
        row
        for row in rows
        if row.get("comparability") == "primary"
        and _float(row, "l1_distance") is not None
        and (stable_ids is None or row["industry_id"] in stable_ids)
    ]
    l1 = [value for row in selected if (value := _float(row, "l1_distance")) is not None]
    cosine = [
        value for row in selected if (value := _float(row, "cosine_similarity")) is not None
    ]
    spearman = [
        value
        for row in selected
        if (value := _float(row, "spearman_rank_correlation")) is not None
    ]
    top = sum(_bool(row, "top_occupation_agreement") is True for row in selected)
    return {
        "industry_count": len(selected),
        "median_l1_distance": _median(l1),
        "median_cosine_similarity": _median(cosine),
        "median_spearman_rank_correlation": _median(spearman),
        "top_occupation_agreement_count": top,
        "top_occupation_agreement_rate": top / len(selected) if selected else None,
    }


def _bound_summary(
    rows: list[dict[str, str]],
    *,
    stable_ids: set[str] | None,
) -> dict[str, object]:
    selected = [
        row
        for row in rows
        if row.get("comparability") == "primary"
        and row.get("bounds_supported") == "True"
        and (stable_ids is None or row["industry_id"] in stable_ids)
    ]
    lower = [
        value for row in selected if (value := _float(row, "l1_lower_bound")) is not None
    ]
    upper = [
        value for row in selected if (value := _float(row, "l1_upper_bound")) is not None
    ]
    widths = [
        value for row in selected if (value := _float(row, "l1_bound_width")) is not None
    ]
    partial = sum(row.get("point_identified") == "False" for row in selected)
    return {
        "industry_count": len(selected),
        "partially_identified_count": partial,
        "median_l1_lower_bound": _median(lower),
        "median_l1_upper_bound": _median(upper),
        "maximum_l1_bound_width": max(widths, default=0.0),
    }


def _vintage_summary(
    rows: list[dict[str, str]],
    *,
    stable_ids: set[str] | None,
) -> dict[str, object]:
    selected = [
        row
        for row in rows
        if row.get("comparability") == "primary"
        and row.get("supported") == "True"
        and (stable_ids is None or row["industry_id"] in stable_ids)
    ]
    l1 = [value for row in selected if (value := _float(row, "l1_distance")) is not None]
    cosine = [
        value for row in selected if (value := _float(row, "cosine_similarity")) is not None
    ]
    spearman = [
        value
        for row in selected
        if (value := _float(row, "spearman_rank_correlation")) is not None
    ]
    top = sum(_bool(row, "top_occupation_agreement") is True for row in selected)
    return {
        "industry_count": len(selected),
        "median_l1_distance": _median(l1),
        "median_cosine_similarity": _median(cosine),
        "median_spearman_rank_correlation": _median(spearman),
        "top_occupation_agreement_count": top,
        "top_occupation_agreement_rate": top / len(selected) if selected else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--period-reliability", type=Path, required=True)
    parser.add_argument("--exact-2025", type=Path, required=True)
    parser.add_argument("--exact-2026", type=Path, required=True)
    parser.add_argument("--bounds-2025", type=Path, required=True)
    parser.add_argument("--bounds-2026", type=Path, required=True)
    parser.add_argument("--cps-vintage-comparison", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--validation-report", type=Path, required=True)
    parser.add_argument("--source-build-commit", required=True)
    args = parser.parse_args()

    policy = _load_json(args.policy)
    rule = policy.get("primary_stability_rule")
    if not isinstance(rule, dict):
        raise ValueError("policy primary_stability_rule must be an object")
    threshold = float(rule["threshold_l1"])
    required_periods_raw = rule.get("required_periods_for_current_cross-vintage_checkpoint")
    if not isinstance(required_periods_raw, list):
        raise ValueError("policy required periods must be a list")
    required_periods = [str(value) for value in required_periods_raw]

    period_rows = _read_csv(args.period_reliability)
    tiers = classify_composition_evidence(
        period_rows,
        required_periods=required_periods,
        threshold_l1=threshold,
    )
    stable_ids = {row.industry_id for row in tiers if row.evidence_tier == "primary_stable"}
    unstable = [row for row in tiers if row.evidence_tier == "sensitivity_unstable"]
    limited = [row for row in tiers if row.evidence_tier == "limited"]
    excluded = [row for row in tiers if row.evidence_tier == "excluded"]

    exact_2025 = _read_csv(args.exact_2025)
    exact_2026 = _read_csv(args.exact_2026)
    bounds_2025 = _read_csv(args.bounds_2025)
    bounds_2026 = _read_csv(args.bounds_2026)
    vintage = _read_csv(args.cps_vintage_comparison)

    unfiltered = {
        "oews_vs_cps_2025_exact": _exact_summary(exact_2025, stable_ids=None),
        "oews_vs_cps_2026_exact": _exact_summary(exact_2026, stable_ids=None),
        "oews_vs_cps_2025_bounds": _bound_summary(bounds_2025, stable_ids=None),
        "oews_vs_cps_2026_bounds": _bound_summary(bounds_2026, stable_ids=None),
        "cps_2025_vs_2026": _vintage_summary(vintage, stable_ids=None),
    }
    stable = {
        "oews_vs_cps_2025_exact": _exact_summary(exact_2025, stable_ids=stable_ids),
        "oews_vs_cps_2026_exact": _exact_summary(exact_2026, stable_ids=stable_ids),
        "oews_vs_cps_2025_bounds": _bound_summary(bounds_2025, stable_ids=stable_ids),
        "oews_vs_cps_2026_bounds": _bound_summary(bounds_2026, stable_ids=stable_ids),
        "cps_2025_vs_2026": _vintage_summary(vintage, stable_ids=stable_ids),
    }

    tier_rows: list[dict[str, object]] = []
    for row in tiers:
        tier_rows.append(
            {
                "industry_index": row.industry_index,
                "industry_id": row.industry_id,
                "industry_name": row.industry_name,
                "source_comparability": row.source_comparability,
                "evidence_tier": row.evidence_tier,
                "stability_threshold_l1": row.stability_threshold_l1,
                "max_lomo_l1_2025_q2": row.maximum_leave_one_month_out_l1_by_period.get(
                    "2025-Q2"
                ),
                "max_lomo_l1_2026_q2": row.maximum_leave_one_month_out_l1_by_period.get(
                    "2026-Q2"
                ),
                "max_lomo_l1_across_required_periods": (
                    row.maximum_leave_one_month_out_l1_across_required_periods
                ),
                "passes_stability_rule": row.passes_stability_rule,
                "reason": row.reason,
            }
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(args.output_dir / "industry_evidence_tiers.csv", tier_rows)
    (args.output_dir / "industry_evidence_tiers.json").write_text(
        json.dumps([asdict(row) for row in tiers], indent=2, sort_keys=True) + "\n"
    )

    generated_at = datetime.now(UTC).isoformat()
    summary = {
        "status": "stability-qualified CPS/OEWS composition evidence tiers built",
        "generated_at_utc": generated_at,
        "source_build_commit": args.source_build_commit,
        "policy_version": str(policy["version"]),
        "policy_status": str(policy["status"]),
        "stability_threshold_l1": threshold,
        "stability_threshold_total_variation": threshold / 2.0,
        "required_periods": required_periods,
        "primary_stable_industry_count": len(stable_ids),
        "sensitivity_unstable_industry_count": len(unstable),
        "sensitivity_unstable_industries": [row.industry_id for row in unstable],
        "limited_industry_count": len(limited),
        "excluded_industry_count": len(excluded),
        "unfiltered_primary_summary": unfiltered,
        "stability_qualified_primary_summary": stable,
        "retrospective_disclosure": str(policy["retrospective_disclosure"]),
        "noninferential_boundary": str(policy["noninferential_boundary"]),
        "sample_redesign_caveat": (
            "Both Q2 2025 and Q2 2026 fall inside the CPS 2020-Census-based sample redesign "
            "phase-in, which began in April 2025 and is scheduled to complete in July 2026. "
            "BLS expects negligible effects on published estimates, but the transition is "
            "retained as a comparability caveat for custom thin-domain composition estimates."
        ),
        "scientific_boundary": (
            "This evidence-tier layer qualifies the reliability of CPS composition inputs. It "
            "does not identify an RPS industry-context effect and does not convert descriptive "
            "stability diagnostics into design-based uncertainty estimates."
        ),
    }
    (args.output_dir / "validation_checks.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )

    unstable_names = ", ".join(row.industry_name for row in unstable) or "none"
    stable_2025_exact = stable["oews_vs_cps_2025_exact"]
    stable_2026_exact = stable["oews_vs_cps_2026_exact"]
    stable_2025_bounds = stable["oews_vs_cps_2025_bounds"]
    stable_2026_bounds = stable["oews_vs_cps_2026_bounds"]
    stable_vintage = stable["cps_2025_vs_2026"]
    report = f"""# Stability-qualified CPS/OEWS composition evidence

## Policy status

This checkpoint applies `{policy['version']}`. The rule was adopted **after** inspecting the
Q2-2025/Q2-2026 empirical reliability diagnostics, so it is not presented as a preregistered
threshold for this checkpoint. Full unfiltered results remain preserved beside this layer.

A definitionally primary-comparable industry is classified as `primary_stable` when dropping any
one constituent month changes the pooled 22-group CPS worker composition by at most **{threshold:.2f}
L1** in every required quarter. Because total variation is half the L1 distance, this corresponds
to at most **{threshold / 2:.2f} total-variation mass**. This is a project robustness standard, not
a BLS/Census significance threshold.

## Classification

- primary stable industries: **{len(stable_ids)}**
- primary sensitivity-only industries: **{len(unstable)}**
- sensitivity-only names: **{unstable_names}**
- limited-comparability industries: **{len(limited)}**
- excluded industries: **{len(excluded)}**

No observation is deleted. Sensitivity-only industries remain in the unfiltered tables and must be
shown when the full robustness picture is reported.

## Stability-qualified OEWS comparison

Among stable primary industries with complete 22-group OEWS vectors:

- May-2025 OEWS vs Q2-2025 CPS exact median L1: **{stable_2025_exact['median_l1_distance']}** across **{stable_2025_exact['industry_count']}** industries
- May-2025 OEWS vs Q2-2025 CPS exact median cosine: **{stable_2025_exact['median_cosine_similarity']}**
- May-2025 OEWS vs Q2-2025 CPS exact median Spearman: **{stable_2025_exact['median_spearman_rank_correlation']}**
- May-2025 OEWS vs Q2-2026 CPS exact median L1: **{stable_2026_exact['median_l1_distance']}** across **{stable_2026_exact['industry_count']}** industries
- May-2025 OEWS vs Q2-2026 CPS exact median cosine: **{stable_2026_exact['median_cosine_similarity']}**
- May-2025 OEWS vs Q2-2026 CPS exact median Spearman: **{stable_2026_exact['median_spearman_rank_correlation']}**

Using partial-identification bounds so that unpublished OEWS cells do not force industry deletion:

- Q2-2025 stable-primary median L1 interval: **[{stable_2025_bounds['median_l1_lower_bound']}, {stable_2025_bounds['median_l1_upper_bound']}]** across **{stable_2025_bounds['industry_count']}** industries
- Q2-2026 stable-primary median L1 interval: **[{stable_2026_bounds['median_l1_lower_bound']}, {stable_2026_bounds['median_l1_upper_bound']}]** across **{stable_2026_bounds['industry_count']}** industries

The CPS stable-primary Q2-2025 versus Q2-2026 worker-composition comparison has median L1
**{stable_vintage['median_l1_distance']}**, median cosine **{stable_vintage['median_cosine_similarity']}**,
and median Spearman **{stable_vintage['median_spearman_rank_correlation']}** across
**{stable_vintage['industry_count']}** industries.

## Methodological caveats

The stability gate is descriptive. Kish weight-dispersion effective n is also descriptive and does
not account for CPS clustering, stratification, or rotation-group dependence. Formal uncertainty
for custom 22-dimensional industry-composition vectors remains an open design-based inference task.

Both comparison quarters occur during the CPS 2020-Census-based sample redesign phase-in, which
BLS says began in April 2025 and will complete in July 2026. BLS expects the redesign to have a
negligible effect on published estimates. We nevertheless retain it as a comparability caveat for
custom thin-domain estimates.

## Scientific boundary

This layer decides how strongly to rely on CPS composition as an input. It does not establish an
RPS industry-context effect, productivity effect, or causal mechanism. Those claims remain gated on
an authorized compatible RPS occupation vintage and the subsequent robustness program.
"""
    args.validation_report.parent.mkdir(parents=True, exist_ok=True)
    args.validation_report.write_text(report)

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
