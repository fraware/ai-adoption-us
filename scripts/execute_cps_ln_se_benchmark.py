#!/usr/bin/env python3
"""Execute one official BLS LN/CPS same-period uncertainty benchmark.

The script reconstructs BLS series LNU02032201 from one official Basic Monthly
CPS public-use file and retrieves the corresponding published point estimate and
standard-error aspect through the BLS Public Data API.

This is a same-reference-period validation. It does not estimate covariance
between months and does not authorize significance tests over time.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import urllib.request
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from genai_at_work.cps import (
    download_official_fixed_width_month,
    official_fixed_width_filename,
    official_fixed_width_url,
    official_record_layout_url,
)
from genai_at_work.cps_ln_benchmark import (
    BLS_LN_ASPECT_URL,
    BLS_PUBLIC_API_V2_URL,
    MANAGEMENT_PROFESSIONAL_SERIES_ID,
    extract_bls_api_standard_error,
    month_period,
    parse_bls_api_month_value,
    published_rounding_matches,
    reconstruct_management_professional_employment,
)

BLS_SE_GUIDANCE_URL = (
    "https://www.bls.gov/cps/factsheets/understanding-standard-errors-and-confidence-intervals.htm"
)
BLS_API_FEATURES_URL = "https://www.bls.gov/bls/api_features.htm"
CENSUS_PUBLIC_USE_DISCLOSURE_NOTE_URL = (
    "https://www.census.gov/programs-surveys/cps/technical-documentation/"
    "user-notes/cpsbasic_2013_01.html"
)
CENSUS_PUBLIC_USE_DOCUMENTATION_URL = (
    "https://www2.census.gov/programs-surveys/cps/methodology/PublicUseDocumentation_final.pdf"
)
MAX_PUBLIC_USE_DISCREPANCY_STANDARD_ERRORS = 1.0
USER_AGENT = "ai-adoption-us/1.0 public-data-validation"


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()


def _fetch_bls_series_with_aspects(*, series_id: str) -> tuple[dict[str, Any], dict[str, object]]:
    request_url = f"{BLS_PUBLIC_API_V2_URL}{series_id}?aspects=true"
    request = urllib.request.Request(request_url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        raw_bytes = response.read()
    raw: object = json.loads(raw_bytes.decode("utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("BLS Public Data API returned a non-object payload")
    return (
        {str(key): value for key, value in raw.items()},
        {
            "request_url": request_url,
            "transport_response_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "transport_response_size_bytes": len(raw_bytes),
            "transport_hash_semantics": (
                "exact retrieval bytes; may vary when non-scientific API envelope content changes"
            ),
            "raw_response_published": False,
        },
    )


def _write_report(path: Path, benchmark: dict[str, object]) -> None:
    official = float(benchmark["published_estimate_thousands"])
    se = float(benchmark["published_standard_error_thousands"])
    reconstructed = float(benchmark["reconstructed_estimate_thousands"])
    difference = float(benchmark["reconstruction_difference_thousands"])
    discrepancy_se = float(benchmark["absolute_reconstruction_difference_standard_errors"])
    lower = float(benchmark["published_90pct_ci_lower_thousands"])
    upper = float(benchmark["published_90pct_ci_upper_thousands"])
    threshold = float(benchmark["project_validation_threshold_standard_errors"])
    report = f"""# CPS LN same-period uncertainty benchmark

## Result

The official Basic Monthly CPS public-use file reconstructs BLS series
`{benchmark['series_id']}` for {benchmark['year']} {benchmark['period']} under the
published **employed people age 16+** universe and the broad Management,
Professional, and Related occupation definition.

- BLS published estimate: **{official:,.0f} thousand persons**
- public-use reconstruction: **{reconstructed:,.6f} thousand persons**
- reconstruction minus published estimate: **{difference:,.6f} thousand persons**
- absolute reconstruction discrepancy: **{discrepancy_se:.6f} official standard errors**
- published BLS standard error: **{se:,.6f} thousand persons**
- BLS-style 90% same-period confidence interval: **[{lower:,.3f}, {upper:,.3f}] thousand persons**
- exact published-rounding reproduction: **{benchmark['published_rounding_matches']}**
- project public-use validation threshold: **≤ {threshold:.1f} official standard error**
- threshold satisfied: **{benchmark['public_use_discrepancy_within_project_threshold']}**

## Why exact equality is not the validation rule

