"""Prepare and compare rights-cleared RPS aggregate refresh snapshots.

This module sits upstream of the observatory release engine. It retrieves the
published aggregate RPS series through an authorized distribution client,
validates the complete provider inventory against the canonical 137 -> 131
scope contract, normalizes the 131 in-scope series, and classifies source
changes as new waves, revisions, or definition drift.

The resulting snapshot is a source candidate. It may contain published source
observations and therefore belongs in a private/transient candidate package,
not in the public web tree. Promotion into a public observatory release remains
a separate reviewed operation.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator, Mapping
from datetime import UTC, datetime
from typing import Any, Protocol

from genai_at_work.models import Observation
from genai_at_work.normalize import normalize_observations
from genai_at_work.rps_registry import (
    build_series_metadata,
    is_known_excluded_title,
    learn_entity_labels,
)


class RpsRefreshError(RuntimeError):
    """Raised when an RPS refresh candidate violates a source contract."""


class RpsSourceClient(Protocol):
    """Protocol required by the aggregate RPS refresh builder."""

    def iter_release_series(
        self, release_id: int, page_size: int = 1000
    ) -> Iterator[dict[str, Any]]: ...

    def series_metadata(self, series_id: str) -> dict[str, Any]: ...

    def series_tags(self, series_id: str) -> list[dict[str, Any]]: ...

    def series_observations(self, series_id: str) -> list[dict[str, Any]]: ...


_DEFINITION_FIELDS = (
    "title",
    "metric_id",
    "entity_id",
    "entity_type",
    "entity_name",
    "frequency",
    "unit",
    "seasonal_adjustment",
    "notes_hash",
)


def canonical_digest(value: object) -> str:
    """Return a deterministic SHA-256 digest for JSON-compatible content."""

    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _json_object(value: object, *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RpsRefreshError(f"{label} must be a JSON object")
    return {str(key): item for key, item in value.items()}


def _object_rows(value: object, *, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise RpsRefreshError(f"{label} must be a JSON array")
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise RpsRefreshError(f"{label}[{index}] must be a JSON object")
        rows.append({str(key): cell for key, cell in item.items()})
    return rows


def _required_string(row: Mapping[str, Any], key: str, *, label: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RpsRefreshError(f"{label}.{key} must be a non-empty string")
    return value


def _required_int(row: Mapping[str, Any], key: str, *, label: str) -> int:
    value = row.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise RpsRefreshError(f"{label}.{key} must be an integer")
    return value


def _utc_timestamp(value: datetime | None) -> str:
    timestamp = value or datetime.now(UTC)
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise RpsRefreshError("retrieved_at must be timezone-aware")
    return timestamp.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _unique_series_rows(rows: list[dict[str, Any]], *, label: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        series_id = _required_string(row, "series_id", label=f"{label}[{index}]")
        if series_id in indexed:
            raise RpsRefreshError(f"Duplicate series_id in {label}: {series_id}")
        indexed[series_id] = row
    return indexed


def _release_rows_by_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        series_id = _required_string(row, "id", label=f"provider_release[{index}]")
        if series_id in indexed:
            raise RpsRefreshError(f"Duplicate series_id in provider release: {series_id}")
        indexed[series_id] = row
    return indexed


def _validate_manifest_identity(
    manifest_row: Mapping[str, Any], normalized: Mapping[str, Any], *, series_id: str
) -> None:
    expected = {
        "series_id": _required_string(manifest_row, "series_id", label=series_id),
        "metric_id": _required_string(manifest_row, "metric_id", label=series_id),
        "entity_id": _required_string(manifest_row, "entity_id", label=series_id),
        "entity_type": _required_string(manifest_row, "entity_type", label=series_id),
        "entity_name": _required_string(manifest_row, "entity_name", label=series_id),
    }
    observed = {key: normalized.get(key) for key in expected}
    if observed != expected:
        raise RpsRefreshError(
            f"Canonical manifest identity drift for {series_id}: expected {expected!r}, "
            f"observed {observed!r}"
        )


def _observation_payload(observation: Observation) -> dict[str, Any]:
    return {
        "date": observation.date.isoformat(),
        "period": observation.period,
        "value": observation.value,
        "unit": observation.unit,
        "realtime_start": (
            observation.realtime_start.isoformat() if observation.realtime_start else None
        ),
        "realtime_end": observation.realtime_end.isoformat() if observation.realtime_end else None,
        "source_last_updated": observation.source_last_updated,
    }


def build_refresh_snapshot(
    client: RpsSourceClient,
    canonical_manifest: Mapping[str, Any],
    provider_scope: Mapping[str, Any],
    *,
    retrieved_at: datetime | None = None,
) -> dict[str, Any]:
    """Build a private source snapshot after exact provider-scope validation.

    The function fails closed when the provider release gains, loses, duplicates,
    or renames a series relative to the registered 137-series provider contract.
    The six intentionally excluded national constructs are inventory-validated but
    their observations are not retrieved.
    """

    manifest_count = _required_int(canonical_manifest, "series_count", label="manifest")
    manifest_rows = _object_rows(canonical_manifest.get("series"), label="manifest.series")
    manifest_by_id = _unique_series_rows(manifest_rows, label="manifest.series")
    if len(manifest_rows) != manifest_count:
        raise RpsRefreshError(
            f"Canonical manifest count mismatch: declared {manifest_count}, observed {len(manifest_rows)}"
        )

    release_id = _required_int(provider_scope, "provider_release_id", label="provider_scope")
    provider_count = _required_int(
        provider_scope, "provider_release_series_count", label="provider_scope"
    )
    observatory_count = _required_int(
        provider_scope, "observatory_registry_series_count", label="provider_scope"
    )
    if observatory_count != manifest_count:
        raise RpsRefreshError(
            "Provider scope and canonical manifest disagree on observatory series count: "
            f"{observatory_count} != {manifest_count}"
        )

    excluded_rows = _object_rows(
        provider_scope.get("intentionally_excluded_national_series"),
        label="provider_scope.intentionally_excluded_national_series",
    )
    excluded_by_id = _unique_series_rows(
        excluded_rows, label="provider_scope.intentionally_excluded_national_series"
    )
    manifest_ids = set(manifest_by_id)
    excluded_ids = set(excluded_by_id)
    overlap = manifest_ids & excluded_ids
    if overlap:
        raise RpsRefreshError(f"Included/excluded provider scope overlaps: {sorted(overlap)}")

    expected_provider_ids = manifest_ids | excluded_ids
    if len(expected_provider_ids) != provider_count:
        raise RpsRefreshError(
            "Registered provider inventory does not reconcile: "
            f"expected {provider_count} total IDs, constructed {len(expected_provider_ids)}"
        )

    release_rows = list(client.iter_release_series(release_id))
    release_by_id = _release_rows_by_id(release_rows)
    observed_provider_ids = set(release_by_id)
    if len(release_rows) != provider_count or observed_provider_ids != expected_provider_ids:
        missing = sorted(expected_provider_ids - observed_provider_ids)
        unexpected = sorted(observed_provider_ids - expected_provider_ids)
        raise RpsRefreshError(
            "Provider release inventory drift: "
            f"declared={provider_count}, observed={len(release_rows)}, "
            f"missing={missing}, unexpected={unexpected}"
        )

    known_industries, known_occupations = learn_entity_labels(release_rows)
    timestamp = retrieved_at or datetime.now(UTC)
    retrieved_at_utc = _utc_timestamp(timestamp)

    series_payloads: list[dict[str, Any]] = []
    observation_count = 0
    for series_id in sorted(manifest_ids):
        release_row = release_by_id[series_id]
        detail_row = client.series_metadata(series_id)
        tags = client.series_tags(series_id)
        metadata = build_series_metadata(
            release_row,
            detail_row,
            tags,
            known_industries,
            known_occupations,
        )
        normalized_identity = {
            "series_id": metadata.series_id,
            "metric_id": metadata.metric_id,
            "entity_id": metadata.entity_id,
            "entity_type": metadata.entity_type.value,
            "entity_name": metadata.entity_name,
        }
        _validate_manifest_identity(
            manifest_by_id[series_id], normalized_identity, series_id=series_id
        )

        observations = normalize_observations(
            metadata,
            client.series_observations(series_id),
            ingested_at=timestamp,
        )
        dates = [observation.date for observation in observations]
        if dates != sorted(dates) or len(set(dates)) != len(dates):
            raise RpsRefreshError(f"Observation dates are not unique and sorted for {series_id}")
        observation_count += len(observations)

        series_payloads.append(
            {
                "series_id": metadata.series_id,
                "title": metadata.title,
                "metric_id": metadata.metric_id,
                "entity_id": metadata.entity_id,
                "entity_type": metadata.entity_type.value,
                "entity_name": metadata.entity_name,
                "frequency": metadata.frequency,
                "unit": metadata.unit,
                "seasonal_adjustment": metadata.seasonal_adjustment,
                "observation_start": metadata.observation_start.isoformat(),
                "observation_end": metadata.observation_end.isoformat(),
                "last_updated": metadata.last_updated,
                "notes_hash": metadata.notes_hash,
                "source_url": metadata.source_url,
                "copyright_status": metadata.copyright_status,
                "citation_text": metadata.citation_text,
                "observations": [_observation_payload(observation) for observation in observations],
            }
        )

    excluded_payloads: list[dict[str, Any]] = []
    for series_id in sorted(excluded_ids):
        release_row = release_by_id[series_id]
        title = _required_string(release_row, "title", label=f"excluded[{series_id}]")
        if not is_known_excluded_title(title):
            raise RpsRefreshError(
                f"Registered excluded series no longer has an excluded RPS title: {series_id}: {title!r}"
            )
        excluded_payloads.append(
            {
                "series_id": series_id,
                "title": title,
                "construct": excluded_by_id[series_id].get("construct"),
                "reason": excluded_by_id[series_id].get("reason"),
                "observations_retrieved": False,
            }
        )

    stable_content = {
        "provider_release_id": release_id,
        "provider_series_ids": sorted(observed_provider_ids),
        "series": series_payloads,
        "excluded_series": excluded_payloads,
    }
    content_sha256 = canonical_digest(stable_content)

    return {
        "schema_version": 1,
        "snapshot_type": "rps_published_aggregate_refresh",
        "source_id": f"rps-genai-tracker-fred-release-{release_id}",
        "provider": "FRED/ALFRED distribution of the RPS GenAI Adoption Tracker",
        "provider_release_id": release_id,
        "retrieved_at": retrieved_at_utc,
        "rights": {
            "status": "approved",
            "scope": "published aggregate project use",
            "decision_ref": "docs/source-rights/RPS_SOURCE_DECISION.md",
            "public_bulk_redistribution_approved": False,
        },
        "inventory": {
            "provider_series_count": len(release_rows),
            "observatory_series_count": len(series_payloads),
            "excluded_series_count": len(excluded_payloads),
            "provider_inventory_status": "pass",
        },
        "observation_count": observation_count,
        "content_sha256": content_sha256,
        "series": series_payloads,
        "excluded_series": excluded_payloads,
    }


def _snapshot_series(snapshot: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    rows = _object_rows(snapshot.get("series"), label="snapshot.series")
    return _unique_series_rows(rows, label="snapshot.series")


def _observation_map(series: Mapping[str, Any], *, series_id: str) -> dict[str, dict[str, Any]]:
    rows = _object_rows(series.get("observations"), label=f"{series_id}.observations")
    indexed: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        date = _required_string(row, "date", label=f"{series_id}.observations[{index}]")
        if date in indexed:
            raise RpsRefreshError(f"Duplicate observation date for {series_id}: {date}")
        indexed[date] = row
    return indexed


def compare_refresh_snapshots(
    previous: Mapping[str, Any], current: Mapping[str, Any]
) -> dict[str, Any]:
    """Classify source changes between two validated private RPS snapshots."""

    previous_source = _required_string(previous, "source_id", label="previous")
    current_source = _required_string(current, "source_id", label="current")
    if previous_source != current_source:
        raise RpsRefreshError(
            f"Cannot compare different source identities: {previous_source!r} != {current_source!r}"
        )

    previous_series = _snapshot_series(previous)
    current_series = _snapshot_series(current)
    if set(previous_series) != set(current_series):
        raise RpsRefreshError(
            "Snapshot series inventory changed; provider-scope revision is required before comparison"
        )

    new_observations: list[dict[str, Any]] = []
    revised_observations: list[dict[str, Any]] = []
    removed_observations: list[dict[str, Any]] = []
    definition_changes: list[dict[str, Any]] = []

    for series_id in sorted(current_series):
        before = previous_series[series_id]
        after = current_series[series_id]
        changed_fields = [
            field for field in _DEFINITION_FIELDS if before.get(field) != after.get(field)
        ]
        if changed_fields:
            definition_changes.append(
                {
                    "series_id": series_id,
                    "fields": changed_fields,
                }
            )

        before_obs = _observation_map(before, series_id=series_id)
        after_obs = _observation_map(after, series_id=series_id)
        for date in sorted(set(after_obs) - set(before_obs)):
            new_observations.append({"series_id": series_id, "date": date})
        for date in sorted(set(before_obs) - set(after_obs)):
            removed_observations.append({"series_id": series_id, "date": date})
        for date in sorted(set(before_obs) & set(after_obs)):
            if before_obs[date].get("value") != after_obs[date].get("value"):
                revised_observations.append(
                    {
                        "series_id": series_id,
                        "date": date,
                        "previous_value": before_obs[date].get("value"),
                        "current_value": after_obs[date].get("value"),
                    }
                )

    has_new = bool(new_observations)
    has_revision = bool(revised_observations or removed_observations or definition_changes)
    if has_new and has_revision:
        revision_status = "mixed"
    elif has_new:
        revision_status = "new_wave"
    elif has_revision:
        revision_status = "revision"
    else:
        revision_status = "unchanged"

    return {
        "schema_version": 1,
        "source_id": current_source,
        "previous_content_sha256": previous.get("content_sha256"),
        "current_content_sha256": current.get("content_sha256"),
        "revision_status": revision_status,
        "requires_release_review": revision_status != "unchanged",
        "counts": {
            "new_observations": len(new_observations),
            "revised_observations": len(revised_observations),
            "removed_observations": len(removed_observations),
            "definition_changes": len(definition_changes),
        },
        "new_observations": new_observations,
        "revised_observations": revised_observations,
        "removed_observations": removed_observations,
        "definition_changes": definition_changes,
    }


def summarize_refresh_candidate(
    snapshot: Mapping[str, Any],
    *,
    previous_snapshot: Mapping[str, Any] | None = None,
    snapshot_file_sha256: str | None = None,
) -> dict[str, Any]:
    """Create a review-safe candidate summary without source observation rows."""

    if previous_snapshot is None:
        revision_status = "baseline"
        counts = {
            "new_observations": snapshot.get("observation_count", 0),
            "revised_observations": 0,
            "removed_observations": 0,
            "definition_changes": 0,
        }
        requires_release_review = True
        previous_content_sha256 = None
    else:
        diff = compare_refresh_snapshots(previous_snapshot, snapshot)
        revision_status = diff["revision_status"]
        counts = diff["counts"]
        requires_release_review = bool(diff["requires_release_review"])
        previous_content_sha256 = diff["previous_content_sha256"]

    inventory = _json_object(snapshot.get("inventory"), label="snapshot.inventory")
    return {
        "schema_version": 1,
        "candidate_type": "rps_published_aggregate_refresh",
        "source_id": _required_string(snapshot, "source_id", label="snapshot"),
        "retrieved_at": _required_string(snapshot, "retrieved_at", label="snapshot"),
        "content_sha256": _required_string(snapshot, "content_sha256", label="snapshot"),
        "snapshot_file_sha256": snapshot_file_sha256,
        "previous_content_sha256": previous_content_sha256,
        "revision_status": revision_status,
        "requires_release_review": requires_release_review,
        "inventory": {
            "provider_series_count": inventory.get("provider_series_count"),
            "observatory_series_count": inventory.get("observatory_series_count"),
            "excluded_series_count": inventory.get("excluded_series_count"),
            "provider_inventory_status": inventory.get("provider_inventory_status"),
        },
        "observation_count": snapshot.get("observation_count"),
        "change_counts": counts,
        "promotion_state": "source-candidate-only",
        "public_raw_observations_included": False,
        "next_gate": (
            "Review the source candidate and revision classification, regenerate all dependent "
            "derived artifacts, stage an observatory release candidate, and promote only through "
            "the reviewed release engine."
        ),
    }
