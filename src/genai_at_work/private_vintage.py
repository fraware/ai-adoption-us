"""Immutable private-vintage packages for RPS source snapshots.

This module defines a storage-format contract, not a storage vendor. Exact source
snapshot bytes are copied into an operator-controlled private archive root and
addressed by their SHA-256 digest. Optional comparison evidence against a prior
snapshot is retained privately alongside the source snapshot.

The archive must never be placed in the public repository tree except beneath
the explicitly ignored ``data/audit/private/`` boundary enforced by the CLI.
Backends such as private object stores may implement the same package layout and
create-only semantics through a mounted filesystem or a future adapter.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from genai_at_work.rps_refresh import compare_refresh_snapshots
from genai_at_work.rps_release import snapshot_content_sha256

_SOURCE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,255}$")
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
SNAPSHOT_NAME = "rps_source_snapshot.json"
DIFF_NAME = "rps_refresh_diff.json"
MANIFEST_NAME = "private_vintage_manifest.json"


class PrivateVintageError(RuntimeError):
    """Raised when a private RPS vintage package violates the archive contract."""


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a file without loading it fully into memory."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json_object(path: Path, *, context: str) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise PrivateVintageError(f"{context} must be a regular file: {path}")
    try:
        value = json.loads(path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PrivateVintageError(f"Could not read {context}: {path}") from exc
    if not isinstance(value, dict):
        raise PrivateVintageError(f"{context} must contain a JSON object")
    return {str(key): item for key, item in value.items()}


def _required_string(mapping: Mapping[str, Any], key: str, *, context: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PrivateVintageError(f"{context}.{key} must be a non-empty string")
    return value


def _required_int(mapping: Mapping[str, Any], key: str, *, context: str) -> int:
    value = mapping.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise PrivateVintageError(f"{context}.{key} must be a non-negative integer")
    return value


def _hex64(value: object, *, context: str) -> str:
    if not isinstance(value, str) or _HEX64_RE.fullmatch(value.lower()) is None:
        raise PrivateVintageError(f"{context} must be a 64-character SHA-256 digest")
    return value.lower()


def _builder_commit(value: str) -> str:
    normalized = value.lower()
    if _COMMIT_RE.fullmatch(normalized) is None:
        raise PrivateVintageError("builder_commit must be a 40- or 64-character Git hex digest")
    return normalized


def _source_id(snapshot: Mapping[str, Any]) -> str:
    source_id = _required_string(snapshot, "source_id", context="snapshot")
    if _SOURCE_ID_RE.fullmatch(source_id) is None:
        raise PrivateVintageError(
            "snapshot.source_id must be a filesystem-safe identifier using letters, numbers, '.', '_' or '-'"
        )
    return source_id


def _validate_snapshot(snapshot: Mapping[str, Any]) -> tuple[str, str]:
    if snapshot.get("schema_version") != 1:
        raise PrivateVintageError("snapshot.schema_version must equal 1")
    if snapshot.get("snapshot_type") != "rps_published_aggregate_refresh":
        raise PrivateVintageError("Unsupported RPS snapshot_type")
    source_id = _source_id(snapshot)
    declared = _hex64(snapshot.get("content_sha256"), context="snapshot.content_sha256")
    observed = snapshot_content_sha256(snapshot)
    if observed != declared:
        raise PrivateVintageError(
            "RPS snapshot scientific content hash mismatch; archive input may have been modified"
        )

    rights = snapshot.get("rights")
    if not isinstance(rights, Mapping):
        raise PrivateVintageError("snapshot.rights must be an object")
    if rights.get("status") != "approved":
        raise PrivateVintageError("Only rights-approved RPS snapshots may enter the private vintage archive")
    if rights.get("public_bulk_redistribution_approved") is not False:
        raise PrivateVintageError(
            "Private archive contract requires the no-public-bulk-redistribution boundary"
        )

    inventory = snapshot.get("inventory")
    if not isinstance(inventory, Mapping) or inventory.get("provider_inventory_status") != "pass":
        raise PrivateVintageError("Snapshot provider inventory must be validated before archiving")
    for key in ("provider_series_count", "observatory_series_count", "excluded_series_count"):
        _required_int(inventory, key, context="snapshot.inventory")
    if _required_int(snapshot, "observation_count", context="snapshot") < 1:
        raise PrivateVintageError("snapshot.observation_count must be positive")
    _required_string(snapshot, "retrieved_at", context="snapshot")
    provider_release_id = snapshot.get("provider_release_id")
    if not isinstance(provider_release_id, int) or isinstance(provider_release_id, bool):
        raise PrivateVintageError("snapshot.provider_release_id must be an integer")
    return source_id, declared


def _write_json(path: Path, value: object) -> tuple[str, int]:
    payload = json.dumps(value, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    path.write_bytes(payload)
    return sha256_file(path), path.stat().st_size


def _comparison_payload(
    current: Mapping[str, Any],
    previous: Mapping[str, Any] | None,
    *,
    previous_snapshot_sha256: str | None,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    if previous is None:
        return (
            {
                "revision_status": "baseline",
                "previous_snapshot_sha256": None,
                "previous_source_content_sha256": None,
                "counts": {
                    "new_observations": current.get("observation_count"),
                    "revised_observations": 0,
                    "removed_observations": 0,
                    "definition_changes": 0,
                },
            },
            None,
        )

    previous_source_id, previous_content = _validate_snapshot(previous)
    current_source_id = _source_id(current)
    if previous_source_id != current_source_id:
        raise PrivateVintageError(
            f"Previous and current snapshots have different source identities: "
            f"{previous_source_id!r} != {current_source_id!r}"
        )
    diff = compare_refresh_snapshots(previous, current)
    return (
        {
            "revision_status": diff["revision_status"],
            "previous_snapshot_sha256": previous_snapshot_sha256,
            "previous_source_content_sha256": previous_content,
            "counts": diff["counts"],
        },
        diff,
    )


def _manifest(
    snapshot: Mapping[str, Any],
    *,
    source_id: str,
    content_sha256: str,
    snapshot_sha256: str,
    snapshot_size: int,
    builder_commit: str,
    comparison: Mapping[str, Any],
    diff_file: Mapping[str, Any] | None,
) -> dict[str, Any]:
    rights = snapshot["rights"]
    inventory = snapshot["inventory"]
    assert isinstance(rights, Mapping)
    assert isinstance(inventory, Mapping)
    files: dict[str, Any] = {
        "source_snapshot": {
            "path": SNAPSHOT_NAME,
            "sha256": snapshot_sha256,
            "size_bytes": snapshot_size,
        }
    }
    if diff_file is not None:
        files["comparison_diff"] = dict(diff_file)
    return {
        "schema_version": 1,
        "archive_type": "rps_private_source_vintage",
        "archive_event_id": snapshot_sha256,
        "source_id": source_id,
        "source_content_sha256": content_sha256,
        "source_snapshot_sha256": snapshot_sha256,
        "retrieved_at": snapshot["retrieved_at"],
        "provider_release_id": snapshot["provider_release_id"],
        "observation_count": snapshot["observation_count"],
        "inventory": {
            "provider_series_count": inventory.get("provider_series_count"),
            "observatory_series_count": inventory.get("observatory_series_count"),
            "excluded_series_count": inventory.get("excluded_series_count"),
            "provider_inventory_status": inventory.get("provider_inventory_status"),
        },
        "rights": {
            "status": rights.get("status"),
            "scope": rights.get("scope"),
            "decision_ref": rights.get("decision_ref"),
            "storage_scope": "private",
            "public_bulk_redistribution_approved": False,
        },
        "comparison": dict(comparison),
        "builder_commit": builder_commit,
        "immutable": True,
        "public_archive": False,
        "files": files,
    }


def verify_rps_private_vintage(package_dir: Path) -> dict[str, Any]:
    """Verify an archived package's exact bytes, scientific identity, and namespace."""

    if not package_dir.is_dir() or package_dir.is_symlink():
        raise PrivateVintageError(f"Private vintage package is not a regular directory: {package_dir}")
    manifest = _load_json_object(package_dir / MANIFEST_NAME, context="private vintage manifest")
    if manifest.get("schema_version") != 1 or manifest.get("archive_type") != "rps_private_source_vintage":
        raise PrivateVintageError("Unsupported private vintage manifest")
    if manifest.get("immutable") is not True or manifest.get("public_archive") is not False:
        raise PrivateVintageError("Private vintage manifest lost its immutable/private contract")

    source_id = _required_string(manifest, "source_id", context="archive")
    if _SOURCE_ID_RE.fullmatch(source_id) is None:
        raise PrivateVintageError("Archived source_id is not filesystem-safe")
    event_id = _hex64(manifest.get("archive_event_id"), context="archive.archive_event_id")
    snapshot_sha = _hex64(manifest.get("source_snapshot_sha256"), context="archive.source_snapshot_sha256")
    if event_id != snapshot_sha or package_dir.name != event_id:
        raise PrivateVintageError("Private vintage directory/event identity does not match snapshot SHA-256")
    if package_dir.parent.name != source_id:
        raise PrivateVintageError("Private vintage source namespace does not match manifest source_id")

    files = manifest.get("files")
    if not isinstance(files, Mapping):
        raise PrivateVintageError("archive.files must be an object")
    source_file = files.get("source_snapshot")
    if not isinstance(source_file, Mapping) or source_file.get("path") != SNAPSHOT_NAME:
        raise PrivateVintageError("archive.files.source_snapshot is invalid")

    expected_names = {MANIFEST_NAME, SNAPSHOT_NAME}
    diff_file = files.get("comparison_diff")
    if diff_file is not None:
        if not isinstance(diff_file, Mapping) or diff_file.get("path") != DIFF_NAME:
            raise PrivateVintageError("archive.files.comparison_diff is invalid")
        expected_names.add(DIFF_NAME)
    actual_names = {path.name for path in package_dir.iterdir()}
    if actual_names != expected_names:
        raise PrivateVintageError(
            f"Private vintage package contains unexpected/missing files: "
            f"expected={sorted(expected_names)}, actual={sorted(actual_names)}"
        )

    snapshot_path = package_dir / SNAPSHOT_NAME
    if snapshot_path.is_symlink() or not snapshot_path.is_file():
        raise PrivateVintageError("Archived RPS snapshot is not a regular file")
    expected_snapshot_size = _required_int(source_file, "size_bytes", context="source_snapshot")
    expected_snapshot_sha = _hex64(source_file.get("sha256"), context="source_snapshot.sha256")
    if snapshot_path.stat().st_size != expected_snapshot_size or sha256_file(snapshot_path) != expected_snapshot_sha:
        raise PrivateVintageError("Archived RPS snapshot byte identity mismatch")
    if expected_snapshot_sha != snapshot_sha:
        raise PrivateVintageError("Archived source snapshot hash is inconsistent across manifest fields")

    snapshot = _load_json_object(snapshot_path, context="archived RPS snapshot")
    observed_source_id, content_sha = _validate_snapshot(snapshot)
    if observed_source_id != source_id:
        raise PrivateVintageError("Archived snapshot source_id does not match package manifest")
    if content_sha != _hex64(manifest.get("source_content_sha256"), context="archive.source_content_sha256"):
        raise PrivateVintageError("Archived snapshot scientific content identity mismatch")

    if diff_file is not None:
        diff_path = package_dir / DIFF_NAME
        if diff_path.is_symlink() or not diff_path.is_file():
            raise PrivateVintageError("Archived comparison diff is not a regular file")
        expected_diff_size = _required_int(diff_file, "size_bytes", context="comparison_diff")
        expected_diff_sha = _hex64(diff_file.get("sha256"), context="comparison_diff.sha256")
        if diff_path.stat().st_size != expected_diff_size or sha256_file(diff_path) != expected_diff_sha:
            raise PrivateVintageError("Archived comparison diff byte identity mismatch")
        diff = _load_json_object(diff_path, context="archived comparison diff")
        if diff.get("current_content_sha256") != content_sha:
            raise PrivateVintageError("Archived comparison diff is not bound to this source content")
        comparison = manifest.get("comparison")
        if not isinstance(comparison, Mapping) or comparison.get("revision_status") != diff.get("revision_status"):
            raise PrivateVintageError("Archived comparison status disagrees with the detailed diff")

    _builder_commit(_required_string(manifest, "builder_commit", context="archive"))
    rights = manifest.get("rights")
    if not isinstance(rights, Mapping) or rights.get("storage_scope") != "private":
        raise PrivateVintageError("Private vintage manifest must retain storage_scope=private")
    if rights.get("public_bulk_redistribution_approved") is not False:
        raise PrivateVintageError("Private vintage manifest cannot widen redistribution scope")
    return manifest


