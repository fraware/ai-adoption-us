from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from genai_at_work.private_backend_config import (
    PrivateBackendConfigurationError,
    load_private_backend_configuration,
    validate_private_backend_configuration,
)
from genai_at_work.private_vintage import sha256_file


def _configuration() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "evidence_type": "rps_private_backend_configuration",
        "backend_id": "rps-private-vault-v1",
        "configuration_ref": "ops/private-vintage-backend/configuration-v1",
        "environment_scope": "production_rps_refresh",
        "storage_interface": "mounted_filesystem",
        "operator_controlled": True,
        "private_access_required": True,
        "ephemeral": False,
        "persists_beyond_execution": True,
        "source_storage_rights_approved": True,
        "source_rights_decision_ref": "docs/source-rights/RPS_SOURCE_DECISION.md",
        "credentials_embedded": False,
        "public_evidence_approved": False,
        "access_control_review_ref": "ops/private-vintage-backend/access-control-v1",
        "durability_review_ref": "ops/private-vintage-backend/durability-v1",
        "retention_policy_ref": "ops/private-vintage-backend/retention-v1",
        "reviewed_at": "2026-09-03T10:00:00Z",
    }


def _write(path: Path, value: object) -> Path:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    return path


def test_configuration_contract_loads_and_returns_exact_file_identity(tmp_path: Path) -> None:
    path = _write(tmp_path / "configuration.json", _configuration())
    config, digest = load_private_backend_configuration(path)
    assert config == _configuration()
    assert digest == sha256_file(path)


def test_configuration_contract_rejects_unknown_or_missing_fields() -> None:
    unknown = _configuration()
    unknown["endpoint"] = "forbidden-extra-field"
    with pytest.raises(
        PrivateBackendConfigurationError,
        match="fields must exactly match",
    ):
        validate_private_backend_configuration(unknown)

    missing = _configuration()
    del missing["durability_review_ref"]
    with pytest.raises(
        PrivateBackendConfigurationError,
        match="fields must exactly match",
    ):
        validate_private_backend_configuration(missing)


def test_configuration_contract_rejects_false_infrastructure_claim_shape() -> None:
    for key in (
        "operator_controlled",
        "private_access_required",
        "persists_beyond_execution",
        "source_storage_rights_approved",
    ):
        value = copy.deepcopy(_configuration())
        value[key] = False
        with pytest.raises(
            PrivateBackendConfigurationError,
            match=rf"configuration\.{key} must be true",
        ):
            validate_private_backend_configuration(value)

    ephemeral = _configuration()
    ephemeral["ephemeral"] = True
    with pytest.raises(
        PrivateBackendConfigurationError,
        match=r"configuration\.ephemeral must be false",
    ):
        validate_private_backend_configuration(ephemeral)


def test_configuration_contract_rejects_embedded_credentials_or_public_approval() -> None:
    credentials = _configuration()
    credentials["credentials_embedded"] = True
    with pytest.raises(
        PrivateBackendConfigurationError,
        match=r"configuration\.credentials_embedded must be false",
    ):
        validate_private_backend_configuration(credentials)

    publication = _configuration()
    publication["public_evidence_approved"] = True
    with pytest.raises(
        PrivateBackendConfigurationError,
        match=r"configuration\.public_evidence_approved must be false",
    ):
        validate_private_backend_configuration(publication)


def test_configuration_references_cannot_contain_url_or_secret_like_syntax() -> None:
    for key in (
        "configuration_ref",
        "access_control_review_ref",
        "durability_review_ref",
        "retention_policy_ref",
    ):
        value = copy.deepcopy(_configuration())
        value[key] = "https://private.example.invalid/review?token=secret"
        with pytest.raises(
            PrivateBackendConfigurationError,
            match="non-secret path-like review identifier",
        ):
            validate_private_backend_configuration(value)


def test_configuration_requires_canonical_rights_binding_and_timezone() -> None:
    rights = _configuration()
    rights["source_rights_decision_ref"] = "ops/alternate-rights-decision"
    with pytest.raises(
        PrivateBackendConfigurationError,
        match="canonical RPS rights decision",
    ):
        validate_private_backend_configuration(rights)

    naive_time = _configuration()
    naive_time["reviewed_at"] = "2026-09-03T10:00:00"
    with pytest.raises(
        PrivateBackendConfigurationError,
        match="explicit timezone",
    ):
        validate_private_backend_configuration(naive_time)

    invalid_time = _configuration()
    invalid_time["reviewed_at"] = "not-a-time"
    with pytest.raises(
        PrivateBackendConfigurationError,
        match="ISO-8601 timestamp",
    ):
        validate_private_backend_configuration(invalid_time)


def test_configuration_loader_rejects_symlink_and_invalid_json(tmp_path: Path) -> None:
    real = _write(tmp_path / "real.json", _configuration())
    link = tmp_path / "link.json"
    link.symlink_to(real)
    with pytest.raises(
        PrivateBackendConfigurationError,
        match="must be a regular file",
    ):
        load_private_backend_configuration(link)

    invalid = tmp_path / "invalid.json"
    invalid.write_text("{not-json}\n")
    with pytest.raises(
        PrivateBackendConfigurationError,
        match="Could not read private-backend configuration evidence",
    ):
        load_private_backend_configuration(invalid)
