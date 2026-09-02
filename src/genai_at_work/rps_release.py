"""Build release-engine-compatible RPS longitudinal candidate packages.

The input is a previously validated private RPS aggregate refresh snapshot. This
module revalidates the snapshot's scientific content identity, materializes
period-partitioned private source objects, regenerates rights-safe longitudinal
artifacts, and emits a release manifest compatible with the generic observatory
release engine.

It never fetches data and never promotes a release. Source observation bytes
remain under ``inputs/`` in the private/transient candidate package; only
declared derived artifacts are eligible for the release engine's public archive.
"""

from __future__ import annotations

import csv
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from math import comb, isfinite
from pathlib import Path
from typing import Any

from genai_at_work.longitudinal import (
    AuditRecord,
    METRIC_MAP,
    REQUIRED_ENTITY_COUNTS,
    quarter_diagnostic,
    ranks,
    spearman,
)
from genai_at_work.release_engine import canonical_digest, sha256_file

SUBGROUP_ENTITY_TYPES = {"industry", "occupation"}
SUBGROUP_METRIC_IDS = tuple(METRIC_MAP)
SUBGROUP_METRICS = frozenset(SUBGROUP_METRIC_IDS)
RPS_SOURCE_URL = "https://fred.stlouisfed.org/release?rid=6"
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
    "source_url",
    "copyright_status",
    "citation_text",
)
_QUARTER_RE = re.compile(r"^(\d{4})-Q([1-4])$")


class RpsReleaseError(RuntimeError):
    """Raised when a private RPS snapshot cannot form a release candidate."""


@dataclass(frozen=True)
class PreparedRpsPanel:
    """Validated source rows needed by the RPS release-candidate builder."""

    periods: tuple[str, ...]
    period_rows: Mapping[str, tuple[dict[str, Any], ...]]
    subgroup_records: tuple[AuditRecord, ...]
    definition_id: str
    taxonomy_version: str
    series_count: int
    observation_count: int


