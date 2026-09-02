#!/usr/bin/env python3
"""Execute one official BLS LN/CPS same-period uncertainty benchmark.

The script reconstructs BLS series LNU02032201 from one official Basic Monthly
CPS public-use file, retrieves the corresponding BLS point estimate through the
Public Data API, and extracts the official standard error from the public LN
bulk aspect file.

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
    extract_ln_standard_error,
    month_period,
    parse_bls_api_month_value,
    published_rounding_matches,
    reconstruct_management_professional_employment,
)

BLS_SE_GUIDANCE_URL = (
    "https://www.bls.gov/cps/factsheets/understanding-standard-errors-and-confidence-intervals.htm"
)
USER_AGENT = "ai-adoption-us/1.0 public-data validation"


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()


def _download_public_file(url: str, destination: Path) -> dict[str, object]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    hasher = hashlib.sha256()
    try:
        with urllib.request.urlopen(request, timeout=120) as response, destination.open("wb") as out:
            while chunk := response.read(1024 * 1024):
                out.write(chunk)
                hasher.update(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return {
        "source_url": url,
        "sha256": hasher.hexdigest(),
        "file_size_bytes": destination.stat().st_size,
    }


def _fetch_bls_point_estimate(*, series_id: str, year: int) -> dict[str, Any]:
    payload = json.dumps(
        {
            "seriesid": [series_id],
            "startyear": str(year),
            "endyear": str(year),
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        BLS_PUBLIC_API_V2_URL,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        raw: object = json.loads(response.read().decode("utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("BLS Public Data API returned a non-object payload")
    return {str(key): value for key, value in raw.items()}


def _write_report(path: Path, benchmark: dict[str, object]) -> None:
    official = float(benchmark["published_estimate_thousands"])
    se = float(benchmark["published_standard_error_thousands"])
    reconstructed = float(benchmark["reconstructed_estimate_thousands"])
    difference = float(benchmark["reconstruction_difference_thousands"])
    lower = float(benchmark["published_90pct_ci_lower_thousands"])
    upper = float(benchmark["published_90pct_ci_upper_thousands"])
    report = f"""# CPS LN same-period uncertainty benchmark

## Result

The official Basic Monthly CPS public-use file reconstructs BLS series
`{benchmark['series_id']}` for {benchmark['year']} {benchmark['period']} under the
published **employed people age 16+** universe and the broad Management,
Professional, and Related occupation definition.

- BLS published estimate: **{official:,.0f} thousand persons**
- public-use reconstruction: **{reconstructed:,.6f} thousand persons**
- reconstruction minus published estimate: **{difference:,.6f} thousand persons**
- published BLS standard error: **{se:,.6f} thousand persons**
- BLS-style 90% same-period confidence interval: **[{lower:,.3f}, {upper:,.3f}] thousand persons**
- published-rounding reproduction: **{benchmark['published_rounding_matches']}**

## What this validates

This benchmark establishes a reproducible connection among three official artifacts:
the Basic Monthly CPS public-use record, the BLS LN published point estimate, and the
BLS LN published standard-error aspect. The public-use reconstruction is a check on
universe/weight/occupation coding. The standard error itself remains an official BLS
design-based output; it is not reconstructed from the public-use file.

## What this does not validate

The LN standard error is intended for comparisons within the same reference period.
It does not provide the cross-month covariance needed for month-, quarter-, or
shorter year-over-year inference under the CPS rotating-panel design. This benchmark
therefore does not supply a covariance matrix for the observatory's 22-dimensional
industry occupation shares and does not support a confidence interval for a pooled
quarter residual.
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
    }

    aspect_path = args.input_dir / "ln.aspect"
    aspect_provenance = _download_public_file(BLS_LN_ASPECT_URL, aspect_path)
    official_se = extract_ln_standard_error(
        aspect_path,
        series_id=args.series_id,
        year=args.year,
        period=period,
    )

    api_payload = _fetch_bls_point_estimate(series_id=args.series_id, year=args.year)
    official_estimate = parse_bls_api_month_value(
        api_payload,
        series_id=args.series_id,
        year=args.year,
        period=period,
    )
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
        "published_rounding_matches": rounding_match,
        "cps_rows_read": reconstruction.rows_read,
        "cps_employed_16_plus_rows": reconstruction.employed_16_plus_rows,
        "cps_benchmark_rows": reconstruction.benchmark_rows,
        "universe": "employed people age 16 and over",
        "occupation_definition": "PRDTOCC1 major occupation recodes 1 through 10",
        "weight_variable": "PWSSWGT with four implied decimals",
        "interpretation": "same-reference-period validation only; no temporal covariance inference",
        "source_build_commit": source_build_commit,
        "generated_at_utc": generated_at,
    }
    validation = {
        "status": "pass" if rounding_match else "fail",
        "series_id": args.series_id,
        "year": args.year,
        "period": period,
        "published_rounding_reproduced": rounding_match,
        "official_standard_error_present": math.isfinite(official_se.value) and official_se.value > 0,
        "raw_cps_file_published": False,
        "raw_ln_aspect_file_published": False,
        "cross_month_covariance_available": False,
        "pooled_quarter_design_based_interval_supported": False,
        "source_build_commit": source_build_commit,
    }
    manifest = {
        "schema_version": 1,
        "benchmark_type": benchmark["benchmark_type"],
        "retrieved_at_utc": generated_at,
        "series_id": args.series_id,
        "bls_public_api_url": BLS_PUBLIC_API_V2_URL,
        "bls_ln_aspect": aspect_provenance,
        "bls_standard_error_guidance_url": BLS_SE_GUIDANCE_URL,
        "cps_public_use": cps_provenance,
        "raw_cps_file_published": False,
        "raw_ln_aspect_file_published": False,
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

    if not rounding_match:
        raise ValueError(
            "official CPS public-use reconstruction does not round to the published BLS level: "
            f"reconstructed={reconstruction.benchmark_thousands}, published={official_estimate}"
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
    validation = execute(parse_args())
    print(json.dumps(validation, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
