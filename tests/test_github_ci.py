from __future__ import annotations

from typing import Any

import httpx
import pytest

from genai_at_work.github_ci import (
    GithubCiVerificationError,
    fetch_and_verify_github_ci,
    verify_ci_run_payloads,
)

COMMIT = "0123456789abcdef0123456789abcdef01234567"
POLICY: dict[str, Any] = {
    "schema_version": 1,
    "policy_id": "observatory-release-ci-v1",
    "repository": "fraware/ai-adoption-us",
    "required_head_branch": "main",
    "required_workflows": [
        {
            "name": "Release candidate CI",
            "path": ".github/workflows/ci.yml",
            "allowed_events": ["push"],
        }
    ],
}


def _run_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": 12345,
        "name": "Release candidate CI",
        "path": ".github/workflows/ci.yml",
        "event": "push",
        "head_branch": "main",
        "head_sha": COMMIT,
        "status": "completed",
        "conclusion": "success",
        "run_attempt": 1,
        "repository": {"full_name": "fraware/ai-adoption-us"},
    }
    payload.update(overrides)
    return payload


def test_exact_successful_run_is_normalized_and_digest_bound() -> None:
    evidence = verify_ci_run_payloads(
        [_run_payload()],
        run_ids=[12345],
        candidate_commit=COMMIT,
        policy=POLICY,
    )
    assert evidence["verification_status"] == "pass"
    assert evidence["candidate_commit"] == COMMIT
    assert evidence["run_ids"] == [12345]
    assert evidence["runs"][0]["path"] == ".github/workflows/ci.yml"
    assert len(evidence["evidence_digest"]) == 64


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"head_sha": "f" * 40}, "head_sha"),
        ({"head_branch": "feature"}, "required branch"),
        ({"status": "in_progress", "conclusion": None}, "completed successfully"),
        ({"conclusion": "failure"}, "completed successfully"),
        ({"path": ".github/workflows/other.yml"}, "unapproved workflow"),
        ({"name": "Different workflow"}, "workflow name"),
        ({"event": "pull_request"}, "event is not allowed"),
        ({"repository": {"full_name": "other/repo"}}, "does not belong"),
    ],
)
def test_mismatched_ci_evidence_fails_closed(
    override: dict[str, Any],
    message: str,
) -> None:
    with pytest.raises(GithubCiVerificationError, match=message):
        verify_ci_run_payloads(
            [_run_payload(**override)],
            run_ids=[12345],
            candidate_commit=COMMIT,
            policy=POLICY,
        )


def test_duplicate_or_missing_run_ids_fail_closed() -> None:
    with pytest.raises(GithubCiVerificationError, match="duplicates"):
        verify_ci_run_payloads(
            [_run_payload(), _run_payload()],
            run_ids=[12345, 12345],
            candidate_commit=COMMIT,
            policy=POLICY,
        )
    with pytest.raises(GithubCiVerificationError, match="count"):
        verify_ci_run_payloads(
            [],
            run_ids=[12345],
            candidate_commit=COMMIT,
            policy=POLICY,
        )


def test_api_fetch_is_part_of_verification_boundary() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/actions/runs/12345")
        return httpx.Response(200, json=_run_payload())

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        evidence = fetch_and_verify_github_ci(
            repository="fraware/ai-adoption-us",
            run_ids=[12345],
            candidate_commit=COMMIT,
            token="synthetic-token",
            policy=POLICY,
            api_url="https://api.github.test",
            client=client,
        )
    assert evidence["verification_status"] == "pass"


def test_api_failure_cannot_be_reinterpreted_as_pass() -> None:
    with httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(404, json={}))
    ) as client:
        with pytest.raises(GithubCiVerificationError, match="HTTP 404"):
            fetch_and_verify_github_ci(
                repository="fraware/ai-adoption-us",
                run_ids=[12345],
                candidate_commit=COMMIT,
                token="synthetic-token",
                policy=POLICY,
                api_url="https://api.github.test",
                client=client,
            )
