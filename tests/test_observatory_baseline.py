from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from genai_at_work.observatory_baseline import (
    REQUIRED_COMPONENTS,
    REQUIRED_GLOBAL_CLAIM_IDS,
    REQUIRED_GLOBAL_GATE_IDS,
    REQUIRED_RPS_ARTIFACT_IDS,
    ObservatoryBaselineError,
    compose_v1_global_baseline,
    validate_v1_baseline_contract,
)
from genai_at_work.release_engine import (
    load_json_object,
    sha256_file,
    validate_release_manifest,
)
from genai_at_work.rps_public_view import NATIONAL_METRICS, PUBLIC_SUBGROUP_METRICS

ROOT = Path(__file__).parents[1]
CONTRACT_PATH = ROOT / "data" / "registry" / "observatory_v1_baseline_contract.json"
RPS_SOURCE_ID = "rps-genai-tracker-fred-release-6"
RPS_BUILDER_ID = "rps-published-aggregate-observatory-release-v4"
RPS_BUILDER_COMMIT = "0123456789abcdef0123456789abcdef01234567"
PUBLIC_VIEW_ID = "rps-public-observation-view"
PUBLIC_VIEW_PATH = "artifacts/public/rps_public_observation_view.json"


def _digest_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _write(path: Path, content: str) -> tuple[str, int]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return sha256_file(path), path.stat().st_size


def _head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _observation(
    *,
    period: str,
    entity_type: str,
    entity_id: str,
    metric_id: str,
    index: int,
) -> dict[str, Any]:
    return {
        "date": "2025-05-01" if period == "2025-Q2" else "2026-05-01",
        "period": period,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "metric_id": metric_id,
        "value": float(10 + index % 80),
        "unit": "Percent",
        "series_id": f"series-{entity_type}-{entity_id}-{metric_id}",
        "source_url": "https://fred.stlouisfed.org/",
    }


def _public_view() -> dict[str, Any]:
    national_history = [
        _observation(
            period=period,
            entity_type="national",
            entity_id="us",
            metric_id=metric_id,
            index=period_index * 10 + metric_index,
        )
        for period_index, period in enumerate(("2025-Q2", "2026-Q2"))
        for metric_index, metric_id in enumerate(NATIONAL_METRICS)
    ]
    industry_latest = [
        _observation(
            period="2026-Q2",
            entity_type="industry",
            entity_id=f"industry-{entity_index:02d}",
            metric_id=metric_id,
            index=entity_index * 3 + metric_index,
        )
        for entity_index in range(1, 21)
        for metric_index, metric_id in enumerate(PUBLIC_SUBGROUP_METRICS)
    ]
    occupation_latest = [
        _observation(
            period="2026-Q2",
            entity_type="occupation",
            entity_id=f"occupation-{entity_index:02d}",
            metric_id=metric_id,
            index=entity_index * 3 + metric_index,
        )
        for entity_index in range(1, 23)
        for metric_index, metric_id in enumerate(PUBLIC_SUBGROUP_METRICS)
    ]
    return {
        "schema_version": 1,
        "view_contract_id": "rps-public-observation-delivery-v1",
        "source_id": RPS_SOURCE_ID,
        "source_vintage_id": "sha256:" + _digest_text("rps-vintage"),
        "publication_scope": "selected_attributed_aggregate_views",
        "source_input_bytes_included": False,
        "generic_query_api_included": False,
        "historical_subgroup_panel_included": False,
        "latest_subgroup_period": "2026-Q2",
        "national_history": national_history,
        "industry_latest": industry_latest,
        "occupation_latest": occupation_latest,
        "attribution": {
            "dataset": "Real-Time Population Survey: Generative Artificial Intelligence Adoption Tracker",
            "authors": "Alexander Bick, Adam Blandin, and David Deming",
            "transport": "FRED/ALFRED",
            "citation_required": True,
        },
        "interpretation_boundary": "Synthetic bounded-view test fixture.",
    }


