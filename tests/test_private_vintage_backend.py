from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from genai_at_work.private_vintage import PrivateVintageError, sha256_file
from genai_at_work.private_vintage_backend import (
    PrivateVintageBackendError,
    validate_backend_challenge,
    verify_backend_challenge,
    write_backend_challenge,
)
from genai_at_work.rps_release import snapshot_content_sha256

WRITE_COMMIT = "0123456789abcdef0123456789abcdef01234567"
VERIFY_COMMIT = "fedcba9876543210fedcba9876543210fedcba98"
BACKEND_ID = "rps-private-vault-v1"
CONFIG_REF = "ops/private-vintage-backend/configuration-v1"


def _snapshot(
    *,
    retrieved_at: str = "2026-09-02T12:00:00Z",
    value: float = 50.0,
) -> dict[str, Any]:
    snapshot: dict[str, Any] = {
        "schema_version": 1,
        "snapshot_type": "rps_published_aggregate_refresh",
        "source_id": "rps-genai-tracker-fred-release-6",
        "provider": "Synthetic FRED/ALFRED RPS distribution",
        "provider_release_id": 6,
        "retrieved_at": retrieved_at,
        "rights": {
            "status": "approved",
            "scope": "published aggregate project use",
            "decision_ref": "docs/source-rights/RPS_SOURCE_DECISION.md",
            "public_bulk_redistribution_approved": False,
        },
        "inventory": {
            "provider_series_count": 2,
            "observatory_series_count": 1,
            "excluded_series_count": 1,
            "provider_inventory_status": "pass",
        },
        "observation_count": 1,
        "series": [
            {
                "series_id": "RPSGENAIUSAGESHAREWORK",
                "title": "Synthetic RPS work adoption",
                "metric_id": "adoption_work",
                "entity_id": "us",
                "entity_type": "national",
                "entity_name": "Employed Adults",
                "frequency": "Quarterly",
                "unit": "Percent",
                "seasonal_adjustment": "Not Seasonally Adjusted",
                "observation_start": "2026-05-01",
                "observation_end": "2026-05-01",
                "last_updated": "2026-08-04 10:00:00-05",
                "notes_hash": "a" * 64,
                "source_url": "https://fred.stlouisfed.org/series/RPSGENAIUSAGESHAREWORK",
                "copyright_status": "Copyrighted: Citation Required",
                "citation_text": "Synthetic test citation that must remain private.",
                "observations": [
                    {
                        "date": "2026-05-01",
                        "period": "2026-Q2",
                        "value": value,
                        "unit": "Percent",
                        "realtime_start": retrieved_at[:10],
                        "realtime_end": retrieved_at[:10],
                        "source_last_updated": "2026-08-04 10:00:00-05",
                    }
                ],
            }
        ],
        "excluded_series": [
            {
                "series_id": "RPSGENAIUSAGESHAREALL",
                "title": "Synthetic excluded national construct",
                "construct": "Adoption Rate Overall",
                "reason": "Outside the work-focused observatory scope.",
                "observations_retrieved": False,
            }
        ],
    }
    snapshot["content_sha256"] = snapshot_content_sha256(snapshot)
    return snapshot


