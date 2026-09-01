#!/usr/bin/env python3
"""Execute descriptive CPS domain-stability diagnostics for Q2 2025 and Q2 2026."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from genai_at_work.cps import download_official_fixed_width_month as download_2026_month
from genai_at_work.cps import (
    official_fixed_width_filename,
    read_quarter_fixed_width_gz,
)
from genai_at_work.cps_domain_diagnostics import (
    CpsDomainDiagnostic,
    build_cps_domain_diagnostics,
    validate_domain_diagnostics,
)
from genai_at_work.cps_historical import (
    download_official_fixed_width_month_2025,
    read_quarter_fixed_width_gz_2025,
)


def _load_json(path: Path) -> dict[str, Any]:
    raw: object = json.loads(path.read_text())
    if not isinstance(raw, dict):
        raise ValueError(f"expected JSON object in {path}")
    return {str(key): value for key, value in raw.items()}


def _load_cross_year_l1(path: Path) -> dict[str, float]:
    values: dict[str, float] = {}
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("comparability") != "primary" or row.get("supported") != "True":
                continue
            industry_id = row.get("industry_id")
            value = row.get("l1_distance")
            if industry_id and value:
                values[industry_id] = float(value)
    return values


def _industry_names(path: Path) -> dict[str, str]:
    document = _load_json(path)
    entries = document.get("entries")
    if not isinstance(entries, list):
        raise ValueError("industry crosswalk entries must be a list")
    return {
        str(entry["entity_id"]): str(entry["entity_name"])
        for entry in entries
        if isinstance(entry, dict)
    }


def _occupation_ids(path: Path) -> tuple[str, ...]:
    document = _load_json(path)
    entries = document.get("entries")
    if not isinstance(entries, list):
        raise ValueError("occupation crosswalk entries must be a list")
    return tuple(
        str(entry["entity_id"])
        for entry in entries
        if isinstance(entry, dict)
    )


def _download_q2_2025(input_dir: Path) -> None:
    input_dir.mkdir(parents=True, exist_ok=True)
    for month in ("apr", "may", "jun"):
        path = input_dir / official_fixed_width_filename(2025, month)
        if not path.exists():
            download_official_fixed_width_month_2025(month, path)


def _download_q2_2026(input_dir: Path) -> None:
    input_dir.mkdir(parents=True, exist_ok=True)
    for month in ("apr", "may", "jun"):
        path = input_dir / official_fixed_width_filename(2026, month)
        if not path.exists():
            download_2026_month(2026, month, path)


def _serialize(
    rows: list[CpsDomainDiagnostic],
    *,
    names: dict[str, str],
) -> list[dict[str, Any]]:
    serialized: list[dict[str, Any]] = []
    for row in rows:
        document = asdict(row)
        document["industry_name"] = names[row.industry_id]
        document["monthly_person_counts"] = json.dumps(
            row.monthly_person_counts,
            sort_keys=True,
        )
        document["monthly_top_occupations"] = json.dumps(
            row.monthly_top_occupations,
            sort_keys=True,
        )
        serialized.append(document)
    return serialized


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"cannot write empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _join_years(
    rows_2025: list[CpsDomainDiagnostic],
    rows_2026: list[CpsDomainDiagnostic],
    *,
    names: dict[str, str],
    cross_year_l1: dict[str, float],
) -> list[dict[str, Any]]:
    by_2025 = {row.industry_id: row for row in rows_2025}
    by_2026 = {row.industry_id: row for row in rows_2026}
    output: list[dict[str, Any]] = []
    for industry_id in sorted(by_2025, key=lambda key: by_2025[key].industry_index):
        first = by_2025[industry_id]
        second = by_2026[industry_id]
        cross_l1 = cross_year_l1.get(industry_id)
        within_max = max(
            value
            for value in (
                first.maximum_pairwise_month_l1,
                second.maximum_pairwise_month_l1,
            )
            if value is not None
        )
        output.append(
            {
                "industry_index": first.industry_index,
                "industry_id": industry_id,
                "industry_name": names[industry_id],
                "q2_2025_person_month_count": first.person_month_count,
                "q2_2026_person_month_count": second.person_month_count,
                "q2_2025_minimum_month_person_count": first.minimum_month_person_count,
                "q2_2026_minimum_month_person_count": second.minimum_month_person_count,
                "q2_2025_kish_effective_person_months": first.kish_effective_person_months,
                "q2_2026_kish_effective_person_months": second.kish_effective_person_months,
                "q2_2025_max_pairwise_month_l1": first.maximum_pairwise_month_l1,
                "q2_2026_max_pairwise_month_l1": second.maximum_pairwise_month_l1,
                "q2_2025_monthly_top_agreement": first.monthly_top_occupation_agreement,
                "q2_2026_monthly_top_agreement": second.monthly_top_occupation_agreement,
                "q2_2025_pooled_top_two_margin": first.pooled_top_two_margin,
                "q2_2026_pooled_top_two_margin": second.pooled_top_two_margin,
                "cross_year_l1": cross_l1,
                "maximum_within_quarter_pairwise_l1": within_max,
                "cross_year_to_within_quarter_max_ratio": (
                    cross_l1 / within_max
                    if cross_l1 is not None and within_max > 0
                    else None
                ),
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
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--cross-year-comparison", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--validation-report", type=Path, required=True)
    parser.add_argument("--source-build-commit", required=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    registry = root / "data" / "registry"
    input_2025 = args.input_root / "2025-q2"
    input_2026 = args.input_root / "2026-q2"
    _download_q2_2025(input_2025)
    _download_q2_2026(input_2026)

    people_2025, provenance_2025 = read_quarter_fixed_width_gz_2025(
        input_2025,
        quarter=2,
        registry_dir=registry,
    )
    people_2026, provenance_2026 = read_quarter_fixed_width_gz(
        input_2026,
        year=2026,
        quarter=2,
        registry_dir=registry,
    )
    occupation_ids = _occupation_ids(registry / "cps_occupation_crosswalk_v1.json")
    names = _industry_names(registry / "cps_industry_crosswalk_v2.json")
    diagnostics_2025 = build_cps_domain_diagnostics(
        people_2025,
        occupation_ids=occupation_ids,
    )
    diagnostics_2026 = build_cps_domain_diagnostics(
        people_2026,
        occupation_ids=occupation_ids,
    )
    validate_domain_diagnostics(diagnostics_2025)
    validate_domain_diagnostics(diagnostics_2026)

    cross_year_l1 = _load_cross_year_l1(args.cross_year_comparison)
    joined = _join_years(
        diagnostics_2025,
        diagnostics_2026,
        names=names,
        cross_year_l1=cross_year_l1,
    )
    primary_joined = [row for row in joined if row["industry_id"] in cross_year_l1]
    cross_l1_values = [float(row["cross_year_l1"]) for row in primary_joined]
    within_values = [
        float(row["maximum_within_quarter_pairwise_l1"])
        for row in primary_joined
    ]
    ranked = sorted(
        primary_joined,
        key=lambda row: float(row["cross_year_l1"]),
        reverse=True,
    )
    generated_at = datetime.now(UTC).isoformat()
    summary = {
        "status": "descriptive CPS domain stability diagnostics executed",
        "generated_at_utc": generated_at,
        "source_build_commit": args.source_build_commit,
        "industry_count": 20,
        "primary_cross_year_industry_count": len(primary_joined),
        "q2_2025_in_scope_person_months": len(people_2025),
        "q2_2026_in_scope_person_months": len(people_2026),
        "median_primary_cross_year_l1": _median(cross_l1_values),
        "median_primary_maximum_within_quarter_pairwise_l1": _median(within_values),
        "largest_primary_cross_year_shifts": ranked[:5],
        "provenance_2025": provenance_2025,
        "provenance_2026": provenance_2026,
        "inferential_boundary": (
            "Kish effective person-month counts are weight-dispersion diagnostics only. "
            "They do not account for CPS stratification, clustering, the 4-8-4 rotating "
            "panel, repeat observations, or replicate variance structure, and are not "
            "standard errors or design-based effective sample sizes."
        ),
        "raw_files_retained_in_repository": False,
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(
        args.output_dir / "cps_q2_2025_domain_diagnostics.csv",
        _serialize(diagnostics_2025, names=names),
    )
    _write_csv(
        args.output_dir / "cps_q2_2026_domain_diagnostics.csv",
        _serialize(diagnostics_2026, names=names),
    )
    _write_csv(args.output_dir / "cps_cross_year_domain_diagnostics.csv", joined)
    (args.output_dir / "validation_checks.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )

    top = ranked[0] if ranked else None
    report = f"""# CPS Q2 2025-Q2 2026 domain-stability diagnostics

