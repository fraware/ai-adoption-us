from __future__ import annotations

import json
from pathlib import Path

import pytest

from genai_at_work.revision_gate import (
    affected_claims,
    diff_artifacts,
    diff_fixture_records,
    fixture_records,
    sha256_file,
    stage_fingerprint,
    validate_review_attestation,
    validate_source_vintage,
    verify_current_fixture,
)


def _fixture() -> dict[str, object]:
    records: list[dict[str, object]] = []
    periods = ["2025-Q2", "2025-Q3", "2025-Q4", "2026-Q1", "2026-Q2"]
    metrics = ["adoption_work", "assisted_hours_share", "reported_time_savings_share"]
    for entity_type, count in (("industry", 20), ("occupation", 22)):
        for entity_index in range(1, count + 1):
            entity_id = f"{entity_type}-{entity_index:02d}"
            for metric_index, metric_id in enumerate(metrics, start=1):
                series_id = f"S-{entity_type}-{entity_index:02d}-{metric_index}"
                for period_index, period in enumerate(periods):
                    records.append(
                        {
                            "entity_type": entity_type,
                            "entity_id": entity_id,
                            "entity_index": entity_index,
                            "metric_id": metric_id,
                            "period": period,
                            "value": float(entity_index + metric_index + period_index),
                            "series_id": series_id,
                            "audit_scope": "private_research_only",
                            "rights_status": "Copyrighted: Citation Required",
                        }
                    )
    return {"records": records}


def _registry(fixture_path: Path) -> dict[str, object]:
    return {
        "freeze_id": "freeze-1",
        "fixture_sha256": sha256_file(fixture_path),
        "contract": {"rights_status": "Copyrighted: Citation Required"},
    }


def test_fixture_contract_and_frozen_checksum(tmp_path: Path):
    path = tmp_path / "fixture.json"
    path.write_text(json.dumps(_fixture()))
    registry = _registry(path)
    records = fixture_records(path)
    assert len(records) == 630
    assert verify_current_fixture(path, registry) == registry["fixture_sha256"]
    payload = _fixture()
    payload["records"][0]["value"] = 99.0  # type: ignore[index]
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="does not match the frozen registry"):
        verify_current_fixture(path, registry)


def test_source_vintage_fails_closed_on_rights_or_definition_change(tmp_path: Path):
    fixture = tmp_path / "fixture.json"
    fixture.write_text(json.dumps(_fixture()))
    registry = _registry(fixture)
    good = {
        "source_vintage_id": "rps-v2",
        "retrieved_at": "2026-09-01T12:00:00Z",
        "checkpoint_date": "2026-09-01",
        "rights_status": "Copyrighted: Citation Required",
        "definitions_status": "unchanged",
    }
    validate_source_vintage(good, registry)
    changed_rights = dict(good, rights_status="unknown")
    with pytest.raises(ValueError, match="Rights status changed"):
        validate_source_vintage(changed_rights, registry)
    changed_definition = dict(good, definitions_status="changed")
    with pytest.raises(ValueError, match="definition changes"):
        validate_source_vintage(changed_definition, registry)


def test_private_cell_diff_is_keyed_and_exact(tmp_path: Path):
    current_path = tmp_path / "current.json"
    candidate_path = tmp_path / "candidate.json"
    current = _fixture()
    candidate = _fixture()
    candidate["records"][0]["value"] = 17.0  # type: ignore[index]
    current_path.write_text(json.dumps(current))
    candidate_path.write_text(json.dumps(candidate))
    diff = diff_fixture_records(fixture_records(current_path), fixture_records(candidate_path))
    assert diff["changed_cell_count"] == 1
    change = diff["changes"][0]
    assert change["change"] == "modified"
    assert change["old_value"] != change["new_value"]


def test_artifact_diff_detects_post_stage_change(tmp_path: Path):
    canonical = tmp_path / "canonical"
    candidate = tmp_path / "candidate"
    canonical.mkdir()
    candidate.mkdir()
    names = (
        "longitudinal_diagnostics.json",
        "validation_checks.json",
        "quarter_diagnostics.csv",
        "rank_stability.csv",
    )
    for name in names:
        (canonical / name).write_text("same\n")
        (candidate / name).write_text("same\n")
    assert diff_artifacts(canonical, candidate)["changed_artifact_count"] == 0
    (candidate / "rank_stability.csv").write_text("changed\n")
    assert diff_artifacts(canonical, candidate)["changed_artifact_count"] == 1


def test_changed_artifacts_force_registered_claim_review():
    inventory = {
        "claims": [
            {"claim_id": "a", "surface": "one"},
            {"claim_id": "b", "surface": "two"},
        ]
    }
    claims = affected_claims(inventory, True)
    assert [claim["review_status"] for claim in claims] == ["PENDING", "PENDING"]


def test_review_attestation_is_bound_to_exact_stage_hashes_and_claims():
    artifact_diff = {
        "artifacts": [
            {"artifact": "a.json", "new_sha256": "aaa"},
            {"artifact": "b.csv", "new_sha256": "bbb"},
        ]
    }
    affected = [
        {"claim_id": "home", "review_status": "PENDING"},
        {"claim_id": "blog", "review_status": "PENDING"},
    ]
    manifest = {"candidate_fixture_sha256": "fixture", "changed_artifact_count": 2}
    stage_id = stage_fingerprint(manifest)
    attestation = {
        "stage_id": stage_id,
        "candidate_fixture_sha256": "fixture",
        "reviewer": "reviewer",
        "reviewed_at": "2026-09-01T12:00:00Z",
        "rights_reviewed": True,
        "definitions_reviewed": True,
        "all_affected_claims_reviewed": True,
        "artifact_sha256": {"a.json": "aaa", "b.csv": "bbb"},
        "reviewed_claim_ids": ["blog", "home"],
    }
    validate_review_attestation(
        attestation,
        stage_id=stage_id,
        candidate_fixture_sha256="fixture",
        artifact_diff=artifact_diff,
        affected=affected,
    )
    tampered = dict(attestation, artifact_sha256={"a.json": "aaa", "b.csv": "changed"})
    with pytest.raises(ValueError, match="artifact hashes"):
        validate_review_attestation(
            tampered,
            stage_id=stage_id,
            candidate_fixture_sha256="fixture",
            artifact_diff=artifact_diff,
            affected=affected,
        )
    incomplete = dict(attestation, reviewed_claim_ids=["home"])
    with pytest.raises(ValueError, match="every affected public claim"):
        validate_review_attestation(
            incomplete,
            stage_id=stage_id,
            candidate_fixture_sha256="fixture",
            artifact_diff=artifact_diff,
            affected=affected,
        )


def test_public_registry_matches_private_boundary():
    root = Path(__file__).parents[1]
    registry = json.loads((root / "data/registry/private_fixture_freeze.json").read_text())
    assert registry["fixture_sha256"] == "bdeffa95911a94cb60f904c51efc48f7ce4d1bf1eaaec490f5c4bfacd20d4fba"
    assert registry["fixture_path"].startswith("data/audit/private/")
    assert not (root / registry["fixture_path"]).exists()
