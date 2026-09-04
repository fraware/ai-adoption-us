#!/usr/bin/env python3
"""Validate a presentation-only publication over the current promoted Observatory evidence.

This gate is separate from Observatory release promotion. It permits a canonical
main commit to publish revised public presentation and QA surfaces only when the
current promoted evidence release, its registry binding, and every immutable
release artifact remain unchanged from the release-authorization commit.
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
REGISTRY_PATH = "data/registry/observatory_release_registry.json"
RELEASE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")

# Public presentation surfaces may change without advancing the evidence release.
# Runtime data loaders, build/dependency configuration, source registries, release
# artifacts, and analytical code are intentionally absent.
ALLOWED_EXACT_PATHS = {
    ".github/workflows/pages.yml",
    "apps/web/app/design.css",
    "apps/web/app/layout.tsx",
    "apps/web/app/page.tsx",
    "apps/web/scripts/native-safari-qa.mjs",
    "scripts/validate_content_publication_commit.py",
}
ALLOWED_PREFIXES = (
    "apps/web/app/blog/",
    "apps/web/app/explore/",
    "apps/web/app/methodology/",
    "apps/web/app/sources/",
    "apps/web/components/",
    "apps/web/tests/",
    "tests/",
)


class ContentPublicationError(RuntimeError):
    """Raised when a presentation-only publication violates evidence boundaries."""


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
        raise ContentPublicationError(f"Git command failed: {' '.join(args)}") from exc


def _git_json(commit: str, path: str) -> dict[str, Any]:
    try:
        payload = _git("show", f"{commit}:{path}")
        value = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ContentPublicationError(f"JSON file {path} is invalid at {commit}") from exc
    if not isinstance(value, dict):
        raise ContentPublicationError(f"JSON file {path} must be an object at {commit}")
    return {str(key): item for key, item in value.items()}


def _path_allowed(path: str) -> bool:
    return path in ALLOWED_EXACT_PATHS or any(path.startswith(prefix) for prefix in ALLOWED_PREFIXES)


def _authorization_commit(release_id: str) -> str:
    expected_subject = f"Authorize Observatory release {release_id}"
    rows = _git("log", "--format=%H%x09%s", "--", REGISTRY_PATH).splitlines()
    matches = [row.split("\t", 1)[0] for row in rows if row.endswith(f"\t{expected_subject}")]
    if len(matches) != 1:
        raise ContentPublicationError(
            f"Expected exactly one authorization commit for {release_id}; found {len(matches)}"
        )
    return matches[0].lower()


def _validate_release_artifacts(release_id: str, manifest_sha: str) -> None:
    release_root = RELEASES_ROOT / release_id
    manifest_path = release_root / "release_manifest.json"
    if not manifest_path.is_file() or sha256_file(manifest_path) != manifest_sha:
        raise ContentPublicationError("Current promoted release manifest checksum mismatch")
    manifest = load_json_object(manifest_path)
    if manifest.get("release_id") != release_id:
        raise ContentPublicationError("Current promoted manifest release_id mismatch")
    if manifest.get("release_status") != "PROMOTED_AFTER_EXPLICIT_REVIEW":
        raise ContentPublicationError("Current promoted manifest lacks explicit-review status")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ContentPublicationError("Current promoted release has no artifacts")
    for row in artifacts:
        if not isinstance(row, dict):
            raise ContentPublicationError("Current promoted release has an invalid artifact row")
        relative = row.get("path")
        expected = row.get("sha256")
        if not isinstance(relative, str) or not relative.startswith("artifacts/"):
            raise ContentPublicationError("Current promoted artifact path is invalid")
        if ".." in Path(relative).parts:
            raise ContentPublicationError("Current promoted artifact path escapes release root")
        path = release_root / relative
        if not path.is_file() or not isinstance(expected, str) or sha256_file(path) != expected:
            raise ContentPublicationError(f"Current promoted artifact checksum mismatch: {relative}")


def validate(commit: str) -> dict[str, Any]:
    target = _git("rev-parse", commit).lower()
    registry = load_json_object(REGISTRY)
    release_id = registry.get("current_release_id")
    manifest_sha = registry.get("current_release_manifest_sha256")

    if registry.get("status") != "CURRENT_RELEASE_PROMOTED":
        raise ContentPublicationError("Release registry is not in CURRENT_RELEASE_PROMOTED state")
    if not isinstance(release_id, str) or RELEASE_ID_RE.fullmatch(release_id) is None:
        raise ContentPublicationError("Release registry current_release_id is invalid")
    if not isinstance(manifest_sha, str) or len(manifest_sha) != 64:
        raise ContentPublicationError("Release registry manifest hash is invalid")

    authorization = _authorization_commit(release_id)
    try:
        _git("merge-base", "--is-ancestor", authorization, target)
    except ContentPublicationError as exc:
        raise ContentPublicationError(
            "Content publication target does not descend from the current release authorization"
        ) from exc

    authorization_registry = _git_json(authorization, REGISTRY_PATH)
    if authorization_registry != registry:
        raise ContentPublicationError(
            "Release registry changed after the current evidence release authorization"
        )

    release_prefix = f"data/releases/{release_id}/"
    release_diff = _git("diff", "--name-only", authorization, target, "--", release_prefix)
    if release_diff:
        raise ContentPublicationError(
            "Current immutable release directory changed after evidence authorization"
        )

    _validate_release_artifacts(release_id, manifest_sha)

    changed = [
        line for line in _git("diff", "--name-only", authorization, target).splitlines() if line
    ]
    unexpected = [path for path in changed if not _path_allowed(path)]
    if unexpected:
        raise ContentPublicationError(
            f"Content publication contains deploy-sensitive or non-presentation changes: {unexpected}"
        )

    return {
        "schema_version": 1,
        "status": "CONTENT_PUBLICATION_VALID",
        "content_commit": target,
        "evidence_release_id": release_id,
        "evidence_manifest_sha256": manifest_sha,
        "evidence_authorization_commit": authorization,
        "changed_paths": changed,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--commit", default="HEAD")
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        result = validate(args.commit)
    except (ContentPublicationError, ValueError) as exc:
        raise SystemExit(f"Content publication blocked: {exc}") from exc
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
