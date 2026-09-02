"""Release adapter for RPS sources with construct-specific history lengths.

The live FRED distribution can expose different valid start dates by construct.
This adapter preserves and hash-binds the complete 131-series source history,
requires every industry/occupation series within each A/H/S construct family to
share one internally complete period set, then defines the joint longitudinal
analytical window as the intersection of those complete construct windows.

It deliberately reuses the established longitudinal artifact/diagnostic logic
from :mod:`genai_at_work.rps_release`; it changes source-history topology, not
the estimands or descriptive analyses.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from typing import Any

from genai_at_work.longitudinal import REQUIRED_ENTITY_COUNTS, AuditRecord
from genai_at_work.release_engine import canonical_digest
from genai_at_work.rps_release import (
    _DEFINITION_FIELDS,
    RPS_SOURCE_URL,
    SUBGROUP_ENTITY_TYPES,
    SUBGROUP_METRICS,
    PreparedRpsPanel,
    RpsReleaseError,
    _claim_rows,
    _diagnostic_manifest,
    _period_key,
    _quarter_for_date,
    _release_type,
    _required_int,
    _required_string,
    _rows,
    _source_transition_status,
    _validate_registered_scope,
    _write_csv,
    _write_json,
    build_longitudinal_artifacts,
)

SUBGROUP_SERIES_PER_METRIC = sum(REQUIRED_ENTITY_COUNTS.values())


@dataclass(frozen=True)
class PreparedRpsSourceHistory:
    """Full source history plus the complete joint A/H/S analytical panel."""

    analysis_panel: PreparedRpsPanel
    source_periods: tuple[str, ...]
    metric_periods: Mapping[str, tuple[str, ...]]
    subgroup_series_count: int
    national_series_count: int


def prepare_rps_source_history(
    snapshot: Mapping[str, Any],
    canonical_manifest: Mapping[str, Any],
    provider_scope: Mapping[str, Any],
) -> PreparedRpsSourceHistory:
    """Validate full history and derive a complete common construct window.

    Different constructs may have different legitimate source starts. What is not
    accepted is heterogeneity *within* one construct family across the 20 industry
    and 22 occupation entities. Each metric family must therefore be internally
    complete before its intersection with the other A/H/S families is considered.
    """

    manifest, series, _ = _validate_registered_scope(snapshot, canonical_manifest, provider_scope)
    manifest_digest = canonical_digest(
        [
            {
                "series_id": row["series_id"],
                "entity_type": row.get("entity_type"),
                "entity_index": row.get("entity_index"),
                "entity_id": row.get("entity_id"),
                "metric_id": row.get("metric_id"),
            }
            for row in sorted(manifest.values(), key=lambda item: str(item["series_id"]))
        ]
    )
    definition_digest = canonical_digest(
        [
            {field: row.get(field) for field in ("series_id", *_DEFINITION_FIELDS)}
            for row in sorted(series, key=lambda item: str(item.get("series_id")))
        ]
    )

    expected_subgroup_series = {
        series_id
        for series_id, row in manifest.items()
        if row.get("entity_type") in SUBGROUP_ENTITY_TYPES
        and row.get("metric_id") in SUBGROUP_METRICS
    }
    expected_national_series = {
        series_id for series_id, row in manifest.items() if row.get("entity_type") == "national"
    }
    if len(expected_subgroup_series) != 126:
        raise RpsReleaseError(
            f"Canonical subgroup inventory must contain 126 series, observed {len(expected_subgroup_series)}"
        )
    if len(expected_national_series) != 5:
        raise RpsReleaseError(
            f"Canonical national work inventory must contain 5 series, observed {len(expected_national_series)}"
        )

    expected_metric_series: dict[str, set[str]] = {
        metric_id: {
            series_id
            for series_id, row in manifest.items()
            if row.get("entity_type") in SUBGROUP_ENTITY_TYPES
            and row.get("metric_id") == metric_id
        }
        for metric_id in SUBGROUP_METRICS
    }
    for metric_id, series_ids in expected_metric_series.items():
        if len(series_ids) != SUBGROUP_SERIES_PER_METRIC:
            raise RpsReleaseError(
                f"Canonical {metric_id} subgroup inventory must contain "
                f"{SUBGROUP_SERIES_PER_METRIC} series, observed {len(series_ids)}"
            )

    period_rows: dict[str, list[dict[str, Any]]] = {}
    period_sets: dict[str, set[str]] = {}
    subgroup_records_all: list[AuditRecord] = []
    observed_count = 0

    for series_index, raw_series in enumerate(series):
        series_id = _required_string(
            raw_series, "series_id", context=f"snapshot.series[{series_index}]"
        )
        canonical = manifest[series_id]
        expected_identity = {
            "entity_type": canonical.get("entity_type"),
            "entity_id": canonical.get("entity_id"),
            "entity_name": canonical.get("entity_name"),
            "metric_id": canonical.get("metric_id"),
        }
        actual_identity = {key: raw_series.get(key) for key in expected_identity}
        if actual_identity != expected_identity:
            raise RpsReleaseError(
                f"Snapshot identity drift for {series_id}: expected {expected_identity!r}, "
                f"observed {actual_identity!r}"
            )
        entity_index = canonical.get("entity_index")
        if not isinstance(entity_index, int) or isinstance(entity_index, bool):
            raise RpsReleaseError(f"Canonical entity_index is invalid for {series_id}")

        observations = _rows(raw_series.get("observations"), context=f"{series_id}.observations")
        if not observations:
            raise RpsReleaseError(f"RPS series has no observations: {series_id}")
        seen_periods: set[str] = set()
        seen_dates: set[str] = set()
        for obs_index, observation in enumerate(observations):
            context = f"{series_id}.observations[{obs_index}]"
            obs_date = _required_string(observation, "date", context=context)
            period = _required_string(observation, "period", context=context)
            _period_key(period)
            if _quarter_for_date(obs_date) != period:
                raise RpsReleaseError(
                    f"Observation date/period mismatch for {series_id}: {obs_date} != {period}"
                )
            if period in seen_periods:
                raise RpsReleaseError(
                    f"Multiple observations for {series_id} in quarterly period {period}"
                )
            if obs_date in seen_dates:
                raise RpsReleaseError(f"Duplicate observation date for {series_id}: {obs_date}")
            seen_periods.add(period)
            seen_dates.add(obs_date)

            value = observation.get("value")
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise RpsReleaseError(f"{context}.value must be numeric")
            numeric = float(value)
            if not isfinite(numeric) or not 0.0 <= numeric <= 100.0:
                raise RpsReleaseError(
                    f"Observation value outside the registered percentage domain: "
                    f"{series_id} {period} {numeric!r}"
                )
            unit = _required_string(observation, "unit", context=context)
            source_url = _required_string(raw_series, "source_url", context=series_id)
            source_row = {
                "date": obs_date,
                "entity_id": str(raw_series["entity_id"]),
                "entity_type": str(raw_series["entity_type"]),
                "metric_id": str(raw_series["metric_id"]),
                "period": period,
                "series_id": series_id,
                "source_url": source_url,
                "unit": unit,
                "value": numeric,
            }
            period_rows.setdefault(period, []).append(source_row)
            observed_count += 1

            if series_id in expected_subgroup_series:
                subgroup_records_all.append(
                    AuditRecord(
                        entity_type=str(raw_series["entity_type"]),
                        entity_id=str(raw_series["entity_id"]),
                        entity_index=entity_index,
                        metric_id=str(raw_series["metric_id"]),
                        period=period,
                        value=numeric,
                        series_id=series_id,
                        audit_scope="private_release_candidate_input",
                        rights_status=str(raw_series.get("copyright_status", "")),
                    )
                )
        period_sets[series_id] = seen_periods

    metric_periods: dict[str, tuple[str, ...]] = {}
    for metric_id, series_ids in sorted(expected_metric_series.items()):
        family_shapes = {
            tuple(sorted(period_sets[series_id], key=_period_key)) for series_id in series_ids
        }
        if len(family_shapes) != 1:
            raise RpsReleaseError(
                f"RPS subgroup metric family {metric_id} does not share one complete "
                "quarterly period set across all 42 industry/occupation series"
            )
        metric_periods[metric_id] = next(iter(family_shapes))

    common_periods = set(metric_periods[next(iter(sorted(metric_periods)))])
    for periods in metric_periods.values():
        common_periods.intersection_update(periods)
    analysis_periods = tuple(sorted(common_periods, key=_period_key))
    if len(analysis_periods) < 2:
        raise RpsReleaseError(
            "Joint A/H/S longitudinal release candidates require at least two common quarters"
        )

    source_periods = tuple(
        sorted({period for values in period_sets.values() for period in values}, key=_period_key)
    )
    if not source_periods:
        raise RpsReleaseError("RPS source history contains no quarterly periods")

    expected_series_count = len(manifest)
    for period in source_periods:
        period_rows[period].sort(key=lambda row: str(row["series_id"]))
        series_ids = {str(row["series_id"]) for row in period_rows[period]}
        expected_ids = {
            series_id for series_id, values in period_sets.items() if period in values
        }
        if series_ids != expected_ids:
            raise RpsReleaseError(f"RPS source-period identity mismatch for {period}")

    # Every joint analytical quarter must contain all five national work series plus
    # every A/H/S subgroup series, producing a complete 131-series cross-section.
    for period in analysis_periods:
        rows = period_rows.get(period, [])
        if len(rows) != expected_series_count:
            raise RpsReleaseError(
                f"Incomplete canonical RPS analytical period {period}: "
                f"{len(rows)} of {expected_series_count}"
            )

    declared_observations = _required_int(snapshot, "observation_count", context="snapshot")
    if declared_observations != observed_count:
        raise RpsReleaseError(
            f"Snapshot observation_count mismatch: declared {declared_observations}, observed {observed_count}"
        )
    if sum(len(rows) for rows in period_rows.values()) != observed_count:
        raise RpsReleaseError("Period-partitioned RPS source rows do not cover every source observation")

    subgroup_series_ids = {record.series_id for record in subgroup_records_all}
    if subgroup_series_ids != expected_subgroup_series:
        raise RpsReleaseError("Subgroup RPS series coverage does not match the canonical manifest")
    expected_full_subgroup_observations = sum(
        SUBGROUP_SERIES_PER_METRIC * len(periods) for periods in metric_periods.values()
    )
    if len(subgroup_records_all) != expected_full_subgroup_observations:
        raise RpsReleaseError(
            f"Incomplete full subgroup history: expected {expected_full_subgroup_observations} rows, "
            f"observed {len(subgroup_records_all)}"
        )

    analysis_records = tuple(
        record for record in subgroup_records_all if record.period in common_periods
    )
    expected_analysis_observations = len(expected_subgroup_series) * len(analysis_periods)
    if len(analysis_records) != expected_analysis_observations:
        raise RpsReleaseError(
            f"Incomplete joint A/H/S analytical panel: expected {expected_analysis_observations} rows, "
            f"observed {len(analysis_records)}"
        )

    for period in analysis_periods:
        for entity_type, expected_entities in REQUIRED_ENTITY_COUNTS.items():
            entities = {
                record.entity_id
                for record in analysis_records
                if record.period == period and record.entity_type == entity_type
            }
            if len(entities) != expected_entities:
                raise RpsReleaseError(
                    f"Incomplete {entity_type} entity coverage for {period}: "
                    f"{len(entities)} of {expected_entities}"
                )

    analysis_panel = PreparedRpsPanel(
        periods=analysis_periods,
        period_rows={period: tuple(rows) for period, rows in period_rows.items()},
        subgroup_records=analysis_records,
        definition_id=f"sha256:{definition_digest}",
        taxonomy_version=f"sha256:{manifest_digest}",
        series_count=expected_series_count,
        observation_count=observed_count,
    )
    return PreparedRpsSourceHistory(
        analysis_panel=analysis_panel,
        source_periods=source_periods,
        metric_periods=metric_periods,
        subgroup_series_count=len(expected_subgroup_series),
        national_series_count=len(expected_national_series),
    )


def build_rps_release_candidate_complete_history(
    snapshot: Mapping[str, Any],
    canonical_manifest: Mapping[str, Any],
    provider_scope: Mapping[str, Any],
    claim_inventory: Mapping[str, Any],
    *,
    output_dir: Path,
    release_id: str,
    builder_commit: str,
    previous_release: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a release candidate that binds full source history and joint A/H/S analytics."""

    if not re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", builder_commit):
        raise RpsReleaseError("builder_commit must be a 40- or 64-character hexadecimal commit")
    if not release_id or re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,127}", release_id) is None:
        raise RpsReleaseError("release_id must be a lowercase release slug")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise RpsReleaseError(f"Candidate output directory must be new or empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    prepared = prepare_rps_source_history(snapshot, canonical_manifest, provider_scope)
    panel = prepared.analysis_panel
    source_id = _required_string(snapshot, "source_id", context="snapshot")
    source_content_sha = _required_string(snapshot, "content_sha256", context="snapshot")
    provider_release_id = _required_int(snapshot, "provider_release_id", context="snapshot")

    source_objects: list[dict[str, Any]] = []
    input_hashes: dict[str, str] = {}
    for period in prepared.source_periods:
        object_id = period.lower()
        relative = f"inputs/rps/{period}.json"
        source_payload: object = {
            "schema_version": 1,
            "source_id": source_id,
            "provider_release_id": provider_release_id,
            "period": period,
            "record_count": len(panel.period_rows[period]),
            "records": list(panel.period_rows[period]),
        }
        sha256, size = _write_json(output_dir / relative, source_payload)
        source_objects.append(
            {
                "object_id": object_id,
                "locator": RPS_SOURCE_URL,
                "local_path": relative,
                "sha256": sha256,
                "size_bytes": size,
            }
        )
        input_hashes[f"{source_id}:{object_id}"] = sha256

    longitudinal, quarter_rows, rank_rows, validation = build_longitudinal_artifacts(
        panel, source_content_sha256=source_content_sha
    )
    validation["source_history_periods"] = list(prepared.source_periods)
    validation["analysis_metric_periods"] = {
        metric_id: list(periods) for metric_id, periods in sorted(prepared.metric_periods.items())
    }
    validation["source_history_observation_count"] = panel.observation_count
    validation["subgroup_series_count"] = prepared.subgroup_series_count
    validation["national_series_count"] = prepared.national_series_count

    artifact_specs: list[tuple[str, str, str, object, Sequence[str] | None]] = [
        (
            "rps-longitudinal-diagnostics",
            "artifacts/longitudinal/longitudinal_diagnostics.json",
            "json",
            longitudinal,
            None,
        ),
        (
            "rps-quarter-diagnostics",
            "artifacts/longitudinal/quarter_diagnostics.csv",
            "csv",
            quarter_rows,
            list(quarter_rows[0]),
        ),
        (
            "rps-rank-stability",
            "artifacts/longitudinal/rank_stability.csv",
            "csv",
            rank_rows,
            list(rank_rows[0]),
        ),
        (
            "rps-longitudinal-validation",
            "artifacts/longitudinal/validation_checks.json",
            "json",
            validation,
            None,
        ),
    ]
    artifacts: list[dict[str, Any]] = []
    output_hashes: dict[str, str] = {}
    for artifact_id, relative, kind, artifact_payload, fieldnames in artifact_specs:
        path = output_dir / relative
        if kind == "json":
            sha256, size = _write_json(path, artifact_payload)
        else:
            assert isinstance(artifact_payload, list)
            assert fieldnames is not None
            sha256, size = _write_csv(path, artifact_payload, fieldnames=fieldnames)
        artifacts.append(
            {
                "artifact_id": artifact_id,
                "path": relative,
                "sha256": sha256,
                "size_bytes": size,
                "evidence_class": 2,
                "source_ids": [source_id],
            }
        )
        output_hashes[artifact_id] = sha256

    source_status = _source_transition_status(
        previous_release,
        source_id=source_id,
        current_objects=source_objects,
        current_periods=prepared.source_periods,
    )
    release_type = _release_type(
        previous_release, source_status=source_status, artifacts=artifacts
    )
    diagnostics = _diagnostic_manifest(
        longitudinal, quarter_rows, validation, periods=panel.periods
    )
    claims = _claim_rows(claim_inventory, periods=panel.periods, artifacts=artifacts)

    provider_title = _required_string(
        provider_scope, "provider_release_title", context="provider_scope"
    )
    analytical_observed = sum(len(panel.period_rows[period]) for period in panel.periods)
    analytical_required = panel.series_count * len(panel.periods)
    if analytical_observed != analytical_required:
        raise RpsReleaseError(
            "RPS analytical-period full-series coverage failed after source-history preparation"
        )
    source = {
        "source_id": source_id,
        "provider": _required_string(snapshot, "provider", context="snapshot"),
        "dataset": provider_title,
        "source_vintage_id": f"sha256:{source_content_sha}",
        "retrieved_at": _required_string(snapshot, "retrieved_at", context="snapshot"),
        "revision_status": source_status,
        "reference_periods": list(prepared.source_periods),
        "analysis_reference_periods": list(panel.periods),
        "analysis_metric_reference_periods": {
            metric_id: list(periods)
            for metric_id, periods in sorted(prepared.metric_periods.items())
        },
        "instrument_version": "not-versioned-in-fred-distribution",
        "definition_id": panel.definition_id,
        "taxonomy_versions": {"rps_source_series_manifest": panel.taxonomy_version},
        "rights": {
            "status": "approved",
            "storage_scope": "private",
            "publication_scope": "derived_only",
            "redistribution_scope": "derived_only",
        },
        "coverage": {
            "status": "pass",
            "required_units": analytical_required,
            "observed_units": analytical_observed,
            "full_source_observed_units": panel.observation_count,
            "subgroup_series_count": prepared.subgroup_series_count,
            "national_series_count": prepared.national_series_count,
        },
        "objects": source_objects,
    }

    supersedes = previous_release.get("release_id") if previous_release is not None else None
    if supersedes is not None and (not isinstance(supersedes, str) or not supersedes):
        raise RpsReleaseError("Previous release manifest has an invalid release_id")
    candidate = {
        "schema_version": 1,
        "release_id": release_id,
        "release_type": release_type,
        "data_mode": "derived_only",
        "created_at": _required_string(snapshot, "retrieved_at", context="snapshot"),
        "supersedes_release_id": supersedes,
        "sources": [source],
        "artifacts": artifacts,
        "diagnostics": diagnostics,
        "claims": claims,
        "build": {
            "builder_id": "rps-published-aggregate-construct-window-release-v3",
            "builder_commit": builder_commit.lower(),
            "deterministic": True,
            "input_sha256": input_hashes,
            "output_sha256": output_hashes,
        },
        "candidate_scope": (
            "RPS longitudinal component only; complete 131-series source history is bound in "
            "private inputs. Each A/H/S subgroup construct family must be internally complete; "
            "joint longitudinal claims use only their common complete period window. Do not "
            "promote as the first global observatory baseline unless the complete public "
            "observatory release composition has been reviewed."
        ),
        "source_input_bytes_publication": False,
    }
    _write_json(output_dir / "release.json", candidate)
    return candidate
