"""Two-phase conformance protocol for durable private RPS vintage backends.

The private-vintage package codec defines exact bytes and immutable provenance.
This module adds a vendor-neutral write challenge and later independent read-back
verification. It deliberately does not infer that a filesystem path is durable,
private, or production-controlled: those are infrastructure facts that must be
supported by separately reviewed configuration evidence.
"""

from __future__ import annotations

import json
import re
import shutil
import tempfile
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from genai_at_work.private_backend_config import load_private_backend_configuration
from genai_at_work.private_vintage import (
    MANIFEST_NAME,
    PrivateVintageError,
    sha256_file,
    verify_rps_private_vintage,
)
from genai_at_work.private_vintage_store import store_rps_private_vintage
from genai_at_work.release_engine import canonical_digest

_BACKEND_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_SOURCE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,255}$")
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_CHALLENGE_TYPE = "rps_private_backend_write_challenge"
_VERIFICATION_TYPE = "rps_private_backend_write_read_verify"
_CHALLENGE_KEYS = {
    "schema_version",
    "challenge_type",
    "backend_id",
    "configuration_evidence_ref",
    "configuration_evidence_sha256",
    "backend_namespace",
    "source_id",
    "archive_event_id",
    "source_content_sha256",
    "source_snapshot_sha256",
    "previous_snapshot_sha256",
    "package_digest",
    "builder_commit",
    "storage_scope",
    "public_archive",
    "source_bytes_in_evidence",
    "public_evidence_approved",
    "activation_gates_updated",
    "durability_established_by_software_alone",
}


class PrivateVintageBackendError(PrivateVintageError):
    """Raised when private-backend conformance evidence is invalid or fails."""


