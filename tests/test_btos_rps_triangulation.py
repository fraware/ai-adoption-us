from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from genai_at_work.btos_rps_triangulation import (
    average_ranks,
    execute_v1,
    pearson_correlation,
    spearman_correlation,
)

ROOT = Path(__file__).parents[1]
BTOS = ROOT / "data" / "derived" / "btos" / "btos_core_ai_202611.json"
RPS = ROOT / "data" / "registry" / "rps_industry_adoption_q2_2026_v1.json"
CROSSWALK = ROOT / "data" / "registry" / "btos_rps_industry_crosswalk_v1.json"
ARTIFACT = ROOT / "data" / "derived" / "btos_rps" / "industry_triangulation_q2_2026_v1.json"
EXECUTION = ROOT / "data" / "registry" / "btos_rps_comparison_execution_state_v1.json"
RIGHTS = ROOT / "docs" / "source-rights" / "RPS_SOURCE_DECISION.md"
PUBLICATION_COMMIT = "75b94550be97c2e500db6c7b796330d0d8e90c40"
PUBLICATION_ROUTE = "/explore/industries"


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text())
    assert isinstance(value, dict)
    return value


def test_permission_decision_clears_only_live_aggregate_gate() -> None:
    text = RIGHTS.read_text()
    assert "Status: **GRANTED — live aggregate observatory gate**" in text
    assert "project-owner attestation of source-owner permission" in text
    assert "respondent-level or other non-public microdata" in text
    assert "unrestricted bulk mirroring" in text
    assert "legacy static exporter" in text


def test_rps_q2_2026_snapshot_has_complete_exact_industry_contract() -> None:
    source = _load(RPS)
    rows = source["rows"]
    assert isinstance(rows, list)
    assert source["period"] == "Q2 2026"
    assert source["metric_id"] == "adoption_work"
    assert source["question"] == "Do you use Generative AI for your job?"
    assert source["permission_basis"]["status"] == "user-attested-source-owner-permission"
    assert len(rows) == 20
    assert [row["entity_index"] for row in rows] == list(range(1, 21))
    assert [row["series_id"] for row in rows] == [
        f"RPSGENAIUSAGESHAREIND{index}" for index in range(1, 21)
    ]
    values = {row["entity_index"]: row["value_pct"] for row in rows}
    assert values[1] == pytest.approx(34.77068)
    assert values[9] == pytest.approx(82.19260)
    assert values[16] == pytest.approx(37.16530)
    assert values[19] == pytest.approx(24.67841)
    assert values[20] == pytest.approx(23.35467)


def test_rank_implementation_uses_average_ranks_for_ties() -> None:
    assert average_ranks([8.9, 12.0, 8.9]) == [1.5, 3.0, 1.5]


def test_basic_correlations_match_known_examples() -> None:
    assert pearson_correlation([1.0, 2.0, 3.0], [2.0, 4.0, 6.0]) == pytest.approx(1.0)
    assert spearman_correlation([1.0, 2.0, 3.0], [3.0, 2.0, 1.0]) == pytest.approx(-1.0)


def test_preregistered_primary_and_sensitivity_results_reproduce() -> None:
    result = execute_v1(_load(BTOS), _load(RPS), _load(CROSSWALK))
    primary = result["primary"]
    expanded = result["expanded_sensitivity"]

    assert primary["n"] == 14
    assert primary["entity_indices"] == [2, 3, 4, 5, 6, 8, 9, 11, 12, 14, 15, 16, 17, 18]
    assert primary["spearman_rho"] == pytest.approx(0.704070833089, abs=1e-12)
    assert primary["pearson_r"] == pytest.approx(0.797472661352, abs=1e-12)

    assert expanded["n"] == 17
    assert expanded["added_entity_indices"] == [7, 10, 19]
    assert expanded["spearman_rho"] == pytest.approx(0.815450797048, abs=1e-12)
    assert expanded["pearson_r"] == pytest.approx(0.850095624804, abs=1e-12)


def test_suppressed_and_unsupported_entities_are_never_paired() -> None:
    result = execute_v1(_load(BTOS), _load(RPS), _load(CROSSWALK))
    indices = {row["entity_index"] for row in result["pairs"]}
    assert 1 not in indices
    assert 13 not in indices
    assert 20 not in indices
    assert len(indices) == 17


def test_committed_artifact_matches_deterministic_executor_and_publication_state() -> None:
    artifact = _load(ARTIFACT)
    result = execute_v1(_load(BTOS), _load(RPS), _load(CROSSWALK))
    assert artifact["primary"] == result["primary"]
    assert artifact["expanded_sensitivity"] == result["expanded_sensitivity"]
    assert artifact["pairs"] == result["pairs"]
    assert artifact["public_product_status"] == "published"
    assert artifact["public_product_route"] == PUBLICATION_ROUTE
    assert artifact["publication_validated_commit"] == PUBLICATION_COMMIT


def test_cli_rebuilds_committed_analysis(tmp_path: Path) -> None:
    output = tmp_path / "analysis.json"
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "execute_btos_rps_industry_triangulation.py"), "--output", str(output)],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(output.read_text()) == json.loads(ARTIFACT.read_text())


def test_execution_state_records_published_analysis_without_inferential_overclaim() -> None:
    state = _load(EXECUTION)
    assert state["status"] == "cross-source-analysis-executed"
    assert state["rps_execution"]["rights_gate_blocks_execution"] is False
    assert state["rps_execution"]["industry_observation_vector_retrieved"] is True
    assert state["cross_source_execution"]["statistics_computed"] is True
    assert state["cross_source_execution"]["primary_n"] == 14
    assert state["cross_source_execution"]["p_values_computed"] is False
    assert state["cross_source_execution"]["correlation_confidence_intervals_computed"] is False
    assert state["cross_source_execution"]["scatter_plot_created"] is True
    assert state["cross_source_execution"]["scatter_plot_route"] == PUBLICATION_ROUTE
    assert state["cross_source_execution"]["leaderboard_created"] is False
    assert state["governance"]["canonicality_is_commit_scoped"] is True
    assert "reviewed commit" in state["governance"]["canonicality_rule"]
    assert state["governance"]["public_product_release_is_separate"] is True
    assert state["governance"]["public_product_release_status"] == "published"
    assert state["governance"]["public_product_route"] == PUBLICATION_ROUTE
    assert state["governance"]["publication_validated_commit"] == PUBLICATION_COMMIT
    assert state["governance"]["publication_post_merge_checks_verified"] is True
    assert "Maintain the published triangulation" in state["governance"]["next_permitted_step"]
    assert state["governance"]["protocol_v1_modified_after_outcome_inspection"] is False
