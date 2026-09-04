#!/usr/bin/env python3
"""Validate the one-commit transition from reviewed candidate to public release.

A publication commit is permitted to add only the immutable promoted release and
advance the release registry. Its parent must be the exact candidate commit named
in the human review record. This prevents unrelated code, claims, or source files
from hitchhiking on the release authorization commit.
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


def validate(commit: str) -> dict[str, Any]:
    head = _git("rev-parse", commit).lower()
    parent = _git("rev-parse", f"{head}^").lower()
    subject = _git("show", "-s", "--format=%s", head)

    registry = load_json_object(REGISTRY)
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
        raise PublicationCommitError("Promoted release is missing manifest, review record, or rehydration identity")
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
            "Publication commit parent is not the exact human-reviewed candidate commit"
        )
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

    _artifact_hashes(manifest, release_root)

    changed = [
        line
        for line in _git("diff", "--name-only", parent, head).splitlines()
        if line
    ]
    allowed_registry = "data/registry/observatory_release_registry.json"
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
        raise PublicationCommitError("Publication commit did not add the immutable release directory")

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