def _mapping(value: object, *, context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise PrivateVintageBackendError(f"{context} must be an object")
    return value


def _string(mapping: Mapping[str, Any], key: str, *, context: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PrivateVintageBackendError(f"{context}.{key} must be a non-empty string")
    return value


def _hex64(mapping: Mapping[str, Any], key: str, *, context: str) -> str:
    value = _string(mapping, key, context=context).lower()
    if _HEX64_RE.fullmatch(value) is None:
        raise PrivateVintageBackendError(
            f"{context}.{key} must be a 64-character SHA-256 digest"
        )
    return value


def _commit(value: str, *, context: str) -> str:
    normalized = value.lower()
    if _COMMIT_RE.fullmatch(normalized) is None:
        raise PrivateVintageBackendError(
            f"{context} must be a 40- or 64-character Git commit digest"
        )
    return normalized


def _backend_id(value: str) -> str:
    if _BACKEND_ID_RE.fullmatch(value) is None:
        raise PrivateVintageBackendError(
            "backend_id must be a filesystem-safe identifier using letters, numbers, '.', '_' or '-'"
        )
    return value


def _source_id(value: str) -> str:
    if _SOURCE_ID_RE.fullmatch(value) is None:
        raise PrivateVintageBackendError(
            "source_id must be a filesystem-safe identifier using letters, numbers, '.', '_' or '-'"
        )
    return value


def _package_digest(package_dir: Path, manifest: Mapping[str, Any]) -> str:
    files = _mapping(manifest.get("files"), context="archive.files")
    digests: dict[str, str] = {MANIFEST_NAME: sha256_file(package_dir / MANIFEST_NAME)}
    for value in files.values():
        row = _mapping(value, context="archive.files entry")
        relative = _string(row, "path", context="archive.files entry")
        path = package_dir / relative
        digests[relative] = sha256_file(path)
    return canonical_digest(digests)


def _configuration_binding(path: Path) -> tuple[str, str, str]:
    config, file_sha256 = load_private_backend_configuration(path)
    backend_id = _backend_id(str(config["backend_id"]))
    configuration_ref = str(config["configuration_ref"])
    return backend_id, configuration_ref, file_sha256


def write_backend_challenge(
    snapshot_path: Path,
    backend_root: Path,
    *,
    configuration_evidence_path: Path,
    builder_commit: str,
    previous_snapshot_path: Path | None = None,
) -> dict[str, Any]:
    """Write one immutable event and bind it to exact configuration evidence.

    The challenge proves what was written and which exact configuration
    attestation governed the write. It does not independently prove the truth of
    that attestation or the durability/access-control properties of the backend.
    """

    backend_id, configuration_ref, configuration_sha256 = _configuration_binding(
        configuration_evidence_path
    )
    normalized_builder_commit = _commit(
        builder_commit,
        context="builder_commit",
    )

    package_dir, manifest = store_rps_private_vintage(
        snapshot_path,
        backend_root,
        builder_commit=normalized_builder_commit,
        previous_snapshot_path=previous_snapshot_path,
    )
    manifest = verify_rps_private_vintage(package_dir)
    if manifest["builder_commit"] != normalized_builder_commit:
        raise PrivateVintageBackendError(
            "archived builder commit does not match the requested write builder commit"
        )
    comparison = _mapping(manifest.get("comparison"), context="archive.comparison")
    namespace = f"{manifest['source_id']}/{manifest['archive_event_id']}"

    challenge = {
        "schema_version": 1,
        "challenge_type": _CHALLENGE_TYPE,
        "backend_id": backend_id,
        "configuration_evidence_ref": configuration_ref,
        "configuration_evidence_sha256": configuration_sha256,
        "backend_namespace": namespace,
        "source_id": manifest["source_id"],
        "archive_event_id": manifest["archive_event_id"],
        "source_content_sha256": manifest["source_content_sha256"],
        "source_snapshot_sha256": manifest["source_snapshot_sha256"],
        "previous_snapshot_sha256": comparison.get("previous_snapshot_sha256"),
        "package_digest": _package_digest(package_dir, manifest),
        "builder_commit": normalized_builder_commit,
        "storage_scope": manifest["rights"]["storage_scope"],
        "public_archive": manifest["public_archive"],
        "source_bytes_in_evidence": False,
        "public_evidence_approved": False,
        "activation_gates_updated": False,
        "durability_established_by_software_alone": False,
    }
    validate_backend_challenge(challenge)
    return challenge


def validate_backend_challenge(challenge: Mapping[str, Any]) -> None:
    """Validate a source-byte-free backend read-back challenge."""

    if set(challenge) != _CHALLENGE_KEYS:
        raise PrivateVintageBackendError(
            "private-backend challenge fields must exactly match the v1 contract"
        )
    if challenge.get("schema_version") != 1:
        raise PrivateVintageBackendError("challenge.schema_version must equal 1")
    if challenge.get("challenge_type") != _CHALLENGE_TYPE:
        raise PrivateVintageBackendError("Unsupported private-backend challenge type")
    _backend_id(_string(challenge, "backend_id", context="challenge"))
    _string(challenge, "configuration_evidence_ref", context="challenge")
    _hex64(challenge, "configuration_evidence_sha256", context="challenge")
    source_id = _source_id(_string(challenge, "source_id", context="challenge"))
    event_id = _hex64(challenge, "archive_event_id", context="challenge")
    _hex64(challenge, "source_content_sha256", context="challenge")
    snapshot_sha = _hex64(challenge, "source_snapshot_sha256", context="challenge")
    _hex64(challenge, "package_digest", context="challenge")
    if event_id != snapshot_sha:
        raise PrivateVintageBackendError(
            "challenge archive_event_id must equal source_snapshot_sha256"
        )
    if (
        _string(challenge, "backend_namespace", context="challenge")
        != f"{source_id}/{event_id}"
    ):
        raise PrivateVintageBackendError(
            "challenge backend_namespace does not match source/event identity"
        )
    previous = challenge.get("previous_snapshot_sha256")
    if previous is not None and (
        not isinstance(previous, str) or _HEX64_RE.fullmatch(previous.lower()) is None
    ):
        raise PrivateVintageBackendError(
            "challenge.previous_snapshot_sha256 must be null or a SHA-256 digest"
        )
    _commit(
        _string(challenge, "builder_commit", context="challenge"),
        context="challenge.builder_commit",
    )
    if challenge.get("storage_scope") != "private":
        raise PrivateVintageBackendError("challenge.storage_scope must remain private")
    if challenge.get("public_archive") is not False:
        raise PrivateVintageBackendError("challenge.public_archive must remain false")
    if challenge.get("source_bytes_in_evidence") is not False:
        raise PrivateVintageBackendError(
            "backend challenge must not include source bytes"
        )
    if challenge.get("public_evidence_approved") is not False:
        raise PrivateVintageBackendError(
            "backend challenge is review evidence and must not self-approve public distribution"
        )
    if challenge.get("activation_gates_updated") is not False:
        raise PrivateVintageBackendError(
            "backend challenge must not claim activation-gate mutation"
        )
    if challenge.get("durability_established_by_software_alone") is not False:
        raise PrivateVintageBackendError(
            "backend challenge must not claim that software alone establishes durability"
        )


def verify_backend_challenge(
    challenge: Mapping[str, Any],
    backend_root: Path,
    *,
    configuration_evidence_path: Path,
    verification_builder_commit: str,
) -> dict[str, Any]:
    """Read back the package and re-bind it to the exact configuration evidence."""

    validate_backend_challenge(challenge)
    backend_id, configuration_ref, configuration_sha256 = _configuration_binding(
        configuration_evidence_path
    )
    if backend_id != challenge["backend_id"]:
        raise PrivateVintageBackendError(
            "read-back configuration backend_id does not match the write challenge"
        )
    if configuration_ref != challenge["configuration_evidence_ref"]:
        raise PrivateVintageBackendError(
            "read-back configuration reference does not match the write challenge"
        )
    if configuration_sha256 != challenge["configuration_evidence_sha256"]:
        raise PrivateVintageBackendError(
            "read-back configuration evidence SHA-256 does not match the write challenge"
        )

    normalized_verification_commit = _commit(
        verification_builder_commit,
        context="verification_builder_commit",
    )
    source_id = str(challenge["source_id"])
    event_id = str(challenge["archive_event_id"])
    backend_package = backend_root / source_id / event_id
    manifest = verify_rps_private_vintage(backend_package)

    if manifest["builder_commit"] != challenge["builder_commit"]:
        raise PrivateVintageBackendError(
            "read-back archived builder commit does not match the write challenge"
        )
    if manifest["source_content_sha256"] != challenge["source_content_sha256"]:
        raise PrivateVintageBackendError(
            "read-back source scientific identity does not match the write challenge"
        )
    if manifest["source_snapshot_sha256"] != challenge["source_snapshot_sha256"]:
        raise PrivateVintageBackendError(
            "read-back exact snapshot identity does not match the write challenge"
        )
    comparison = _mapping(manifest.get("comparison"), context="archive.comparison")
    if comparison.get("previous_snapshot_sha256") != challenge.get(
        "previous_snapshot_sha256"
    ):
        raise PrivateVintageBackendError(
            "read-back previous-vintage binding does not match the write challenge"
        )
    if _package_digest(backend_package, manifest) != challenge["package_digest"]:
        raise PrivateVintageBackendError(
            "read-back package digest does not match the write challenge"
        )

    with tempfile.TemporaryDirectory(
        prefix="rps-private-backend-recovery-"
    ) as temporary:
        recovery_root = Path(temporary)
        recovered_package = recovery_root / source_id / event_id
        recovered_package.parent.mkdir(parents=True)
        shutil.copytree(backend_package, recovered_package, symlinks=True)
        recovered_manifest = verify_rps_private_vintage(recovered_package)
        if recovered_manifest != manifest:
            raise PrivateVintageBackendError(
                "recovered package manifest differs from backend package manifest"
            )
        recovered_package_digest = _package_digest(
            recovered_package, recovered_manifest
        )
        if recovered_package_digest != challenge["package_digest"]:
            raise PrivateVintageBackendError(
                "recovered package digest differs from the write challenge"
            )

    return {
        "schema_version": 1,
        "verification_type": _VERIFICATION_TYPE,
        "backend_id": challenge["backend_id"],
        "configuration_evidence_ref": challenge["configuration_evidence_ref"],
        "configuration_evidence_sha256": challenge["configuration_evidence_sha256"],
        "backend_namespace": challenge["backend_namespace"],
        "source_id": source_id,
        "archive_event_id": event_id,
        "source_content_sha256": challenge["source_content_sha256"],
        "source_snapshot_sha256": challenge["source_snapshot_sha256"],
        "previous_snapshot_sha256": challenge.get("previous_snapshot_sha256"),
        "package_digest": challenge["package_digest"],
        "write_builder_commit": challenge["builder_commit"],
        "verification_builder_commit": normalized_verification_commit,
        "verified_at": datetime.now(UTC).isoformat(),
        "write_read_verify_passed": True,
        "recovery_copy_verified": True,
        "storage_scope": "private",
        "public_archive": False,
        "source_bytes_in_evidence": False,
        "public_evidence_approved": False,
        "activation_gates_updated": False,
        "durability_established_by_software_alone": False,
        "requires_independent_backend_configuration_review": True,
    }


def load_backend_challenge(path: Path) -> dict[str, Any]:
    """Load and validate a challenge JSON document."""

    try:
        value = json.loads(path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PrivateVintageBackendError(
            f"Could not read private-backend challenge: {path}"
        ) from exc
    if not isinstance(value, dict):
        raise PrivateVintageBackendError(
            "private-backend challenge must be a JSON object"
        )
    challenge = {str(key): item for key, item in value.items()}
    validate_backend_challenge(challenge)
    return challenge
