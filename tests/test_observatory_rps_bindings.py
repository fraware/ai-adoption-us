from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from genai_at_work.observatory_rps_bindings import (
    BINDINGS_REPOSITORY_PATH,
    ObservatoryRpsBindingError,
    validate_rps_repository_bindings,
)
from genai_at_work.release_engine import load_json_object, sha256_file

ROOT = Path(__file__).parents[1]
BASELINE_CONTRACT = ROOT / "data/registry/observatory_v1_baseline_contract.json"
BINDINGS = ROOT / BINDINGS_REPOSITORY_PATH
CPS_PROVENANCE = (
    ROOT / "data/derived/composition/rps-cps-residuals-2026-09-02/provenance.json"
)
BTOS_CHECKPOINT = ROOT / "data/registry/rps_industry_adoption_q2_2026_v1.json"
RPS_SOURCE_ID = "rps-genai-tracker-fred-release-6"


def _digest_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _write(path: Path, value: object) -> tuple[str, int]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    return sha256_file(path), path.stat().st_size


def _candidate(root: Path) -> dict[str, Any]:
    provenance = load_json_object(CPS_PROVENANCE)
    source_digest = str(provenance["source_content_sha256"])
    checkpoint = load_json_object(BTOS_CHECKPOINT)
    checkpoint_rows = checkpoint["rows"]
    assert isinstance(checkpoint_rows, list)

    records = [
        {
            "period": "2026-Q2",
            "entity_type": "industry",
            "entity_id": f"industry-{index:02d}",
            "metric_id": "adoption_work",
            "series_id": row["series_id"],
            "value": row["value_pct"],
        }
        for index, row in enumerate(checkpoint_rows, start=1)
        if isinstance(row, dict)
    ]
    source_sha, source_size = _write(
        root / "inputs/rps/2026-Q2.json",
        {
            "schema_version": 1,
            "source_id": RPS_SOURCE_ID,
            "period": "2026-Q2",
            "records": records,
        },
    )
    artifact_sha, artifact_size = _write(
        root / "artifacts/test/binding.json",
        {"status": "test"},
    )
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
        "release_id": "rps-binding-test",
        "release_type": "baseline",
        "data_mode": "derived_only",
        "created_at": "2026-09-03T12:00:00Z",
        "supersedes_release_id": None,
        "sources": [
            {
                "source_id": RPS_SOURCE_ID,
                "provider": "Synthetic test provider",
                "dataset": "Synthetic RPS binding candidate",
                "source_vintage_id": f"sha256:{source_digest}",
                "retrieved_at": "2026-09-03T12:00:00Z",
                "revision_status": "new_wave",
                "reference_periods": ["2026-Q2"],
                "instrument_version": "test",
                "definition_id": "test-definition",
                "taxonomy_versions": {"rps": "test-taxonomy"},
                "rights": {
                    "status": "approved",
                    "storage_scope": "private",
                    "publication_scope": "derived_only",
                    "redistribution_scope": "derived_only",
                },
                "coverage": {
                    "status": "pass",
                    "required_units": 20,
                    "observed_units": 20,
                },
                "objects": [
                    {
                        "object_id": "2026-q2",
                        "locator": "https://example.test/rps",
                        "local_path": "inputs/rps/2026-Q2.json",
                        "sha256": source_sha,
                        "size_bytes": source_size,
                    }
                ],
            }
        ],
        "artifacts": [
            {
                "artifact_id": "binding-test-artifact",
                "path": "artifacts/test/binding.json",
                "sha256": artifact_sha,
                "size_bytes": artifact_size,
                "evidence_class": 2,
                "source_ids": [RPS_SOURCE_ID],
            }
        ],
        "diagnostics": diagnostics,
        "claims": [
            {
                "claim_id": "binding-test-claim",
                "surfaces": ["/methodology"],
                "artifact_ids": ["binding-test-artifact"],
                "value_digest": _digest_text("binding-test-claim"),
                "value_summary": "Synthetic binding test claim.",
                "truth_state": "supported",
                "evidence_class": 2,
                "interpretation_boundary": "Test only.",
            }
        ],
        "build": {
            "builder_id": "rps-binding-test-builder",
            "builder_commit": "0" * 40,
            "deterministic": True,
            "input_sha256": {f"{RPS_SOURCE_ID}:2026-q2": source_sha},
            "output_sha256": {"binding-test-artifact": artifact_sha},
        },
    }
    (root / "release.json").write_text(
        json.dumps(candidate, indent=2, sort_keys=True) + "\n"
    )
    return candidate


