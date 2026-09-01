#!/usr/bin/env python3
"""Execute an official 2025 Basic Monthly CPS occupation-composition quarter."""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from genai_at_work.cps import build_composition, official_fixed_width_filename, quarter_months
from genai_at_work.cps_historical import (
    download_official_fixed_width_month_2025,
    read_quarter_fixed_width_gz_2025,
)


def _load_json(path: Path) -> dict[str, Any]:
    raw: object = json.loads(path.read_text())
    if not isinstance(raw, dict):
        raise ValueError(f"expected JSON object in {path}")
    return {str(key): value for key, value in raw.items()}


def _industry_names(document: dict[str, Any]) -> dict[str, str]:
    entries = document.get("entries")
    if not isinstance(entries, list):
        raise ValueError("industry crosswalk entries must be a list")
    names: dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("industry crosswalk entry must be an object")
        names[str(entry["entity_id"])] = str(entry["entity_name"])
    return names


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"cannot write empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quarter", type=int, choices=(1, 2, 3, 4), default=2)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--validation-report", type=Path, required=True)
    parser.add_argument("--coverage-gate", type=float, default=0.98)
    parser.add_argument("--download-missing", action="store_true")
    parser.add_argument("--source-build-commit", required=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    registry = root / "data" / "registry"
    months = quarter_months(2025, args.quarter, registry)
    args.input_dir.mkdir(parents=True, exist_ok=True)

    if args.download_missing:
        for month in months:
            destination = args.input_dir / official_fixed_width_filename(2025, month)
            if not destination.exists():
                download_official_fixed_width_month_2025(month, destination)

    people, provenance = read_quarter_fixed_width_gz_2025(
        args.input_dir,
        quarter=args.quarter,
        registry_dir=registry,
    )
    composition = build_composition(people, coverage_gate=args.coverage_gate)
    timestamp = datetime.now(UTC).isoformat()
    for item in provenance:
        source_path = args.input_dir / str(item["filename"])
        item["file_size_bytes"] = source_path.stat().st_size
        item["retrieval_validation_timestamp_utc"] = timestamp

    industry_crosswalk = _load_json(registry / "cps_industry_crosswalk_v2.json")
    occupation_crosswalk = _load_json(registry / "cps_occupation_crosswalk_v1.json")
    names = _industry_names(industry_crosswalk)
    serialized: list[dict[str, object]] = []
    coverage_rows: list[dict[str, object]] = []
    for row in composition:
        document = asdict(row)
        document["industry_name"] = names[row.industry_id]
        serialized.append(document)
        coverage_rows.append(
            {
                "industry_index": row.industry_index,
                "industry_id": row.industry_id,
                "industry_name": names[row.industry_id],
                "worker_coverage": row.worker_coverage,
                "actual_hours_valid_worker_coverage": row.actual_hours_valid_worker_coverage,
                "actual_hours_mapping_coverage": row.actual_hours_mapping_coverage,
                "usual_hours_valid_worker_coverage": row.usual_hours_valid_worker_coverage,
                "usual_hours_mapping_coverage": row.usual_hours_mapping_coverage,
                "worker_suppressed": row.worker_suppressed,
            }
        )

    weighted_population = sum(person.worker_weight for person in people)
    supported_worker = [row for row in composition if not row.worker_suppressed]
    weight_sums_valid = all(
        row.worker_weights is None
        or math.isclose(sum(row.worker_weights.values()), 1.0, abs_tol=1e-10)
        for row in composition
    )
    weights_nonnegative = all(
        row.worker_weights is None
        or all(value >= 0 for value in row.worker_weights.values())
        for row in composition
    )
    sanity_checks = {
        "industry_count_is_20": len(composition) == 20,
        "all_worker_vectors_supported": len(supported_worker) == 20,
        "supported_worker_vectors_sum_to_one": weight_sums_valid,
        "supported_worker_weights_nonnegative": weights_nonnegative,
    }
    if not all(sanity_checks.values()):
        raise ValueError(f"Q2 2025 CPS composition sanity checks failed: {sanity_checks}")

    period = f"2025-Q{args.quarter}"
    industry_version = str(industry_crosswalk["version"])
    occupation_version = str(occupation_crosswalk["version"])
    args.output_dir.mkdir(parents=True, exist_ok=True)
    composition_payload = {
        "status": "official 2025 CPS composition weights; no RPS observations or residuals",
        "period": period,
        "coverage_gate": args.coverage_gate,
        "sample_rows": len(people),
        "weighted_worker_population_age_18_64_employed": weighted_population,
        "source_build_commit": args.source_build_commit,
        "provenance": provenance,
        "crosswalk_versions": {
            "industry": industry_version,
            "occupation": occupation_version,
            "fixed_width_layout": "cps-basic-fixed-width-2025-v1",
        },
        "industries": serialized,
    }
    manifest = {
        "dataset": "U.S. Census Bureau Current Population Survey Basic Monthly public-use data",
        "period": period,
        "months": list(months),
        "input_format": "official_fixed_width_gzip",
        "population": "employed adults age 18-64 under PREMPNOT=1 project filter",
        "month_factor": 1 / len(months),
        "weight_variable": "PWSSWGT",
        "actual_hours_variable": "PEHRACT1",
        "usual_hours_variable": "PEHRUSL1",
        "industry_variable": "PRDTIND1",
        "occupation_variable": "PRDTOCC1",
        "industry_crosswalk_version": industry_version,
        "occupation_crosswalk_version": occupation_version,
        "fixed_width_layout_version": "cps-basic-fixed-width-2025-v1",
        "source_build_commit": args.source_build_commit,
        "files": provenance,
        "raw_files_retained_in_repository": False,
    }
    checks = {
        "status": "Q2 2025 official CPS worker composition executed",
        "period": period,
        "coverage_gate": args.coverage_gate,
        "sample_rows": len(people),
        "weighted_worker_population_age_18_64_employed": weighted_population,
        "industry_count": len(composition),
        "supported_worker_industries": len(supported_worker),
        "minimum_worker_coverage": min(row.worker_coverage for row in composition),
        "sanity_checks": sanity_checks,
        "source_build_commit": args.source_build_commit,
        "generated_at_utc": timestamp,
        "scientific_boundary": (
            "This artifact provides household-side occupation composition only. It does not "
            "contain RPS observations and does not identify an industry-context effect."
        ),
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

    report = f"""# CPS {period} composition execution

This checkpoint executes the project's occupation-composition contract on official Basic Monthly CPS public-use files for {period}. It exists to provide a same-vintage household-side comparison for May 2025 OEWS.

- in-scope person-month rows: **{len(people):,}**
- pooled weighted employed population age 18-64: **{weighted_population:,.0f}**
- worker-share-supported industries: **{len(supported_worker)}/20**
- minimum worker occupation-mapping coverage: **{min(row.worker_coverage for row in composition):.6f}**
- fixed-width layout registry: `cps-basic-fixed-width-2025-v1`

Raw CPS files are downloaded into the workflow temporary directory and are not committed. Exact Census source URLs, SHA-256 hashes, file sizes, row counts, and retrieval timestamps are recorded in `input_manifest.json`.

This artifact validates composition inputs only. It does not join RPS observations, estimate a counterfactual, or establish an industry-context effect.
"""
    args.validation_report.parent.mkdir(parents=True, exist_ok=True)
    args.validation_report.write_text(report)

    print(json.dumps(checks, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
