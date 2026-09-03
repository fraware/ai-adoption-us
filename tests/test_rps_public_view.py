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


def test_repository_public_observation_contract_is_valid() -> None:
    validate_rps_public_observation_contract(_contract())


def test_public_view_contains_national_history_and_only_latest_subgroup_rows() -> None:
    view = build_rps_public_observation_view(
        _panel(),
        source_id="rps-genai-tracker-fred-release-6",
        source_vintage_id="sha256:" + "a" * 64,
        source_reference_periods=PERIODS,
        contract=_contract(),
    )

    assert len(view["national_history"]) == len(PERIODS) * 5
    assert len(view["industry_latest"]) == 20 * 3
    assert len(view["occupation_latest"]) == 22 * 3
    assert view["latest_subgroup_period"] == "2026-Q2"
    assert {row["period"] for row in view["industry_latest"]} == {"2026-Q2"}
    assert {row["period"] for row in view["occupation_latest"]} == {"2026-Q2"}
    assert view["source_input_bytes_included"] is False
    assert view["generic_query_api_included"] is False
    assert view["historical_subgroup_panel_included"] is False


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
        build_rps_public_observation_view(
            incomplete,
            source_id="rps-genai-tracker-fred-release-6",
            source_vintage_id="sha256:" + "b" * 64,
            source_reference_periods=PERIODS,
            contract=_contract(),
        )