def _rps_candidate(root: Path) -> dict[str, Any]:
    source_sha, source_size = _write(
        root / "inputs/rps/2025-Q2.json",
        '{"period":"2025-Q2","records":[]}\n',
    )
    source_2026_sha, source_2026_size = _write(
        root / "inputs/rps/2026-Q2.json",
        '{"period":"2026-Q2","records":[]}\n',
    )

    artifact_specs = {
        "rps-longitudinal-diagnostics": (
            "artifacts/longitudinal/longitudinal_diagnostics.json",
            '{"status":"synthetic-test"}\n',
            2,
        ),
        "rps-quarter-diagnostics": (
            "artifacts/longitudinal/quarter_diagnostics.csv",
            "period,value\n2025-Q2,1\n2026-Q2,2\n",
            2,
        ),
        "rps-rank-stability": (
            "artifacts/longitudinal/rank_stability.csv",
            "period,value\n2025-Q2,1\n2026-Q2,1\n",
            2,
        ),
        "rps-longitudinal-validation": (
            "artifacts/longitudinal/validation_checks.json",
            '{"status":"pass"}\n',
            2,
        ),
        PUBLIC_VIEW_ID: (
            PUBLIC_VIEW_PATH,
            json.dumps(_public_view(), indent=2, sort_keys=True) + "\n",
            1,
        ),
    }
    artifacts: list[dict[str, Any]] = []
    output_hashes: dict[str, str] = {}
    for artifact_id, (relative, content, evidence_class) in artifact_specs.items():
        sha256, size = _write(root / relative, content)
        artifacts.append(
            {
                "artifact_id": artifact_id,
                "path": relative,
                "sha256": sha256,
                "size_bytes": size,
                "evidence_class": evidence_class,
                "source_ids": [RPS_SOURCE_ID],
            }
        )
        output_hashes[artifact_id] = sha256

    diagnostics = [
        {
            "diagnostic_id": diagnostic_class,
            "diagnostic_class": diagnostic_class,
            "status": "pass",
            "value_digest": _digest_text(f"{diagnostic_class}:pass"),
        }
        for diagnostic_class in (
            "stability",
            "influence",
            "regression_contract",
            "suppression_coverage",
        )
    ]
    candidate: dict[str, Any] = {
        "schema_version": 1,
        "release_id": "rps-component-test",
        "release_type": "baseline",
        "data_mode": "derived_only",
        "created_at": "2026-09-02T12:00:00Z",
        "supersedes_release_id": None,
        "sources": [
            {
                "source_id": RPS_SOURCE_ID,
                "provider": "Synthetic test provider",
                "dataset": "Synthetic complete-history RPS component",
                "source_vintage_id": "sha256:" + _digest_text("rps-vintage"),
                "retrieved_at": "2026-09-02T12:00:00Z",
                "revision_status": "new_wave",
                "reference_periods": ["2025-Q2", "2026-Q2"],
                "analysis_reference_periods": ["2025-Q2", "2026-Q2"],
                "analysis_metric_reference_periods": {
                    "adoption_work": ["2025-Q2", "2026-Q2"],
                    "assisted_hours_share": ["2025-Q2", "2026-Q2"],
                    "reported_time_savings_share": ["2025-Q2", "2026-Q2"],
                },
                "instrument_version": "not-versioned-in-fred-distribution",
                "definition_id": "sha256:" + _digest_text("definition"),
                "taxonomy_versions": {
                    "rps_source_series_manifest": "sha256:"
                    + _digest_text("taxonomy")
                },
                "rights": {
                    "status": "approved",
                    "storage_scope": "private",
                    "publication_scope": "derived_only",
                    "redistribution_scope": "derived_only",
                },
                "coverage": {
                    "status": "pass",
                    "required_units": 262,
                    "observed_units": 262,
                    "full_source_observed_units": 500,
                    "subgroup_series_count": 126,
                    "national_series_count": 5,
                },
                "objects": [
                    {
                        "object_id": "2025-q2",
                        "locator": "https://example.test/rps",
                        "local_path": "inputs/rps/2025-Q2.json",
                        "sha256": source_sha,
                        "size_bytes": source_size,
                    },
                    {
                        "object_id": "2026-q2",
                        "locator": "https://example.test/rps",
                        "local_path": "inputs/rps/2026-Q2.json",
                        "sha256": source_2026_sha,
                        "size_bytes": source_2026_size,
                    },
                ],
            }
        ],
        "artifacts": artifacts,
        "diagnostics": diagnostics,
        "claims": [
            {
                "claim_id": "rps-synthetic-test-claim",
                "surfaces": ["/", "/methodology"],
                "artifact_ids": ["rps-longitudinal-diagnostics"],
                "value_digest": _digest_text("synthetic-rps-claim"),
                "value_summary": "Synthetic RPS component test claim.",
                "truth_state": "supported",
                "evidence_class": 2,
                "interpretation_boundary": "Test-only descriptive claim.",
            }
        ],
        "build": {
            "builder_id": RPS_BUILDER_ID,
            "builder_commit": RPS_BUILDER_COMMIT,
            "deterministic": True,
            "input_sha256": {
                f"{RPS_SOURCE_ID}:2025-q2": source_sha,
                f"{RPS_SOURCE_ID}:2026-q2": source_2026_sha,
            },
            "output_sha256": output_hashes,
        },
        "candidate_scope": "Synthetic test representation of the RPS v4 component.",
        "source_input_bytes_publication": False,
    }
    (root / "release.json").write_text(
        json.dumps(candidate, indent=2, sort_keys=True) + "\n"
    )
    validate_release_manifest(candidate, root)
    return candidate


