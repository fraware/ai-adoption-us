#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from genai_at_work.longitudinal import (
    REQUIRED_PERIODS,
    all_quarter_diagnostics,
    all_rank_stability,
    all_rank_stability_detail,
    cross_level_comparison,
    dominance_checks,
    nested_quarter_diagnostics,
    normalize_records,
    rank_stability_dominance,
    validate_private_fixture,
)


def _round(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 10)
    if isinstance(value, list):
        return [_round(v) for v in value]
    if isinstance(value, dict):
        return {k: _round(v) for k, v in value.items()}
    return value


def _publication_validation(records, fixture_checks: dict[str, bool]) -> dict[str, object]:
    qd = {(d["entity_type"], d["period"]): d for d in all_quarter_diagnostics(records)}
    dominance = dominance_checks(records)
    checks = {
        "all_private": fixture_checks["all_private"],
        "entities_42": fixture_checks["entities_42"],
        "industry_H_beats_A_in_3_of_5": dominance["industry_H_beats_A_waves"] == 3,
        "industry_adoption_rank_more_stable_than_H_all_10": dominance["industry_adoption_rank_gt_H_pairs"] == 10,
        "industry_adoption_rank_more_stable_than_S_all_10": dominance["industry_adoption_rank_gt_S_pairs"] == 10,
        "occupation_AH_pearson_gt_industry_all_5": dominance["occupation_AH_pearson_exceeds_industry_all_5"] is True,
        "occupation_AH_spearman_gt_industry_all_5": dominance["occupation_AH_spearman_exceeds_industry_all_5"] is True,
        "occupation_A_predicts_S_gt_H_all_5": dominance["occupation_A_beats_H_for_S_all_5"] is True,
        "occupation_LOO_A_beats_H_all_110": dominance["occupation_leave_one_out_A_beats_H"] == 110,
        "occupation_adoption_rank_more_stable_than_H_all_10": dominance["occupation_adoption_rank_gt_H_pairs"] == 10,
        "occupation_adoption_rank_more_stable_than_S_all_10": dominance["occupation_adoption_rank_gt_S_pairs"] == 10,
        "periods_5": len(REQUIRED_PERIODS) == 5,
        "q2_industry_r2_H_A": abs(float(qd[("industry", "2026-Q2")]["r2_H_A"]) - 0.5720649640229158) < 1e-12,
        "q2_industry_r2_S_A": abs(float(qd[("industry", "2026-Q2")]["r2_S_A"]) - 0.6743621529087418) < 1e-12,
        "q2_industry_r2_S_A_H": abs(float(qd[("industry", "2026-Q2")]["r2_S_A_H"]) - 0.8011260611502208) < 1e-12,
        "q2_industry_r2_S_H": abs(float(qd[("industry", "2026-Q2")]["r2_S_H"]) - 0.729350702198649) < 1e-12,
        "rights_marked": fixture_checks["rights_marked"],
        "row_count_630": fixture_checks["rows_630"],
        "series_126": fixture_checks["series_126"],
        "unique_key_630": fixture_checks["unique_keys_630"],
        "values_finite_0_100": fixture_checks["values_finite_0_100"],
    }
    return {"all_passed": all(checks.values()), "check_count": len(checks), "checks": checks}


def build(fixture_path: Path, output_dir: Path, checkpoint_date: str = "2026-08-30") -> None:
    raw_bytes = fixture_path.read_bytes()
    fixture = json.loads(raw_bytes)
    records = normalize_records(fixture["records"])
    fixture_checks = validate_private_fixture(records)
    if not all(fixture_checks.values()):
        failed = [k for k, v in fixture_checks.items() if not v]
        raise SystemExit(f"Private fixture validation failed: {failed}")

    quarter_rows = all_quarter_diagnostics(records)
    rank_rows = all_rank_stability(records)
    diagnostics = _round(
        {
            "checkpoint_date": checkpoint_date,
            "cross_level_comparison": cross_level_comparison(records),
            "input_private_fixture_rows": len(records),
            "input_private_fixture_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "input_scope": {
                "industry_entities": 20,
                "metrics": ["adoption_work", "assisted_hours_share", "reported_time_savings_share"],
                "occupation_entities": 22,
                "periods": list(REQUIRED_PERIODS),
                "source_vintage_note": "Current FRED series pages show Aug 4, 2026 updates for the Q2 2026 wave.",
            },
            "interpretive_guardrails": [
                "All regressions are unweighted aggregate cross-sectional descriptive diagnostics.",
                "No conventional significance claims are licensed because subgroup standard errors are not available in the audited FRED series pages.",
                "Reported time savings are self-reported counterfactual hours, not measured labor productivity.",
                "Quarterly instability may reflect both true changes and sampling noise in subgroup estimates.",
            ],
            "quarter_diagnostics": nested_quarter_diagnostics(records),
            "rank_stability": all_rank_stability_detail(records),
            "rank_stability_dominance": rank_stability_dominance(records),
            "status": "DERIVED RESEARCH DIAGNOSTICS; DESCRIPTIVE, NOT CAUSAL",
        }
    )
    validation = _publication_validation(records, fixture_checks)

    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "quarter_diagnostics.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(quarter_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(quarter_rows)
    with (output_dir / "rank_stability.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rank_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rank_rows)
    (output_dir / "longitudinal_diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2, sort_keys=True) + "\n"
    )
    (output_dir / "validation_checks.json").write_text(
        json.dumps(validation, indent=2, sort_keys=True) + "\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--checkpoint-date", default="2026-08-30")
    args = parser.parse_args()
    build(args.fixture, args.output_dir, args.checkpoint_date)
    validation = json.loads((args.output_dir / "validation_checks.json").read_text())
    print(json.dumps(validation, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
