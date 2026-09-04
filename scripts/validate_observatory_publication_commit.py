#!/usr/bin/env python3
"""Validate the one-commit transition from an exact candidate to public release.

A publication commit may introduce exactly one new immutable promoted release and
advance the release registry by one append-only row. Its parent must be the exact
candidate commit named in the release review record. For the first Observatory
release, the review record must also bind the repository's one-shot project-owner
authorization and must state explicitly that no separate human review was performed.
This prevents unrelated code, claims, source files, or rewrites of an already
promoted release from hitchhiking on the release authorization commit.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from genai_at_work.release_engine import load_json_object, sha256_file

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "registry" / "observatory_release_registry.json"
RELEASES_ROOT = ROOT / "data" / "releases"
OWNER_AUTHORIZATION = ROOT / "data" / "registry" / "release1_owner_authorization.json"
REGISTRY_PATH = "data/registry/observatory_release_registry.json"
RELEASE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")


class PublicationCommitError(RuntimeError):
    """Raised when a public authorization commit violates release invariants."""


def _git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except subprocess.CalledProcessError as exc:
        raise PublicationCommitError(f"Git command failed: {' '.join(args)}") from exc


def _git_json(commit: str, path: str) -> dict[str, Any]:
    try:
        payload = _git("show", f"{commit}:{path}")
        value = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise PublicationCommitError(
            f"JSON file {path} is invalid at commit {commit}"
        ) from exc
    if not isinstance(value, dict):
        raise PublicationCommitError(f"JSON file {path} must be an object at commit {commit}")
    return {str(key): item for key, item in value.items()}


def _release_rows(registry: dict[str, Any], *, context: str) -> list[dict[str, Any]]:
    rows = registry.get("releases")
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise PublicationCommitError(f"{context} releases must be a list of objects")
    return [{str(key): item for key, item in row.items()} for row in rows]


def _artifact_hashes(manifest: dict[str, Any], release_root: Path) -> None:
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise PublicationCommitError("Promoted release manifest has no artifacts")
    for row in artifacts:
        if not isinstance(row, dict):
            raise PublicationCommitError("Promoted release contains an invalid artifact row")
        relative = row.get("path")
        expected = row.get("sha256")
        if not isinstance(relative, str) or not relative.startswith("artifacts/"):
            raise PublicationCommitError("Promoted artifact path is invalid")
        if ".." in Path(relative).parts:
            raise PublicationCommitError("Promoted artifact path escapes release root")
        path = release_root / relative
        if not path.is_file() or not isinstance(expected, str) or sha256_file(path) != expected:
            raise PublicationCommitError(f"Promoted artifact checksum mismatch: {relative}")


def _validate_first_release_owner_authorization(review: dict[str, Any]) -> None:
    if not OWNER_AUTHORIZATION.is_file():
        raise PublicationCommitError("Release 1 project-owner authorization record is missing")
    authorization = load_json_object(OWNER_AUTHORIZATION)
    required_authorization = {
        "schema_version": 1,
        "first_release_only": True,
        "automated_release_review_authorized": True,
        "human_review_required": False,
        "formal_github_release_tag": "v1.0.0",
        "active": True,
    }
    for key, expected in required_authorization.items():
        if authorization.get(key) != expected:
            raise PublicationCommitError(
                f"Release 1 owner authorization field {key!r} is invalid"
            )
    authorization_id = authorization.get("authorization_id")
    authorized_by = authorization.get("authorized_by")
    authorized_at = authorization.get("authorized_at")
    if not isinstance(authorization_id, str) or not authorization_id:
        raise PublicationCommitError("Release 1 owner authorization ID is invalid")
    if not isinstance(authorized_by, str) or not authorized_by:
        raise PublicationCommitError("Release 1 authorized_by is invalid")
    if not isinstance(authorized_at, str) or not authorized_at:
        raise PublicationCommitError("Release 1 authorized_at is invalid")

    expected_review = {
        "review_mode": "owner_authorized_automated_release_review",
        "owner_authorized": True,
        "owner_authorization_id": authorization_id,
        "authorized_by": authorized_by,
        "authorized_at": authorized_at,
        "human_review_performed": False,
    }
    for key, expected in expected_review.items():
        if review.get(key) != expected:
            raise PublicationCommitError(
                f"Release 1 review record does not bind owner authorization field {key!r}"
            )


def _validate_append_only_registry_transition(
    *,
    parent: str,
    parent_registry: dict[str, Any],
    registry: dict[str, Any],
    release_id: str,
    manifest_sha: str,
    manifest: dict[str, Any],
    identity_sha: str,
) -> None:
    parent_current = parent_registry.get("current_release_id")
    if parent_current is not None and (
        not isinstance(parent_current, str) or RELEASE_ID_RE.fullmatch(parent_current) is None
    ):
        raise PublicationCommitError("Parent registry current_release_id is invalid")
    if release_id == parent_current:
        raise PublicationCommitError(
            "Publication commit must advance to a new immutable release ID"
        )
    if manifest.get("supersedes_release_id") != parent_current:
        raise PublicationCommitError(
            "Promoted manifest does not explicitly supersede the parent registry release"
        )

    release_prefix = f"data/releases/{release_id}"
    existing = _git("ls-tree", "-r", "--name-only", parent, "--", release_prefix)
    if existing:
        raise PublicationCommitError(
            "Publication commit attempts to rewrite a release directory that already existed in its parent"
        )

    parent_rows = _release_rows(parent_registry, context="Parent registry")
    current_rows = _release_rows(registry, context="Current registry")
    if len(current_rows) != len(parent_rows) + 1 or current_rows[:-1] != parent_rows:
        raise PublicationCommitError(
            "Release registry history must advance by exactly one append-only release row"
        )
    added = current_rows[-1]
    expected_added = {
        "release_id": release_id,
        "manifest_sha256": manifest_sha,
        "promoted_at": manifest.get("promoted_at"),
        "supersedes_release_id": parent_current,
        "data_mode": manifest.get("data_mode"),
        "candidate_commit": parent,
        "rehydration_status": "REHYDRATED_EXACT_CANDIDATE",
        "rehydration_identity_sha256": identity_sha,
    }
    for key, expected in expected_added.items():
        if added.get(key) != expected:
            raise PublicationCommitError(
                f"Appended registry release row mismatch for {key}: {added.get(key)!r} != {expected!r}"
            )

    mutable_keys = {
        "current_release_id",
        "current_release_manifest_sha256",
        "status",
        "releases",
    }
    parent_static = {
        key: value for key, value in parent_registry.items() if key not in mutable_keys
    }
    current_static = {
        key: value for key, value in registry.items() if key not in mutable_keys
    }
    if current_static != parent_static:
        raise PublicationCommitError(
            "Publication commit changed release-registry fields outside the governed release transition"
        )


def validate(commit: str) -> dict[str, Any]:
    head = _git("rev-parse", commit).lower()
    parent = _git("rev-parse", f"{head}^").lower()
    subject = _git("show", "-s", "--format=%s", head)

    registry = load_json_object(REGISTRY)
    parent_registry = _git_json(parent, REGISTRY_PATH)
    release_id = registry.get("current_release_id")
    manifest_sha = registry.get("current_release_manifest_sha256")
    if not isinstance(release_id, str) or RELEASE_ID_RE.fullmatch(release_id) is None:
        raise PublicationCommitError("Release registry current_release_id is invalid")
    if registry.get("status") != "CURRENT_RELEASE_PROMOTED":
        raise PublicationCommitError("Release registry is not in CURRENT_RELEASE_PROMOTED state")
    expected_subject = f"Authorize Observatory release {release_id}"
    if subject != expected_subject:
        raise PublicationCommitError(
            f"Publication commit subject mismatch: {subject!r} != {expected_subject!r}"
        )

    release_root = RELEASES_ROOT / release_id
    manifest_path = release_root / "release_manifest.json"
    review_path = release_root / "review_record.json"
    identity_path = release_root / "rehydration_identity.json"
    if not manifest_path.is_file() or not review_path.is_file() or not identity_path.is_file():
        raise PublicationCommitError(
            "Promoted release is missing manifest, review record, or rehydration identity"
        )
    if not isinstance(manifest_sha, str) or sha256_file(manifest_path) != manifest_sha:
        raise PublicationCommitError("Release registry manifest checksum mismatch")

    manifest = load_json_object(manifest_path)
    review = load_json_object(review_path)
    identity = load_json_object(identity_path)
    if manifest.get("release_id") != release_id:
        raise PublicationCommitError("Promoted manifest release_id disagrees with registry")
    if manifest.get("release_status") != "PROMOTED_AFTER_EXPLICIT_REVIEW":
        raise PublicationCommitError("Promoted manifest lacks explicit-review status")
    if review.get("candidate_commit") != parent:
        raise PublicationCommitError(
            "Publication commit parent is not the exact release-reviewed candidate commit"
        )
    if parent_registry.get("current_release_id") is None:
        _validate_first_release_owner_authorization(review)
    if review.get("rehydration_status") != "REHYDRATED_EXACT_CANDIDATE":
        raise PublicationCommitError("Review record lacks exact-rehydration status")
    identity_sha = sha256_file(identity_path)
    if review.get("rehydration_identity_sha256") != identity_sha:
        raise PublicationCommitError("Review record does not bind the rehydration identity")
    if identity.get("candidate_commit") != parent:
        raise PublicationCommitError("Rehydration identity is not bound to the publication parent")
    if identity.get("release_id") != release_id:
        raise PublicationCommitError("Rehydration identity release_id mismatch")
    if identity.get("status") != "REHYDRATED_EXACT_CANDIDATE":
        raise PublicationCommitError("Rehydration identity status is invalid")
    if identity.get("source_input_bytes_included") is not False:
        raise PublicationCommitError("Rehydration identity widened private-source publication")

    assert isinstance(manifest_sha, str)
    _validate_append_only_registry_transition(
        parent=parent,
        parent_registry=parent_registry,
        registry=registry,
        release_id=release_id,
        manifest_sha=manifest_sha,
        manifest=manifest,
        identity_sha=identity_sha,
    )
    _artifact_hashes(manifest, release_root)

    changed = [
        line for line in _git("diff", "--name-only", parent, head).splitlines() if line
    ]
    allowed_registry = REGISTRY_PATH
    release_prefix = f"data/releases/{release_id}/"
    if not changed:
        raise PublicationCommitError("Publication commit contains no changes")
    unexpected = [
        path
        for path in changed
        if path != allowed_registry and not path.startswith(release_prefix)
    ]
    if unexpected:
        raise PublicationCommitError(
            f"Publication commit contains unrelated changed paths: {unexpected}"
        )
    if allowed_registry not in changed:
        raise PublicationCommitError("Publication commit did not advance the release registry")
    if not any(path.startswith(release_prefix) for path in changed):
        raise PublicationCommitError(
            "Publication commit did not add the immutable release directory"
        )

    return {
        "schema_version": 1,
        "status": "PUBLICATION_COMMIT_VALID",
        "release_id": release_id,
        "publication_commit": head,
        "candidate_commit": parent,
        "rehydration_identity_sha256": identity_sha,
        "changed_paths": changed,
    }


def parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", default="HEAD")
    return parser


def main() -> int:
    args = parser().parse_args()
    try:
        result = validate(args.commit)
    except (PublicationCommitError, ValueError) as exc:
        raise SystemExit(f"Observatory publication commit blocked: {exc}") from exc
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
