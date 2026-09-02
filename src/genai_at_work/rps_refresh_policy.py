"""Executable policy contract for RPS source checking versus release actions."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

_ALLOWED_REFRESH_STATUSES = {"baseline", "unchanged", "new_wave", "revision", "mixed"}
_REQUIRED_ACTIVATION_GATES = {
    "successful_manual_live_probe",
    "fred_api_key_verified_in_execution_environment",
    "operator_controlled_private_vintage_backend_configured",
    "private_backend_write_read_verify_rehearsal_passed",
}
_TIME_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


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


def _strings(mapping: Mapping[str, Any], key: str, *, context: str) -> list[str]:
    value = mapping.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise RpsRefreshPolicyError(f"{context}.{key} must be a list of non-empty strings")
    return list(value)


def validate_rps_refresh_policy(policy: Mapping[str, Any]) -> None:
    """Validate the pinned source-check, retention, and publication separation."""

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
            "RPS schedule activation requirements must exactly cover live probe, credential, private backend, and backend rehearsal"
        )

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


def activation_gates_satisfied(policy: Mapping[str, Any], satisfied: Sequence[str]) -> bool:
    """Check whether every pinned precondition for scheduled checking is satisfied."""

    validate_rps_refresh_policy(policy)
    return set(satisfied) == _REQUIRED_ACTIVATION_GATES
