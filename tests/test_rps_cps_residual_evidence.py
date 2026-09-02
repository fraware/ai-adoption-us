from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
EVIDENCE = ROOT / "data" / "derived" / "composition" / "rps-cps-residuals-2026-09-02"
EXPECTED_SOURCE_CONTENT_SHA = "fe8bffa7cacd029cc23e2ba7e310d925e8c05322f6d53bd89e8234f02e825b73"
EXPECTED_SOURCE_SNAPSHOT_SHA = "6aebc5a9c317e0ae376b04eb7ae9a7c32342503679f740a3e4085e706177139e"
EXPECTED_RUN_ID = "33683408001"
EXPECTED_RUN_COMMIT = "3fd0abd9c5573c3c2bca7bb53205bc52fa2cd453"


def _json(name: str) -> dict[str, object]:
    value = json.loads((EVIDENCE / name).read_text())
    assert isinstance(value, dict)
    return value


def _csv(name: str) -> list[dict[str, str]]:
    with (EVIDENCE / name).open(newline="") as handle:
        return list(csv.DictReader(handle))


def test_live_residual_evidence_is_bound_to_successful_source_run() -> None:
    provenance = _json("provenance.json")
    assert provenance["source_content_sha256"] == EXPECTED_SOURCE_CONTENT_SHA
    assert provenance["source_snapshot_file_sha256"] == EXPECTED_SOURCE_SNAPSHOT_SHA
    assert provenance["source_observation_count"] == 962
    assert provenance["source_series_count"] == 131
    assert provenance["github_validation_run_id"] == EXPECTED_RUN_ID
    assert provenance["github_validation_commit"] == EXPECTED_RUN_COMMIT
    assert provenance["github_validation_result"] == "success"
    assert provenance["promotion_performed"] is False
    rights = provenance["rights"]
    assert isinstance(rights, dict)
    assert rights["public_raw_source_snapshot_included"] is False
    assert rights["complete_source_catalog_mirror_included"] is False


def test_primary_residual_table_is_complete_and_algebraically_consistent() -> None:
    rows = _csv("primary_residuals.csv")
    assert len(rows) == 120
    keys: set[tuple[str, str, str]] = set()
    expected_industries = {str(index) for index in range(1, 21)}
    expected_metrics = {
        "adoption_work",
        "assisted_hours_share",
        "reported_time_savings_share",
    }
    expected_periods = {"2025-Q2", "2026-Q2"}
    for row in rows:
        key = (row["industry_index"], row["period"], row["metric_id"])
        assert key not in keys
        keys.add(key)
        assert row["suppressed"] == "False"
        observed = float(row["observed"])
        predicted = float(row["predicted_from_occupation_mix"])
        residual = float(row["occupation_adjusted_industry_context_residual"])
        assert abs((observed - predicted) - residual) < 1e-10
        if row["metric_id"] == "adoption_work":
            assert row["weight_basis"] == "CPS worker share"
        else:
            assert row["weight_basis"] == "CPS actual main-job hour share"
    assert {row["industry_index"] for row in rows} == expected_industries
    assert {row["metric_id"] for row in rows} == expected_metrics
    assert {row["period"] for row in rows} == expected_periods


def test_validation_and_persistence_contracts_are_retained() -> None:
    validation = _json("validation_checks.json")
    assert validation["status"] == "pass"
    assert validation["primary_row_count"] == 120
    assert validation["primary_supported_row_count"] == 120
    assert validation["primary_suppressed_row_count"] == 0
    assert validation["leave_one_occupation_out_row_count"] == 120
    assert validation["usual_hours_sensitivity_row_count"] == 80

    persistence = _csv("cross_period_persistence.csv")
    assert len(persistence) == 6
    assert {row["cohort"] for row in persistence} == {"all_supported", "primary_stable"}
    assert {row["metric_id"] for row in persistence} == {
        "adoption_work",
        "assisted_hours_share",
        "reported_time_savings_share",
    }
    for row in persistence:
        assert row["earlier_period"] == "2025-Q2"
        assert row["later_period"] == "2026-Q2"
        assert -1.0 <= float(row["residual_rank_spearman"]) <= 1.0
        assert 0.0 <= float(row["sign_agreement_share"]) <= 1.0


def test_robustness_summary_does_not_convert_sensitivity_into_inference() -> None:
    robustness = _json("robustness_summary.json")
    assert robustness["interpretation"] == "descriptive sensitivity, not sampling inference"
    leave_one_out = robustness["leave_one_occupation_out"]
    assert isinstance(leave_one_out, dict)
    assert leave_one_out["row_count"] == 120
    assert leave_one_out["supported_row_count"] == 120
    usual = robustness["usual_hours_sensitivity"]
    assert isinstance(usual, dict)
    assert usual["coverage_gate"] == 0.98
    assert usual["row_count"] == 80
    assert usual["supported_row_count"] == 2


def test_public_evidence_directory_contains_no_raw_source_snapshot() -> None:
    names = {path.name for path in EVIDENCE.iterdir() if path.is_file()}
    assert "rps_source_snapshot.json" not in names
    assert "rps_refresh_diff.json" not in names
    assert "rps-component-release.json" not in names
    assert not any("private_vintage" in name for name in names)
