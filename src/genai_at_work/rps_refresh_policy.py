"""Executable policy contract for RPS source checking versus release actions."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

_ALLOWED_REFRESH_STATUSES = {"baseline", "unchanged", "new_wave", "revision", "mixed"}
_REQUIRED_ACTIVATION_GATES = {
    "successful_live_validation",
    "fred_api_key_verified_in_execution_environment",
    "operator_controlled_private_vintage_backend_configured",
    "private_backend_write_read_verify_rehearsal_passed",
}
_ALLOWED_ACTIVATION_EVIDENCE_STATUSES = {"passed", "pending"}
_TIME_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")
_COMMIT_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_ARTIFACT_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class RpsRefreshPolicyError(ValueError):
    """Raised when the pinned RPS operational policy is invalid or contradicted."""


def _mapping(value: object, *, context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise RpsRefreshPolicyError(f"{context} must be an object")
    return value


def _string(mapping: Mapping[str, Any], key: str, *, context: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RpsRefreshPolicyError(f"{context}.{key} must be a non-empty string")
    return value


def _bool(mapping: Mapping[str, Any], key: str, *, context: str) -> bool:
    value = mapping.get(key)
    if not isinstance(value, bool):
        raise RpsRefreshPolicyError(f"{context}.{key} must be boolean")
    return value


def _positive_int(mapping: Mapping[str, Any], key: str, *, context: str) -> int:
    value = mapping.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise RpsRefreshPolicyError(f"{context}.{key} must be a positive integer")
    return value


def _nonnegative_int(mapping: Mapping[str, Any], key: str, *, context: str) -> int:
    value = mapping.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise RpsRefreshPolicyError(f"{context}.{key} must be a non-negative integer")
    return value


def _strings(mapping: Mapping[str, Any], key: str, *, context: str) -> list[str]:
    value = mapping.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise RpsRefreshPolicyError(f"{context}.{key} must be a list of non-empty strings")
    return list(value)


def _hex64(mapping: Mapping[str, Any], key: str, *, context: str) -> str:
    value = _string(mapping, key, context=context).lower()
    if _HEX64_RE.fullmatch(value) is None:
        raise RpsRefreshPolicyError(f"{context}.{key} must be a 64-character SHA-256 digest")
    return value


def _validate_activation_evidence(policy: Mapping[str, Any]) -> set[str]:
    evidence = _mapping(policy.get("activation_evidence"), context="policy.activation_evidence")
    if set(evidence) != _REQUIRED_ACTIVATION_GATES:
        raise RpsRefreshPolicyError(
            "policy.activation_evidence must exactly cover every pinned activation requirement"
        )

    rows: dict[str, Mapping[str, Any]] = {}
    statuses: dict[str, str] = {}
    for gate in sorted(_REQUIRED_ACTIVATION_GATES):
        row = _mapping(evidence.get(gate), context=f"policy.activation_evidence.{gate}")
        status = _string(row, "status", context=f"policy.activation_evidence.{gate}")
        if status not in _ALLOWED_ACTIVATION_EVIDENCE_STATUSES:
            raise RpsRefreshPolicyError(
                f"Unsupported activation evidence status for {gate}: {status}"
            )
        if status == "pending":
            _string(row, "reason", context=f"policy.activation_evidence.{gate}")
        rows[gate] = row
        statuses[gate] = status

    live = rows["successful_live_validation"]
    if statuses["successful_live_validation"] == "passed":
        live_context = "policy.activation_evidence.successful_live_validation"
        live_run_id = _positive_int(live, "github_run_id", context=live_context)
        live_sha = _string(live, "github_sha", context=live_context).lower()
        if _COMMIT_RE.fullmatch(live_sha) is None:
            raise RpsRefreshPolicyError(
                "successful_live_validation.github_sha must be a Git commit digest"
            )
        if _string(live, "workflow", context=live_context) != "RPS live validation":
            raise RpsRefreshPolicyError(
                "successful_live_validation.workflow must identify the canonical RPS live validation workflow"
            )
        _positive_int(live, "artifact_id", context=live_context)
        artifact_digest = _string(live, "artifact_digest", context=live_context).lower()
        if _ARTIFACT_DIGEST_RE.fullmatch(artifact_digest) is None:
            raise RpsRefreshPolicyError(
                "successful_live_validation.artifact_digest must be a sha256: digest"
            )
        _hex64(live, "source_content_sha256", context=live_context)
        _hex64(live, "source_snapshot_file_sha256", context=live_context)
        _string(live, "retrieved_at", context=live_context)
        if _string(live, "revision_status", context=live_context) not in _ALLOWED_REFRESH_STATUSES:
            raise RpsRefreshPolicyError(
                "successful_live_validation.revision_status is unsupported"
            )
        provider_count = _positive_int(live, "provider_series_count", context=live_context)
        observatory_count = _positive_int(live, "observatory_series_count", context=live_context)
        excluded_count = _nonnegative_int(live, "excluded_series_count", context=live_context)
        if provider_count != observatory_count + excluded_count:
            raise RpsRefreshPolicyError(
                "successful_live_validation series inventory does not reconcile"
            )
        _positive_int(live, "observation_count", context=live_context)
        if _bool(live, "archive_contract_rehearsed", context=live_context) is not True:
            raise RpsRefreshPolicyError(
                "successful live validation must record archive_contract_rehearsed=true"
            )
        if _bool(live, "archive_persisted_durably", context=live_context) is not False:
            raise RpsRefreshPolicyError(
                "transient live validation cannot be recorded as durable archive persistence"
            )
        _string(live, "verified_on", context=live_context)
    else:
        live_run_id = None

    credential = rows["fred_api_key_verified_in_execution_environment"]
    if statuses["fred_api_key_verified_in_execution_environment"] == "passed":
        credential_context = (
            "policy.activation_evidence.fred_api_key_verified_in_execution_environment"
        )
        credential_run_id = _positive_int(
            credential,
            "github_run_id",
            context=credential_context,
        )
        _string(credential, "evidence_basis", context=credential_context)
        _string(credential, "verified_on", context=credential_context)
        if statuses["successful_live_validation"] != "passed":
            raise RpsRefreshPolicyError(
                "FRED credential evidence cannot pass before successful live validation"
            )
        if live_run_id != credential_run_id:
            raise RpsRefreshPolicyError(
                "FRED credential evidence must be bound to the successful live-validation run"
            )

    backend = rows["operator_controlled_private_vintage_backend_configured"]
    if statuses["operator_controlled_private_vintage_backend_configured"] == "passed":
        backend_context = (
            "policy.activation_evidence.operator_controlled_private_vintage_backend_configured"
        )
        _string(backend, "backend_id", context=backend_context)
        _string(backend, "configuration_evidence_ref", context=backend_context)
        _string(backend, "verified_on", context=backend_context)

    rehearsal = rows["private_backend_write_read_verify_rehearsal_passed"]
    if statuses["private_backend_write_read_verify_rehearsal_passed"] == "passed":
        if statuses["operator_controlled_private_vintage_backend_configured"] != "passed":
            raise RpsRefreshPolicyError(
                "Private backend rehearsal cannot pass before backend configuration"
            )
        rehearsal_context = (
            "policy.activation_evidence.private_backend_write_read_verify_rehearsal_passed"
        )
        _string(rehearsal, "rehearsal_id", context=rehearsal_context)
        _string(
            rehearsal,
            "write_read_verify_evidence_ref",
            context=rehearsal_context,
        )
        _string(rehearsal, "verified_on", context=rehearsal_context)

    return {gate for gate, status in statuses.items() if status == "passed"}


def validate_rps_refresh_policy(policy: Mapping[str, Any]) -> None:
    """Validate the pinned source-check, retention, publication, and activation evidence."""

    if policy.get("schema_version") != 1:
        raise RpsRefreshPolicyError("policy.schema_version must equal 1")
    _string(policy, "source_id", context="policy")
    if _string(policy, "policy_status", context="policy") != "PINNED_NOT_ACTIVATED":
        raise RpsRefreshPolicyError("RPS refresh policy must remain PINNED_NOT_ACTIVATED until gates pass")

    evidence = _mapping(policy.get("evidence_basis"), context="policy.evidence_basis")
    if _string(evidence, "source_frequency", context="policy.evidence_basis") != "quarterly":
        raise RpsRefreshPolicyError("Registered RPS source frequency must remain quarterly")
    if _string(evidence, "provider_next_release_date_status", context="policy.evidence_basis") != "not_available":
        raise RpsRefreshPolicyError("Pinned cadence assumes no provider next-release date is available")

    check = _mapping(policy.get("source_check"), context="policy.source_check")
    if _string(check, "cadence", context="policy.source_check") != "weekly":
        raise RpsRefreshPolicyError("RPS source-check cadence must be weekly")
    if _string(check, "weekday", context="policy.source_check") != "Wednesday":
        raise RpsRefreshPolicyError("RPS source-check weekday must be Wednesday")
    if _TIME_RE.fullmatch(_string(check, "time_utc", context="policy.source_check")) is None:
        raise RpsRefreshPolicyError("policy.source_check.time_utc must be HH:MM")
    lag = check.get("maximum_nominal_detection_lag_days")
    if not isinstance(lag, int) or isinstance(lag, bool) or lag != 7:
        raise RpsRefreshPolicyError("Weekly RPS checks require maximum_nominal_detection_lag_days=7")
    if _string(check, "schedule_activation", context="policy.source_check") != "deferred":
        raise RpsRefreshPolicyError("Scheduled RPS retrieval must remain deferred until activation gates pass")
    gates = set(_strings(check, "activation_requirements", context="policy.source_check"))
    if gates != _REQUIRED_ACTIVATION_GATES:
        raise RpsRefreshPolicyError(
            "RPS schedule activation requirements must exactly cover live validation, credential, private backend, and backend rehearsal"
        )
    _validate_activation_evidence(policy)

    unchanged = _mapping(policy.get("unchanged_source"), context="policy.unchanged_source")
    for key in (
        "archive_exact_source_bytes",
        "build_observatory_candidate",
        "stage_release",
        "publish_release",
    ):
        if _bool(unchanged, key, context="policy.unchanged_source"):
            raise RpsRefreshPolicyError(f"Unchanged-source policy must keep {key}=false")
    if not _bool(unchanged, "retain_review_safe_check_evidence", context="policy.unchanged_source"):
        raise RpsRefreshPolicyError("Unchanged checks must retain review-safe check evidence")

    changed = _mapping(policy.get("changed_source"), context="policy.changed_source")
    statuses = set(_strings(changed, "statuses", context="policy.changed_source"))
    if statuses != {"baseline", "new_wave", "revision", "mixed"}:
        raise RpsRefreshPolicyError("Changed-source statuses must exactly cover baseline/new_wave/revision/mixed")
    for key in (
        "archive_exact_source_bytes_privately",
        "retain_private_detailed_diff_when_predecessor_exists",
        "build_observatory_candidate",
        "requires_human_scientific_editorial_rights_review",
    ):
        if not _bool(changed, key, context="policy.changed_source"):
            raise RpsRefreshPolicyError(f"Changed-source policy requires {key}=true")
    for key in ("stage_release_automatically", "publish_release_automatically"):
        if _bool(changed, key, context="policy.changed_source"):
            raise RpsRefreshPolicyError(f"Changed-source policy requires {key}=false")

    publication = _mapping(policy.get("publication"), context="policy.publication")
    if _bool(publication, "automatic", context="policy.publication"):
        raise RpsRefreshPolicyError("RPS publication may never be automatic under this policy")
    for key in ("requires_ci", "requires_exact_staged_hash_review", "requires_global_observatory_release_composition"):
        if not _bool(publication, key, context="policy.publication"):
            raise RpsRefreshPolicyError(f"Publication policy requires {key}=true")


def _change_counts(summary: Mapping[str, Any]) -> Mapping[str, Any]:
    counts = _mapping(summary.get("change_counts"), context="summary.change_counts")
    for key in ("new_observations", "revised_observations", "removed_observations", "definition_changes"):
        value = counts.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise RpsRefreshPolicyError(f"summary.change_counts.{key} must be a non-negative integer")
    return counts


def action_for_refresh_summary(
    policy: Mapping[str, Any],
    summary: Mapping[str, Any],
) -> dict[str, Any]:
    """Return the allowed next action for one validated source-refresh summary."""

    validate_rps_refresh_policy(policy)
    if summary.get("schema_version") != 1 or summary.get("candidate_type") != "rps_published_aggregate_refresh":
        raise RpsRefreshPolicyError("Unsupported RPS refresh summary")
    if summary.get("source_id") != policy.get("source_id"):
        raise RpsRefreshPolicyError("Refresh summary source_id does not match the pinned policy")
    inventory = _mapping(summary.get("inventory"), context="summary.inventory")
    if inventory.get("provider_inventory_status") != "pass":
        raise RpsRefreshPolicyError("Refresh summary inventory must pass before policy routing")

    status = _string(summary, "revision_status", context="summary")
    if status not in _ALLOWED_REFRESH_STATUSES:
        raise RpsRefreshPolicyError(f"Unsupported refresh revision_status: {status}")
    counts = _change_counts(summary)
    definition_changes = int(counts["definition_changes"])
    total_changes = sum(int(counts[key]) for key in counts)

    if status == "unchanged":
        if total_changes != 0 or summary.get("requires_release_review") is not False:
            raise RpsRefreshPolicyError("Unchanged summary contradicts its change counts/review flag")
        return {
            "action": "NO_SOURCE_CHANGE",
            "archive_exact_source_bytes": False,
            "build_observatory_candidate": False,
            "stage_release": False,
            "publish_release": False,
            "requires_human_review": False,
            "retain_review_safe_check_evidence": True,
        }

    if summary.get("requires_release_review") is not True:
        raise RpsRefreshPolicyError("Changed/baseline source summary must require release review")
    if status != "baseline" and total_changes == 0:
        raise RpsRefreshPolicyError("Changed source status has zero recorded changes")

    if definition_changes > 0:
        return {
            "action": "ARCHIVE_AND_BLOCK_DEFINITION_REVIEW",
            "archive_exact_source_bytes": True,
            "build_observatory_candidate": False,
            "stage_release": False,
            "publish_release": False,
            "requires_human_review": True,
            "retain_private_detailed_diff": True,
        }

    return {
        "action": "ARCHIVE_BUILD_AND_REVIEW",
        "archive_exact_source_bytes": True,
        "build_observatory_candidate": True,
        "stage_release": False,
        "publish_release": False,
        "requires_human_review": True,
        "retain_private_detailed_diff": status != "baseline",
    }


def recorded_activation_gates(policy: Mapping[str, Any]) -> set[str]:
    """Return activation gates backed by the evidence recorded in the policy."""

    validate_rps_refresh_policy(policy)
    return _validate_activation_evidence(policy)


def activation_gates_satisfied(policy: Mapping[str, Any], satisfied: Sequence[str]) -> bool:
    """Check whether every pinned precondition for scheduled checking is satisfied."""

    validate_rps_refresh_policy(policy)
    return set(satisfied) == _REQUIRED_ACTIVATION_GATES
