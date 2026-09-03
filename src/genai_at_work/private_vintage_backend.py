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

from genai_at_work.private_vintage import (
    MANIFEST_NAME,
    PrivateVintageError,
    sha256_file,
    verify_rps_private_vintage,
)
from genai_at_work.private_vintage_store import store_rps_private_vintage
from genai_at_work.release_engine import canonical_digest

_BACKEND_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_CHALLENGE_TYPE = "rps_private_backend_write_challenge"
_VERIFICATION_TYPE = "rps_private_backend_write_read_verify"


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


def _backend_id(value: str) -> str:
    if _BACKEND_ID_RE.fullmatch(value) is None:
        raise PrivateVintageBackendError(
            "backend_id must be a filesystem-safe identifier using letters, numbers, '.', '_' or '-'"
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


def write_backend_challenge(
    snapshot_path: Path,
    backend_root: Path,
    *,
    backend_id: str,
    configuration_evidence_ref: str,
    builder_commit: str,
    previous_snapshot_path: Path | None = None,
) -> dict[str, Any]:
    """Write one immutable event and return a rights-safe read-back challenge.

    The challenge proves what was written, not that the supplied backend root is
    actually durable or access-controlled. Infrastructure durability remains a
    separately reviewed fact identified by ``configuration_evidence_ref``.
    """

    normalized_backend_id = _backend_id(backend_id)
    if not configuration_evidence_ref.strip():
        raise PrivateVintageBackendError(
            "configuration_evidence_ref must identify separately reviewable backend configuration evidence"
        )

    package_dir, manifest = store_rps_private_vintage(
        snapshot_path,
        backend_root,
        builder_commit=builder_commit,
        previous_snapshot_path=previous_snapshot_path,
    )
    manifest = verify_rps_private_vintage(package_dir)
    comparison = _mapping(manifest.get("comparison"), context="archive.comparison")
    namespace = f"{manifest['source_id']}/{manifest['archive_event_id']}"

    challenge = {
        "schema_version": 1,
        "challenge_type": _CHALLENGE_TYPE,
        "backend_id": normalized_backend_id,
        "configuration_evidence_ref": configuration_evidence_ref,
        "backend_namespace": namespace,
        "source_id": manifest["source_id"],
        "archive_event_id": manifest["archive_event_id"],
        "source_content_sha256": manifest["source_content_sha256"],
        "source_snapshot_sha256": manifest["source_snapshot_sha256"],
        "previous_snapshot_sha256": comparison.get("previous_snapshot_sha256"),
        "package_digest": _package_digest(package_dir, manifest),
        "builder_commit": manifest["builder_commit"],
        "storage_scope": manifest["rights"]["storage_scope"],
        "public_archive": manifest["public_archive"],
        "activation_gates_updated": False,
        "durability_established_by_software_alone": False,
    }
    validate_backend_challenge(challenge)
    return challenge


def validate_backend_challenge(challenge: Mapping[str, Any]) -> None:
    """Validate a rights-safe backend read-back challenge."""

    if challenge.get("schema_version") != 1:
        raise PrivateVintageBackendError("challenge.schema_version must equal 1")
    if challenge.get("challenge_type") != _CHALLENGE_TYPE:
        raise PrivateVintageBackendError("Unsupported private-backend challenge type")
    backend_id = _backend_id(_string(challenge, "backend_id", context="challenge"))
    del backend_id
    _string(challenge, "configuration_evidence_ref", context="challenge")
    source_id = _string(challenge, "source_id", context="challenge")
    event_id = _hex64(challenge, "archive_event_id", context="challenge")
    _hex64(challenge, "source_content_sha256", context="challenge")
    snapshot_sha = _hex64(challenge, "source_snapshot_sha256", context="challenge")
    package_digest = _hex64(challenge, "package_digest", context="challenge")
    del package_digest
    if event_id != snapshot_sha:
        raise PrivateVintageBackendError(
            "challenge archive_event_id must equal source_snapshot_sha256"
        )
    if _string(challenge, "backend_namespace", context="challenge") != f"{source_id}/{event_id}":
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
    _string(challenge, "builder_commit", context="challenge")
    if challenge.get("storage_scope") != "private":
        raise PrivateVintageBackendError("challenge.storage_scope must remain private")
    if challenge.get("public_archive") is not False:
        raise PrivateVintageBackendError("challenge.public_archive must remain false")
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
) -> dict[str, Any]:
    """Independently read back and verify the exact package named by a challenge."""

    validate_backend_challenge(challenge)
    source_id = str(challenge["source_id"])
    event_id = str(challenge["archive_event_id"])
    backend_package = backend_root / source_id / event_id
    manifest = verify_rps_private_vintage(backend_package)

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

    with tempfile.TemporaryDirectory(prefix="rps-private-backend-recovery-") as temporary:
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
        "backend_namespace": challenge["backend_namespace"],
        "source_id": source_id,
        "archive_event_id": event_id,
        "source_content_sha256": challenge["source_content_sha256"],
        "source_snapshot_sha256": challenge["source_snapshot_sha256"],
        "previous_snapshot_sha256": challenge.get("previous_snapshot_sha256"),
        "package_digest": challenge["package_digest"],
        "write_builder_commit": challenge["builder_commit"],
        "verified_at": datetime.now(UTC).isoformat(),
        "write_read_verify_passed": True,
        "recovery_copy_verified": True,
        "storage_scope": "private",
        "public_archive": False,
        "source_bytes_in_evidence": False,
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
        raise PrivateVintageBackendError("private-backend challenge must be a JSON object")
    challenge = {str(key): item for key, item in value.items()}
    validate_backend_challenge(challenge)
    return challenge
