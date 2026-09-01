#!/usr/bin/env python3
"""Execute empirical reliability diagnostics for Q2 2025 and Q2 2026 CPS composition.

The script downloads official Census Basic Monthly files into temporary input directories,
recomputes the worker-share composition vectors, verifies them against committed reference
artifacts, and quantifies within-quarter sensitivity. It does not compute design-based standard
errors and does not query BLS/OEWS or RPS sources.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from genai_at_work.cps import (
    build_composition,
    download_official_fixed_width_month,
    official_fixed_width_filename,
    quarter_months,
    read_quarter_fixed_width_gz,
)
from genai_at_work.cps_historical import (
    download_official_fixed_width_month_2025,
    read_quarter_fixed_width_gz_2025,
)
from genai_at_work.cps_reliability import (
    build_period_reliability,
    compare_period_reliability,
    verify_reference_vectors,
)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def _worker_vectors(people: list[Any]) -> dict[str, dict[str, float]]:
    vectors: dict[str, dict[str, float]] = {}
    for row in build_composition(people, coverage_gate=0.98):
        if row.worker_suppressed or row.worker_weights is None:
            raise ValueError(f"worker vector unsupported during reliability execution: {row.industry_id}")
        vectors[row.industry_id] = dict(row.worker_weights)
    return vectors


def _write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _download_2025(input_dir: Path, months: tuple[str, ...]) -> None:
    input_dir.mkdir(parents=True, exist_ok=True)
    for month in months:
        destination = input_dir / official_fixed_width_filename(2025, month)
        if not destination.exists():
            download_official_fixed_width_month_2025(month, destination)


def _download_2026(input_dir: Path, months: tuple[str, ...]) -> None:
    input_dir.mkdir(parents=True, exist_ok=True)
    for month in months:
        destination = input_dir / official_fixed_width_filename(2026, month)
        if not destination.exists():
            download_official_fixed_width_month(2026, month, destination)


def _flatten_period_rows(
    rows: list[Any],
    *,
    period: str,
    metadata: dict[str, dict[str, str]],
) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for row in rows:
        meta = metadata[row.industry_id]
        output.append(
            {
                "period": period,
                "industry_index": row.industry_index,
                "industry_id": row.industry_id,
                "industry_name": meta["industry_name"],
                "comparability": meta["comparability"],
                "person_month_count": row.person_month_count,
                "weighted_worker_population": row.weighted_worker_population,
                "kish_weight_dispersion_effective_n": row.kish_weight_dispersion_effective_n,
                "minimum_monthly_person_count": min(row.monthly_person_month_counts.values()),
                "minimum_monthly_kish_weight_dispersion_effective_n": min(
                    row.monthly_kish_weight_dispersion_effective_n.values()
                ),
                "maximum_pairwise_month_l1": row.maximum_pairwise_month_l1,
                "maximum_monthly_l1_to_quarter": row.maximum_monthly_l1_to_quarter,
                "maximum_leave_one_month_out_l1_to_quarter": (
                    row.maximum_leave_one_month_out_l1_to_quarter
                ),
                "quarter_top_occupation": row.quarter_top_occupation,
                "all_monthly_tops_match_quarter": row.all_monthly_tops_match_quarter,
            }
        )
    return output


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-2025", type=Path, required=True)
    parser.add_argument("--input-2026", type=Path, required=True)
    parser.add_argument("--reference-2025", type=Path, required=True)
    parser.add_argument("--reference-2026", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--validation-report", type=Path, required=True)
    parser.add_argument("--source-build-commit", required=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    registry = root / "data" / "registry"
    months_2025 = quarter_months(2025, 2, registry)
    months_2026 = quarter_months(2026, 2, registry)
    if months_2025 != months_2026:
        raise ValueError("Q2 month definitions differ across 2025 and 2026")

    _download_2025(args.input_2025, months_2025)
    _download_2026(args.input_2026, months_2026)
    people_2025, provenance_2025 = read_quarter_fixed_width_gz_2025(
        args.input_2025, quarter=2, registry_dir=registry
    )
    people_2026, provenance_2026 = read_quarter_fixed_width_gz(
        args.input_2026, year=2026, quarter=2, registry_dir=registry
    )

    vectors_2025 = _worker_vectors(people_2025)
    vectors_2026 = _worker_vectors(people_2026)
    reference_2025 = _load_json(args.reference_2025)
    reference_2026 = _load_json(args.reference_2026)
    verify_reference_vectors(vectors_2025, reference_2025["industries"])
    verify_reference_vectors(vectors_2026, reference_2026["industries"])

    reliability_2025 = build_period_reliability(people_2025, months=months_2025)
    reliability_2026 = build_period_reliability(people_2026, months=months_2026)
    cross = compare_period_reliability(
        reliability_2025,
        reliability_2026,
        quarter_weights_2025=vectors_2025,
        quarter_weights_2026=vectors_2026,
    )

    industry_registry = _load_json(registry / "oews_industry_crosswalk_v1.json")
    metadata = {
        str(entry["entity_id"]): {
            "industry_name": str(entry["entity_name"]),
            "comparability": str(entry["comparability"]),
        }
        for entry in industry_registry["entries"]
    }
    if set(metadata) != set(vectors_2025) or set(metadata) != set(vectors_2026):
        raise ValueError("industry metadata universe does not match CPS vectors")

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    period_payload = {
        "2025-Q2": [asdict(row) for row in reliability_2025],
        "2026-Q2": [asdict(row) for row in reliability_2026],
    }
    (output_dir / "period_reliability.json").write_text(
        json.dumps(period_payload, indent=2, sort_keys=True) + "\n"
    )
    (output_dir / "cross_vintage_reliability.json").write_text(
        json.dumps([asdict(row) for row in cross], indent=2, sort_keys=True) + "\n"
    )

    period_rows = _flatten_period_rows(
        reliability_2025, period="2025-Q2", metadata=metadata
    ) + _flatten_period_rows(reliability_2026, period="2026-Q2", metadata=metadata)
    _write_csv(
        output_dir / "period_reliability.csv",
        period_rows,
        list(period_rows[0]),
    )
    cross_rows: list[dict[str, object]] = []
    for row in cross:
        meta = metadata[row.industry_id]
        cross_rows.append(
            {
                "industry_index": row.industry_index,
                "industry_id": row.industry_id,
                "industry_name": meta["industry_name"],
                "comparability": meta["comparability"],
                "l1_q2_2025_to_q2_2026": row.l1_q2_2025_to_q2_2026,
                "within_quarter_l1_envelope": row.within_quarter_l1_envelope,
                "year_over_year_to_within_quarter_ratio": (
                    row.year_over_year_to_within_quarter_ratio
                ),
                "year_over_year_exceeds_within_quarter_envelope": (
                    row.year_over_year_exceeds_within_quarter_envelope
                ),
                "minimum_kish_weight_dispersion_effective_n": (
                    row.minimum_kish_weight_dispersion_effective_n
                ),
                "maximum_leave_one_month_out_l1": row.maximum_leave_one_month_out_l1,
                "tops_match_across_quarters": row.tops_match_across_quarters,
            }
        )
    _write_csv(output_dir / "cross_vintage_reliability.csv", cross_rows, list(cross_rows[0]))

    primary_ids = {
        industry_id
        for industry_id, meta in metadata.items()
        if meta["comparability"] == "primary"
    }
    primary_cross = [row for row in cross if row.industry_id in primary_ids]
    primary_2025 = [row for row in reliability_2025 if row.industry_id in primary_ids]
    primary_2026 = [row for row in reliability_2026 if row.industry_id in primary_ids]
    all_period_primary = primary_2025 + primary_2026
    highest_cross_year = max(primary_cross, key=lambda row: row.l1_q2_2025_to_q2_2026)
    lowest_ess = min(
        all_period_primary,
        key=lambda row: row.kish_weight_dispersion_effective_n,
    )
    highest_lomo = max(
        all_period_primary,
        key=lambda row: row.maximum_leave_one_month_out_l1_to_quarter,
    )

    generated_at = datetime.now(UTC).isoformat()
    validation = {
        "status": "CPS Q2 2025/Q2 2026 empirical composition reliability executed",
        "source_build_commit": args.source_build_commit,
        "generated_at_utc": generated_at,
        "periods": ["2025-Q2", "2026-Q2"],
        "months": list(months_2025),
        "industry_count": len(cross),
        "primary_comparable_industry_count": len(primary_cross),
        "reference_vectors_reproduced": True,
        "raw_cps_files_retained_in_repository": False,
        "primary_median_person_month_count": _median(
            [float(row.person_month_count) for row in all_period_primary]
        ),
        "primary_minimum_person_month_count": min(
            row.person_month_count for row in all_period_primary
        ),
        "primary_median_kish_weight_dispersion_effective_n": _median(
            [row.kish_weight_dispersion_effective_n for row in all_period_primary]
        ),
        "primary_minimum_kish_weight_dispersion_effective_n": (
            lowest_ess.kish_weight_dispersion_effective_n
        ),
        "lowest_effective_n_industry_period": {
            "industry_id": lowest_ess.industry_id,
            "industry_name": metadata[lowest_ess.industry_id]["industry_name"],
            "period": "2025-Q2" if lowest_ess in primary_2025 else "2026-Q2",
            "person_month_count": lowest_ess.person_month_count,
            "kish_weight_dispersion_effective_n": lowest_ess.kish_weight_dispersion_effective_n,
        },
        "highest_leave_one_month_out_industry_period": {
            "industry_id": highest_lomo.industry_id,
            "industry_name": metadata[highest_lomo.industry_id]["industry_name"],
            "period": "2025-Q2" if highest_lomo in primary_2025 else "2026-Q2",
            "maximum_leave_one_month_out_l1": highest_lomo.maximum_leave_one_month_out_l1_to_quarter,
        },
        "highest_cross_vintage_l1_industry": {
            "industry_id": highest_cross_year.industry_id,
            "industry_name": metadata[highest_cross_year.industry_id]["industry_name"],
            "l1_q2_2025_to_q2_2026": highest_cross_year.l1_q2_2025_to_q2_2026,
            "within_quarter_l1_envelope": highest_cross_year.within_quarter_l1_envelope,
            "year_over_year_to_within_quarter_ratio": (
                highest_cross_year.year_over_year_to_within_quarter_ratio
            ),
        },
        "primary_cross_vintage_changes_exceeding_within_quarter_envelope": sum(
            row.year_over_year_exceeds_within_quarter_envelope for row in primary_cross
        ),
        "interpretation_boundary": (
            "Kish effective n measures weight dispersion only and is not a CPS design-based "
            "effective sample size. Monthly and leave-one-month-out L1 measures are empirical "
            "stability diagnostics, not significance tests. BLS/Census GVF or replicate-based "
            "inference is not claimed for these custom 22-dimensional composition vectors."
        ),
        "official_methodology_basis": [
            "BLS July 2026 Calculating Approximate Standard Errors and Confidence Intervals for CPS Estimates",
            "CPS Technical Paper 77, Chapter 2-4: Variance Estimation",
        ],
    }
    (output_dir / "validation_checks.json").write_text(
        json.dumps(validation, indent=2, sort_keys=True) + "\n"
    )
    input_manifest = {
        "dataset": "U.S. Census Bureau Current Population Survey Basic Monthly public-use data",
        "purpose": "empirical occupation-composition reliability diagnostics",
        "source_build_commit": args.source_build_commit,
        "generated_at_utc": generated_at,
        "2025_files": provenance_2025,
        "2026_files": provenance_2026,
        "reference_2025": str(args.reference_2025),
        "reference_2026": str(args.reference_2026),
        "raw_files_retained_in_repository": False,
    }
    (output_dir / "input_manifest.json").write_text(
        json.dumps(input_manifest, indent=2, sort_keys=True) + "\n"
    )

    report = f"""# CPS occupation-composition empirical reliability checkpoint

