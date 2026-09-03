from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from genai_at_work.rps_public_view import (
    NATIONAL_METRICS,
    PUBLIC_SUBGROUP_METRICS,
    build_rps_public_observation_view,
    validate_rps_public_observation_contract,
)
from genai_at_work.rps_release import PreparedRpsPanel, RpsReleaseError

ROOT = Path(__file__).parents[1]
CONTRACT = ROOT / "data" / "registry" / "rps_public_observation_delivery_v1.json"
PERIODS = ("2026-Q1", "2026-Q2")
DATES = {"2026-Q1": "2026-02-01", "2026-Q2": "2026-05-01"}


def _contract() -> dict[str, Any]:
    value = json.loads(CONTRACT.read_text())
    assert isinstance(value, dict)
    return value


def _row(
    *,
    period: str,
    entity_type: str,
    entity_id: str,
    metric_id: str,
    index: int,
) -> dict[str, Any]:
    return {
        "date": DATES[period],
        "entity_id": entity_id,
        "entity_type": entity_type,
        "metric_id": metric_id,
        "period": period,
        "series_id": f"series-{entity_type}-{entity_id}-{metric_id}",
        "source_url": "https://fred.stlouisfed.org/",
        "unit": "Percent",
        "value": float(10 + index % 80),
    }


def _canonical_manifest() -> dict[str, Any]:
    series: list[dict[str, Any]] = []
    for metric_id in NATIONAL_METRICS:
        series.append(
            {
                "entity_type": "national",
                "entity_id": "us",
                "entity_name": "Employed Adults",
                "metric_id": metric_id,
                "series_id": f"series-national-us-{metric_id}",
            }
        )
    for entity_type, count in (("industry", 20), ("occupation", 22)):
        for entity_index in range(1, count + 1):
            entity_id = f"{entity_type}-{entity_index:02d}"
            entity_name = f"{entity_type.title()} {entity_index:02d}"
            for metric_id in PUBLIC_SUBGROUP_METRICS:
                series.append(
                    {
                        "entity_type": entity_type,
                        "entity_id": entity_id,
                        "entity_name": entity_name,
                        "metric_id": metric_id,
                        "series_id": f"series-{entity_type}-{entity_id}-{metric_id}",
                    }
                )
    return {"series": series}


def _panel() -> PreparedRpsPanel:
    period_rows: dict[str, tuple[dict[str, Any], ...]] = {}
    observation_count = 0
    for period in PERIODS:
        rows: list[dict[str, Any]] = []
        for metric_index, metric_id in enumerate(NATIONAL_METRICS):
            rows.append(
                _row(
                    period=period,
                    entity_type="national",
                    entity_id="us",
                    metric_id=metric_id,
                    index=metric_index,
                )
            )
        for entity_type, count in (("industry", 20), ("occupation", 22)):
            for entity_index in range(1, count + 1):
                for metric_index, metric_id in enumerate(PUBLIC_SUBGROUP_METRICS):
                    rows.append(
                        _row(
                            period=period,
                            entity_type=entity_type,
                            entity_id=f"{entity_type}-{entity_index:02d}",
                            metric_id=metric_id,
                            index=entity_index * 3 + metric_index,
                        )
                    )
        period_rows[period] = tuple(rows)
        observation_count += len(rows)

    return PreparedRpsPanel(
        periods=PERIODS,
        period_rows=period_rows,
        subgroup_records=(),
        definition_id="sha256:" + "1" * 64,
        taxonomy_version="sha256:" + "2" * 64,
        series_count=131,
        observation_count=observation_count,
    )


def _build(panel: PreparedRpsPanel) -> dict[str, Any]:
    return build_rps_public_observation_view(
        panel,
        source_id="rps-genai-tracker-fred-release-6",
        source_vintage_id="sha256:" + "a" * 64,
        source_reference_periods=PERIODS,
        canonical_manifest=_canonical_manifest(),
        contract=_contract(),
    )


def test_repository_public_observation_contract_is_valid() -> None:
    validate_rps_public_observation_contract(_contract())


