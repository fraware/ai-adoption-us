"""Verify promotion CI evidence against the GitHub Actions API.

Human review attestations name CI run IDs, but a run ID alone does not establish
that the run succeeded or that it executed for the exact candidate commit. This
module resolves those IDs through GitHub's API and applies a pinned repository
policy before promotion can treat CI as verified evidence.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

import httpx

_COMMIT_RE = re.compile(r"^[0-9a-fA-F]{40}(?:[0-9a-fA-F]{24})?$")


class GithubCiVerificationError(ValueError):
    """Raised when CI evidence cannot be proven for the candidate commit."""


def _canonical_digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _string(value: object, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GithubCiVerificationError(f"{context} must be a non-empty string")
    return value


def _run_id(value: object, context: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise GithubCiVerificationError(f"{context} must be a positive integer")
    return value


def validate_ci_policy(policy: Mapping[str, Any]) -> None:
    """Validate the fail-closed set of workflows accepted for promotion."""

    if policy.get("schema_version") != 1:
        raise GithubCiVerificationError("CI policy schema_version must equal 1")
    _string(policy.get("policy_id"), "CI policy policy_id")
    _string(policy.get("repository"), "CI policy repository")
    _string(policy.get("required_head_branch"), "CI policy required_head_branch")
    workflows = policy.get("required_workflows")
    if not isinstance(workflows, list) or not workflows:
        raise GithubCiVerificationError("CI policy required_workflows must be non-empty")

    paths: set[str] = set()
    for index, raw in enumerate(workflows):
        if not isinstance(raw, Mapping):
            raise GithubCiVerificationError(
                f"CI policy required_workflows[{index}] must be an object"
            )
        path = _string(raw.get("path"), f"CI policy required_workflows[{index}].path")
        _string(raw.get("name"), f"CI policy required_workflows[{index}].name")
        if path in paths:
            raise GithubCiVerificationError(f"Duplicate required CI workflow path: {path}")
        paths.add(path)
        events = raw.get("allowed_events")
        if (
            not isinstance(events, list)
            or not events
            or not all(isinstance(event, str) and event for event in events)
            or len(set(events)) != len(events)
        ):
            raise GithubCiVerificationError(
                f"CI policy required_workflows[{index}].allowed_events is invalid"
            )


def verify_ci_run_payloads(
    payloads: Sequence[Mapping[str, Any]],
    *,
    run_ids: Sequence[int],
    candidate_commit: str,
    policy: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate API-returned workflow runs against one exact candidate commit."""

    validate_ci_policy(policy)
    if _COMMIT_RE.fullmatch(candidate_commit) is None:
        raise GithubCiVerificationError(
            "candidate_commit must be a 40- or 64-character hexadecimal Git commit"
        )
    expected_commit = candidate_commit.lower()
    expected_ids = [_run_id(value, "ci_run_ids entry") for value in run_ids]
    if len(set(expected_ids)) != len(expected_ids):
        raise GithubCiVerificationError("ci_run_ids contains duplicates")
    if len(payloads) != len(expected_ids):
        raise GithubCiVerificationError("CI API evidence count does not match ci_run_ids")

    repository = _string(policy.get("repository"), "CI policy repository")
    required_branch = _string(
        policy.get("required_head_branch"), "CI policy required_head_branch"
    )
    raw_required = policy.get("required_workflows")
    assert isinstance(raw_required, list)
    required = {
        str(row["path"]): row for row in raw_required if isinstance(row, Mapping)
    }

    observed_paths: set[str] = set()
    normalized_runs: list[dict[str, Any]] = []
    for expected_id, payload in zip(expected_ids, payloads, strict=True):
        run_id = _run_id(payload.get("id"), "GitHub workflow run id")
        if run_id != expected_id:
            raise GithubCiVerificationError(
                f"GitHub workflow run ID mismatch: expected {expected_id}, observed {run_id}"
            )
        repo_payload = payload.get("repository")
        if not isinstance(repo_payload, Mapping) or repo_payload.get("full_name") != repository:
            raise GithubCiVerificationError(
                f"CI run {run_id} does not belong to repository {repository}"
            )
        head_sha = _string(payload.get("head_sha"), f"CI run {run_id} head_sha").lower()
        if head_sha != expected_commit:
            raise GithubCiVerificationError(
                f"CI run {run_id} head_sha does not match candidate_commit"
            )
        if payload.get("head_branch") != required_branch:
            raise GithubCiVerificationError(
                f"CI run {run_id} did not execute on required branch {required_branch}"
            )
        if payload.get("status") != "completed" or payload.get("conclusion") != "success":
            raise GithubCiVerificationError(f"CI run {run_id} is not completed successfully")

        path = _string(payload.get("path"), f"CI run {run_id} path")
        rule = required.get(path)
        if rule is None:
            raise GithubCiVerificationError(
                f"CI run {run_id} uses unapproved workflow path {path}"
            )
        if path in observed_paths:
            raise GithubCiVerificationError(f"Multiple CI runs supplied for workflow {path}")
        observed_paths.add(path)
        if payload.get("name") != rule.get("name"):
            raise GithubCiVerificationError(
                f"CI run {run_id} workflow name does not match pinned policy"
            )
        allowed_events = rule.get("allowed_events")
        assert isinstance(allowed_events, list)
        if payload.get("event") not in allowed_events:
            raise GithubCiVerificationError(
                f"CI run {run_id} event is not allowed by promotion policy"
            )
        attempt = payload.get("run_attempt")
        if not isinstance(attempt, int) or isinstance(attempt, bool) or attempt < 1:
            raise GithubCiVerificationError(f"CI run {run_id} has invalid run_attempt")

        normalized_runs.append(
            {
                "id": run_id,
                "name": payload["name"],
                "path": path,
                "event": payload["event"],
                "head_branch": payload["head_branch"],
                "head_sha": head_sha,
                "status": payload["status"],
                "conclusion": payload["conclusion"],
                "run_attempt": attempt,
            }
        )

    missing = sorted(set(required) - observed_paths)
    if missing:
        raise GithubCiVerificationError(
            f"CI evidence is missing required workflow runs: {missing}"
        )
    extra = sorted(observed_paths - set(required))
    if extra:
        raise GithubCiVerificationError(f"CI evidence contains unexpected workflows: {extra}")

    normalized_runs.sort(key=lambda row: str(row["path"]))
    evidence: dict[str, Any] = {
        "schema_version": 1,
        "policy_id": policy["policy_id"],
        "repository": repository,
        "candidate_commit": expected_commit,
        "run_ids": sorted(expected_ids),
        "runs": normalized_runs,
        "verification_status": "pass",
    }
    evidence["evidence_digest"] = _canonical_digest(evidence)
    return evidence


