"""Rights-safe RPS source-checkpoint construction.

A checkpoint is a review artifact for remembering the exact scientific/source
identity of an accepted live aggregate refresh without publishing source
observations. It is deliberately weaker than a durable private raw-vintage
archive and does not promote an observatory release.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any


class RpsCheckpointError(ValueError):
    """Raised when a proposed public checkpoint violates its contract."""


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
_PERIOD = re.compile(r"^(\d{4})-Q([1-4])$")
_EXPECTED_METRICS = {
    "adoption_work",
    "assisted_hours_share",
    "reported_time_savings_share",
}
_FORBIDDEN_OUTPUT_KEYS = {
    "records",
    "observations",
    "value",
    "values",
    "local_path",
    "source_row",
    "source_rows",
}


def _mapping(value: object, *, context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise RpsCheckpointError(f"{context} must be an object")
    return value


def _rows(value: object, *, context: str) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        raise RpsCheckpointError(f"{context} must be a list")
    rows: list[Mapping[str, Any]] = []
    for index, item in enumerate(value):
        rows.append(_mapping(item, context=f"{context}[{index}]"))
    return rows


def _string(mapping: Mapping[str, Any], key: str, *, context: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise RpsCheckpointError(f"{context}.{key} must be a non-empty string")
    return value


def _integer(mapping: Mapping[str, Any], key: str, *, context: str) -> int:
    value = mapping.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise RpsCheckpointError(f"{context}.{key} must be an integer")
    return value


def _false(mapping: Mapping[str, Any], key: str, *, context: str) -> None:
    if mapping.get(key) is not False:
        raise RpsCheckpointError(f"{context}.{key} must be false")


def _sha256(value: object, *, context: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise RpsCheckpointError(f"{context} must be a lowercase SHA-256 digest")
    return value


def _period_key(period: str) -> tuple[int, int]:
    match = _PERIOD.fullmatch(period)
    if match is None:
        raise RpsCheckpointError(f"invalid quarterly period: {period!r}")
    return int(match.group(1)), int(match.group(2))


def _periods(value: object, *, context: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise RpsCheckpointError(f"{context} must be a non-empty period list")
    if any(not isinstance(period, str) for period in value):
        raise RpsCheckpointError(f"{context} contains a non-string period")
    periods = tuple(str(period) for period in value)
    if len(set(periods)) != len(periods):
        raise RpsCheckpointError(f"{context} contains duplicate periods")
    for period in periods:
        _period_key(period)
    if periods != tuple(sorted(periods, key=_period_key)):
        raise RpsCheckpointError(f"{context} must be chronologically sorted")
    return periods


def _assert_no_forbidden_keys(value: object, *, context: str = "checkpoint") -> None:
    if isinstance(value, Mapping):
        for raw_key, item in value.items():
            key = str(raw_key)
            if key in _FORBIDDEN_OUTPUT_KEYS:
                raise RpsCheckpointError(f"{context} contains forbidden source-data key {key!r}")
            _assert_no_forbidden_keys(item, context=f"{context}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            _assert_no_forbidden_keys(item, context=f"{context}[{index}]")


def build_public_rps_source_checkpoint(
    source_summary: Mapping[str, Any],
    release_manifest: Mapping[str, Any],
    *,
    validation_run_id: str,
    validation_commit: str,
) -> dict[str, Any]:
    """Build a reviewable source checkpoint containing hashes/metadata only."""

    if not validation_run_id or not validation_run_id.isdigit():
        raise RpsCheckpointError("validation_run_id must be a numeric GitHub Actions run id")
    commit = validation_commit.lower()
    if _GIT_SHA.fullmatch(commit) is None:
        raise RpsCheckpointError("validation_commit must be a 40-character Git commit SHA")

    if source_summary.get("candidate_type") != "rps_published_aggregate_refresh":
        raise RpsCheckpointError("source summary is not an RPS published-aggregate refresh")
    _false(source_summary, "public_raw_observations_included", context="source_summary")
    if source_summary.get("promotion_state") != "source-candidate-only":
        raise RpsCheckpointError("source summary must remain source-candidate-only")
    if source_summary.get("requires_release_review") is not True:
        raise RpsCheckpointError("source summary must require release review")

    source_id = _string(source_summary, "source_id", context="source_summary")
    content_sha = _sha256(source_summary.get("content_sha256"), context="source_summary.content_sha256")
    snapshot_file_sha = _sha256(
        source_summary.get("private_snapshot_file_sha256"),
        context="source_summary.private_snapshot_file_sha256",
    )
    observation_count = _integer(source_summary, "observation_count", context="source_summary")
    if observation_count <= 0:
        raise RpsCheckpointError("source_summary.observation_count must be positive")

    inventory = _mapping(source_summary.get("inventory"), context="source_summary.inventory")
    expected_inventory = {
        "provider_series_count": 137,
        "observatory_series_count": 131,
        "excluded_series_count": 6,
        "provider_inventory_status": "pass",
    }
    for key, expected in expected_inventory.items():
        if inventory.get(key) != expected:
            raise RpsCheckpointError(
                f"source_summary.inventory.{key} must equal {expected!r}, observed {inventory.get(key)!r}"
            )

    if release_manifest.get("data_mode") != "derived_only":
        raise RpsCheckpointError("release manifest must remain derived_only")
    _false(release_manifest, "source_input_bytes_publication", context="release_manifest")
    sources = _rows(release_manifest.get("sources"), context="release_manifest.sources")
    if len(sources) != 1:
        raise RpsCheckpointError("RPS component release must contain exactly one source")
    source = sources[0]
    if _string(source, "source_id", context="release source") != source_id:
        raise RpsCheckpointError("release/source-summary source_id mismatch")
    if source.get("source_vintage_id") != f"sha256:{content_sha}":
        raise RpsCheckpointError("release source_vintage_id does not bind source scientific content")

    rights = _mapping(source.get("rights"), context="release source rights")
    expected_rights = {
        "status": "approved",
        "storage_scope": "private",
        "publication_scope": "derived_only",
        "redistribution_scope": "derived_only",
    }
    for key, expected in expected_rights.items():
        if rights.get(key) != expected:
            raise RpsCheckpointError(
                f"release source rights.{key} must equal {expected!r}, observed {rights.get(key)!r}"
            )

    source_periods = _periods(source.get("reference_periods"), context="source.reference_periods")
    analysis_periods = _periods(
        source.get("analysis_reference_periods"), context="source.analysis_reference_periods"
    )
    if not set(analysis_periods).issubset(source_periods):
        raise RpsCheckpointError("analysis periods must be a subset of source periods")

    metric_periods_raw = _mapping(
        source.get("analysis_metric_reference_periods"),
        context="source.analysis_metric_reference_periods",
    )
    if set(metric_periods_raw) != _EXPECTED_METRICS:
        raise RpsCheckpointError("metric-specific period families must be exactly A/H/S")
    metric_periods = {
        metric_id: _periods(value, context=f"source.analysis_metric_reference_periods.{metric_id}")
        for metric_id, value in sorted(metric_periods_raw.items())
    }
    for metric_id, periods in metric_periods.items():
        if not set(periods).issubset(source_periods):
            raise RpsCheckpointError(f"{metric_id} periods must be a subset of source periods")
    common = set(next(iter(metric_periods.values())))
    for periods in metric_periods.values():
        common.intersection_update(periods)
    expected_analysis = tuple(sorted(common, key=_period_key))
    if analysis_periods != expected_analysis:
        raise RpsCheckpointError("joint analysis periods must equal the A/H/S construct intersection")

    coverage = _mapping(source.get("coverage"), context="release source coverage")
    if coverage.get("status") != "pass":
        raise RpsCheckpointError("release source coverage must pass")
    if coverage.get("full_source_observed_units") != observation_count:
        raise RpsCheckpointError("release full-source observation count does not match source summary")
    if coverage.get("subgroup_series_count") != 126 or coverage.get("national_series_count") != 5:
        raise RpsCheckpointError("release source subgroup/national inventory is not 126/5")
    expected_analytical_units = 131 * len(analysis_periods)
    if coverage.get("required_units") != expected_analytical_units:
        raise RpsCheckpointError("release required analytical units do not match 131 × joint periods")
    if coverage.get("observed_units") != expected_analytical_units:
        raise RpsCheckpointError("release observed analytical units do not match required units")

    objects = _rows(source.get("objects"), context="release source objects")
    if len(objects) != len(source_periods):
        raise RpsCheckpointError("source object count must equal source-period count")
    checkpoint_objects: list[dict[str, Any]] = []
    for period, item in zip(source_periods, objects, strict=True):
        object_id = _string(item, "object_id", context=f"source object {period}")
        if object_id != period.lower():
            raise RpsCheckpointError(f"source object identity mismatch for {period}")
        object_sha = _sha256(item.get("sha256"), context=f"source object {period}.sha256")
        size = _integer(item, "size_bytes", context=f"source object {period}")
        if size <= 0:
            raise RpsCheckpointError(f"source object {period}.size_bytes must be positive")
        checkpoint_objects.append(
            {"period": period, "object_id": object_id, "sha256": object_sha, "size_bytes": size}
        )

    build = _mapping(release_manifest.get("build"), context="release_manifest.build")
    if build.get("deterministic") is not True:
        raise RpsCheckpointError("release builder must be deterministic")
    builder_commit = _string(build, "builder_commit", context="release_manifest.build").lower()
    if builder_commit != commit:
        raise RpsCheckpointError("release builder_commit must equal the validated GitHub commit")

    checkpoint: dict[str, Any] = {
        "schema_version": 1,
        "checkpoint_type": "rps_published_aggregate_source_checkpoint",
        "checkpoint_state": "candidate_for_review",
        "source_id": source_id,
        "source_content_sha256": content_sha,
        "source_snapshot_file_sha256": snapshot_file_sha,
        "source_vintage_id": f"sha256:{content_sha}",
        "retrieved_at": _string(source_summary, "retrieved_at", context="source_summary"),
        "revision_status": _string(source_summary, "revision_status", context="source_summary"),
        "inventory": dict(expected_inventory),
        "observation_count": observation_count,
        "source_reference_periods": list(source_periods),
        "analysis_reference_periods": list(analysis_periods),
        "analysis_metric_reference_periods": {
            metric_id: list(periods) for metric_id, periods in metric_periods.items()
        },
        "definition_id": _string(source, "definition_id", context="release source"),
        "taxonomy_versions": dict(
            _mapping(source.get("taxonomy_versions"), context="release source taxonomy_versions")
        ),
        "source_objects": checkpoint_objects,
        "builder": {
            "builder_id": _string(build, "builder_id", context="release_manifest.build"),
            "builder_commit": builder_commit,
        },
        "validation": {
            "github_run_id": validation_run_id,
            "github_sha": commit,
        },
        "rights_boundary": {
            "source_storage_scope": "private",
            "publication_scope": "derived_only",
            "redistribution_scope": "derived_only",
            "checkpoint_contains_observation_values": False,
            "source_input_bytes_in_checkpoint": False,
            "durable_private_raw_archive_attested": False,
        },
        "requires_human_acceptance": True,
        "promotion_performed": False,
    }
    _assert_no_forbidden_keys(checkpoint)
    return checkpoint
