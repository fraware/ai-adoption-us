"""Build rights-bounded public RPS observation views.

The complete RPS source history remains private release-candidate input. This
module materializes only the presentation-oriented aggregate views explicitly
allowed by ``rps_public_observation_delivery_v1.json``: complete national work
history and the latest complete A/H/S cross-sections for industries and
occupations.

The output is intentionally not a generic source mirror or query surface.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from genai_at_work.longitudinal import REQUIRED_ENTITY_COUNTS
from genai_at_work.rps_release import SUBGROUP_METRICS, PreparedRpsPanel, RpsReleaseError

CONTRACT_ID = "rps-public-observation-delivery-v1"
SOURCE_ID = "rps-genai-tracker-fred-release-6"
NATIONAL_METRICS = (
    "adoption_work",
    "work_use_last_week",
    "work_use_daily",
    "assisted_hours_share",
    "reported_time_savings_share",
)
PUBLIC_SUBGROUP_METRICS = tuple(sorted(SUBGROUP_METRICS))
REQUIRED_VIEW_IDS = {"national_history", "industry_latest", "occupation_latest"}
PROHIBITED_PUBLIC_PRODUCTS = {
    "complete_rps_source_history_bundle",
    "historical_industry_observation_panel",
    "historical_occupation_observation_panel",
    "generic_rps_series_query_api",
    "unrestricted_bulk_source_mirror",
}
PUBLIC_ROW_FIELDS = (
    "date",
    "period",
    "entity_type",
    "entity_id",
    "entity_name",
    "metric_id",
    "value",
    "unit",
    "series_id",
    "source_url",
)


def _mapping(value: object, context: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise RpsReleaseError(f"{context} must be an object")
    return {str(key): item for key, item in value.items()}


def _rows(value: object, context: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not all(isinstance(item, Mapping) for item in value):
        raise RpsReleaseError(f"{context} must be a list of objects")
    return [{str(key): item for key, item in row.items()} for row in value]


def _strings(value: object, context: str) -> list[str]:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise RpsReleaseError(f"{context} must be a list of non-empty strings")
    if len(set(value)) != len(value):
        raise RpsReleaseError(f"{context} contains duplicate values")
    return list(value)


def validate_rps_public_observation_contract(contract: Mapping[str, Any]) -> None:
    """Validate the exact fail-closed public observation product boundary."""

    if contract.get("schema_version") != 1:
        raise RpsReleaseError("RPS public observation contract schema_version must equal 1")
    if contract.get("contract_id") != CONTRACT_ID:
        raise RpsReleaseError(f"RPS public observation contract_id must equal {CONTRACT_ID}")
    if contract.get("source_id") != SOURCE_ID:
        raise RpsReleaseError(f"RPS public observation source_id must equal {SOURCE_ID}")
    if contract.get("rights_decision") != "docs/source-rights/RPS_SOURCE_DECISION.md":
        raise RpsReleaseError("RPS public observation contract must cite the canonical rights decision")
    if contract.get("publication_model") != "bounded_surface_projection":
        raise RpsReleaseError("RPS public observation publication_model must stay bounded")

    for field in (
        "public_bulk_redistribution_approved",
        "generic_series_api_approved",
        "historical_subgroup_panel_approved",
        "raw_source_objects_public",
    ):
        if contract.get(field) is not False:
            raise RpsReleaseError(f"RPS public observation contract must keep {field}=false")

    excluded = set(_strings(contract.get("excluded_public_products"), "excluded_public_products"))
    if excluded != PROHIBITED_PUBLIC_PRODUCTS:
        raise RpsReleaseError("RPS public observation excluded product inventory changed")

    views = _mapping(contract.get("views"), "views")
    if set(views) != REQUIRED_VIEW_IDS:
        raise RpsReleaseError("RPS public observation contract must define exactly three bounded views")

    national = _mapping(views["national_history"], "views.national_history")
    if national.get("entity_type") != "national":
        raise RpsReleaseError("national_history must use entity_type=national")
    if tuple(_strings(national.get("metrics"), "views.national_history.metrics")) != NATIONAL_METRICS:
        raise RpsReleaseError("national_history metric inventory changed")
    if national.get("period_mode") != "complete_available_work_family":
        raise RpsReleaseError("national_history period_mode changed")

    for view_id, entity_type in (
        ("industry_latest", "industry"),
        ("occupation_latest", "occupation"),
    ):
        view = _mapping(views[view_id], f"views.{view_id}")
        if view.get("entity_type") != entity_type:
            raise RpsReleaseError(f"{view_id} entity_type changed")
        if set(_strings(view.get("metrics"), f"views.{view_id}.metrics")) != set(PUBLIC_SUBGROUP_METRICS):
            raise RpsReleaseError(f"{view_id} metric inventory changed")
        if view.get("period_mode") != "latest_complete_common":
            raise RpsReleaseError(f"{view_id} period_mode changed")
        if view.get("entity_count") != REQUIRED_ENTITY_COUNTS[entity_type]:
            raise RpsReleaseError(f"{view_id} entity_count changed")

    attribution = _mapping(contract.get("attribution"), "attribution")
    if attribution.get("citation_required") is not True:
        raise RpsReleaseError("RPS public observation attribution must require citation")
    for field in ("dataset", "authors", "transport"):
        if not isinstance(attribution.get(field), str) or not attribution[field].strip():
            raise RpsReleaseError(f"RPS public observation attribution.{field} is invalid")


def _entity_names(canonical_manifest: Mapping[str, Any]) -> dict[tuple[str, str], str]:
    """Return one immutable display name for every canonical RPS entity."""

    names: dict[tuple[str, str], str] = {}
    for index, row in enumerate(_rows(canonical_manifest.get("series"), "canonical_manifest.series")):
        context = f"canonical_manifest.series[{index}]"
        entity_type = row.get("entity_type")
        entity_id = row.get("entity_id")
        entity_name = row.get("entity_name")
        if not isinstance(entity_type, str) or not entity_type:
            raise RpsReleaseError(f"{context}.entity_type is invalid")
        if not isinstance(entity_id, str) or not entity_id:
            raise RpsReleaseError(f"{context}.entity_id is invalid")
        if not isinstance(entity_name, str) or not entity_name.strip():
            raise RpsReleaseError(f"{context}.entity_name is invalid")
        key = (entity_type, entity_id)
        previous = names.get(key)
        if previous is not None and previous != entity_name:
            raise RpsReleaseError(
                f"Canonical entity name conflicts for {entity_type}/{entity_id}: "
                f"{previous!r} != {entity_name!r}"
            )
        names[key] = entity_name

    expected_counts = {"national": 1, **REQUIRED_ENTITY_COUNTS}
    for entity_type, expected in expected_counts.items():
        observed = sum(1 for key in names if key[0] == entity_type)
        if observed != expected:
            raise RpsReleaseError(
                f"Canonical entity-name inventory for {entity_type} must contain "
                f"{expected} entities, observed {observed}"
            )
    return names


def _public_row(
    row: Mapping[str, Any],
    names: Mapping[tuple[str, str], str],
) -> dict[str, Any]:
    required_source_fields = tuple(field for field in PUBLIC_ROW_FIELDS if field != "entity_name")
    missing = [field for field in required_source_fields if field not in row]
    if missing:
        raise RpsReleaseError(f"RPS public observation source row is missing fields: {missing}")
    entity_type = str(row["entity_type"])
    entity_id = str(row["entity_id"])
    entity_name = names.get((entity_type, entity_id))
    if entity_name is None:
        raise RpsReleaseError(
            f"RPS public observation entity is absent from canonical taxonomy: "
            f"{entity_type}/{entity_id}"
        )
    public = {field: row[field] for field in required_source_fields}
    public["entity_name"] = entity_name
    return {field: public[field] for field in PUBLIC_ROW_FIELDS}


def _sort_rows(
    rows: Sequence[Mapping[str, Any]],
    names: Mapping[tuple[str, str], str],
) -> list[dict[str, Any]]:
    public = [_public_row(row, names) for row in rows]
    return sorted(
        public,
        key=lambda row: (
            str(row["period"]),
            str(row["entity_type"]),
            str(row["entity_id"]),
            str(row["metric_id"]),
        ),
    )


def build_rps_public_observation_view(
    panel: PreparedRpsPanel,
    *,
    source_id: str,
    source_vintage_id: str,
    source_reference_periods: Sequence[str],
    canonical_manifest: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    """Materialize the bounded public view from a validated private RPS panel.

    National history contains every source quarter for which the complete five-
    metric national work family is actually observed. Quarters with only a
    partial national family are outside that view rather than treated as source
    failures. Historical industry/occupation rows remain deliberately excluded.
    """

    validate_rps_public_observation_contract(contract)
    if source_id != SOURCE_ID or source_id != contract.get("source_id"):
        raise RpsReleaseError("RPS public view source_id does not match its contract")
    if not isinstance(source_vintage_id, str) or not source_vintage_id.startswith("sha256:"):
        raise RpsReleaseError("RPS public view source_vintage_id must be sha256-bound")
    if not panel.periods:
        raise RpsReleaseError("RPS public view requires at least one complete subgroup period")

    reference_periods = tuple(str(period) for period in source_reference_periods)
    if not reference_periods:
        raise RpsReleaseError("RPS public view requires source reference periods")
    if len(set(reference_periods)) != len(reference_periods):
        raise RpsReleaseError("RPS public view source reference periods contain duplicates")
    latest_period = panel.periods[-1]
    if latest_period not in reference_periods:
        raise RpsReleaseError("Latest complete subgroup period is outside source history")

    names = _entity_names(canonical_manifest)
    national_rows: list[Mapping[str, Any]] = []
    national_complete_periods: list[str] = []
    for period in reference_periods:
        rows = [
            row
            for row in panel.period_rows.get(period, ())
            if row.get("entity_type") == "national" and row.get("metric_id") in NATIONAL_METRICS
        ]
        metrics = {str(row.get("metric_id")) for row in rows}
        if len(rows) == len(NATIONAL_METRICS) and metrics == set(NATIONAL_METRICS):
            national_rows.extend(rows)
            national_complete_periods.append(period)
        elif len(rows) > len(metrics):
            raise RpsReleaseError(f"Duplicate national public-view metric for {period}")
    if not national_complete_periods:
        raise RpsReleaseError("RPS public view has no complete national work-family period")
    if latest_period not in national_complete_periods:
        raise RpsReleaseError(
            "Latest complete subgroup period lacks the complete national work family"
        )

    latest_rows = panel.period_rows.get(latest_period, ())
    subgroup_views: dict[str, list[dict[str, Any]]] = {}
    for entity_type in ("industry", "occupation"):
        rows = [
            row
            for row in latest_rows
            if row.get("entity_type") == entity_type
            and row.get("metric_id") in PUBLIC_SUBGROUP_METRICS
        ]
        expected_entities = REQUIRED_ENTITY_COUNTS[entity_type]
        expected_rows = expected_entities * len(PUBLIC_SUBGROUP_METRICS)
        entities = {str(row.get("entity_id")) for row in rows}
        metrics = {str(row.get("metric_id")) for row in rows}
        identities = {
            (str(row.get("entity_id")), str(row.get("metric_id"))) for row in rows
        }
        if len(identities) != len(rows):
            raise RpsReleaseError(
                f"Duplicate latest {entity_type} public-view observation for {latest_period}"
            )
        if len(rows) != expected_rows or len(entities) != expected_entities or metrics != set(PUBLIC_SUBGROUP_METRICS):
            raise RpsReleaseError(
                f"Incomplete latest {entity_type} public view for {latest_period}"
            )
        subgroup_views[entity_type] = _sort_rows(rows, names)

    attribution = _mapping(contract.get("attribution"), "attribution")
    return {
        "schema_version": 1,
        "view_contract_id": CONTRACT_ID,
        "source_id": source_id,
        "source_vintage_id": source_vintage_id,
        "publication_scope": "selected_attributed_aggregate_views",
        "source_input_bytes_included": False,
        "generic_query_api_included": False,
        "historical_subgroup_panel_included": False,
        "national_complete_periods": national_complete_periods,
        "latest_subgroup_period": latest_period,
        "national_history": _sort_rows(national_rows, names),
        "industry_latest": subgroup_views["industry"],
        "occupation_latest": subgroup_views["occupation"],
        "attribution": dict(attribution),
        "interpretation_boundary": contract.get("interpretation_boundary"),
    }
