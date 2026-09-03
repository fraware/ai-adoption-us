#!/usr/bin/env python3
"""Publish the one-shot Release 1 GitHub tag/release after exact-head gates pass."""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

TAG = "v1.0.0"
RELEASE_NAME = "GenAI at Work — Release 1"
AUTHORIZATION_TITLE = "Authorize Release 1 publication"
REQUIRED_WORKFLOWS = (
    "Release candidate CI",
    "Rendered browser and accessibility QA",
    "Native Safari desktop QA",
    "GitHub Pages Release 1",
)
REQUIRED_CLOSED_ISSUES = (2, 3)
POLL_SECONDS = 10
MAX_POLLS = 180
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class ReleaseError(RuntimeError):
    """Fail-closed publication error."""


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def validate_local_release_contract(root: Path | None = None) -> None:
    """Require the committed Release 1 notes and exactly one final unchecked item."""

    base = root or _root()
    notes = base / "docs" / "RELEASE1_NOTES.md"
    checklist = base / "docs" / "RELEASE_CHECKLIST.md"
    if not notes.is_file() or not notes.read_text(encoding="utf-8").strip():
        raise ReleaseError("Release 1 notes are missing or empty")
    if not checklist.is_file():
        raise ReleaseError("Release checklist is missing")

    unchecked = [
        line.strip()
        for line in checklist.read_text(encoding="utf-8").splitlines()
        if line.lstrip().startswith("- [ ]")
    ]
    if len(unchecked) != 1 or "formal Release 1 tag/release" not in unchecked[0]:
        raise ReleaseError(
            "Release checklist must have exactly one unchecked item: the formal tag/release operation"
        )


def classify_required_workflows(runs: list[dict[str, Any]]) -> tuple[bool, dict[str, str]]:
    """Return whether all required exact-head push workflows are complete and successful."""

    latest: dict[str, dict[str, Any]] = {}
    for run in runs:
        name = run.get("name")
        if name not in REQUIRED_WORKFLOWS or run.get("event") != "push":
            continue
        previous = latest.get(name)
        if previous is None or int(run.get("id", 0)) > int(previous.get("id", 0)):
            latest[name] = run

    states: dict[str, str] = {}
    for name in REQUIRED_WORKFLOWS:
        run = latest.get(name)
        if run is None:
            states[name] = "missing"
            continue
        status = str(run.get("status"))
        conclusion = run.get("conclusion")
        if status == "completed":
            states[name] = str(conclusion)
            if conclusion != "success":
                raise ReleaseError(f"required workflow failed: {name} -> {conclusion}")
        else:
            states[name] = status

    return all(states.get(name) == "success" for name in REQUIRED_WORKFLOWS), states


class GitHubClient:
    def __init__(self, repository: str, token: str) -> None:
        if repository.count("/") != 1:
            raise ReleaseError(f"invalid GITHUB_REPOSITORY: {repository!r}")
        if not token:
            raise ReleaseError("GITHUB_TOKEN is required")
        self.repository = repository
        self.token = token
        self.base = f"https://api.github.com/repos/{repository}"

    def request(
        self,
        path: str,
        *,
        method: str = "GET",
        payload: dict[str, Any] | None = None,
        allowed_statuses: tuple[int, ...] = (200,),
    ) -> tuple[int, Any]:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        req = Request(
            f"{self.base}{path}",
            data=data,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "genai-at-work-release1-publisher",
                "Content-Type": "application/json",
            },
        )
        try:
            with urlopen(req, timeout=30) as response:  # noqa: S310 - fixed GitHub API origin
                status = response.status
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            status = exc.code
            raw = exc.read().decode("utf-8", errors="replace")

        body: Any
        try:
            body = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            body = raw

        if status not in allowed_statuses:
            raise ReleaseError(f"GitHub API {method} {path} returned {status}: {body!r}")
        return status, body


def verify_authorization_commit(client: GitHubClient, sha: str) -> None:
    _, commit = client.request(f"/commits/{sha}")
    message = str(commit["commit"]["message"])
    if message.splitlines()[0] != AUTHORIZATION_TITLE:
        raise ReleaseError(
            f"publication commit title mismatch: {message.splitlines()[0]!r} != {AUTHORIZATION_TITLE!r}"
        )