def fetch_and_verify_github_ci(
    *,
    repository: str,
    run_ids: Sequence[int],
    candidate_commit: str,
    token: str,
    policy: Mapping[str, Any],
    api_url: str = "https://api.github.com",
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    """Resolve run IDs through GitHub and return normalized verified evidence."""

    validate_ci_policy(policy)
    if repository != policy.get("repository"):
        raise GithubCiVerificationError(
            "Requested GitHub repository does not match the pinned CI policy"
        )
    if not token.strip():
        raise GithubCiVerificationError("A GitHub token is required to verify CI evidence")
    base = api_url.rstrip("/")
    own_client = client is None
    http = client or httpx.Client(
        timeout=httpx.Timeout(20.0),
        follow_redirects=False,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        payloads: list[Mapping[str, Any]] = []
        for raw_id in run_ids:
            run_id = _run_id(raw_id, "ci_run_ids entry")
            response = http.get(f"{base}/repos/{repository}/actions/runs/{run_id}")
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise GithubCiVerificationError(
                    f"GitHub API could not verify CI run {run_id}: HTTP {response.status_code}"
                ) from exc
            value = response.json()
            if not isinstance(value, Mapping):
                raise GithubCiVerificationError(
                    f"GitHub API returned invalid evidence for CI run {run_id}"
                )
            payloads.append(value)
        return verify_ci_run_payloads(
            payloads,
            run_ids=run_ids,
            candidate_commit=candidate_commit,
            policy=policy,
        )
    finally:
        if own_client:
            http.close()
