from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from genai_at_work.release_engine import (
    candidate_gate_failures,
    diff_releases,
    gate_status,
    sha256_file,
    validate_release_manifest,
    validate_review_attestation,
)


def _digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _digest_text(value: str) -> str:
    return _digest_bytes(value.encode())


def _write(path: Path, content: str) -> tuple[str, int]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return sha256_file(path), path.stat().st_size


def _candidate(
    root: Path,
    *,
    release_id: str = "release-1",
    supersedes: str | None = None,
    periods: list[str] | None = None,
    extra_object: bool = False,
    artifact_text: str = '{"value": 1}\n',
    claim_text: str = "claim-v1",
    rights_status: str = "approved",
    redistribution_scope: str = "derived_only",
    definition_id: str = "definition-v1",
    coverage_status: str = "pass",
    observed_units: int = 10,
    required_units: int = 10,
    revision_status: str = "new_wave",
    data_mode: str = "derived_only",
) -> dict[str, Any]:
    periods = periods or ["2026-Q1"]
    source_sha, source_size = _write(root / "inputs/source-q1.csv", "series,value\na,1\n")
    objects: list[dict[str, Any]] = [
        {
            "object_id": "q1",
            "locator": "https://example.test/source-q1.csv",
            "local_path": "inputs/source-q1.csv",
            "sha256": source_sha,
            "size_bytes": source_size,
        }
    ]
    if extra_object:
        q2_sha, q2_size = _write(root / "inputs/source-q2.csv", "series,value\na,2\n")
        objects.append(
            {
                "object_id": "q2",
                "locator": "https://example.test/source-q2.csv",
                "local_path": "inputs/source-q2.csv",
                "sha256": q2_sha,
                "size_bytes": q2_size,
            }
        )
    artifact_sha, artifact_size = _write(root / "artifacts/result.json", artifact_text)
    artifacts = [
        {
            "artifact_id": "result",
            "path": "artifacts/result.json",
            "sha256": artifact_sha,
            "size_bytes": artifact_size,
            "evidence_class": 2,
            "source_ids": ["survey"],
        }
    ]
    diagnostics = [
        {
            "diagnostic_id": diagnostic_class,
            "diagnostic_class": diagnostic_class,
            "status": "pass",
            "value_digest": _digest_text(f"{diagnostic_class}:{artifact_sha}"),
        }
        for diagnostic_class in (
            "stability",
            "influence",
            "regression_contract",
            "suppression_coverage",
        )
    ]
    claims = [
        {
            "claim_id": "claim-1",
            "surfaces": ["/", "/methodology"],
            "artifact_ids": ["result"],
            "value_digest": _digest_text(claim_text),
            "value_summary": claim_text,
            "truth_state": "supported",
            "evidence_class": 2,
            "interpretation_boundary": "Descriptive synthetic test claim; no causal interpretation.",
        }
    ]
    return {
        "schema_version": 1,
        "release_id": release_id,
        "release_type": "baseline" if supersedes is None else "new_wave",
        "data_mode": data_mode,
        "created_at": "2026-09-01T13:00:00Z",
        "supersedes_release_id": supersedes,
        "sources": [
            {
                "source_id": "survey",
                "provider": "Synthetic Provider",
                "dataset": "Synthetic Survey",
                "source_vintage_id": release_id,
                "retrieved_at": "2026-09-01T12:00:00Z",
                "revision_status": revision_status,
                "reference_periods": periods,
                "instrument_version": "instrument-v1",
                "definition_id": definition_id,
                "taxonomy_versions": {"industry": "taxonomy-v1"},
                "rights": {
                    "status": rights_status,
                    "storage_scope": "private",
                    "publication_scope": "derived_only",
                    "redistribution_scope": redistribution_scope,
                },
                "coverage": {
                    "status": coverage_status,
                    "required_units": required_units,
                    "observed_units": observed_units,
                },
                "objects": objects,
            }
        ],
        "artifacts": artifacts,
        "diagnostics": diagnostics,
        "claims": claims,
        "build": {
            "builder_id": "synthetic-builder-v1",
            "builder_commit": "0123456789abcdef",
            "deterministic": True,
            "input_sha256": {f"survey:{row['object_id']}": row["sha256"] for row in objects},
            "output_sha256": {"result": artifact_sha},
        },
    }