def _validate(
    candidate: dict[str, Any],
    root: Path,
    *,
    bindings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return validate_rps_repository_bindings(
        candidate,
        rps_candidate_root=root,
        baseline_contract=load_json_object(BASELINE_CONTRACT),
        bindings=bindings or load_json_object(BINDINGS),
        repo_root=ROOT,
    )


def test_current_repository_rps_bindings_pass_and_cover_exact_inventory(
    tmp_path: Path,
) -> None:
    candidate = _candidate(tmp_path)
    summary = _validate(candidate, tmp_path)

    assert summary["status"] == "pass"
    assert summary["source_id"] == RPS_SOURCE_ID
    assert len(summary["binding_ids"]) == 3
    assert len(summary["covered_artifact_ids"]) == 12


def test_source_vintage_mismatch_is_rejected(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    candidate["sources"][0]["source_vintage_id"] = "sha256:" + "1" * 64
    (tmp_path / "release.json").write_text(
        json.dumps(candidate, indent=2, sort_keys=True) + "\n"
    )

    with pytest.raises(ObservatoryRpsBindingError, match="source vintage mismatch"):
        _validate(candidate, tmp_path)


def test_one_changed_btos_input_value_is_rejected(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    source_path = tmp_path / "inputs/rps/2026-Q2.json"
    payload = load_json_object(source_path)
    records = payload["records"]
    assert isinstance(records, list) and isinstance(records[0], dict)
    records[0]["value"] = float(records[0]["value"]) + 0.01
    source_sha, source_size = _write(source_path, payload)
    source_object = candidate["sources"][0]["objects"][0]
    source_object["sha256"] = source_sha
    source_object["size_bytes"] = source_size
    candidate["build"]["input_sha256"][f"{RPS_SOURCE_ID}:2026-q2"] = source_sha
    (tmp_path / "release.json").write_text(
        json.dumps(candidate, indent=2, sort_keys=True) + "\n"
    )

    with pytest.raises(ObservatoryRpsBindingError, match="changed for 1 series"):
        _validate(candidate, tmp_path)


def test_binding_inventory_cannot_omit_rps_dependent_artifact(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    bindings = deepcopy(load_json_object(BINDINGS))
    source_bindings = bindings["source_vintage_bindings"]
    assert isinstance(source_bindings, list) and isinstance(source_bindings[0], dict)
    artifact_ids = source_bindings[0]["artifact_ids"]
    assert isinstance(artifact_ids, list)
    artifact_ids.pop()

    with pytest.raises(
        ObservatoryRpsBindingError,
        match="coverage must exactly match",
    ):
        _validate(candidate, tmp_path, bindings=bindings)


def test_binding_registry_rejects_unsafe_repository_path(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    bindings = deepcopy(load_json_object(BINDINGS))
    source_bindings = bindings["source_vintage_bindings"]
    assert isinstance(source_bindings, list) and isinstance(source_bindings[0], dict)
    source_bindings[0]["repository_path"] = "../outside.json"

    with pytest.raises(ObservatoryRpsBindingError, match="Unsafe repository binding path"):
        _validate(candidate, tmp_path, bindings=bindings)


def test_binding_registry_must_match_repository_pinned_bytes(tmp_path: Path) -> None:
    candidate = _candidate(tmp_path)
    bindings = deepcopy(load_json_object(BINDINGS))
    bindings["binding_id"] = "edited-out-of-band"

    with pytest.raises(
        ObservatoryRpsBindingError,
        match="exact repository-pinned registry",
    ):
        _validate(candidate, tmp_path, bindings=bindings)
