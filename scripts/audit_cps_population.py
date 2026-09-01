#!/usr/bin/env python3
"""Audit the CPS population boundary used by the RPS composition analysis.

The RPS comparison sample is the civilian population ages 18-64. This script
independently audits the official 2026 Basic Monthly fixed-width files before the
industry/occupation composition transformation. It records Armed Forces and unmapped
exclusions explicitly and verifies the final civilian employed weight used by the
composition pipeline.
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
from pathlib import Path

from genai_at_work.cps import (
    decode_fixed_width_record_2026,
    official_fixed_width_filename,
    parse_final_weight,
    quarter_months,
)

POPULATION_WEIGHT_ABS_TOLERANCE = 1e-4


def _as_int(value: str) -> int | None:
    text = value.strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--quarter", type=int, choices=(1, 2, 3, 4), required=True)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--composition-validation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.year != 2026:
        raise SystemExit("population audit is pinned to the audited 2026 CPS record layout")

    root = Path(__file__).resolve().parents[1]
    registry = root / "data" / "registry"
    months = quarter_months(args.year, args.quarter, registry)
    month_factor = 1.0 / len(months)

    monthly: list[dict[str, object]] = []
    totals = {
        "rows": 0,
        "age_18_64_employed_rows_positive_weight": 0,
        "age_18_64_employed_weight": 0.0,
        "civilian_analysis_rows": 0,
        "civilian_analysis_weight": 0.0,
        "armed_forces_industry_rows": 0,
        "armed_forces_industry_weight": 0.0,
        "armed_forces_occupation_rows": 0,
        "armed_forces_occupation_weight": 0.0,
        "unmapped_industry_rows": 0,
        "unmapped_industry_weight": 0.0,
        "civilian_industry_unmapped_occupation_rows": 0,
        "civilian_industry_unmapped_occupation_weight": 0.0,
    }

    for month in months:
        path = args.input_dir / official_fixed_width_filename(args.year, month)
        if not path.exists():
            raise SystemExit(f"missing official CPS input for population audit: {path}")

        month_stats = {key: (0.0 if key.endswith("_weight") else 0) for key in totals}
        with gzip.open(path, "rt", encoding="ascii", newline="") as handle:
            for line in handle:
                month_stats["rows"] += 1
                row = decode_fixed_width_record_2026(line)
                age = _as_int(row["PRTAGE"])
                employed = _as_int(row["PREMPNOT"])
                weight = parse_final_weight(row["PWSSWGT"])
                if age is None or not 18 <= age <= 64 or employed != 1 or weight is None:
                    continue

                pooled_weight = weight * month_factor
                month_stats["age_18_64_employed_rows_positive_weight"] += 1
                month_stats["age_18_64_employed_weight"] += pooled_weight

                industry = _as_int(row["PRDTIND1"])
                occupation = _as_int(row["PRDTOCC1"])

                if industry == 52:
                    month_stats["armed_forces_industry_rows"] += 1
                    month_stats["armed_forces_industry_weight"] += pooled_weight
                    continue
                if industry is None or not 1 <= industry <= 51:
                    month_stats["unmapped_industry_rows"] += 1
                    month_stats["unmapped_industry_weight"] += pooled_weight
                    continue

                if occupation == 23:
                    month_stats["armed_forces_occupation_rows"] += 1
                    month_stats["armed_forces_occupation_weight"] += pooled_weight
                if occupation is None or not 1 <= occupation <= 22:
                    month_stats["civilian_industry_unmapped_occupation_rows"] += 1
                    month_stats["civilian_industry_unmapped_occupation_weight"] += pooled_weight

                month_stats["civilian_analysis_rows"] += 1
                month_stats["civilian_analysis_weight"] += pooled_weight

        for key, value in month_stats.items():
            totals[key] += value
        monthly.append({"month": month, **month_stats})

    validation = json.loads(args.composition_validation.read_text())
    composition_weight = float(validation["weighted_worker_population_age_18_64_employed"])
    civilian_weight = float(totals["civilian_analysis_weight"])
    absolute_difference = abs(civilian_weight - composition_weight)
    matches_composition = math.isclose(
        civilian_weight,
        composition_weight,
        rel_tol=0.0,
        abs_tol=POPULATION_WEIGHT_ABS_TOLERANCE,
    )
    if not matches_composition:
        raise SystemExit(
            "civilian population audit does not match composition weight: "
            f"audit={civilian_weight}, composition={composition_weight}, "
            f"abs_difference={absolute_difference}"
        )

    payload = {
        "status": "independent CPS population-boundary audit",
        "period": f"{args.year}-Q{args.quarter}",
        "population_target": "civilian employed population ages 18-64",
        "month_factor": month_factor,
        "civilian_industry_codes": "PRDTIND1 1-51",
        "armed_forces_industry_code": 52,
        "civilian_occupation_codes": "PRDTOCC1 1-22",
        "armed_forces_occupation_code": 23,
        "monthly": monthly,
        "totals": totals,
        "composition_weight": composition_weight,
        "civilian_weight_matches_composition": matches_composition,
        "population_weight_absolute_difference": absolute_difference,
        "population_weight_absolute_tolerance": POPULATION_WEIGHT_ABS_TOLERANCE,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
