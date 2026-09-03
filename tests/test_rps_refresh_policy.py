from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from genai_at_work.rps_refresh_policy import (
    RpsRefreshPolicyError,
    action_for_refresh_summary,
    activation_gates_satisfied,
    recorded_activation_gates,
    validate_rps_refresh_policy,
)

ROOT = Path(__file__).parents[1]
POLICY = ROOT / "data" / "registry" / "rps_refresh_policy.json"


def policy() -> dict[str, Any]:
    return json.loads(POLICY.read_text())


def summary(
    status: str,
    *,
    new_observations: int = 0,
    revised_observations: int = 0,
    removed_observations: int = 0,
    definition_changes: int = 0,
) -> dict[str, Any]:
    changed = status != "unchanged"
    return {
        "schema_version": 1,
        "candidate_type": "rps_published_aggregate_refresh",
        "source_id": "rps-genai-tracker-fred-release-6",
        "retrieved_at": "2026-09-02T12:00:00Z",
        "content_sha256": "a" * 64,
        "snapshot_file_sha256": "b" * 64,
        "previous_content_sha256": None,
        "revision_status": status,
        "requires_release_review": changed,
        "inventory": {
            "provider_series_count": 137,
            "observatory_series_count": 131,
            "excluded_series_count": 6,
            "provider_inventory_status": "pass",
        },
        "observation_count": 1048,
        "change_counts": {
            "new_observations": new_observations,
            "revised_observations": revised_observations,
            "removed_observations": removed_observations,
            "definition_changes": definition_changes,
        },
        "promotion_state": "source-candidate-only",
        "public_raw_observations_included": False,
    }


def test_pinned_policy_is_valid_and_scheduled_activation_remains_deferred() -> None:
    value = policy()
    validate_rps_refresh_policy(value)
    assert value["policy_status"] == "PINNED_NOT_ACTIVATED"
    assert value["source_check"] == {
        "cadence": "weekly",
        "weekday": "Wednesday",
        "time_utc": "18:00",
        "maximum_nominal_detection_lag_days": 7,
        "schedule_activation": "deferred",
        "activation_requirements": [
            "successful_live_validation",
            "fred_api_key_verified_in_execution_environment",
            "operator_controlled_private_vintage_backend_configured",
            "private_backend_write_read_verify_rehearsal_passed",
        ],
        "rationale": value["source_check"]["rationale"],
    }
    assert value["publication"]["automatic"] is False


def test_recorded_activation_evidence_has_exact_two_passed_runtime_gates() -> None:
    value = policy()
    assert recorded_activation_gates(value) == {
        "successful_live_validation",
        "fred_api_key_verified_in_execution_environment",
    }
    live = value["activation_evidence"]["successful_live_validation"]
    assert live == {
        "status": "passed",
        "github_run_id": 33687737639,
        "github_sha": "3fb2cff4a9b1cbc2f340c8db00328efaa2c30130",
        "workflow": "RPS live validation",
        "artifact_id": 9868969207,
        "artifact_digest": "sha256:fd8b4ed3f828755efaaa00c80b7d444480f7d0e058b88dddf2ffae8f17539de7",
        "source_content_sha256": "fe8bffa7cacd029cc23e2ba7e310d925e8c05322f6d53bd89e8234f02e825b73",
        "source_snapshot_file_sha256": "66b3ffbaebf43c3c8434556eec9329a232d8f17483ba3a613e6b00d214af3f74",
        "retrieved_at": "2026-09-02T21:56:17.680314Z",
        "revision_status": "baseline",
        "provider_series_count": 137,
        "observatory_series_count": 131,
        "excluded_series_count": 6,
        "observation_count": 962,
        "archive_contract_rehearsed": True,
        "archive_persisted_durably": False,
        "verified_on": "2026-09-03",
    }
    credential = value["activation_evidence"][
        "fred_api_key_verified_in_execution_environment"
    ]
    assert credential["status"] == "passed"
    assert credential["github_run_id"] == live["github_run_id"]
    assert (
        value["activation_evidence"][
            "operator_controlled_private_vintage_backend_configured"
        ]["status"]
        == "pending"
    )
    assert (
        value["activation_evidence"][
            "private_backend_write_read_verify_rehearsal_passed"
        ]["status"]
        == "pending"
    )
    assert activation_gates_satisfied(value, recorded_activation_gates(value)) is False


def test_activation_requires_every_exact_gate() -> None:
    value = policy()
    gates = value["source_check"]["activation_requirements"]
    assert activation_gates_satisfied(value, gates) is True
    assert activation_gates_satisfied(value, gates[:-1]) is False
    assert activation_gates_satisfied(value, [*gates, "invented_gate"]) is False


