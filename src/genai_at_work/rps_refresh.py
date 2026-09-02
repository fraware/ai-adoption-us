"""Build non-canonical review candidates for recurring RPS aggregate source checks."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any


class RpsRefreshError(RuntimeError):
    """Raised when source-refresh inputs violate the pinned RPS contracts."""


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise RpsRefreshError(f"{label} must be an object")
    return value


def _rows(value: object, *, label: str) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        raise RpsRefreshError(f"{label} must be an array")
    rows: list[Mapping[str, object]] = []
    for index, item in enumerate(value):
        rows.append(_mapping(item, label=f"{label}[{index}]"))
    return rows


def _string(row: Mapping[str, object], key: str, *, label: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value:
        raise RpsRefreshError(f"{label}.{key} must be a non-empty string")
    return value


def _integer(row: Mapping[str, object], key: str, *, label: str) -> int:
    value = row.get(key)
    if not isinstance(value, int):
        raise RpsRefreshError(f"{label}.{key} must be an integer")
    return value


def _decimal(value: object, *, label: str) -> Decimal | None:
    if value is None or value == ".":
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation as exc:
        raise RpsRefreshError(f"{label} is not numeric: {value!r}") from exc


def _numeric_observations(rows: Sequence[Mapping[str, object]]) -> list[Mapping[str, object]]:
    numeric: list[Mapping[str, object]] = []
    for row in rows:
        if _decimal(row.get("value"), label="observation.value") is not None:
            date.fromisoformat(_string(row, "date", label="observation"))
            numeric.append(row)
    return numeric


def _latest_observation(rows: Sequence[Mapping[str, object]]) -> Mapping[str, object] | None:
    numeric = _numeric_observations(rows)
    if not numeric:
        return None
    return max(numeric, key=lambda row: _string(row, "date", label="observation"))


def _observation_on_date(
    rows: Sequence[Mapping[str, object]], observation_date: str
) -> Mapping[str, object] | None:
    matches = [row for row in _numeric_observations(rows) if row.get("date") == observation_date]
    if len(matches) > 1:
        raise RpsRefreshError(f"Multiple observations found for {observation_date}")
    return matches[0] if matches else None


def _observation_record(row: Mapping[str, object] | None) -> dict[str, object] | None:
    if row is None:
        return None
    value = _decimal(row.get("value"), label="observation.value")
    if value is None:
        return None
    return {
        "date": _string(row, "date", label="observation"),
        "value": str(value),
        "realtime_start": str(row.get("realtime_start", "")),
        "realtime_end": str(row.get("realtime_end", "")),
    }


def build_refresh_candidate(
    *,
    manifest: Mapping[str, object],
    provider_scope: Mapping[str, object],
    canonical_checkpoint: Mapping[str, object],
    release_rows: Sequence[Mapping[str, object]],
    observations_by_series: Mapping[str, Sequence[Mapping[str, object]]],
    retrieved_at: str,
) -> dict[str, object]:
    """Compare a live provider read to pinned RPS source contracts without promoting it.

    The returned object is review evidence only. It contains the latest numeric observation for
    each supported series plus an exact comparison of the canonical Q2-2026 industry-adoption
    checkpoint. It intentionally does not reproduce complete historical series.
    """

    manifest_rows = _rows(manifest.get("series"), label="manifest.series")
    excluded_rows = _rows(
        provider_scope.get("intentionally_excluded_national_series"),
        label="provider_scope.intentionally_excluded_national_series",
    )
    checkpoint_rows = _rows(canonical_checkpoint.get("rows"), label="checkpoint.rows")

    manifest_count = _integer(manifest, "series_count", label="manifest")
    expected_provider_count = _integer(
        provider_scope, "provider_release_series_count", label="provider_scope"
    )
    release_id = _integer(provider_scope, "provider_release_id", label="provider_scope")
    if manifest_count != 131 or len(manifest_rows) != manifest_count:
        raise RpsRefreshError(
            f"Expected the pinned 131-series manifest; count={manifest_count}, rows={len(manifest_rows)}"
        )

    manifest_ids = {_string(row, "series_id", label="manifest.series") for row in manifest_rows}
    excluded_ids = {
        _string(row, "series_id", label="provider_scope.excluded") for row in excluded_rows
    }
    if manifest_ids & excluded_ids:
        raise RpsRefreshError("Supported and intentionally excluded RPS series overlap")

    release_by_id = {
        _string(row, "id", label="release.series"): row
        for row in release_rows
    }
    release_ids = set(release_by_id)
    expected_ids = manifest_ids | excluded_ids
    catalog_added_ids = sorted(release_ids - expected_ids)
    catalog_removed_ids = sorted(expected_ids - release_ids)

    missing_observation_payloads = sorted(manifest_ids - set(observations_by_series))
    if missing_observation_payloads:
        raise RpsRefreshError(
            "Observation payloads missing for supported series: "
            + ", ".join(missing_observation_payloads[:10])
        )

    series_records: list[dict[str, object]] = []
    for spec in manifest_rows:
        series_id = _string(spec, "series_id", label="manifest.series")
        release = release_by_id.get(series_id)
        observations = observations_by_series[series_id]
        latest = _latest_observation(observations)
        series_records.append(
            {
                "series_id": series_id,
                "entity_type": _string(spec, "entity_type", label="manifest.series"),
                "entity_id": _string(spec, "entity_id", label="manifest.series"),
                "entity_name": _string(spec, "entity_name", label="manifest.series"),
                "metric_id": _string(spec, "metric_id", label="manifest.series"),
                "source_url": _string(spec, "source_url", label="manifest.series"),
                "provider_present": release is not None,
                "provider_last_updated": "" if release is None else str(release.get("last_updated", "")),
                "provider_observation_end": "" if release is None else str(release.get("observation_end", "")),
                "latest_observation": _observation_record(latest),
            }
        )

    checkpoint_date = _string(
        canonical_checkpoint, "observation_date", label="canonical_checkpoint"
    )
    date.fromisoformat(checkpoint_date)
    checkpoint_comparisons: list[dict[str, object]] = []
    revised = 0
    missing = 0
    unchanged = 0
    newer = 0

    for pinned in checkpoint_rows:
        series_id = _string(pinned, "series_id", label="checkpoint.rows")
        if series_id not in manifest_ids:
            raise RpsRefreshError(f"Pinned checkpoint series is outside manifest: {series_id}")
        observations = observations_by_series[series_id]
        observed = _observation_on_date(observations, checkpoint_date)
        latest = _latest_observation(observations)
        pinned_value = _decimal(pinned.get("value_pct"), label=f"checkpoint {series_id} value")
        if pinned_value is None:
            raise RpsRefreshError(f"Canonical checkpoint value missing for {series_id}")
        observed_value = None if observed is None else _decimal(
            observed.get("value"), label=f"provider {series_id} value"
        )

        if observed_value is None:
            status = "missing-pinned-observation"
            missing += 1
        elif observed_value == pinned_value:
            status = "unchanged"
            unchanged += 1
        else:
            status = "revised"
            revised += 1

        latest_date = None if latest is None else _string(latest, "date", label="observation")
        has_newer = latest_date is not None and latest_date > checkpoint_date
        newer += int(has_newer)
        checkpoint_comparisons.append(
            {
                "series_id": series_id,
                "entity_index": pinned.get("entity_index"),
                "entity_name": _string(pinned, "entity_name", label="checkpoint.rows"),
                "pinned_date": checkpoint_date,
                "pinned_value": str(pinned_value),
                "provider_value_on_pinned_date": (
                    None if observed_value is None else str(observed_value)
                ),
                "pinned_value_status": status,
                "latest_observation": _observation_record(latest),
                "newer_observation_available": has_newer,
            }
        )

    supported_newer = sum(
        1
        for record in series_records
        if isinstance(record["latest_observation"], dict)
        and str(record["latest_observation"]["date"]) > checkpoint_date
    )

    review_reasons: list[str] = []
    if len(release_rows) != expected_provider_count or catalog_added_ids or catalog_removed_ids:
        review_reasons.append("provider-catalog-drift")
    if revised:
        review_reasons.append("canonical-q2-industry-values-revised")
    if missing:
        review_reasons.append("canonical-q2-industry-values-missing")
    if supported_newer:
        review_reasons.append("newer-supported-observations-available")

    if any(reason != "newer-supported-observations-available" for reason in review_reasons):
        status = "review-required-provider-drift"
    elif supported_newer:
        status = "new-wave-review-required"
    else:
        status = "no-provider-change-detected"

    return {
        "schema_version": 1,
        "candidate_type": "rps-aggregate-refresh-review-candidate",
        "status": status,
        "retrieved_at": retrieved_at,
        "transport": "FRED API distribution layer",
        "provider_release_id": release_id,
        "candidate_is_canonical": False,
        "candidate_is_publication_ready": False,
        "automatic_repository_write": False,
        "full_history_included": False,
        "review_reasons": review_reasons,
        "catalog": {
            "expected_provider_series_count": expected_provider_count,
            "observed_provider_series_count": len(release_rows),
            "supported_manifest_series_count": manifest_count,
            "catalog_added_ids": catalog_added_ids,
            "catalog_removed_ids": catalog_removed_ids,
        },
        "canonical_q2_industry_adoption_check": {
            "checkpoint_snapshot_id": _string(
                canonical_checkpoint, "snapshot_id", label="canonical_checkpoint"
            ),
            "observation_date": checkpoint_date,
            "pinned_series_count": len(checkpoint_rows),
            "unchanged": unchanged,
            "revised": revised,
            "missing": missing,
            "with_newer_observation": newer,
            "comparisons": checkpoint_comparisons,
        },
        "supported_series_latest": series_records,
        "supported_series_with_newer_observation_than_q2_baseline": supported_newer,
        "promotion_rule": (
            "This artifact is monitoring evidence only. Any new or revised observations require "
            "an explicit versioned source checkpoint, revision review, ordinary PR review, and CI "
            "before they become canonical or public-product inputs."
        ),
    }
