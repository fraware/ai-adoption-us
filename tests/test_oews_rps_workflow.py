from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "rps-live-validation.yml"
SCRIPT = ROOT / "scripts" / "build_oews_rps_adoption_robustness.py"


def test_live_workflow_runs_oews_rps_robustness_from_private_source_snapshot() -> None:
    text = WORKFLOW.read_text()
    assert "scripts/build_oews_rps_adoption_robustness.py" in text
    assert "src/genai_at_work/oews_rps.py" in text
    assert "data/derived/composition/oews-may-2025/oews_composition.json" in text
    assert "data/registry/oews_occupation_crosswalk_v1.json" in text
    assert "--source-snapshot /tmp/rps-refresh/rps_source_snapshot.json" in text
    assert "--cps-primary-residuals /tmp/rps-composition/primary_residuals.json" in text
    assert "--period 2025-Q2" in text
    assert "--period 2026-Q2" in text
    assert "--output-dir /tmp/oews-rps-adoption" in text


def test_live_artifact_assembly_does_not_copy_private_rps_snapshot() -> None:
    text = WORKFLOW.read_text()
    assert 'cp -R /tmp/oews-rps-adoption/. "$evidence/oews-rps-adoption/"' in text
    assert 'test ! -e "$evidence/oews-rps-adoption/rps_source_snapshot.json"' in text
    assert "public_raw_rps_observations_included" in text
    assert "oews_inputs.get(\"source_content_sha256\") != source.get(\"content_sha256\")" in text


def test_oews_rps_builder_is_offline_and_fail_closed() -> None:
    text = SCRIPT.read_text()
    assert "FredClient" not in text
    assert "httpx" not in text
    assert "requests" not in text
    assert "source_snapshot_published\": False" in text
    assert "public_raw_rps_observations_included\": False" in text
    assert "snapshot_content_sha256(snapshot)" in text
    assert "prepare_rps_source_history(snapshot, manifest, scope)" in text
    assert "CPS and OEWS residuals are never averaged" in text