def _manifest(path: Path, value: dict[str, Any]) -> Path:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    return path


def _registry(path: Path) -> Path:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "current_release_id": None,
                "current_release_manifest_sha256": None,
                "releases": [],
                "status": "NO_OBSERVATORY_RELEASE_PROMOTED_YET",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    return path


def _run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, str(root / "scripts/observatory_release.py"), *args],
        cwd=root,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )


def _attestation(stage_dir: Path, candidate_manifest: Path, candidate: dict[str, Any]) -> dict[str, Any]:
    stage = json.loads((stage_dir / "stage_manifest.json").read_text())
    diff = json.loads((stage_dir / "release_diff.json").read_text())
    return {
        "stage_id": stage["stage_id"],
        "release_id": candidate["release_id"],
        "candidate_manifest_sha256": sha256_file(candidate_manifest),
        "reviewer": "synthetic-reviewer",
        "reviewed_at": "2026-09-01T14:00:00Z",
        "scientific_reviewed": True,
        "editorial_reviewed": True,
        "source_rights_reviewed": True,
        "ci_passed": True,
        "candidate_commit": "abcdef0123456789",
        "ci_run_ids": [12345],
        "artifact_sha256": {row["artifact_id"]: row["sha256"] for row in candidate["artifacts"]},
        "reviewed_source_ids": diff["changed_source_ids"],
        "reviewed_diagnostic_ids": diff["changed_diagnostic_ids"],
        "reviewed_claim_ids": diff["affected_claim_ids"],
    }


def test_manifest_integrity_namespaces_and_build_contract(tmp_path: Path):
    candidate = _candidate(tmp_path)
    validate_release_manifest(candidate, tmp_path)
    candidate["artifacts"][0]["path"] = "result.json"
    with pytest.raises(ValueError, match="must live under artifacts"):
        validate_release_manifest(candidate, tmp_path)

    candidate = _candidate(tmp_path / "build")
    candidate["build"]["input_sha256"]["survey:q1"] = "0" * 64
    with pytest.raises(ValueError, match="exactly cover every verified source object"):
        validate_release_manifest(candidate, tmp_path / "build")


def test_unresolved_rights_nonredistributable_rights_and_failed_coverage_are_closed(tmp_path: Path):
    unresolved = _candidate(tmp_path / "rights", rights_status="unresolved")
    validate_release_manifest(unresolved, tmp_path / "rights")
    diff = diff_releases(None, unresolved)
    assert gate_status(candidate_gate_failures(unresolved, diff), True) == "BLOCKED_RIGHTS"

    nonredistributable = _candidate(tmp_path / "redist", redistribution_scope="none")
    validate_release_manifest(nonredistributable, tmp_path / "redist")
    diff = diff_releases(None, nonredistributable)
    assert gate_status(candidate_gate_failures(nonredistributable, diff), True) == "BLOCKED_RIGHTS"

    coverage = _candidate(tmp_path / "coverage", coverage_status="fail", observed_units=9)
    validate_release_manifest(coverage, tmp_path / "coverage")
    diff = diff_releases(None, coverage)
    assert gate_status(candidate_gate_failures(coverage, diff), True) == "BLOCKED_COVERAGE"


def test_definition_data_mode_and_missing_history_fail_closed(tmp_path: Path):
    old = _candidate(tmp_path / "old")
    definition = _candidate(
        tmp_path / "definition",
        release_id="release-2",
        supersedes="release-1",
        definition_id="definition-v2",
    )
    diff = diff_releases(old, definition)
    assert "DEFINITION_CHANGE" in {row["code"] for row in diff["contract_failures"]}
    assert gate_status(candidate_gate_failures(definition, diff), True) == "BLOCKED_DEFINITION_CHANGE"

    mode = _candidate(
        tmp_path / "mode",
        release_id="release-2",
        supersedes="release-1",
        data_mode="rights_cleared_direct",
    )
    diff = diff_releases(old, mode)
    assert gate_status(candidate_gate_failures(mode, diff), True) == "BLOCKED_DATA_MODE_CHANGE"

    previous = _candidate(tmp_path / "history-old", periods=["2026-Q1", "2026-Q2"], extra_object=True)
    missing = _candidate(
        tmp_path / "history-new",
        release_id="release-2",
        supersedes="release-1",
        periods=["2026-Q1"],
    )
    diff = diff_releases(previous, missing)
    codes = {row["code"] for row in diff["contract_failures"]}
    assert {"MISSING_PERIOD", "MISSING_SOURCE_OBJECT"} <= codes
    assert gate_status(candidate_gate_failures(missing, diff), True) == "BLOCKED_MISSING_SERIES"


