from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from genai_at_work.rps_refresh_policy import RpsRefreshPolicyError, validate_rps_refresh_policy

ROOT = Path(__file__).parents[1]
POLICY = ROOT / "data" / "registry" / "rps_refresh_policy.json"


def _policy() -> dict[str, Any]:
    return json.loads(POLICY.read_text())


def test_pending_activation_evidence_rejects_unsupported_claims() -> None:
    value = _policy()
    value["activation_evidence"][
        "operator_controlled_private_vintage_backend_configured"
    ]["durable"] = True
    with pytest.raises(
        RpsRefreshPolicyError,
        match="fields must exactly match the activation-evidence contract",
    ):
        validate_rps_refresh_policy(value)


def test_passed_live_evidence_rejects_unsupported_claims() -> None:
    value = _policy()
    value["activation_evidence"]["successful_live_validation"][
        "backend_persisted"
    ] = True
    with pytest.raises(
        RpsRefreshPolicyError,
        match="fields must exactly match the activation-evidence contract",
    ):
        validate_rps_refresh_policy(value)


def test_passed_backend_and_rehearsal_evidence_reject_extra_fields() -> None:
    value = _policy()
    value["activation_evidence"][
        "operator_controlled_private_vintage_backend_configured"
    ] = {
        "status": "passed",
        "backend_id": "private-vintage-production-v1",
        "configuration_evidence_ref": "ops/private-vintage-backend/configuration-v1",
        "configuration_evidence_sha256": "c" * 64,
        "verified_on": "2026-09-03",
    }
    value["activation_evidence"][
        "private_backend_write_read_verify_rehearsal_passed"
    ] = {
        "status": "passed",
        "rehearsal_id": "private-vintage-write-read-verify-v1",
        "write_read_verify_evidence_ref": "ops/private-vintage-backend/rehearsal-v1",
        "write_read_verify_evidence_sha256": "d" * 64,
        "backend_id": "private-vintage-production-v1",
        "configuration_evidence_ref": "ops/private-vintage-backend/configuration-v1",
        "configuration_evidence_sha256": "c" * 64,
        "verified_on": "2026-09-03",
    }
    validate_rps_refresh_policy(value)

    backend_extra = copy.deepcopy(value)
    backend_extra["activation_evidence"][
        "operator_controlled_private_vintage_backend_configured"
    ]["self_certified"] = True
    with pytest.raises(
        RpsRefreshPolicyError,
        match="fields must exactly match the activation-evidence contract",
    ):
        validate_rps_refresh_policy(backend_extra)

    rehearsal_extra = copy.deepcopy(value)
    rehearsal_extra["activation_evidence"][
        "private_backend_write_read_verify_rehearsal_passed"
    ]["publicly_verified"] = True
    with pytest.raises(
        RpsRefreshPolicyError,
        match="fields must exactly match the activation-evidence contract",
    ):
        validate_rps_refresh_policy(rehearsal_extra)