def test_activation_evidence_inventory_and_dependencies_fail_closed() -> None:
    missing = copy.deepcopy(policy())
    del missing["activation_evidence"][
        "private_backend_write_read_verify_rehearsal_passed"
    ]
    with pytest.raises(
        RpsRefreshPolicyError,
        match="exactly cover every pinned activation requirement",
    ):
        validate_rps_refresh_policy(missing)

    credential_without_live = copy.deepcopy(policy())
    credential_without_live["activation_evidence"]["successful_live_validation"] = {
        "status": "pending",
        "reason": "synthetic pending state",
    }
    with pytest.raises(
        RpsRefreshPolicyError,
        match="credential evidence cannot pass before successful live validation",
    ):
        validate_rps_refresh_policy(credential_without_live)

    mismatched_run = copy.deepcopy(policy())
    mismatched_run["activation_evidence"][
        "fred_api_key_verified_in_execution_environment"
    ]["github_run_id"] = 33687737640
    with pytest.raises(
        RpsRefreshPolicyError,
        match="must be bound to the successful live-validation run",
    ):
        validate_rps_refresh_policy(mismatched_run)

    inconsistent_inventory = copy.deepcopy(policy())
    inconsistent_inventory["activation_evidence"]["successful_live_validation"][
        "provider_series_count"
    ] = 138
    with pytest.raises(
        RpsRefreshPolicyError,
        match="series inventory does not reconcile",
    ):
        validate_rps_refresh_policy(inconsistent_inventory)

    false_durable_claim = copy.deepcopy(policy())
    false_durable_claim["activation_evidence"]["successful_live_validation"][
        "archive_persisted_durably"
    ] = True
    with pytest.raises(
        RpsRefreshPolicyError,
        match="cannot be recorded as durable archive persistence",
    ):
        validate_rps_refresh_policy(false_durable_claim)

    rehearsal_without_backend = copy.deepcopy(policy())
    rehearsal_without_backend["activation_evidence"][
        "private_backend_write_read_verify_rehearsal_passed"
    ] = {
        "status": "passed",
        "rehearsal_id": "synthetic-rehearsal",
        "write_read_verify_evidence_ref": "synthetic-evidence",
        "verified_on": "2026-09-03",
    }
    with pytest.raises(
        RpsRefreshPolicyError,
        match="cannot pass before backend configuration",
    ):
        validate_rps_refresh_policy(rehearsal_without_backend)


def test_unchanged_source_retains_only_review_safe_check_evidence() -> None:
    action = action_for_refresh_summary(policy(), summary("unchanged"))
    assert action == {
        "action": "NO_SOURCE_CHANGE",
        "archive_exact_source_bytes": False,
        "build_observatory_candidate": False,
        "stage_release": False,
        "publish_release": False,
        "requires_human_review": False,
        "retain_review_safe_check_evidence": True,
    }


def test_new_wave_archives_builds_and_requires_review_without_staging_or_publication() -> None:
    action = action_for_refresh_summary(
        policy(),
        summary("new_wave", new_observations=131),
    )
    assert action == {
        "action": "ARCHIVE_BUILD_AND_REVIEW",
        "archive_exact_source_bytes": True,
        "build_observatory_candidate": True,
        "stage_release": False,
        "publish_release": False,
        "requires_human_review": True,
        "retain_private_detailed_diff": True,
    }


def test_baseline_archives_and_builds_without_claiming_predecessor_diff() -> None:
    action = action_for_refresh_summary(
        policy(),
        summary("baseline", new_observations=1048),
    )
    assert action["action"] == "ARCHIVE_BUILD_AND_REVIEW"
    assert action["archive_exact_source_bytes"] is True
    assert action["build_observatory_candidate"] is True
    assert action["retain_private_detailed_diff"] is False
    assert action["stage_release"] is False
    assert action["publish_release"] is False


def test_definition_change_is_archived_then_blocked_from_ordinary_candidate_path() -> None:
    action = action_for_refresh_summary(
        policy(),
        summary("mixed", new_observations=131, definition_changes=1),
    )
    assert action == {
        "action": "ARCHIVE_AND_BLOCK_DEFINITION_REVIEW",
        "archive_exact_source_bytes": True,
        "build_observatory_candidate": False,
        "stage_release": False,
        "publish_release": False,
        "requires_human_review": True,
        "retain_private_detailed_diff": True,
    }


def test_policy_and_summary_contradictions_fail_closed() -> None:
    invalid = copy.deepcopy(policy())
    invalid["publication"]["automatic"] = True
    with pytest.raises(RpsRefreshPolicyError, match="may never be automatic"):
        validate_rps_refresh_policy(invalid)

    with pytest.raises(RpsRefreshPolicyError, match="contradicts"):
        action_for_refresh_summary(
            policy(),
            summary("unchanged", revised_observations=1),
        )

    changed_without_counts = summary("revision")
    with pytest.raises(RpsRefreshPolicyError, match="zero recorded changes"):
        action_for_refresh_summary(policy(), changed_without_counts)


def test_live_validation_can_run_automatically_without_enabling_periodic_schedule() -> None:
    workflow = (ROOT / ".github" / "workflows" / "rps-live-validation.yml").read_text()
    assert "push:" in workflow
    assert "branches: [main]" in workflow
    assert "workflow_dispatch:" in workflow
    assert "schedule:" not in workflow
    assert "cron:" not in workflow
    assert policy()["source_check"]["schedule_activation"] == "deferred"