def _required_string(mapping: Mapping[str, Any], key: str, *, context: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise RpsReleaseError(f"{context}.{key} must be a non-empty string")
    return value


def _required_int(mapping: Mapping[str, Any], key: str, *, context: str) -> int:
    value = mapping.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise RpsReleaseError(f"{context}.{key} must be an integer")
    return value


def _rows(value: object, *, context: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise RpsReleaseError(f"{context} must be a JSON array")
    rows: list[dict[str, Any]] = []
    for index, raw in enumerate(value):
        if not isinstance(raw, dict):
            raise RpsReleaseError(f"{context}[{index}] must be a JSON object")
        rows.append({str(key): item for key, item in raw.items()})
    return rows


def _canonical_json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _write_bytes(path: Path, payload: bytes) -> tuple[str, int]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return sha256_file(path), path.stat().st_size


def _write_json(path: Path, value: object) -> tuple[str, int]:
    return _write_bytes(path, _canonical_json_bytes(value))


def _write_csv(
    path: Path,
    rows: Sequence[Mapping[str, Any]],
    *,
    fieldnames: Sequence[str],
) -> tuple[str, int]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return sha256_file(path), path.stat().st_size


def _period_key(period: str) -> tuple[int, int]:
    match = _QUARTER_RE.fullmatch(period)
    if match is None:
        raise RpsReleaseError(f"Invalid quarterly period label: {period!r}")
    return int(match.group(1)), int(match.group(2))


def _quarter_for_date(value: str) -> str:
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise RpsReleaseError(f"Invalid observation date: {value!r}") from exc
    quarter = ((parsed.month - 1) // 3) + 1
    return f"{parsed.year}-Q{quarter}"


def _median(values: Sequence[float]) -> float:
    if not values:
        raise RpsReleaseError("Median requires at least one value")
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def _stable_snapshot_series(series: Mapping[str, Any]) -> dict[str, Any]:
    observations = _rows(series.get("observations"), context="series.observations")
    stable_observations = sorted(
        (
            {
                "date": row.get("date"),
                "period": row.get("period"),
                "value": row.get("value"),
                "unit": row.get("unit"),
            }
            for row in observations
        ),
        key=lambda row: str(row["date"]),
    )
    return {
        **{field: series.get(field) for field in _DEFINITION_FIELDS},
        "observations": stable_observations,
    }


def snapshot_content_sha256(snapshot: Mapping[str, Any]) -> str:
    """Recompute the scientific content identity defined by the refresh layer."""

    series = _rows(snapshot.get("series"), context="snapshot.series")
    excluded = _rows(snapshot.get("excluded_series"), context="snapshot.excluded_series")
    stable_series = sorted(
        (_stable_snapshot_series(row) for row in series),
        key=lambda row: str(row.get("series_id")),
    )
    included_ids = {str(row.get("series_id")) for row in series}
    excluded_ids = {str(row.get("series_id")) for row in excluded}
    provider_series_ids = sorted(included_ids | excluded_ids)
    stable_content = {
        "provider_release_id": snapshot.get("provider_release_id"),
        "provider_series_ids": provider_series_ids,
        "series": stable_series,
        "excluded_series_ids": sorted(excluded_ids),
    }
    return canonical_digest(stable_content)


def _manifest_by_series_id(canonical_manifest: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    expected_count = _required_int(canonical_manifest, "series_count", context="manifest")
    rows = _rows(canonical_manifest.get("series"), context="manifest.series")
    indexed: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        series_id = _required_string(row, "series_id", context=f"manifest.series[{index}]")
        if series_id in indexed:
            raise RpsReleaseError(f"Duplicate canonical series_id: {series_id}")
        indexed[series_id] = row
    if len(indexed) != expected_count:
        raise RpsReleaseError(
            f"Canonical manifest count mismatch: declared {expected_count}, observed {len(indexed)}"
        )
    return indexed


def _validate_registered_scope(
    snapshot: Mapping[str, Any],
    canonical_manifest: Mapping[str, Any],
    provider_scope: Mapping[str, Any],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    if snapshot.get("schema_version") != 1:
        raise RpsReleaseError("snapshot.schema_version must equal 1")
    if snapshot.get("snapshot_type") != "rps_published_aggregate_refresh":
        raise RpsReleaseError("Unsupported RPS snapshot_type")
    if snapshot.get("rights") is None or not isinstance(snapshot.get("rights"), Mapping):
        raise RpsReleaseError("snapshot.rights must be an object")
    rights = snapshot["rights"]
    assert isinstance(rights, Mapping)
    if rights.get("status") != "approved":
        raise RpsReleaseError("RPS snapshot rights are not approved")
    if rights.get("public_bulk_redistribution_approved") is not False:
        raise RpsReleaseError("RPS snapshot must preserve the no-bulk-redistribution boundary")

    scope_status = provider_scope.get("source_owner_permission_status")
    if scope_status != "granted_for_published_aggregate_project_use":
        raise RpsReleaseError(
            "Current provider scope does not grant published aggregate project use"
        )
    if snapshot.get("provider_release_id") != provider_scope.get("provider_release_id"):
        raise RpsReleaseError("Snapshot provider release does not match the registered scope")

    inventory = snapshot.get("inventory")
    if not isinstance(inventory, Mapping):
        raise RpsReleaseError("snapshot.inventory must be an object")
    exact_inventory = {
        "provider_series_count": provider_scope.get("provider_release_series_count"),
        "observatory_series_count": provider_scope.get("observatory_registry_series_count"),
        "excluded_series_count": len(
            _rows(
                provider_scope.get("intentionally_excluded_national_series"),
                context="provider_scope.intentionally_excluded_national_series",
            )
        ),
        "provider_inventory_status": "pass",
    }
    observed_inventory = {key: inventory.get(key) for key in exact_inventory}
    if observed_inventory != exact_inventory:
        raise RpsReleaseError(
            f"Snapshot inventory does not match registered provider scope: {observed_inventory!r}"
        )

    manifest = _manifest_by_series_id(canonical_manifest)
    series = _rows(snapshot.get("series"), context="snapshot.series")
    excluded = _rows(snapshot.get("excluded_series"), context="snapshot.excluded_series")

    series_ids = [str(row.get("series_id")) for row in series]
    if len(series_ids) != len(set(series_ids)):
        raise RpsReleaseError("snapshot.series contains duplicate series_id values")
    if set(series_ids) != set(manifest):
        missing = sorted(set(manifest) - set(series_ids))
        unexpected = sorted(set(series_ids) - set(manifest))
        raise RpsReleaseError(
            f"Snapshot canonical series inventory drift: missing={missing}, unexpected={unexpected}"
        )

    expected_excluded = {
        str(row["series_id"])
        for row in _rows(
            provider_scope.get("intentionally_excluded_national_series"),
            context="provider_scope.intentionally_excluded_national_series",
        )
    }
    observed_excluded = {str(row.get("series_id")) for row in excluded}
    if observed_excluded != expected_excluded:
        raise RpsReleaseError("Snapshot excluded-series inventory does not match provider scope")
    if any(row.get("observations_retrieved") is not False for row in excluded):
        raise RpsReleaseError("Excluded RPS constructs must not contain retrieved observations")

    expected_content = _required_string(snapshot, "content_sha256", context="snapshot")
    actual_content = snapshot_content_sha256(snapshot)
    if actual_content != expected_content:
        raise RpsReleaseError(
            "RPS snapshot scientific content hash mismatch; source bytes may have changed"
        )
    return manifest, series, excluded


def prepare_rps_panel(
    snapshot: Mapping[str, Any],
    canonical_manifest: Mapping[str, Any],
    provider_scope: Mapping[str, Any],
) -> PreparedRpsPanel:
    """Validate an RPS snapshot and prepare complete period-partitioned source rows."""

    manifest, series, _ = _validate_registered_scope(
        snapshot, canonical_manifest, provider_scope
    )
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

    period_rows: dict[str, list[dict[str, Any]]] = {}
    period_sets: dict[str, set[str]] = {}
    subgroup_records: list[AuditRecord] = []
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
                f"Snapshot identity drift for {series_id}: "
                f"expected {expected_identity!r}, observed {actual_identity!r}"
            )
        entity_index = canonical.get("entity_index")
        if not isinstance(entity_index, int) or isinstance(entity_index, bool):
            raise RpsReleaseError(f"Canonical entity_index is invalid for {series_id}")

        observations = _rows(
            raw_series.get("observations"), context=f"{series_id}.observations"
        )
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

            if (
                str(raw_series["entity_type"]) in SUBGROUP_ENTITY_TYPES
                and str(raw_series["metric_id"]) in SUBGROUP_METRICS
            ):
                subgroup_records.append(
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

    distinct_period_sets = {tuple(sorted(values, key=_period_key)) for values in period_sets.values()}
    if len(distinct_period_sets) != 1:
        raise RpsReleaseError(
            "RPS canonical series do not share one complete quarterly period set"
        )
    periods = tuple(sorted(next(iter(period_sets.values())), key=_period_key))
    if len(periods) < 2:
        raise RpsReleaseError("Longitudinal release candidates require at least two quarters")

    expected_series = len(manifest)
    expected_total = expected_series * len(periods)
    if observed_count != expected_total:
        raise RpsReleaseError(
            f"RPS panel coverage mismatch: expected {expected_total} observations, "
            f"observed {observed_count}"
        )
    for period in periods:
        rows = period_rows.get(period, [])
        if len(rows) != expected_series:
            raise RpsReleaseError(
                f"Incomplete canonical RPS period {period}: {len(rows)} of {expected_series}"
            )
        rows.sort(key=lambda row: str(row["series_id"]))

    subgroup_series_ids = {record.series_id for record in subgroup_records}
    expected_subgroup_series = {
        series_id
        for series_id, row in manifest.items()
        if row.get("entity_type") in SUBGROUP_ENTITY_TYPES
        and row.get("metric_id") in SUBGROUP_METRICS
    }
    if subgroup_series_ids != expected_subgroup_series:
        raise RpsReleaseError("Subgroup RPS series coverage does not match the canonical manifest")
    expected_subgroup_observations = len(expected_subgroup_series) * len(periods)
    if len(subgroup_records) != expected_subgroup_observations:
        raise RpsReleaseError(
            f"Incomplete subgroup panel: expected {expected_subgroup_observations} rows, "
            f"observed {len(subgroup_records)}"
        )

    for period in periods:
        for entity_type, expected_entities in REQUIRED_ENTITY_COUNTS.items():
            entities = {
                record.entity_id
                for record in subgroup_records
                if record.period == period and record.entity_type == entity_type
            }
            if len(entities) != expected_entities:
                raise RpsReleaseError(
                    f"Incomplete {entity_type} entity coverage for {period}: "
                    f"{len(entities)} of {expected_entities}"
                )

    return PreparedRpsPanel(
        periods=periods,
        period_rows={
            period: tuple(period_rows[period])
            for period in periods
        },
        subgroup_records=tuple(subgroup_records),
        definition_id=f"sha256:{definition_digest}",
        taxonomy_version=f"sha256:{manifest_digest}",
        series_count=expected_series,
        observation_count=observed_count,
    )


def _rank_vector(
    records: Sequence[AuditRecord],
    entity_type: str,
    period: str,
    metric: str,
) -> list[float]:
    metric_id = next(
        (source for source, short in METRIC_MAP.items() if short == metric),
        None,
    )
    if metric_id is None:
        raise RpsReleaseError(f"Unsupported rank-stability metric: {metric}")
    rows = [
        row for row in records
        if row.entity_type == entity_type
        and row.period == period
        and row.metric_id == metric_id
    ]
    rows.sort(key=lambda row: row.entity_index)
    if len(rows) != REQUIRED_ENTITY_COUNTS[entity_type]:
        raise RpsReleaseError(
            f"Incomplete {metric} vector for {entity_type} {period}: {len(rows)}"
        )
    return ranks([row.value for row in rows])


def _rank_stability_detail(
    records: Sequence[AuditRecord],
    entity_type: str,
    metric: str,
    periods: Sequence[str],
) -> dict[str, object]:
    rank_by_period = {
        period: _rank_vector(records, entity_type, period, metric)
        for period in periods
    }
    pairs = [
        (periods[left], periods[right])
        for left in range(len(periods))
        for right in range(left + 1, len(periods))
    ]
    pairwise = [
        spearman(rank_by_period[first], rank_by_period[second])
        for first, second in pairs
    ]
    consecutive = [
        [
            periods[index],
            periods[index + 1],
            spearman(
                rank_by_period[periods[index]],
                rank_by_period[periods[index + 1]],
            ),
        ]
        for index in range(len(periods) - 1)
    ]
    return {
        "consecutive": consecutive,
        "endpoint": spearman(rank_by_period[periods[0]], rank_by_period[periods[-1]]),
        "max_pairwise": max(pairwise),
        "median_pairwise": _median(pairwise),
        "min_pairwise": min(pairwise),
    }


def _rank_stability_summary(
    records: Sequence[AuditRecord],
    entity_type: str,
    metric: str,
    periods: Sequence[str],
) -> dict[str, Any]:
    detail = _rank_stability_detail(records, entity_type, metric, periods)
    consecutive = detail["consecutive"]
    if not isinstance(consecutive, list):
        raise RpsReleaseError("Rank-stability consecutive detail must be a list")
    consecutive_values = [float(row[2]) for row in consecutive if isinstance(row, list)]
    if len(consecutive_values) != len(periods) - 1:
        raise RpsReleaseError("Rank-stability consecutive detail is incomplete")
    return {
        "metric": metric,
        "median_pairwise_rank_corr": detail["median_pairwise"],
        "min_pairwise": detail["min_pairwise"],
        "max_pairwise": detail["max_pairwise"],
        "median_consecutive": _median(consecutive_values),
        "endpoint": detail["endpoint"],
        "entity_type": entity_type,
    }


def _rank_stability_dominance(
    records: Sequence[AuditRecord],
    periods: Sequence[str],
) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    pairs = [
        (periods[left], periods[right])
        for left in range(len(periods))
        for right in range(left + 1, len(periods))
    ]
    for entity_type in ("industry", "occupation"):
        vectors = {
            metric: {
                period: _rank_vector(records, entity_type, period, metric)
                for period in periods
            }
            for metric in ("A", "H", "S")
        }
        a_gt_h = a_gt_s = s_gt_h = 0
        for first, second in pairs:
            corr_a = spearman(vectors["A"][first], vectors["A"][second])
            corr_h = spearman(vectors["H"][first], vectors["H"][second])
            corr_s = spearman(vectors["S"][first], vectors["S"][second])
            a_gt_h += int(corr_a > corr_h)
            a_gt_s += int(corr_a > corr_s)
            s_gt_h += int(corr_s > corr_h)
        result[entity_type] = {
            "adoption_rank_corr_gt_assisted_hours_rank_corr": a_gt_h,
            "adoption_rank_corr_gt_reported_savings_rank_corr": a_gt_s,
            "quarter_pairs": len(pairs),
            "reported_savings_rank_corr_gt_assisted_hours_rank_corr": s_gt_h,
        }
    return result


def _quarter_rows(
    records: Sequence[AuditRecord],
    periods: Sequence[str],
) -> list[dict[str, Any]]:
    return [
        dict(quarter_diagnostic(records, entity_type, period))
        for entity_type in ("industry", "occupation")
        for period in periods
    ]


def _nested_quarter_rows(
    quarter_rows: Sequence[Mapping[str, Any]],
) -> dict[str, dict[str, dict[str, float | int]]]:
    nested: dict[str, dict[str, dict[str, float | int]]] = {
        "industry": {},
        "occupation": {},
    }
    for row in quarter_rows:
        entity_type = str(row["entity_type"])
        period = str(row["period"])
        nested[entity_type][period] = {
            str(key): value
            for key, value in row.items()
            if key not in {"entity_type", "period"}
            and isinstance(value, (int, float))
            and not isinstance(value, bool)
        }
    return nested


def _cross_level_comparison(
    nested: Mapping[str, Mapping[str, Mapping[str, float | int]]],
    periods: Sequence[str],
) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    for period in periods:
        industry = nested["industry"][period]
        occupation = nested["occupation"][period]
        result[period] = {
            "industry_H_minus_A_for_S_r2": (
                float(industry["r2_S_H"]) - float(industry["r2_S_A"])
            ),
            "industry_incremental_H_given_A_r2": float(
                industry["increment_H_given_A"]
            ),
            "occupation_A_minus_H_for_S_r2": (
                float(occupation["r2_S_A"]) - float(occupation["r2_S_H"])
            ),
            "occupation_incremental_H_given_A_r2": float(
                occupation["increment_H_given_A"]
            ),
            "occupation_minus_industry_pearson_A_H": (
                float(occupation["r_A_H"]) - float(industry["r_A_H"])
            ),
            "occupation_minus_industry_spearman_A_H": (
                float(occupation["spearman_A_H"]) - float(industry["spearman_A_H"])
            ),
        }
    return result


def _rounded(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 10)
    if isinstance(value, list):
        return [_rounded(item) for item in value]
    if isinstance(value, tuple):
        return [_rounded(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _rounded(item) for key, item in value.items()}
    return value


def build_longitudinal_artifacts(
    panel: PreparedRpsPanel,
    *,
    source_content_sha256: str,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Regenerate deterministic longitudinal artifacts for every complete quarter."""

    periods = panel.periods
    records = panel.subgroup_records
    quarter_rows = _quarter_rows(records, periods)
    nested = _nested_quarter_rows(quarter_rows)
    rank_detail = {
        entity_type: {
            metric: _rank_stability_detail(records, entity_type, metric, periods)
            for metric in ("A", "H", "S")
        }
        for entity_type in ("industry", "occupation")
    }
    rank_rows = [
        _rank_stability_summary(records, entity_type, metric, periods)
        for entity_type in ("industry", "occupation")
        for metric in ("A", "H", "S")
    ]
    rank_dominance = _rank_stability_dominance(records, periods)

    diagnostics = _rounded(
        {
            "schema_version": 1,
            "source_content_sha256": source_content_sha256,
            "input_scope": {
                "industry_entities": REQUIRED_ENTITY_COUNTS["industry"],
                "metrics": list(SUBGROUP_METRIC_IDS),
                "occupation_entities": REQUIRED_ENTITY_COUNTS["occupation"],
                "periods": list(periods),
                "subgroup_series": len({record.series_id for record in records}),
            },
            "interpretive_guardrails": [
                "All regressions are unweighted aggregate cross-sectional descriptive diagnostics.",
                "No conventional significance claims are licensed without approved subgroup uncertainty inputs.",
                "Reported time savings are self-reported counterfactual hours, not measured labor productivity.",
                "Quarterly instability may reflect both underlying change and sampling noise.",
            ],
            "quarter_diagnostics": nested,
            "rank_stability": rank_detail,
            "rank_stability_dominance": rank_dominance,
            "cross_level_comparison": _cross_level_comparison(nested, periods),
            "status": "DERIVED RESEARCH DIAGNOSTICS; DESCRIPTIVE, NOT CAUSAL",
        }
    )

    unique_keys = {
        (record.entity_type, record.entity_id, record.metric_id, record.period)
        for record in records
    }
    expected_subgroup = (
        sum(REQUIRED_ENTITY_COUNTS.values())
        * len(SUBGROUP_METRICS)
        * len(periods)
    )
    validation_checks = {
        "canonical_series_count": panel.series_count == 131,
        "complete_period_source_rows": all(
            len(panel.period_rows[period]) == panel.series_count for period in periods
        ),
        "industry_entities_complete": all(
            len(
                {
                    record.entity_id
                    for record in records
                    if record.period == period and record.entity_type == "industry"
                }
            )
            == REQUIRED_ENTITY_COUNTS["industry"]
            for period in periods
        ),
        "metrics_exact": {record.metric_id for record in records} == set(SUBGROUP_METRICS),
        "occupation_entities_complete": all(
            len(
                {
                    record.entity_id
                    for record in records
                    if record.period == period and record.entity_type == "occupation"
                }
            )
            == REQUIRED_ENTITY_COUNTS["occupation"]
            for period in periods
        ),
        "period_count_at_least_two": len(periods) >= 2,
        "subgroup_observation_count": len(records) == expected_subgroup,
        "unique_subgroup_keys": len(unique_keys) == len(records),
        "values_finite_0_100": all(
            isfinite(record.value) and 0.0 <= record.value <= 100.0
            for record in records
        ),
    }
    validation = {
        "schema_version": 1,
        "all_passed": all(validation_checks.values()),
        "check_count": len(validation_checks),
        "checks": validation_checks,
        "periods": list(periods),
        "source_content_sha256": source_content_sha256,
    }
    if not validation["all_passed"]:
        raise RpsReleaseError("RPS longitudinal validation checks failed unexpectedly")
    return diagnostics, quarter_rows, rank_rows, validation


def _diagnostic_manifest(
    longitudinal: Mapping[str, Any],
    quarter_rows: Sequence[Mapping[str, Any]],
    validation: Mapping[str, Any],
    *,
    periods: Sequence[str],
) -> list[dict[str, Any]]:
    rank_stability = longitudinal["rank_stability"]
    assert isinstance(rank_stability, Mapping)
    expected_pairs = comb(len(periods), 2)

    stability_values: list[float] = []
    stability_pass = True
    for entity_type in ("industry", "occupation"):
        by_metric = rank_stability.get(entity_type)
        if not isinstance(by_metric, Mapping):
            stability_pass = False
            continue
        for metric in ("A", "H", "S"):
            detail = by_metric.get(metric)
            if not isinstance(detail, Mapping):
                stability_pass = False
                continue
            values = [
                detail.get("endpoint"),
                detail.get("max_pairwise"),
                detail.get("median_pairwise"),
                detail.get("min_pairwise"),
            ]
            if not all(
                isinstance(value, (int, float))
                and not isinstance(value, bool)
                and isfinite(float(value))
                and -1.0 <= float(value) <= 1.0
                for value in values
            ):
                stability_pass = False
            stability_values.extend(
                float(value) for value in values if isinstance(value, (int, float))
            )
            consecutive = detail.get("consecutive")
            if not isinstance(consecutive, list) or len(consecutive) != len(periods) - 1:
                stability_pass = False

    dominance = longitudinal.get("rank_stability_dominance")
    if not isinstance(dominance, Mapping):
        stability_pass = False
    else:
        for entity_type in ("industry", "occupation"):
            detail = dominance.get(entity_type)
            if not isinstance(detail, Mapping) or detail.get("quarter_pairs") != expected_pairs:
                stability_pass = False

    influence_pass = True
    influence_evidence: list[dict[str, Any]] = []
    regression_pass = True
    regression_evidence: list[dict[str, Any]] = []
    for row in quarter_rows:
        n = row.get("n")
        loo_a = row.get("loo_A_beats_H")
        loo_h = row.get("loo_H_beats_A")
        low = row.get("loo_H_minus_A_min")
        high = row.get("loo_H_minus_A_max")
        if (
            not isinstance(n, int)
            or isinstance(n, bool)
            or not isinstance(loo_a, int)
            or isinstance(loo_a, bool)
            or not isinstance(loo_h, int)
            or isinstance(loo_h, bool)
            or loo_a < 0
            or loo_h < 0
            or loo_a + loo_h > n
            or not isinstance(low, (int, float))
            or not isinstance(high, (int, float))
            or not isfinite(float(low))
            or not isfinite(float(high))
            or float(low) > float(high)
        ):
            influence_pass = False
        influence_evidence.append(
            {
                "entity_type": row.get("entity_type"),
                "period": row.get("period"),
                "n": n,
                "loo_A_beats_H": loo_a,
                "loo_H_beats_A": loo_h,
                "loo_H_minus_A_min": low,
                "loo_H_minus_A_max": high,
            }
        )

        correlation_fields = ("r_A_H", "spearman_A_H")
        r2_fields = ("r2_H_A", "r2_S_A", "r2_S_H", "r2_S_A_H")
        for field in correlation_fields:
            value = row.get(field)
            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not isfinite(float(value))
                or not -1.0 <= float(value) <= 1.0
            ):
                regression_pass = False
        for field in r2_fields:
            value = row.get(field)
            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not isfinite(float(value))
                or not -1e-10 <= float(value) <= 1.0 + 1e-10
            ):
                regression_pass = False
        for field in ("increment_H_given_A", "increment_A_given_H"):
            value = row.get(field)
            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not isfinite(float(value))
                or float(value) < -1e-9
            ):
                regression_pass = False
        regression_evidence.append(
            {
                "entity_type": row.get("entity_type"),
                "period": row.get("period"),
                **{
                    field: row.get(field)
                    for field in (*correlation_fields, *r2_fields)
                },
                "increment_H_given_A": row.get("increment_H_given_A"),
                "increment_A_given_H": row.get("increment_A_given_H"),
            }
        )

    coverage_pass = validation.get("all_passed") is True
    return [
        {
            "diagnostic_id": "rps-longitudinal-stability",
            "diagnostic_class": "stability",
            "status": "pass" if stability_pass else "fail",
            "value_digest": canonical_digest(
                {
                    "periods": list(periods),
                    "rank_stability": rank_stability,
                    "rank_stability_dominance": dominance,
                    "finite_values": stability_values,
                }
            ),
        },
        {
            "diagnostic_id": "rps-longitudinal-influence",
            "diagnostic_class": "influence",
            "status": "pass" if influence_pass else "fail",
            "value_digest": canonical_digest(influence_evidence),
        },
        {
            "diagnostic_id": "rps-longitudinal-regression-contract",
            "diagnostic_class": "regression_contract",
            "status": "pass" if regression_pass else "fail",
            "value_digest": canonical_digest(regression_evidence),
        },
        {
            "diagnostic_id": "rps-longitudinal-suppression-coverage",
            "diagnostic_class": "suppression_coverage",
            "status": "pass" if coverage_pass else "fail",
            "value_digest": canonical_digest(validation),
        },
    ]


def _source_transition_status(
    previous_release: Mapping[str, Any] | None,
    *,
    source_id: str,
    current_objects: Sequence[Mapping[str, Any]],
    current_periods: Sequence[str],
) -> str:
    if previous_release is None:
        return "new_wave"
    previous_sources = previous_release.get("sources")
    if not isinstance(previous_sources, list):
        raise RpsReleaseError("Previous release manifest has no source list")
    previous_source = next(
        (
            row
            for row in previous_sources
            if isinstance(row, Mapping) and row.get("source_id") == source_id
        ),
        None,
    )
    if previous_source is None:
        return "new_wave"

    old_periods = {str(value) for value in previous_source.get("reference_periods", [])}
    new_periods = set(current_periods)
    old_objects_raw = previous_source.get("objects")
    if not isinstance(old_objects_raw, list):
        raise RpsReleaseError("Previous RPS source has no source-object list")
    old_objects = {
        str(row.get("object_id")): row
        for row in old_objects_raw
        if isinstance(row, Mapping)
    }
    new_objects = {str(row["object_id"]): row for row in current_objects}

    added_periods = new_periods - old_periods
    removed_periods = old_periods - new_periods
    added_objects = set(new_objects) - set(old_objects)
    removed_objects = set(old_objects) - set(new_objects)
    modified_objects = {
        object_id
        for object_id in set(old_objects) & set(new_objects)
        if old_objects[object_id].get("sha256") != new_objects[object_id].get("sha256")
    }
    has_new_wave = bool(added_periods)
    has_revision = bool(
        removed_periods
        or removed_objects
        or modified_objects
        or (added_objects and not added_periods)
    )
    if has_new_wave and has_revision:
        return "mixed"
    if has_new_wave:
        return "new_wave"
    if has_revision:
        return "revision"
    return "unchanged"


def _release_type(
    previous_release: Mapping[str, Any] | None,
    *,
    source_status: str,
    artifacts: Sequence[Mapping[str, Any]],
) -> str:
    if previous_release is None:
        return "baseline"
    if source_status in {"new_wave", "revision", "mixed"}:
        return source_status

    previous_artifacts_raw = previous_release.get("artifacts")
    if not isinstance(previous_artifacts_raw, list):
        return "revision"
    previous_artifacts = {
        str(row.get("artifact_id")): row
        for row in previous_artifacts_raw
        if isinstance(row, Mapping)
    }
    changed = any(
        previous_artifacts.get(str(row["artifact_id"]), {}).get("sha256")
        != row.get("sha256")
        for row in artifacts
    )
    if changed or set(previous_artifacts) != {str(row["artifact_id"]) for row in artifacts}:
        return "revision"
    return "revision"


def _claim_rows(
    claim_inventory: Mapping[str, Any],
    *,
    periods: Sequence[str],
    artifacts: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    claims = _rows(claim_inventory.get("claims"), context="claim_inventory.claims")
    artifact_ids = [str(row["artifact_id"]) for row in artifacts]
    artifact_hashes = {
        str(row["artifact_id"]): str(row["sha256"])
        for row in artifacts
    }
    period_summary = f"{len(periods)} complete quarterly waves through {periods[-1]}"
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, claim in enumerate(claims):
        claim_id = _required_string(
            claim, "claim_id", context=f"claim_inventory.claims[{index}]"
        )
        if claim_id in seen:
            raise RpsReleaseError(f"Duplicate longitudinal claim_id: {claim_id}")
        seen.add(claim_id)
        surface = _required_string(
            claim, "surface", context=f"claim_inventory.claims[{index}]"
        )
        description = _required_string(
            claim, "description", context=f"claim_inventory.claims[{index}]"
        )
        digest_payload = {
            "claim_id": claim_id,
            "periods": list(periods),
            "artifact_sha256": artifact_hashes,
        }
        output.append(
            {
                "claim_id": claim_id,
                "surfaces": [surface],
                "artifact_ids": artifact_ids,
                "value_digest": canonical_digest(digest_payload),
                "value_summary": (
                    f"{description} Source-backed longitudinal evidence currently covers "
                    f"{period_summary}; any changed candidate requires explicit review."
                ),
                "truth_state": "supported-descriptive-with-guardrails",
                "evidence_class": 2,
                "interpretation_boundary": (
                    "Aggregate descriptive RPS relationships only. No causal, productivity, "
                    "organizational-effect, or cross-source equivalence inference is licensed."
                ),
            }
        )
    if not output:
        raise RpsReleaseError("Longitudinal claim inventory is empty")
    return output


def build_rps_release_candidate(
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
    """Build a private RPS release candidate package without staging or promotion."""

    if not re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", builder_commit):
        raise RpsReleaseError("builder_commit must be a 40- or 64-character hexadecimal commit")
    if not release_id or re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,127}", release_id) is None:
        raise RpsReleaseError("release_id must be a lowercase release slug")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise RpsReleaseError(f"Candidate output directory must be new or empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    panel = prepare_rps_panel(snapshot, canonical_manifest, provider_scope)
    source_id = _required_string(snapshot, "source_id", context="snapshot")
    source_content_sha = _required_string(snapshot, "content_sha256", context="snapshot")
    provider_release_id = _required_int(
        snapshot, "provider_release_id", context="snapshot"
    )

    source_objects: list[dict[str, Any]] = []
    input_hashes: dict[str, str] = {}
    for period in panel.periods:
        object_id = period.lower()
        relative = f"inputs/rps/{period}.json"
        payload = {
            "schema_version": 1,
            "source_id": source_id,
            "provider_release_id": provider_release_id,
            "period": period,
            "records": list(panel.period_rows[period]),
        }
        sha256, size = _write_json(output_dir / relative, payload)
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
        panel,
        source_content_sha256=source_content_sha,
    )

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
    for artifact_id, relative, kind, payload, fieldnames in artifact_specs:
        path = output_dir / relative
        if kind == "json":
            sha256, size = _write_json(path, payload)
        else:
            assert isinstance(payload, list)
            assert fieldnames is not None
            sha256, size = _write_csv(
                path,
                payload,
                fieldnames=fieldnames,
            )
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
        current_periods=panel.periods,
    )
    release_type = _release_type(
        previous_release,
        source_status=source_status,
        artifacts=artifacts,
    )
    diagnostics = _diagnostic_manifest(
        longitudinal,
        quarter_rows,
        validation,
        periods=panel.periods,
    )
    claims = _claim_rows(
        claim_inventory,
        periods=panel.periods,
        artifacts=artifacts,
    )

    provider_title = _required_string(
        provider_scope, "provider_release_title", context="provider_scope"
    )
    source = {
        "source_id": source_id,
        "provider": _required_string(snapshot, "provider", context="snapshot"),
        "dataset": provider_title,
        "source_vintage_id": f"sha256:{source_content_sha}",
        "retrieved_at": _required_string(snapshot, "retrieved_at", context="snapshot"),
        "revision_status": source_status,
        "reference_periods": list(panel.periods),
        "instrument_version": "not-versioned-in-fred-distribution",
        "definition_id": panel.definition_id,
        "taxonomy_versions": {
            "rps_source_series_manifest": panel.taxonomy_version,
        },
        "rights": {
            "status": "approved",
            "storage_scope": "private",
            "publication_scope": "derived_only",
            "redistribution_scope": "derived_only",
        },
        "coverage": {
            "status": "pass",
            "required_units": panel.series_count * len(panel.periods),
            "observed_units": panel.observation_count,
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
            "builder_id": "rps-published-aggregate-longitudinal-release-v1",
            "builder_commit": builder_commit.lower(),
            "deterministic": True,
            "input_sha256": input_hashes,
            "output_sha256": output_hashes,
        },
        "candidate_scope": (
            "RPS longitudinal component only; do not promote as the first global observatory "
            "baseline unless the complete public observatory release composition has been reviewed."
        ),
        "source_input_bytes_publication": False,
    }
    _write_json(output_dir / "release.json", candidate)
    return candidate