## Purpose

This checkpoint investigates whether large year-to-year occupation-composition changes are concentrated in thin or unstable CPS industry domains. It is descriptive, not a substitute for design-based CPS variance estimation.

Across primary-comparability industries:

- median Q2-2025 to Q2-2026 worker-composition L1: **{_median(cross_l1_values)}**
- median of each industry's maximum within-quarter pairwise monthly L1: **{_median(within_values)}**

Largest primary cross-year shift: **{top['industry_name'] if top else 'n/a'}**, with L1 **{top['cross_year_l1'] if top else 'n/a'}**, Q2-2025 person-month count **{top['q2_2025_person_month_count'] if top else 'n/a'}**, and Q2-2026 person-month count **{top['q2_2026_person_month_count'] if top else 'n/a'}**.

## Interpretation boundary

The reported unweighted counts, final-weight concentration, Kish effective person-month counts, and month-to-month L1 movements are diagnostics. They do not account for CPS stratification, clustering, the 4-8-4 rotation scheme, or replicate variance structure and must not be presented as design-based confidence intervals or standard errors.

Raw Basic Monthly CPS files are downloaded to the workflow temporary directory and are not committed.
"""
    args.validation_report.parent.mkdir(parents=True, exist_ok=True)
    args.validation_report.write_text(report)

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())