Census documents that disclosure-avoidance protections in Basic Monthly CPS public-use
files can cause estimates below the top-line labor-force totals—including estimates
using occupation—to differ slightly from BLS estimates based on internal files. Census
states that these differences should remain well within the sampling variability of the
CPS estimate. Accordingly, this project does not require an occupation estimate from the
public-use file to round exactly to the internal-file BLS publication.

The project uses **one published BLS standard error** as a conservative, explicit
validation threshold for this reconstruction. This is a project quality-control rule,
not a BLS significance test and not a Census-prescribed threshold. The exact difference
and its standardized value remain published regardless of pass/fail status.

## What this validates

This benchmark establishes a reproducible connection among three official outputs:
the Basic Monthly CPS public-use record, the BLS LN published point estimate, and the
BLS LN published standard-error aspect. The public-use reconstruction checks the
universe, occupation coding, and composited-final-weight arithmetic. The standard error
itself remains an official BLS design-based output; it is not reconstructed from the
public-use file.

## What this does not validate

BLS states that LN standard errors are intended for comparisons within the same
reference period. They do not provide the cross-month covariance needed for month-,
quarter-, or shorter year-over-year inference under the CPS rotating-panel design.
This benchmark therefore does not supply a covariance matrix for the observatory's
22-dimensional industry occupation shares and does not support a confidence interval
for a pooled-quarter residual.
"""
    path.write_text(report)


def execute(args: argparse.Namespace) -> dict[str, object]:
    if args.year != 2026:
        raise ValueError("benchmark execution is pinned to the audited 2026 CPS layout")
    period = month_period(args.month)
    args.input_dir.mkdir(parents=True, exist_ok=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    cps_filename = official_fixed_width_filename(args.year, args.month)
    cps_path = args.input_dir / cps_filename
    if not cps_path.exists():
        download_official_fixed_width_month(args.year, args.month, cps_path)
    cps_provenance = {
        "source_url": official_fixed_width_url(args.year, args.month),
        "record_layout_url": official_record_layout_url(args.year),
        "filename": cps_filename,
        "sha256": _sha256_file(cps_path),
        "file_size_bytes": cps_path.stat().st_size,
        "raw_file_published": False,
    }

    api_payload, api_provenance = _fetch_bls_series_with_aspects(series_id=args.series_id)
    official_estimate = parse_bls_api_month_value(
        api_payload,
        series_id=args.series_id,
        year=args.year,
        period=period,
    )
    official_se = extract_bls_api_standard_error(
        api_payload,
        series_id=args.series_id,
        year=args.year,
        period=period,
    )
    api_scientific_content = {
        "series_id": args.series_id,
        "year": args.year,
        "period": period,
        "published_estimate_thousands": official_estimate,
        "published_standard_error_thousands": official_se.value,
        "standard_error_aspect_type": official_se.aspect_type,
        "standard_error_footnote_code": official_se.footnote_code,
    }
    api_provenance["scientific_content_sha256"] = _canonical_sha256(api_scientific_content)
    api_provenance["scientific_content"] = api_scientific_content

    reconstruction = reconstruct_management_professional_employment(
        cps_path,
        year=args.year,
        month=args.month,
    )

    rounding_match = published_rounding_matches(
        reconstruction.benchmark_thousands,
        official_estimate,
    )
    difference = reconstruction.benchmark_thousands - official_estimate
    absolute_difference_se = abs(difference) / official_se.value
    discrepancy_within_threshold = (
        absolute_difference_se <= MAX_PUBLIC_USE_DISCREPANCY_STANDARD_ERRORS
    )
    confidence_half_width = 1.645 * official_se.value
    source_build_commit = args.source_build_commit or os.environ.get("GITHUB_SHA", "unrecorded")
    generated_at = _utc_now()

    benchmark = {
        "schema_version": 1,
        "benchmark_type": "bls_ln_same_period_cps_public_use_reconstruction",
        "series_id": args.series_id,
        "series_title": "Employment Level - Management, Professional, and Related Occupations",
        "year": args.year,
        "month": args.month.strip().lower(),
        "period": period,
        "published_estimate_thousands": official_estimate,
        "published_standard_error_thousands": official_se.value,
        "published_standard_error_aspect_type": official_se.aspect_type,
        "published_standard_error_footnote_code": official_se.footnote_code,
        "published_90pct_ci_lower_thousands": official_estimate - confidence_half_width,
        "published_90pct_ci_upper_thousands": official_estimate + confidence_half_width,
        "reconstructed_estimate_thousands": reconstruction.benchmark_thousands,
        "reconstruction_difference_thousands": difference,
        "absolute_reconstruction_difference_standard_errors": absolute_difference_se,
        "published_rounding_matches": rounding_match,
        "project_validation_threshold_standard_errors": MAX_PUBLIC_USE_DISCREPANCY_STANDARD_ERRORS,
        "public_use_discrepancy_within_project_threshold": discrepancy_within_threshold,
        "project_threshold_is_bls_or_census_rule": False,
        "cps_rows_read": reconstruction.rows_read,
        "cps_employed_16_plus_rows": reconstruction.employed_16_plus_rows,
        "cps_benchmark_rows": reconstruction.benchmark_rows,
        "universe": "employed people age 16 and over",
        "occupation_definition": "PRDTOCC1 major occupation recodes 1 through 10",
        "weight_variable": "PWCMPWGT composited final weight with four implied decimals",
        "interpretation": "same-reference-period validation only; no temporal covariance inference",
        "source_build_commit": source_build_commit,
        "generated_at_utc": generated_at,
    }
    validation = {
        "status": "pass" if discrepancy_within_threshold else "fail",
        "series_id": args.series_id,
        "year": args.year,
        "period": period,
        "published_rounding_reproduced": rounding_match,
        "official_standard_error_present": math.isfinite(official_se.value) and official_se.value > 0,
        "absolute_reconstruction_difference_standard_errors": absolute_difference_se,
        "project_validation_threshold_standard_errors": MAX_PUBLIC_USE_DISCREPANCY_STANDARD_ERRORS,
        "public_use_discrepancy_within_project_threshold": discrepancy_within_threshold,
        "project_threshold_is_bls_or_census_rule": False,
        "raw_cps_file_published": False,
        "raw_bls_api_response_published": False,
        "cross_month_covariance_available": False,
        "pooled_quarter_design_based_interval_supported": False,
        "source_build_commit": source_build_commit,
    }
    manifest = {
        "schema_version": 1,
        "benchmark_type": benchmark["benchmark_type"],
        "retrieved_at_utc": generated_at,
        "series_id": args.series_id,
        "bls_public_api": api_provenance,
        "bls_api_features_url": BLS_API_FEATURES_URL,
        "bls_ln_flat_aspect_reference_url": BLS_LN_ASPECT_URL,
        "bls_standard_error_guidance_url": BLS_SE_GUIDANCE_URL,
        "census_public_use_disclosure_note_url": CENSUS_PUBLIC_USE_DISCLOSURE_NOTE_URL,
        "census_public_use_documentation_url": CENSUS_PUBLIC_USE_DOCUMENTATION_URL,
        "cps_public_use": cps_provenance,
        "source_build_commit": source_build_commit,
    }

    (args.output_dir / "benchmark.json").write_text(
        json.dumps(benchmark, indent=2, sort_keys=True) + "\n"
    )
    (args.output_dir / "validation_checks.json").write_text(
        json.dumps(validation, indent=2, sort_keys=True) + "\n"
    )
    (args.output_dir / "input_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    (args.output_dir / "standard_error_observation.json").write_text(
        json.dumps(asdict(official_se), indent=2, sort_keys=True) + "\n"
    )
    _write_report(args.output_dir / "BENCHMARK_REPORT.md", benchmark)

    if not discrepancy_within_threshold:
        raise ValueError(
            "official CPS public-use reconstruction differs from the published BLS level by more "
            "than the project validation threshold: "
            f"difference={difference}, standard_errors={absolute_difference_se}, "
            f"threshold={MAX_PUBLIC_USE_DISCREPANCY_STANDARD_ERRORS}"
        )
    return validation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument("--month", default="jul")
    parser.add_argument("--series-id", default=MANAGEMENT_PROFESSIONAL_SERIES_ID)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source-build-commit")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        validation = execute(args)
    except Exception as exc:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        failure = {
            "schema_version": 1,
            "benchmark_type": "bls_ln_same_period_cps_public_use_reconstruction",
            "status": "failed",
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "year": args.year,
            "month": args.month,
            "series_id": args.series_id,
            "source_build_commit": args.source_build_commit
            or os.environ.get("GITHUB_SHA", "unrecorded"),
            "generated_at_utc": _utc_now(),
            "raw_cps_file_published": False,
            "raw_bls_api_response_published": False,
        }
        (args.output_dir / "failure.json").write_text(
            json.dumps(failure, indent=2, sort_keys=True) + "\n"
        )
        raise
    print(json.dumps(validation, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
