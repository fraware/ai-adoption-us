#!/usr/bin/env python3
"""Execute and validate an official CPS occupation-composition vintage.

This script turns official Basic Monthly CPS CSV files into a versioned composition
package. It deliberately stops at composition weights: it does not join RPS occupation
observations and therefore does not produce occupation-adjusted industry residuals.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from genai_at_work.cps import (
    IndustryComposition,
    build_composition,
    download_official_month,
    official_month_filename,
    quarter_months,
    read_quarter_csvs,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> dict[str, Any]:
    raw: object = json.loads(path.read_text())
    if not isinstance(raw, dict):
        raise ValueError(f"expected JSON object in {path}")
    return {str(key): value for key, value in raw.items()}


def _l1_distance(
    left: dict[str, float] | None,
    right: dict[str, float] | None,
) -> float | None:
    if left is None or right is None:
        return None
    keys = set(left) | set(right)
    return sum(abs(left.get(key, 0.0) - right.get(key, 0.0)) for key in keys)


def _all_nonnegative(weights: dict[str, float] | None) -> bool:
    return weights is None or all(value >= 0 for value in weights.values())


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"cannot write empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _industry_names(industry_crosswalk: dict[str, Any]) -> dict[str, str]:
    entries = industry_crosswalk.get("entries")
    if not isinstance(entries, list):
        raise ValueError("industry crosswalk entries must be a list")
    names: dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("industry crosswalk entry must be an object")
        entity_id = entry.get("entity_id")
        entity_name = entry.get("entity_name")
        if not isinstance(entity_id, str) or not isinstance(entity_name, str):
            raise ValueError("industry crosswalk entry lacks string entity_id/entity_name")
        names[entity_id] = entity_name
    return names


def _crosswalk_version(document: dict[str, Any], label: str) -> str:
    value = document.get("version")
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} crosswalk version is missing")
    return value


def _composition_rows(
    composition: list[IndustryComposition],
    names: dict[str, str],
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    serialized: list[dict[str, object]] = []
    coverage_rows: list[dict[str, object]] = []
    sensitivity_rows: list[dict[str, object]] = []

    for row in composition:
        if row.industry_id not in names:
            raise ValueError(f"missing industry name for {row.industry_id}")
        name = names[row.industry_id]
        document = asdict(row)
        document["industry_name"] = name
        serialized.append(document)
        coverage_rows.append(
            {
                "industry_index": row.industry_index,
                "industry_id": row.industry_id,
                "industry_name": name,
                "worker_coverage": row.worker_coverage,
                "actual_hours_valid_worker_coverage": row.actual_hours_valid_worker_coverage,
                "actual_hours_mapping_coverage": row.actual_hours_mapping_coverage,
                "usual_hours_valid_worker_coverage": row.usual_hours_valid_worker_coverage,
                "usual_hours_mapping_coverage": row.usual_hours_mapping_coverage,
                "worker_suppressed": row.worker_suppressed,
                "actual_hours_suppressed": row.actual_hours_suppressed,
                "usual_hours_suppressed": row.usual_hours_suppressed,
            }
        )
        sensitivity_rows.append(
            {
                "industry_index": row.industry_index,
                "industry_id": row.industry_id,
                "industry_name": name,
                "worker_vs_actual_hour_weights_l1": _l1_distance(
                    row.worker_weights, row.actual_hour_weights
                ),
                "actual_vs_usual_hour_weights_l1": _l1_distance(
                    row.actual_hour_weights, row.usual_hour_weights
                ),
                "worker_supported": not row.worker_suppressed,
                "actual_hours_supported": not row.actual_hours_suppressed,
                "usual_hours_supported": not row.usual_hours_suppressed,
            }
        )

    return serialized, coverage_rows, sensitivity_rows


def _validation_checks(
    composition: list[IndustryComposition],
    *,
    sample_rows: int,
    weighted_worker_population: float,
    coverage_gate: float,
    source_build_commit: str,
    population_sanity_min: float | None,
    population_sanity_max: float | None,
) -> dict[str, object]:
    all_weight_sums_valid = all(
        weights is None or math.isclose(sum(weights.values()), 1.0, abs_tol=1e-10)
        for row in composition
        for weights in (row.worker_weights, row.actual_hour_weights, row.usual_hour_weights)
    )
    all_weights_nonnegative = all(
        _all_nonnegative(weights)
        for row in composition
        for weights in (row.worker_weights, row.actual_hour_weights, row.usual_hour_weights)
    )
    worker_actual_differences = [
        value
        for row in composition
        if (value := _l1_distance(row.worker_weights, row.actual_hour_weights)) is not None
    ]
    actual_usual_differences = [
        value
        for row in composition
        if (value := _l1_distance(row.actual_hour_weights, row.usual_hour_weights)) is not None
    ]

    population_sanity = True
    if population_sanity_min is not None:
        population_sanity = population_sanity and weighted_worker_population >= population_sanity_min
    if population_sanity_max is not None:
        population_sanity = population_sanity and weighted_worker_population <= population_sanity_max

    checks = {
        "industry_count_is_20": len(composition) == 20,
        "weighted_worker_population_within_configured_sanity_range": population_sanity,
        "all_supported_weight_vectors_sum_to_one": all_weight_sums_valid,
        "all_weights_nonnegative": all_weights_nonnegative,
    }
    return {
        "status": (
            "official CPS composition weights executed; "
            "RPS occupation counterfactual join not executed"
        ),
        "source_build_commit": source_build_commit,
        "generated_at_utc": _utc_now(),
        "coverage_gate": coverage_gate,
        "sample_rows": sample_rows,
        "weighted_worker_population_age_18_64_employed": weighted_worker_population,
        "industry_count": len(composition),
        "supported_worker_industries": sum(not row.worker_suppressed for row in composition),
        "supported_actual_hours_industries": sum(
            not row.actual_hours_suppressed for row in composition
        ),
        "supported_usual_hours_industries": sum(
            not row.usual_hours_suppressed for row in composition
        ),
        "minimum_worker_coverage": min(row.worker_coverage for row in composition),
        "minimum_actual_hours_valid_worker_coverage": min(
            row.actual_hours_valid_worker_coverage for row in composition
        ),
        "minimum_actual_hours_mapping_coverage": min(
            row.actual_hours_mapping_coverage
            for row in composition
            if row.actual_hours_mapping_coverage is not None
        ),
        "minimum_usual_hours_valid_worker_coverage": min(
            row.usual_hours_valid_worker_coverage for row in composition
        ),
        "minimum_usual_hours_mapping_coverage": min(
            row.usual_hours_mapping_coverage
            for row in composition
            if row.usual_hours_mapping_coverage is not None
        ),
        "all_supported_weight_vectors_sum_to_one": all_weight_sums_valid,
        "all_weights_nonnegative": all_weights_nonnegative,
        "industries_with_worker_vs_actual_hour_weight_difference_gt_1e_6": sum(
            value > 1e-6 for value in worker_actual_differences
        ),
        "median_worker_vs_actual_hour_weights_l1": _median(worker_actual_differences),
        "median_actual_vs_usual_hour_weights_l1": _median(actual_usual_differences),
        "sanity_checks": checks,
        "remaining_gate": (
            "Occupation-composition counterfactuals/residuals require a compatible authorized "
            "RPS occupation observation vintage; the public repository intentionally contains no "
            "raw RPS subgroup fixture."
        ),
    }


def _write_report(
    path: Path,
    *,
    period: str,
    checks: dict[str, object],
    source_build_commit: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    report = f"""# CPS {period} composition execution — official-data checkpoint