def archive_rps_private_vintage(
    snapshot_path: Path,
    archive_root: Path,
    *,
    builder_commit: str,
    previous_snapshot_path: Path | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Install one immutable RPS retrieval event into a private archive root.

    The event directory is addressed by the exact source-snapshot file SHA-256.
    Re-archiving byte-identical input is idempotent. Existing corrupt or
    mismatched packages fail closed and are never overwritten.
    """

    normalized_commit = _builder_commit(builder_commit)
    snapshot = _load_json_object(snapshot_path, context="RPS source snapshot")
    source_id, content_sha = _validate_snapshot(snapshot)
    snapshot_sha = sha256_file(snapshot_path)
    snapshot_size = snapshot_path.stat().st_size

    previous: dict[str, Any] | None = None
    previous_snapshot_sha: str | None = None
    if previous_snapshot_path is not None:
        previous = _load_json_object(previous_snapshot_path, context="previous RPS source snapshot")
        previous_snapshot_sha = sha256_file(previous_snapshot_path)
    comparison, diff = _comparison_payload(
        snapshot,
        previous,
        previous_snapshot_sha256=previous_snapshot_sha,
    )

    source_root = archive_root / source_id
    target = source_root / snapshot_sha
    if target.exists():
        manifest = verify_rps_private_vintage(target)
        if manifest.get("source_snapshot_sha256") != snapshot_sha:
            raise PrivateVintageError("Existing archive event does not match the requested snapshot")
        return target, manifest

    source_root.mkdir(parents=True, exist_ok=True)
    temporary = source_root / f".{snapshot_sha}.tmp"
    if temporary.exists():
        raise PrivateVintageError(f"Temporary private vintage directory already exists: {temporary}")
    temporary.mkdir()
    try:
        archived_snapshot = temporary / SNAPSHOT_NAME
        shutil.copyfile(snapshot_path, archived_snapshot, follow_symlinks=False)
        if archived_snapshot.stat().st_size != snapshot_size or sha256_file(archived_snapshot) != snapshot_sha:
            raise PrivateVintageError("Copied private RPS snapshot failed byte verification")

        diff_file: dict[str, Any] | None = None
        if diff is not None:
            diff_sha, diff_size = _write_json(temporary / DIFF_NAME, diff)
            diff_file = {
                "path": DIFF_NAME,
                "sha256": diff_sha,
                "size_bytes": diff_size,
            }

        manifest = _manifest(
            snapshot,
            source_id=source_id,
            content_sha256=content_sha,
            snapshot_sha256=snapshot_sha,
            snapshot_size=snapshot_size,
            builder_commit=normalized_commit,
            comparison=comparison,
            diff_file=diff_file,
        )
        _write_json(temporary / MANIFEST_NAME, manifest)
        os.replace(temporary, target)
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise

    verified = verify_rps_private_vintage(target)
    return target, verified