def test_release_type_revision_status_and_vintage_identity_are_explicit(tmp_path: Path):
    old = _candidate(tmp_path / "old")
    new = _candidate(
        tmp_path / "new",
        release_id="release-2",
        supersedes="release-1",
        periods=["2026-Q1", "2026-Q2"],
        extra_object=True,
    )
    new["release_type"] = "revision"
    diff = diff_releases(old, new)
    assert "RELEASE_TYPE_MISMATCH" in {row["code"] for row in diff["contract_failures"]}

    unchanged_status = _candidate(
        tmp_path / "status",
        release_id="release-2",
        supersedes="release-1",
        periods=["2026-Q1", "2026-Q2"],
        extra_object=True,
        revision_status="unchanged",
    )
    diff = diff_releases(old, unchanged_status)
    assert "REVISION_STATUS_MISMATCH" in {row["code"] for row in diff["contract_failures"]}

    stale_vintage = _candidate(
        tmp_path / "vintage",
        release_id="release-2",
        supersedes="release-1",
        periods=["2026-Q1", "2026-Q2"],
        extra_object=True,
    )
    stale_vintage["sources"][0]["source_vintage_id"] = "release-1"
    diff = diff_releases(old, stale_vintage)
    assert "SOURCE_VINTAGE_ID_NOT_ADVANCED" in {row["code"] for row in diff["contract_failures"]}


def test_new_wave_diff_exposes_magnitude_truth_and_all_dependency_layers(tmp_path: Path):
    old = _candidate(tmp_path / "old")
    new = _candidate(
        tmp_path / "new",
        release_id="release-2",
        supersedes="release-1",
        periods=["2026-Q1", "2026-Q2"],
        extra_object=True,
        artifact_text='{"value": 2}\n',
        claim_text="claim-v2",
    )
    diff = diff_releases(old, new)
    assert diff["contract_failures"] == []
    assert diff["changed_source_ids"] == ["survey"]
    assert diff["changed_artifact_ids"] == ["result"]
    assert set(diff["changed_diagnostic_ids"]) == {
        "stability",
        "influence",
        "regression_contract",
        "suppression_coverage",
    }
    assert diff["affected_claim_ids"] == ["claim-1"]
    claim = diff["claim_changes"][0]
    assert claim["old_value_summary"] == "claim-v1"
    assert claim["new_value_summary"] == "claim-v2"
    assert claim["surfaces"] == ["/", "/methodology"]
    assert gate_status(candidate_gate_failures(new, diff), True) == "BLOCKED_REVIEW_REQUIRED"


def test_review_attestation_binds_ci_artifacts_sources_diagnostics_and_claims(tmp_path: Path):
    candidate = _candidate(tmp_path)
    diff = diff_releases(None, candidate)
    manifest_path = _manifest(tmp_path / "release.json", candidate)
    attestation = {
        "stage_id": "stage-id",
        "release_id": "release-1",
        "candidate_manifest_sha256": sha256_file(manifest_path),
        "reviewer": "reviewer",
        "reviewed_at": "2026-09-01T14:00:00Z",
        "scientific_reviewed": True,
        "editorial_reviewed": True,
        "source_rights_reviewed": True,
        "ci_passed": True,
        "candidate_commit": "abcdef",
        "ci_run_ids": [1],
        "artifact_sha256": {"result": candidate["artifacts"][0]["sha256"]},
        "reviewed_source_ids": diff["changed_source_ids"],
        "reviewed_diagnostic_ids": diff["changed_diagnostic_ids"],
        "reviewed_claim_ids": diff["affected_claim_ids"],
    }
    validate_review_attestation(
        attestation,
        stage_id="stage-id",
        candidate_manifest_sha256=sha256_file(manifest_path),
        candidate=candidate,
        release_diff=diff,
    )
    incomplete = dict(attestation, ci_run_ids=[])
    with pytest.raises(ValueError, match="ci_run_ids"):
        validate_review_attestation(
            incomplete,
            stage_id="stage-id",
            candidate_manifest_sha256=sha256_file(manifest_path),
            candidate=candidate,
            release_diff=diff,
        )
    incomplete = dict(attestation, reviewed_claim_ids=[])
    with pytest.raises(ValueError, match="reviewed_claim_ids"):
        validate_review_attestation(
            incomplete,
            stage_id="stage-id",
            candidate_manifest_sha256=sha256_file(manifest_path),
            candidate=candidate,
            release_diff=diff,
        )