## Status

This record documents execution of the occupation-composition **weighting layer** on official
Basic Monthly CPS public-use CSV files for {period}.

It does **not** claim completed RPS occupation-composition counterfactuals or
occupation-adjusted industry-context residuals. Those require a compatible authorized RPS
occupation observation vintage, which is intentionally absent from the public repository.

## Execution identity

- source build commit: `{source_build_commit}`
- generated at: `{checks['generated_at_utc']}`
- in-scope CPS person-month rows: **{int(checks['sample_rows']):,}**
- pooled weighted employed population age 18–64: **{float(checks['weighted_worker_population_age_18_64_employed']):,.0f}**
- industry groups produced: **{checks['industry_count']}**
- coverage gate: **{float(checks['coverage_gate']):.1%}**

## Source inputs

Exact official source URLs, SHA-256 checksums, file sizes, row counts, and the execution
retrieval/validation timestamp are frozen in the adjacent `input_manifest.json`.

## Weighting contract executed

- adoption composition basis: worker shares;
- assisted-hours/reported-savings composition basis: actual-main-job-hour shares;
- usual-main-job-hours: sensitivity only;
- equal month factors within the quarter;
- employed-absent workers: zero actual hours under the existing implementation contract;
- invalid active-worker actual hours: not imputed;
- unsupported mapping/validity coverage: fail closed at the configured gate.

## Validation summary

- worker-share-supported industries: **{checks['supported_worker_industries']}/{checks['industry_count']}**
- actual-hour-supported industries: **{checks['supported_actual_hours_industries']}/{checks['industry_count']}**
- usual-hour-supported industries: **{checks['supported_usual_hours_industries']}/{checks['industry_count']}**
- minimum worker mapping coverage: **{float(checks['minimum_worker_coverage']):.6f}**
- minimum valid-worker coverage for actual hours: **{float(checks['minimum_actual_hours_valid_worker_coverage']):.6f}**
- minimum actual-hour occupation mapping coverage: **{float(checks['minimum_actual_hours_mapping_coverage']):.6f}**
- supported weight vectors sum to one: **{checks['all_supported_weight_vectors_sum_to_one']}**
- all weights nonnegative: **{checks['all_weights_nonnegative']}**
- industries with worker-share versus actual-hour-share L1 difference > 1e-6: **{checks['industries_with_worker_vs_actual_hour_weight_difference_gt_1e_6']}**

