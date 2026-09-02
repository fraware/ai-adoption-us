"""Create-only storage coordinator for immutable private RPS vintage packages.

The package codec in :mod:`genai_at_work.private_vintage` verifies exact bytes
and scientific identity. This module adds the operator-facing concurrency and
comparison-binding guarantees required when multiple processes may target the
same private archive root.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from genai_at_work.private_vintage import (
    PrivateVintageError,
    archive_rps_private_vintage,
    sha256_file,
    verify_rps_private_vintage,
)

_SOURCE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,255}$")


def _load_object(path: Path, *, context: str) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise PrivateVintageError(f"{context} must be a regular file: {path}")
    try:
        value = json.loads(path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PrivateVintageError(f"Could not read {context}: {path}") from exc
    if not isinstance(value, dict):
        raise PrivateVintageError(f"{context} must contain a JSON object")
    return {str(key): item for key, item in value.items()}


def _source_id(snapshot: Mapping[str, Any]) -> str:
    value = snapshot.get("source_id")
    if not isinstance(value, str) or _SOURCE_ID_RE.fullmatch(value) is None:
        raise PrivateVintageError("Snapshot source_id is missing or not filesystem-safe")
    return value


def _expected_previous_sha(previous_snapshot_path: Path | None) -> str | None:
    if previous_snapshot_path is None:
        return None
    if not previous_snapshot_path.is_file() or previous_snapshot_path.is_symlink():
        raise PrivateVintageError(
            f"Previous RPS source snapshot must be a regular file: {previous_snapshot_path}"
        )
    return sha256_file(previous_snapshot_path)


def _verify_existing_binding(
    target: Path,
    *,
    expected_previous_snapshot_sha256: str | None,
) -> dict[str, Any]:
    manifest = verify_rps_private_vintage(target)
    comparison = manifest.get("comparison")
    if not isinstance(comparison, Mapping):
        raise PrivateVintageError("Existing private vintage has no valid comparison binding")
    observed_previous = comparison.get("previous_snapshot_sha256")
    if observed_previous != expected_previous_snapshot_sha256:
        raise PrivateVintageError(
            "Existing private vintage event is already bound to a different previous snapshot; "
            "immutable comparison provenance cannot be rewritten"
        )
    return manifest


def _harden_local_permissions(package_dir: Path) -> None:
    """Apply owner-only permissions on ordinary POSIX filesystems when supported."""

    try:
        package_dir.chmod(0o700)
        package_dir.parent.chmod(0o700)
        for path in package_dir.iterdir():
            if path.is_file() and not path.is_symlink():
                path.chmod(0o600)
    except OSError as exc:
        raise PrivateVintageError(
            "Could not apply owner-only permissions to the private vintage package"
        ) from exc


def store_rps_private_vintage(
    snapshot_path: Path,
    archive_root: Path,
    *,
    builder_commit: str,
    previous_snapshot_path: Path | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Create or verify one immutable private vintage under an exclusive event lock.

    A lock file is acquired with ``O_EXCL`` before installation. A stale lock is
    deliberately fail-closed and requires explicit operator inspection/removal;
    the store never assumes that an interrupted writer is safe to ignore.
    """

    snapshot = _load_object(snapshot_path, context="RPS source snapshot")
    source_id = _source_id(snapshot)
    snapshot_sha = sha256_file(snapshot_path)
    expected_previous_sha = _expected_previous_sha(previous_snapshot_path)

    source_root = archive_root / source_id
    source_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    target = source_root / snapshot_sha
    if target.exists():
        manifest = _verify_existing_binding(
            target,
            expected_previous_snapshot_sha256=expected_previous_sha,
        )
        _harden_local_permissions(target)
        return target, manifest

    lock_path = source_root / f".{snapshot_sha}.lock"
    try:
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise PrivateVintageError(
            f"Private vintage event is locked by another or interrupted writer: {lock_path}. "
            "Inspect the archive before removing a stale lock."
        ) from exc
    except OSError as exc:
        raise PrivateVintageError(f"Could not acquire private vintage lock: {lock_path}") from exc

    try:
        with os.fdopen(lock_fd, "w", encoding="utf-8") as handle:
            handle.write(f"snapshot_sha256={snapshot_sha}\n")
            handle.write(f"pid={os.getpid()}\n")
            handle.flush()
            os.fsync(handle.fileno())

        if target.exists():
            manifest = _verify_existing_binding(
                target,
                expected_previous_snapshot_sha256=expected_previous_sha,
            )
            _harden_local_permissions(target)
            return target, manifest

        package_dir, manifest = archive_rps_private_vintage(
            snapshot_path,
            archive_root,
            builder_commit=builder_commit,
            previous_snapshot_path=previous_snapshot_path,
        )
        if package_dir != target:
            raise PrivateVintageError("Private vintage package installed outside its locked event path")
        manifest = _verify_existing_binding(
            package_dir,
            expected_previous_snapshot_sha256=expected_previous_sha,
        )
        _harden_local_permissions(package_dir)
        return package_dir, manifest
    finally:
        try:
            lock_path.unlink(missing_ok=True)
        except OSError as exc:
            raise PrivateVintageError(
                f"Private vintage package completed but lock cleanup failed: {lock_path}"
            ) from exc
