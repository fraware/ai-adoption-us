"""Strict private configuration-evidence contract for the RPS vintage backend.

This module validates an operator attestation about the production storage
boundary and returns the exact file SHA-256 used to bind later write/read
conformance evidence. Validation makes the attestation internally consistent; it
does not independently prove the truth of infrastructure claims.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from genai_at_work.private_vintage import sha256_file

_EVIDENCE_TYPE = "rps_private_backend_configuration"
_ENVIRONMENT_SCOPE = "production_rps_refresh"
_ALLOWED_STORAGE_INTERFACES = {"mounted_filesystem", "object_store_mount"}
_BACKEND_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_CONFIG_KEYS = {
    "schema_version",
    "evidence_type",
    "backend_id",
    "configuration_ref",
    "environment_scope",
    "storage_interface",
    "operator_controlled",
    "private_access_required",
    "ephemeral",
    "persists_beyond_execution",
    "source_storage_rights_approved",
    "source_rights_decision_ref",
    "credentials_embedded",
    "public_evidence_approved",
    "access_control_review_ref",
    "durability_review_ref",
    "retention_policy_ref",
    "reviewed_at",
}


class PrivateBackendConfigurationError(ValueError):
    """Raised when private-backend configuration evidence is invalid."""


def _string(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PrivateBackendConfigurationError(
            f"configuration.{key} must be a non-empty string"
        )
    return value


def _bool(mapping: Mapping[str, Any], key: str) -> bool:
    value = mapping.get(key)
    if not isinstance(value, bool):
        raise PrivateBackendConfigurationError(
            f"configuration.{key} must be boolean"
        )
    return value


def validate_private_backend_configuration(config: Mapping[str, Any]) -> None:
    """Validate the exact v1 configuration-attestation schema and safety claims."""

    if set(config) != _CONFIG_KEYS:
        raise PrivateBackendConfigurationError(
            "private-backend configuration fields must exactly match the v1 contract"
        )
    if config.get("schema_version") != 1:
        raise PrivateBackendConfigurationError("configuration.schema_version must equal 1")
    if config.get("evidence_type") != _EVIDENCE_TYPE:
        raise PrivateBackendConfigurationError(
            "configuration.evidence_type must identify RPS private backend configuration"
        )

    backend_id = _string(config, "backend_id")
    if _BACKEND_ID_RE.fullmatch(backend_id) is None:
        raise PrivateBackendConfigurationError(
            "configuration.backend_id must be filesystem-safe"
        )
    _string(config, "configuration_ref")
    if _string(config, "environment_scope") != _ENVIRONMENT_SCOPE:
        raise PrivateBackendConfigurationError(
            "configuration.environment_scope must equal production_rps_refresh"
        )
    storage_interface = _string(config, "storage_interface")
    if storage_interface not in _ALLOWED_STORAGE_INTERFACES:
        raise PrivateBackendConfigurationError(
            "configuration.storage_interface is unsupported"
        )

    required_true = (
        "operator_controlled",
        "private_access_required",
        "persists_beyond_execution",
        "source_storage_rights_approved",
    )
    for key in required_true:
        if _bool(config, key) is not True:
            raise PrivateBackendConfigurationError(
                f"configuration.{key} must be true"
            )

    required_false = (
        "ephemeral",
        "credentials_embedded",
        "public_evidence_approved",
    )
    for key in required_false:
        if _bool(config, key) is not False:
            raise PrivateBackendConfigurationError(
                f"configuration.{key} must be false"
            )

    if _string(config, "source_rights_decision_ref") != (
        "docs/source-rights/RPS_SOURCE_DECISION.md"
    ):
        raise PrivateBackendConfigurationError(
            "configuration.source_rights_decision_ref must bind the canonical RPS rights decision"
        )
    _string(config, "access_control_review_ref")
    _string(config, "durability_review_ref")
    _string(config, "retention_policy_ref")
    _string(config, "reviewed_at")


def load_private_backend_configuration(path: Path) -> tuple[dict[str, Any], str]:
    """Load a regular configuration-evidence file and return its exact SHA-256."""

    if not path.is_file() or path.is_symlink():
        raise PrivateBackendConfigurationError(
            f"private-backend configuration evidence must be a regular file: {path}"
        )
    try:
        value = json.loads(path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PrivateBackendConfigurationError(
            f"Could not read private-backend configuration evidence: {path}"
        ) from exc
    if not isinstance(value, dict):
        raise PrivateBackendConfigurationError(
            "private-backend configuration evidence must contain a JSON object"
        )
    config = {str(key): item for key, item in value.items()}
    validate_private_backend_configuration(config)
    return config, sha256_file(path)