## Status

This checkpoint tests whether the pooled Q2 CPS worker-composition vectors are stable to their
three constituent months. It covers Q2 2025 and Q2 2026 and reproduces the already committed
quarterly worker vectors to machine tolerance before computing diagnostics.

It does **not** estimate CPS design-based standard errors for the custom industry-by-occupation
composition vectors. BLS's published generalized-variance machinery does not directly provide a
parameter series for every custom estimate, and borrowing parameters would assume comparable
design effects. The diagnostics below therefore remain descriptive perturbation checks.

## Primary diagnostics

- primary-comparability industries: **{len(primary_cross)}**
- minimum primary person-month count across the two quarter-industry cells: **{validation['primary_minimum_person_month_count']}**
- minimum primary Kish weight-dispersion effective n: **{validation['primary_minimum_kish_weight_dispersion_effective_n']}**
- primary year-over-year composition changes exceeding their observed within-quarter monthly L1 envelope: **{validation['primary_cross_vintage_changes_exceeding_within_quarter_envelope']}/{len(primary_cross)}**
- largest primary Q2-2025 to Q2-2026 L1 change: **{highest_cross_year.l1_q2_2025_to_q2_2026}** ({metadata[highest_cross_year.industry_id]['industry_name']})
- that industry's maximum observed within-quarter monthly L1 envelope: **{highest_cross_year.within_quarter_l1_envelope}**
- largest primary leave-one-month-out perturbation across both years: **{highest_lomo.maximum_leave_one_month_out_l1_to_quarter}** ({metadata[highest_lomo.industry_id]['industry_name']})

## Interpretation

A large quarter-to-quarter change accompanied by large within-quarter or leave-one-month-out
instability is a warning that the pooled composition is sensitive to a thin or volatile CPS domain.
The envelope comparison is not a hypothesis test and must not be described as statistical
significance. Kish effective n is reported only as a weight-concentration diagnostic.

These diagnostics should govern whether individual industry composition estimates are treated as
primary evidence, sensitivity evidence, or flagged for additional uncertainty work before an RPS
occupation-standardization residual is published.
"""
    args.validation_report.parent.mkdir(parents=True, exist_ok=True)
    args.validation_report.write_text(report)

    print(json.dumps(validation, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