def test_public_view_contains_national_history_and_only_latest_subgroup_rows() -> None:
    view = _build(_panel())

    assert view["national_complete_periods"] == list(PERIODS)
    assert len(view["national_history"]) == len(PERIODS) * 5
    assert len(view["industry_latest"]) == 20 * 3
    assert len(view["occupation_latest"]) == 22 * 3
    assert view["latest_subgroup_period"] == "2026-Q2"
    assert {row["period"] for row in view["industry_latest"]} == {"2026-Q2"}
    assert {row["period"] for row in view["occupation_latest"]} == {"2026-Q2"}
    assert {row["entity_name"] for row in view["national_history"]} == {"Employed Adults"}
    assert all(row["entity_name"].startswith("Industry ") for row in view["industry_latest"])
    assert all(row["entity_name"].startswith("Occupation ") for row in view["occupation_latest"])
    assert view["source_input_bytes_included"] is False
    assert view["generic_query_api_included"] is False
    assert view["historical_subgroup_panel_included"] is False


def test_national_history_uses_only_periods_with_complete_five_metric_family() -> None:
    panel = _panel()
    q1_rows = list(panel.period_rows["2026-Q1"])
    q1_rows = [
        row
        for row in q1_rows
        if not (
            row["entity_type"] == "national"
            and row["metric_id"] == "reported_time_savings_share"
        )
    ]
    partial_early_history = PreparedRpsPanel(
        periods=panel.periods,
        period_rows={**panel.period_rows, "2026-Q1": tuple(q1_rows)},
        subgroup_records=panel.subgroup_records,
        definition_id=panel.definition_id,
        taxonomy_version=panel.taxonomy_version,
        series_count=panel.series_count,
        observation_count=panel.observation_count - 1,
    )

    view = _build(partial_early_history)
    assert view["national_complete_periods"] == ["2026-Q2"]
    assert {row["period"] for row in view["national_history"]} == {"2026-Q2"}
    assert len(view["national_history"]) == 5


def test_latest_subgroup_period_requires_complete_national_family() -> None:
    panel = _panel()
    q2_rows = list(panel.period_rows["2026-Q2"])
    q2_rows = [
        row
        for row in q2_rows
        if not (
            row["entity_type"] == "national"
            and row["metric_id"] == "reported_time_savings_share"
        )
    ]
    incomplete_latest_national = PreparedRpsPanel(
        periods=panel.periods,
        period_rows={**panel.period_rows, "2026-Q2": tuple(q2_rows)},
        subgroup_records=panel.subgroup_records,
        definition_id=panel.definition_id,
        taxonomy_version=panel.taxonomy_version,
        series_count=panel.series_count,
        observation_count=panel.observation_count - 1,
    )

    with pytest.raises(RpsReleaseError, match="latest complete subgroup period lacks"):
        _build(incomplete_latest_national)


def test_contract_cannot_expand_into_bulk_or_historical_subgroup_publication() -> None:
    contract = _contract()
    contract["public_bulk_redistribution_approved"] = True
    with pytest.raises(RpsReleaseError, match="public_bulk_redistribution_approved"):
        validate_rps_public_observation_contract(contract)

    contract = _contract()
    contract["historical_subgroup_panel_approved"] = True
    with pytest.raises(RpsReleaseError, match="historical_subgroup_panel_approved"):
        validate_rps_public_observation_contract(contract)


def test_public_view_fails_closed_on_incomplete_latest_cross_section() -> None:
    panel = _panel()
    rows = list(panel.period_rows["2026-Q2"])
    rows.pop()
    incomplete = PreparedRpsPanel(
        periods=panel.periods,
        period_rows={**panel.period_rows, "2026-Q2": tuple(rows)},
        subgroup_records=panel.subgroup_records,
        definition_id=panel.definition_id,
        taxonomy_version=panel.taxonomy_version,
        series_count=panel.series_count,
        observation_count=panel.observation_count - 1,
    )

    with pytest.raises(RpsReleaseError, match="Incomplete latest occupation public view"):
        _build(incomplete)


def test_conflicting_canonical_entity_names_are_rejected() -> None:
    manifest = _canonical_manifest()
    series = manifest["series"]
    assert isinstance(series, list) and isinstance(series[1], dict)
    series[1]["entity_name"] = "Conflicting National Label"

    with pytest.raises(RpsReleaseError, match="Canonical entity name conflicts"):
        build_rps_public_observation_view(
            _panel(),
            source_id="rps-genai-tracker-fred-release-6",
            source_vintage_id="sha256:" + "b" * 64,
            source_reference_periods=PERIODS,
            canonical_manifest=manifest,
            contract=_contract(),
        )