def verify_release_gate_issues(client: GitHubClient) -> None:
    for issue_number in REQUIRED_CLOSED_ISSUES:
        _, issue = client.request(f"/issues/{issue_number}")
        if issue.get("state") != "closed":
            raise ReleaseError(f"required Release 1 gate issue #{issue_number} is not closed")


def wait_for_workflows(client: GitHubClient, sha: str) -> dict[str, str]:
    query = urlencode({"head_sha": sha, "event": "push", "per_page": 100})
    last_states: dict[str, str] = {}
    for attempt in range(1, MAX_POLLS + 1):
        _, payload = client.request(f"/actions/runs?{query}")
        complete, states = classify_required_workflows(list(payload.get("workflow_runs", [])))
        last_states = states
        print(f"gate poll {attempt}/{MAX_POLLS}: {states}", flush=True)
        if complete:
            return states
        time.sleep(POLL_SECONDS)
    raise ReleaseError(f"timed out waiting for required workflows: {last_states}")


def resolve_tag_target(client: GitHubClient) -> str | None:
    status, ref = client.request(
        f"/git/ref/tags/{TAG}", allowed_statuses=(200, 404)
    )
    if status == 404:
        return None
    obj = ref["object"]
    if obj.get("type") == "commit":
        return str(obj["sha"])
    if obj.get("type") == "tag":
        _, tag = client.request(f"/git/tags/{obj['sha']}")
        target = tag.get("object", {})
        if target.get("type") != "commit":
            raise ReleaseError(f"tag {TAG} does not resolve to a commit")
        return str(target["sha"])
    raise ReleaseError(f"unsupported tag object type for {TAG}: {obj.get('type')!r}")


def get_release(client: GitHubClient) -> dict[str, Any] | None:
    status, release = client.request(
        f"/releases/tags/{TAG}", allowed_statuses=(200, 404)
    )
    return None if status == 404 else dict(release)


def publish_release(client: GitHubClient, sha: str, notes: str) -> dict[str, Any]:
    target = resolve_tag_target(client)
    existing = get_release(client)

    if target is not None and target != sha:
        raise ReleaseError(f"existing {TAG} points to {target}, expected {sha}")
    if existing is not None:
        if target != sha:
            raise ReleaseError(f"existing release {TAG} is not bound to expected commit {sha}")
        if existing.get("draft") or existing.get("prerelease"):
            raise ReleaseError(f"existing {TAG} release is draft or prerelease")
        return existing

    if target is None:
        client.request(
            "/git/refs",
            method="POST",
            payload={"ref": f"refs/tags/{TAG}", "sha": sha},
            allowed_statuses=(201,),
        )

    _, release = client.request(
        "/releases",
        method="POST",
        payload={
            "tag_name": TAG,
            "target_commitish": sha,
            "name": RELEASE_NAME,
            "body": notes,
            "draft": False,
            "prerelease": False,
            "make_latest": "true",
        },
        allowed_statuses=(201,),
    )
    if resolve_tag_target(client) != sha:
        raise ReleaseError(f"post-publication tag verification failed for {TAG}")
    return dict(release)


def write_job_summary(sha: str, states: dict[str, str], release: dict[str, Any]) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    lines = [
        "# Release 1 publication",
        "",
        f"- Tag: `{TAG}`",
        f"- Commit: `{sha}`",
        f"- Release URL: {release.get('html_url', '')}",
        "- Required workflows:",
    ]
    lines.extend(f"  - {name}: {states[name]}" for name in REQUIRED_WORKFLOWS)
    Path(summary_path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    validate_local_release_contract()

    repository = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GITHUB_TOKEN", "")
    sha = os.environ.get("RELEASE_SHA", os.environ.get("GITHUB_SHA", ""))
    if not SHA_RE.fullmatch(sha):
        raise ReleaseError(f"invalid release SHA: {sha!r}")
    if os.environ.get("GITHUB_REF") != "refs/heads/main":
        raise ReleaseError("Release 1 publication is permitted only from refs/heads/main")

    client = GitHubClient(repository, token)
    verify_authorization_commit(client, sha)
    verify_release_gate_issues(client)
    states = wait_for_workflows(client, sha)

    notes = (_root() / "docs" / "RELEASE1_NOTES.md").read_text(encoding="utf-8")
    release = publish_release(client, sha, notes)
    write_job_summary(sha, states, release)
    print(f"Release 1 published: {release.get('html_url', '')}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ReleaseError as exc:
        print(f"Release 1 publication blocked: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
