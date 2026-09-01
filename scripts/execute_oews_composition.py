#!/usr/bin/env python3
"""Execute May-2025 OEWS employee-share composition and compare with CPS.

This script queries public aggregate BLS series only. The primary comparison is OEWS
employee-share occupation composition versus the project's Q2-2026 CPS worker-share
composition. It does not compare OEWS employment counts with CPS actual-hour weights.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from genai_at_work.oews import (
    BLS_API_URL,
    build_oews_composition,
    compare_cps_oews_worker_composition,
    fetch_oews_series_values,
    median,
    required_series_ids,
)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--coverage-gate", type=float, default=0.98)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--cps-composition", type=Path, required=True)
    parser.add_argument("--validation-report", type=Path, required=True)
    parser.add_argument("--source-build-commit", required=True)
    args = parser.parse_args()

    if args.year != 2025:
        raise SystemExit("this execution is pinned to the May-2025 OEWS source vintage")

    root = Path(__file__).resolve().parents[1]
    registry_dir = root / "data" / "registry"
    industry_registry = _load_json(registry_dir / "oews_industry_crosswalk_v1.json")
    occupation_registry = _load_json(registry_dir / "oews_occupation_crosswalk_v1.json")
    cps_payload = _load_json(args.cps_composition)

    industries = industry_registry["entries"]
    occupations = occupation_registry["entries"]
    occupation_ids = [str(row["entity_id"]) for row in occupations]
    series_ids = required_series_ids(industries, occupations)

    with httpx.Client(
        timeout=60.0,
        headers={"User-Agent": "genai-at-work-research/0.1 OEWS-validation"},
    ) as client:
        values, request_manifest = fetch_oews_series_values(
            series_ids,
            year=args.year,
            client=client,
            batch_size=25,
        )

    composition = build_oews_composition(
        values,
        industry_entries=industries,
        occupation_entries=occupations,
        coverage_gate=args.coverage_gate,
    )
    comparisons = compare_cps_oews_worker_composition(
        composition,
        cps_payload["industries"],
        occupation_ids=occupation_ids,
    )

    primary = [
        row
        for row in comparisons
        if row.comparability == "primary"
        and row.oews_supported
        and row.cps_supported
        and row.l1_distance is not None
    ]
    limited = [row for row in comparisons if row.comparability == "limited"]
    excluded = [row for row in comparisons if row.comparability == "excluded"]
    supported_oews = [row for row in composition if row.supported]

    primary_l1 = [row.l1_distance for row in primary if row.l1_distance is not None]
    primary_cosine = [
        row.cosine_similarity
        for row in primary
        if row.cosine_similarity is not None
    ]
    primary_spearman = [
        row.spearman_rank_correlation
        for row in primary
        if row.spearman_rank_correlation is not None
    ]
    top_agreements = [
        row for row in primary if row.top_occupation_agreement is True
    ]

    missing_series = sorted(
        series_id for series_id, value in values.items() if value is None
    )
    generated_at = datetime.now(UTC).isoformat()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    composition_payload = {
        "status": "May-2025 OEWS employee-share occupation composition",
        "year": args.year,
        "period": "A01",
        "coverage_gate": args.coverage_gate,
        "industry_crosswalk_version": industry_registry["version"],
        "occupation_crosswalk_version": occupation_registry["version"],
        "global_scope_note": industry_registry["global_scope_note"],
        "generated_at_utc": generated_at,
        "source_build_commit": args.source_build_commit,
        "industries": [asdict(row) for row in composition],
    }
    (output_dir / "oews_composition.json").write_text(
        json.dumps(composition_payload, indent=2, sort_keys=True) + "\n"
    )

    comparison_rows = [asdict(row) for row in comparisons]
    _write_csv(
        output_dir / "cps_oews_worker_comparison.csv",
        comparison_rows,
        [
            "industry_index",
            "industry_id",
            "industry_name",
            "comparability",
            "oews_supported",
            "cps_supported",
            "l1_distance",
            "cosine_similarity",
            "spearman_rank_correlation",
            "top_occupation_agreement",
            "cps_top_occupation",
            "oews_top_occupation",
            "max_absolute_share_difference",
        ],
    )

    input_manifest = {
        "provider": "U.S. Bureau of Labor Statistics",
        "dataset": "May 2025 Occupational Employment and Wage Statistics",
        "api_url": BLS_API_URL,
        "reference_year": args.year,
        "reference_period": "A01",
        "datatype": "01 Employment",
        "series_count": len(series_ids),
        "request_count": len(request_manifest),
        "request_manifest": request_manifest,
        "industry_crosswalk_version": industry_registry["version"],
        "occupation_crosswalk_version": occupation_registry["version"],
        "cps_comparison_artifact": str(args.cps_composition),
        "cps_comparison_period": cps_payload.get("period", "2026-Q2"),
        "generated_at_utc": generated_at,
        "source_build_commit": args.source_build_commit,
        "raw_api_responses_retained": False,
        "scope_boundary": industry_registry["global_scope_note"],
    }
    (output_dir / "input_manifest.json").write_text(
        json.dumps(input_manifest, indent=2, sort_keys=True) + "\n"
    )

    validation = {
        "status": "May-2025 OEWS composition robustness executed",
        "coverage_gate": args.coverage_gate,
        "industry_count": len(composition),
        "occupation_count": len(occupations),
        "series_count": len(series_ids),
        "api_request_count": len(request_manifest),
        "missing_series_count": len(missing_series),
        "missing_series_ids": missing_series,
        "supported_oews_industries": len(supported_oews),
        "primary_comparable_industries": len(
            [row for row in comparisons if row.comparability == "primary"]
        ),
        "primary_supported_comparisons": len(primary),
        "limited_comparability_industries": [row.industry_id for row in limited],
        "excluded_from_primary_industries": [row.industry_id for row in excluded],
        "minimum_oews_coverage": min(
            (row.coverage for row in composition), default=0.0
        ),
        "median_primary_l1_distance": median(primary_l1),
        "median_primary_cosine_similarity": median(primary_cosine),
        "median_primary_spearman_rank_correlation": median(primary_spearman),
        "primary_top_occupation_agreement_count": len(top_agreements),
        "primary_top_occupation_agreement_rate": (
            len(top_agreements) / len(primary) if primary else None
        ),
        "sanity_checks": {
            "industry_count_is_20": len(composition) == 20,
            "occupation_count_is_22": len(occupations) == 22,
            "series_count_is_460": len(series_ids) == 460,
            "series_ids_unique": len(series_ids) == len(set(series_ids)),
            "request_count_within_unregistered_daily_limit": len(request_manifest) <= 25,
            "supported_vectors_sum_to_one": all(
                row.worker_weights is None
                or abs(sum(row.worker_weights.values()) - 1.0) <= 1e-12
                for row in composition
            ),
            "supported_weights_nonnegative": all(
                row.worker_weights is None
                or all(value >= 0 for value in row.worker_weights.values())
                for row in composition
            ),
        },
        "interpretation_boundary": (
            "OEWS is an employer-based wage-and-salary employment source with a May-2025 "
            "model-based vintage; CPS is a household worker source pooled over 2026-Q2. "
            "The comparison tests occupation-composition robustness across independent "
            "sources and vintages and does not establish population identity or causality."
        ),
        "generated_at_utc": generated_at,
        "source_build_commit": args.source_build_commit,
    }
    (output_dir / "validation_checks.json").write_text(
        json.dumps(validation, indent=2, sort_keys=True) + "\n"
    )

    report = f"""# May 2025 OEWS vs Q2 2026 CPS composition robustness