def _write(path: Path, value: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    return path


def _challenge(tmp_path: Path) -> tuple[Path, Path, dict[str, Any]]:
    snapshot = _write(tmp_path / "source.json", _snapshot())
    backend = tmp_path / "backend"
    challenge = write_backend_challenge(
        snapshot,
        backend,
        backend_id=BACKEND_ID,
        configuration_evidence_ref=CONFIG_REF,
        builder_commit=WRITE_COMMIT,
    )
    return snapshot, backend, challenge


def test_two_phase_write_read_verify_is_exact_and_rights_safe(tmp_path: Path) -> None:
    snapshot, backend, challenge = _challenge(tmp_path)
    validate_backend_challenge(challenge)

    assert challenge == {
        "schema_version": 1,
        "challenge_type": "rps_private_backend_write_challenge",
        "backend_id": BACKEND_ID,
        "configuration_evidence_ref": CONFIG_REF,
        "backend_namespace": (
            "rps-genai-tracker-fred-release-6/" + sha256_file(snapshot)
        ),
        "source_id": "rps-genai-tracker-fred-release-6",
        "archive_event_id": sha256_file(snapshot),
        "source_content_sha256": _snapshot()["content_sha256"],
        "source_snapshot_sha256": sha256_file(snapshot),
        "previous_snapshot_sha256": None,
        "package_digest": challenge["package_digest"],
        "builder_commit": WRITE_COMMIT,
        "storage_scope": "private",
        "public_archive": False,
        "activation_gates_updated": False,
        "durability_established_by_software_alone": False,
    }

    evidence = verify_backend_challenge(
        challenge,
        backend,
        verification_builder_commit=VERIFY_COMMIT,
    )
    assert evidence["write_read_verify_passed"] is True
    assert evidence["recovery_copy_verified"] is True
    assert evidence["write_builder_commit"] == WRITE_COMMIT
    assert evidence["verification_builder_commit"] == VERIFY_COMMIT
    assert evidence["source_snapshot_sha256"] == sha256_file(snapshot)
    assert evidence["package_digest"] == challenge["package_digest"]
    assert evidence["source_bytes_in_evidence"] is False
    assert evidence["activation_gates_updated"] is False
    assert evidence["durability_established_by_software_alone"] is False
    assert evidence["requires_independent_backend_configuration_review"] is True

    serialized = json.dumps({"challenge": challenge, "evidence": evidence})
    assert "Synthetic test citation that must remain private." not in serialized
    assert '"value": 50.0' not in serialized


def test_previous_snapshot_binding_survives_write_and_recovery(tmp_path: Path) -> None:
    previous = _write(
        tmp_path / "previous.json",
        _snapshot(retrieved_at="2026-08-01T12:00:00Z", value=49.0),
    )
    current = _write(
        tmp_path / "current.json",
        _snapshot(retrieved_at="2026-09-02T12:00:00Z", value=50.0),
    )
    backend = tmp_path / "backend"
    challenge = write_backend_challenge(
        current,
        backend,
        backend_id=BACKEND_ID,
        configuration_evidence_ref=CONFIG_REF,
        builder_commit=WRITE_COMMIT,
        previous_snapshot_path=previous,
    )
    assert challenge["previous_snapshot_sha256"] == sha256_file(previous)

    evidence = verify_backend_challenge(
        challenge,
        backend,
        verification_builder_commit=VERIFY_COMMIT,
    )
    assert evidence["previous_snapshot_sha256"] == sha256_file(previous)
    assert evidence["write_read_verify_passed"] is True


def test_backend_source_byte_tampering_fails_readback(tmp_path: Path) -> None:
    _, backend, challenge = _challenge(tmp_path)
    source = (
        backend
        / str(challenge["source_id"])
        / str(challenge["archive_event_id"])
        / "rps_source_snapshot.json"
    )
    payload = source.read_bytes()
    source.write_bytes(payload[:-1] + (b" " if payload[-1:] != b" " else b"\n"))

    with pytest.raises(
        PrivateVintageError,
        match=r"byte identity mismatch|content hash mismatch",
    ):
        verify_backend_challenge(
            challenge,
            backend,
            verification_builder_commit=VERIFY_COMMIT,
        )


def test_missing_backend_package_fails_closed(tmp_path: Path) -> None:
    _, backend, challenge = _challenge(tmp_path)
    shutil.rmtree(
        backend / str(challenge["source_id"]) / str(challenge["archive_event_id"])
    )
    with pytest.raises(PrivateVintageError, match="not a regular directory"):
        verify_backend_challenge(
            challenge,
            backend,
            verification_builder_commit=VERIFY_COMMIT,
        )


def test_challenge_tampering_fails_closed(tmp_path: Path) -> None:
    _, backend, challenge = _challenge(tmp_path)

    bad_digest = copy.deepcopy(challenge)
    bad_digest["package_digest"] = "0" * 64
    with pytest.raises(
        PrivateVintageBackendError,
        match="package digest does not match",
    ):
        verify_backend_challenge(
            bad_digest,
            backend,
            verification_builder_commit=VERIFY_COMMIT,
        )

    bad_scientific_identity = copy.deepcopy(challenge)
    bad_scientific_identity["source_content_sha256"] = "1" * 64
    with pytest.raises(
        PrivateVintageBackendError,
        match="scientific identity does not match",
    ):
        verify_backend_challenge(
            bad_scientific_identity,
            backend,
            verification_builder_commit=VERIFY_COMMIT,
        )

    bad_writer = copy.deepcopy(challenge)
    bad_writer["builder_commit"] = "a" * 40
    with pytest.raises(
        PrivateVintageBackendError,
        match="archived builder commit does not match",
    ):
        verify_backend_challenge(
            bad_writer,
            backend,
            verification_builder_commit=VERIFY_COMMIT,
        )


def test_challenge_schema_and_commit_identity_fail_closed(tmp_path: Path) -> None:
    snapshot = _write(tmp_path / "source.json", _snapshot())
    with pytest.raises(
        PrivateVintageBackendError,
        match="builder_commit must be a 40- or 64-character Git commit digest",
    ):
        write_backend_challenge(
            snapshot,
            tmp_path / "backend-invalid",
            backend_id=BACKEND_ID,
            configuration_evidence_ref=CONFIG_REF,
            builder_commit="not-a-commit",
        )

    _, backend, challenge = _challenge(tmp_path / "valid")
    unknown_field = copy.deepcopy(challenge)
    unknown_field["durable"] = True
    with pytest.raises(
        PrivateVintageBackendError,
        match="fields must exactly match",
    ):
        validate_backend_challenge(unknown_field)

    with pytest.raises(
        PrivateVintageBackendError,
        match="verification_builder_commit must be a 40- or 64-character Git commit digest",
    ):
        verify_backend_challenge(
            challenge,
            backend,
            verification_builder_commit="not-a-commit",
        )


def test_challenge_cannot_claim_durability_or_activation(tmp_path: Path) -> None:
    _, _, challenge = _challenge(tmp_path)

    false_durability = copy.deepcopy(challenge)
    false_durability["durability_established_by_software_alone"] = True
    with pytest.raises(
        PrivateVintageBackendError,
        match="must not claim that software alone establishes durability",
    ):
        validate_backend_challenge(false_durability)

    false_activation = copy.deepcopy(challenge)
    false_activation["activation_gates_updated"] = True
    with pytest.raises(
        PrivateVintageBackendError,
        match="must not claim activation-gate mutation",
    ):
        validate_backend_challenge(false_activation)
