from __future__ import annotations

from json import loads
from pathlib import Path

REGISTRY = Path(__file__).parents[1] / "data" / "registry" / "btos_construct_scope_v1.json"


def test_btos_construct_status_records_source_reproduction_without_cross_source_claim() -> None:
    registry = loads(REGISTRY.read_text())
    status = registry["empirical_status"]

    assert status["observation_values_included"] is True
    assert status["source_ingestion_status"] == "cycle-202617-core-source-reproduction-executed"
    assert "cross-source-analysis-not-executed" in status["construct_alignment_status"]
    assert "no BTOS-RPS statistic published" in status["public_analysis_status"]
    assert status["verified_checkpoint"] == "data/derived/btos/btos_core_ai_202617.json"
    assert status["verified_source_registry"] == "data/registry/btos_core_ai_202617_source_v1.json"


def test_btos_cross_source_analysis_remains_fail_closed() -> None:
    registry = loads(REGISTRY.read_text())
    remaining = " ".join(registry["remaining_before_cross_source_analysis"])

    assert "Pre-specify the BTOS-versus-RPS comparison period" in remaining
    assert "BTOS-suppressed sectors" in remaining
    assert "RPS source-rights gate" in remaining
    assert "causal evidence" in remaining
    assert "composite adoption score" in remaining