## Status

This checkpoint compares **worker/employment-share occupation composition** across two independent source systems:

- May 2025 BLS Occupational Employment and Wage Statistics (OEWS), employer-side wage-and-salary employment estimates;
- Q2 2026 Basic Monthly CPS, household-side worker composition already validated by the project.

It does not compare OEWS employment shares with CPS actual-hour shares and does not generate any RPS adoption counterfactual or industry-context residual.

## Execution

- OEWS industries requested: **{len(composition)}**
- canonical civilian occupation groups: **{len(occupations)}**
- BLS series requested: **{len(series_ids)}**
- BLS API requests: **{len(request_manifest)}**
- missing/suppressed series: **{len(missing_series)}**
- OEWS industries meeting the {args.coverage_gate:.0%} coverage gate: **{len(supported_oews)}/20**
- primary-comparability industries with supported CPS and OEWS vectors: **{len(primary)}**

## Primary comparison contract

Agriculture is excluded from the primary summary because OEWS excludes most agricultural employment. Public Administration is excluded because the OEWS government aggregate is not definitionally identical to the CPS/RPS Public Administration group. Other Services is retained only as a limited-comparability diagnostic because OEWS excludes private households.

Across every industry, OEWS excludes self-employed workers while CPS includes the broader worker population under the project's current filter. The vintages also differ: May 2025 OEWS versus Q2 2026 CPS. The comparison is therefore a robustness test of occupational structure across independent sources and vintages, not a same-population replication.

## Primary diagnostics

- median L1 distance: **{validation['median_primary_l1_distance']}**
- median cosine similarity: **{validation['median_primary_cosine_similarity']}**
- median Spearman rank correlation: **{validation['median_primary_spearman_rank_correlation']}**
- same largest occupation group: **{len(top_agreements)}/{len(primary) if primary else 0}** primary comparisons

These diagnostics should be interpreted together. They quantify agreement in the 22-dimensional occupation-composition vectors and do not by themselves determine whether any downstream RPS composition-adjusted residual is robust.

## Next gate

If the OEWS composition vectors pass coverage and show adequate structural agreement with CPS on the primary-comparability set, the future RPS occupation-standardization analysis should report CPS as the main household-side specification and OEWS as an independent employer-side worker-composition sensitivity. The RPS join remains blocked until a compatible authorized RPS occupation vintage is available.
"""
    args.validation_report.parent.mkdir(parents=True, exist_ok=True)
    args.validation_report.write_text(report)

    print(json.dumps(validation, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