def _rewrite_release(root: Path, candidate: dict[str, Any]) -> None:
    (root / "release.json").write_text(
        json.dumps(candidate, indent=2, sort_keys=True) + "\n"
    )


def _rewrite_public_view(
    root: Path,
    candidate: dict[str, Any],
    payload: dict[str, Any],
) -> None:
    path = root / PUBLIC_VIEW_PATH
    sha256, size = _write(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    artifact = next(
        row for row in candidate["artifacts"] if row["artifact_id"] == PUBLIC_VIEW_ID
    )
    artifact["sha256"] = sha256
    artifact["size_bytes"] = size
    candidate["build"]["output_sha256"][PUBLIC_VIEW_ID] = sha256
    _rewrite_release(root, candidate)


def test_v1_contract_is_complete_and_current_repository_evidence_passes() -> None:
    contract = load_json_object(CONTRACT_PATH)
    validate_v1_baseline_contract(contract, ROOT)
    assert set(contract["required_components"]) == REQUIRED_COMPONENTS
    assert set(contract["rps_component"]["required_artifact_ids"]) == REQUIRED_RPS_ARTIFACT_IDS
    assert {
        row["gate_id"] for row in contract["validation_gates"]
    } == REQUIRED_GLOBAL_GATE_IDS
    assert {
        row["claim_id"] for row in contract["global_claims"]
    } == REQUIRED_GLOBAL_CLAIM_IDS


def test_contract_cannot_silently_drop_a_scientific_gate() -> None:
    contract = deepcopy(load_json_object(CONTRACT_PATH))
    contract["validation_gates"] = contract["validation_gates"][:-1]
    with pytest.raises(
        ObservatoryBaselineError,
        match="validation gate inventory",
    ):
        validate_v1_baseline_contract(contract, ROOT)


def test_contract_cannot_silently_drop_public_observation_view() -> None:
    contract = deepcopy(load_json_object(CONTRACT_PATH))
    contract["rps_component"]["required_artifact_ids"].remove(PUBLIC_VIEW_ID)
    with pytest.raises(
        ObservatoryBaselineError,
        match="complete v4 observatory artifact set",
    ):
        validate_v1_baseline_contract(contract, ROOT)


def test_contract_fails_when_q4_2025_missingness_rule_is_changed() -> None:
    contract = deepcopy(load_json_object(CONTRACT_PATH))
    gate = next(
        row
        for row in contract["validation_gates"]
        if row["gate_id"] == "cps-q4-2025-explicit-unavailability"
    )
    gate["expected"]["unavailable.2025-Q4.reason"] = "Substitute November and December."
    with pytest.raises(
        ObservatoryBaselineError,
        match="cps-q4-2025-explicit-unavailability failed",
    ):
        validate_v1_baseline_contract(contract, ROOT)


def test_contract_must_match_exact_repository_pinned_bytes() -> None:
    contract = deepcopy(load_json_object(CONTRACT_PATH))
    contract["contract_id"] = "observatory-v1-global-baseline-edited-out-of-band"
    with pytest.raises(
        ObservatoryBaselineError,
        match="exact repository-pinned baseline contract",
    ):
        validate_v1_baseline_contract(contract, ROOT)


def test_global_composer_builds_one_valid_complete_baseline(tmp_path: Path) -> None:
    rps_root = tmp_path / "rps"
    _rps_candidate(rps_root)
    output = tmp_path / "global"

    candidate = compose_v1_global_baseline(
        rps_candidate_root=rps_root,
        output_dir=output,
        contract=load_json_object(CONTRACT_PATH),
        repo_root=ROOT,
        release_id="observatory-v1-baseline-test",
        builder_commit=_head(),
    )

    validate_release_manifest(candidate, output)
    assert candidate["release_type"] == "baseline"
    assert candidate["data_mode"] == "derived_only"
    assert candidate["source_input_bytes_publication"] is False
    assert {row["source_id"] for row in candidate["sources"]} == {
        RPS_SOURCE_ID,
        "cps-basic-monthly-composition-v1",
        "oews-may-2025-composition-v1",
        "btos-core-ai-202611-q7-a1-v1",
    }
    artifact_ids = {row["artifact_id"] for row in candidate["artifacts"]}
    assert REQUIRED_RPS_ARTIFACT_IDS <= artifact_ids
    assert "rps-cps-primary-residuals" in artifact_ids
    assert "oews-rps-validation" in artifact_ids
    assert "btos-rps-industry-triangulation" in artifact_ids
    assert REQUIRED_GLOBAL_CLAIM_IDS <= {
        row["claim_id"] for row in candidate["claims"]
    }
    assert candidate["component_builds"]["rps"]["builder_id"] == RPS_BUILDER_ID
    public_view = load_json_object(output / PUBLIC_VIEW_PATH)
    assert public_view["historical_subgroup_panel_included"] is False
    assert len(public_view["national_history"]) == 10
    assert len(public_view["industry_latest"]) == 60
    assert len(public_view["occupation_latest"]) == 66
    assert (output / "release.json").is_file()
    assert not output.with_name(f".{output.name}.tmp").exists()


def test_global_composer_rejects_name_compatible_fake_rps_builder(
    tmp_path: Path,
) -> None:
    rps_root = tmp_path / "rps"
    candidate = _rps_candidate(rps_root)
    candidate["build"]["builder_id"] = "lookalike-builder"
    _rewrite_release(rps_root, candidate)
    output = tmp_path / "global"

    with pytest.raises(ObservatoryBaselineError, match="builder_id"):
        compose_v1_global_baseline(
            rps_candidate_root=rps_root,
            output_dir=output,
            contract=load_json_object(CONTRACT_PATH),
            repo_root=ROOT,
            release_id="observatory-v1-fake-rps-test",
            builder_commit=_head(),
        )
    assert not output.exists()
    assert not output.with_name(f".{output.name}.tmp").exists()


def test_global_composer_rejects_incomplete_rps_source_topology(
    tmp_path: Path,
) -> None:
    rps_root = tmp_path / "rps"
    candidate = _rps_candidate(rps_root)
    candidate["sources"][0]["coverage"]["subgroup_series_count"] = 125
    _rewrite_release(rps_root, candidate)
    output = tmp_path / "global"

    with pytest.raises(ObservatoryBaselineError, match="126 subgroup"):
        compose_v1_global_baseline(
            rps_candidate_root=rps_root,
            output_dir=output,
            contract=load_json_object(CONTRACT_PATH),
            repo_root=ROOT,
            release_id="observatory-v1-incomplete-rps-test",
            builder_commit=_head(),
        )
    assert not output.exists()


def test_global_composer_rejects_missing_reviewed_rps_artifact(
    tmp_path: Path,
) -> None:
    rps_root = tmp_path / "rps"
    candidate = _rps_candidate(rps_root)
    candidate["artifacts"] = [
        row for row in candidate["artifacts"] if row["artifact_id"] != PUBLIC_VIEW_ID
    ]
    del candidate["build"]["output_sha256"][PUBLIC_VIEW_ID]
    _rewrite_release(rps_root, candidate)
    output = tmp_path / "global"

    with pytest.raises(
        ObservatoryBaselineError,
        match="artifact inventory",
    ):
        compose_v1_global_baseline(
            rps_candidate_root=rps_root,
            output_dir=output,
            contract=load_json_object(CONTRACT_PATH),
            repo_root=ROOT,
            release_id="observatory-v1-missing-rps-artifact-test",
            builder_commit=_head(),
        )
    assert not output.exists()


def test_global_composer_rejects_widened_public_observation_scope(
    tmp_path: Path,
) -> None:
    rps_root = tmp_path / "rps"
    candidate = _rps_candidate(rps_root)
    payload = load_json_object(rps_root / PUBLIC_VIEW_PATH)
    payload["historical_subgroup_panel_included"] = True
    _rewrite_public_view(rps_root, candidate, payload)
    output = tmp_path / "global"

    with pytest.raises(
        ObservatoryBaselineError,
        match="historical_subgroup_panel_included=false",
    ):
        compose_v1_global_baseline(
            rps_candidate_root=rps_root,
            output_dir=output,
            contract=load_json_object(CONTRACT_PATH),
            repo_root=ROOT,
            release_id="observatory-v1-expanded-rps-public-view-test",
            builder_commit=_head(),
        )
    assert not output.exists()


def test_global_composer_rejects_incomplete_public_cross_section(
    tmp_path: Path,
) -> None:
    rps_root = tmp_path / "rps"
    candidate = _rps_candidate(rps_root)
    payload = load_json_object(rps_root / PUBLIC_VIEW_PATH)
    payload["industry_latest"] = payload["industry_latest"][:-1]
    _rewrite_public_view(rps_root, candidate, payload)
    output = tmp_path / "global"

    with pytest.raises(
        ObservatoryBaselineError,
        match="industry_latest must contain exactly 60 rows",
    ):
        compose_v1_global_baseline(
            rps_candidate_root=rps_root,
            output_dir=output,
            contract=load_json_object(CONTRACT_PATH),
            repo_root=ROOT,
            release_id="observatory-v1-incomplete-rps-public-view-test",
            builder_commit=_head(),
        )
    assert not output.exists()


def test_global_composer_detects_tampered_private_rps_input_and_cleans_up(
    tmp_path: Path,
) -> None:
    rps_root = tmp_path / "rps"
    _rps_candidate(rps_root)
    # Same byte length as the registered payload so this specifically exercises
    # cryptographic integrity, not the earlier size check.
    (rps_root / "inputs/rps/2026-Q2.json").write_text(
        '{"period":"2026-Q2","changed":[]}\n'
    )
    output = tmp_path / "global"

    with pytest.raises(ValueError, match="checksum mismatch"):
        compose_v1_global_baseline(
            rps_candidate_root=rps_root,
            output_dir=output,
            contract=load_json_object(CONTRACT_PATH),
            repo_root=ROOT,
            release_id="observatory-v1-tamper-test",
            builder_commit=_head(),
        )
    assert not output.exists()
    assert not output.with_name(f".{output.name}.tmp").exists()


def test_global_composer_refuses_false_repository_commit_binding(
    tmp_path: Path,
) -> None:
    rps_root = tmp_path / "rps"
    _rps_candidate(rps_root)

    with pytest.raises(
        ObservatoryBaselineError,
        match="must equal the clean repository HEAD",
    ):
        compose_v1_global_baseline(
            rps_candidate_root=rps_root,
            output_dir=tmp_path / "global",
            contract=load_json_object(CONTRACT_PATH),
            repo_root=ROOT,
            release_id="observatory-v1-wrong-commit-test",
            builder_commit="0" * 40,
        )


def test_operator_cli_blocks_repository_local_nonprivate_output() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/prepare_observatory_v1_candidate.py"),
            "--rps-candidate-root",
            "/tmp/nonexistent-rps",
            "--output-dir",
            str(ROOT / "data" / "forbidden-global-candidate"),
            "--release-id",
            "observatory-v1-cli-boundary-test",
        ],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "may only be written under data/audit/private/" in result.stderr