The machine-readable per-industry coverage and actual-versus-usual-hours sensitivity diagnostics
are committed beside the composition artifact.

## Scientific boundary and next gate

This checkpoint establishes whether official CPS composition inputs and the weighting
implementation are operational on real data. It does not establish an industry-context effect
and it does not produce a productivity or causal claim.

The next step is to inspect suppression and coverage diagnostics and then join validated
composition weights only to an authorized compatible RPS occupation vintage. Only after that
join and the prespecified robustness suite can an occupation-adjusted industry-context residual
be considered for publication.
"""
    path.write_text(report)


def execute(args: argparse.Namespace) -> dict[str, object]:
    root = Path(__file__).resolve().parents[1]
    registry = root / "data" / "registry"
    months = quarter_months(args.year, args.quarter, registry)
    args.input_dir.mkdir(parents=True, exist_ok=True)

    if args.download_missing:
        for month in months:
            destination = args.input_dir / official_month_filename(args.year, month)
            if not destination.exists():
                download_official_month(args.year, month, destination)

    people, provenance = read_quarter_csvs(
        args.input_dir,
        year=args.year,
        quarter=args.quarter,
        registry_dir=registry,
    )
    composition = build_composition(people, coverage_gate=args.coverage_gate)

    timestamp = _utc_now()
    for item in provenance:
        source_path = args.input_dir / str(item["filename"])
        item["file_size_bytes"] = source_path.stat().st_size
        item["retrieval_validation_timestamp_utc"] = timestamp

    industry_crosswalk = _load_json(registry / "cps_industry_crosswalk_v2.json")
    occupation_crosswalk = _load_json(registry / "cps_occupation_crosswalk_v1.json")
    names = _industry_names(industry_crosswalk)
    industry_version = _crosswalk_version(industry_crosswalk, "industry")
    occupation_version = _crosswalk_version(occupation_crosswalk, "occupation")

    serialized, coverage_rows, sensitivity_rows = _composition_rows(composition, names)
    weighted_worker_population = sum(person.worker_weight for person in people)
    source_build_commit = args.source_build_commit or os.environ.get("GITHUB_SHA", "unrecorded")
    checks = _validation_checks(
        composition,
        sample_rows=len(people),
        weighted_worker_population=weighted_worker_population,
        coverage_gate=args.coverage_gate,
        source_build_commit=source_build_commit,
        population_sanity_min=args.population_sanity_min,
        population_sanity_max=args.population_sanity_max,
    )

    sanity = checks.get("sanity_checks")
    if not isinstance(sanity, dict) or not all(bool(value) for value in sanity.values()):
        raise ValueError(f"CPS execution sanity checks failed: {sanity}")

    period = f"{args.year}-Q{args.quarter}"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "dataset": "U.S. Census Bureau Current Population Survey Basic Monthly public-use data",
        "period": period,
        "months": list(months),
        "population": "employed adults age 18-64 under PREMPNOT=1 project filter",
        "month_factor": 1 / len(months),
        "weight_variable": "PWSSWGT",
        "actual_hours_variable": "PEHRACT1",
        "usual_hours_variable": "PEHRUSL1",
        "industry_variable": "PRDTIND1",
        "occupation_variable": "PRDTOCC1",
        "industry_crosswalk_version": industry_version,
        "occupation_crosswalk_version": occupation_version,
        "source_build_commit": source_build_commit,
        "files": provenance,
    }
    composition_payload = {
        "status": "official CPS composition weights; no RPS observations or residuals",
        "period": period,
        "coverage_gate": args.coverage_gate,
        "sample_rows": len(people),
        "weighted_worker_population_age_18_64_employed": weighted_worker_population,
        "source_build_commit": source_build_commit,
        "provenance": provenance,
        "crosswalk_versions": {
            "industry": industry_version,
            "occupation": occupation_version,
        },
        "industries": serialized,
    }

    (args.output_dir / "cps_composition.json").write_text(
        json.dumps(composition_payload, indent=2, sort_keys=True) + "\n"
    )
    (args.output_dir / "input_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    (args.output_dir / "validation_checks.json").write_text(
        json.dumps(checks, indent=2, sort_keys=True) + "\n"
    )
    _write_csv(args.output_dir / "coverage.csv", coverage_rows)
    _write_csv(args.output_dir / "sensitivity.csv", sensitivity_rows)
    _write_report(
        args.validation_report,
        period=period,
        checks=checks,
        source_build_commit=source_build_commit,
    )
    return checks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--quarter", type=int, choices=(1, 2, 3, 4), required=True)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--validation-report", type=Path, required=True)
    parser.add_argument("--coverage-gate", type=float, default=0.98)
    parser.add_argument("--download-missing", action="store_true")
    parser.add_argument("--source-build-commit")
    parser.add_argument("--population-sanity-min", type=float)
    parser.add_argument("--population-sanity-max", type=float)
    return parser.parse_args()


def main() -> int:
    checks = execute(parse_args())
    print(json.dumps(checks, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