def test_stage_promote_baseline_then_stage_new_wave_without_source_redistribution(tmp_path: Path):
    repo = Path(__file__).parents[1]
    registry = _registry(tmp_path / "registry.json")
    releases = tmp_path / "releases"

    baseline_root = tmp_path / "baseline"
    baseline = _candidate(baseline_root)
    baseline_manifest = _manifest(baseline_root / "release.json", baseline)
    baseline_stage = tmp_path / "baseline-stage"
    _run(
        repo,
        "stage",
        "--candidate-manifest",
        str(baseline_manifest),
        "--candidate-root",
        str(baseline_root),
        "--registry",
        str(registry),
        "--releases-root",
        str(releases),
        "--staging-dir",
        str(baseline_stage),
    )
    assert json.loads((baseline_stage / "publication_gate.json").read_text())["status"] == "BLOCKED_REVIEW_REQUIRED"
    attestation_path = tmp_path / "baseline-attestation.json"
    attestation_path.write_text(json.dumps(_attestation(baseline_stage, baseline_manifest, baseline)))
    _run(
        repo,
        "promote",
        "--candidate-manifest",
        str(baseline_manifest),
        "--candidate-root",
        str(baseline_root),
        "--registry",
        str(registry),
        "--releases-root",
        str(releases),
        "--staging-dir",
        str(baseline_stage),
        "--attestation",
        str(attestation_path),
    )
    frozen = json.loads((releases / "release-1/release_manifest.json").read_text())
    assert frozen["source_input_bytes_included"] is False
    assert "local_path" not in frozen["sources"][0]["objects"][0]
    assert not (releases / "release-1/inputs/source-q1.csv").exists()
    assert (releases / "release-1/artifacts/result.json").exists()
    registry_value = json.loads(registry.read_text())
    assert registry_value["current_release_id"] == "release-1"
    assert registry_value["status"] == "CURRENT_RELEASE_PROMOTED"

    next_root = tmp_path / "next"
    next_release = _candidate(
        next_root,
        release_id="release-2",
        supersedes="release-1",
        periods=["2026-Q1", "2026-Q2"],
        extra_object=True,
        artifact_text='{"value": 2}\n',
        claim_text="claim-v2",
    )
    next_manifest = _manifest(next_root / "release.json", next_release)
    next_stage = tmp_path / "next-stage"
    _run(
        repo,
        "stage",
        "--candidate-manifest",
        str(next_manifest),
        "--candidate-root",
        str(next_root),
        "--registry",
        str(registry),
        "--releases-root",
        str(releases),
        "--staging-dir",
        str(next_stage),
    )
    next_gate = json.loads((next_stage / "publication_gate.json").read_text())
    next_diff = json.loads((next_stage / "release_diff.json").read_text())
    assert next_gate["status"] == "BLOCKED_REVIEW_REQUIRED"
    assert next_diff["changed_source_ids"] == ["survey"]
    assert next_diff["affected_claim_ids"] == ["claim-1"]
    assert json.loads(registry.read_text())["current_release_id"] == "release-1"


def test_public_registry_has_no_synthetic_release_promoted():
    root = Path(__file__).parents[1]
    registry = json.loads((root / "data/registry/observatory_release_registry.json").read_text())
    assert registry["current_release_id"] is None
    assert registry["releases"] == []
