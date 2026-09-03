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
    period = "2026-Q2"
    rows: list[dict[str, Any]] = []
    for metric_index, metric_id in enumerate(NATIONAL_METRICS):
        rows.append(
            {
                "date": "2026-05-01",
                "entity_id": "us",
                "entity_type": "national",
                "metric_id": metric_id,
                "period": period,
                "series_id": f"national-{metric_id}",
                "source_url": "https://fred.stlouisfed.org/",
                "unit": "Percent",
                "value": 20.0 + metric_index,
            }
        )
    for entity_type, count in (("industry", 20), ("occupation", 22)):
        for entity_index in range(1, count + 1):
            for metric_index, metric_id in enumerate(PUBLIC_SUBGROUP_METRICS):
                rows.append(
                    {
                        "date": "2026-05-01",
                        "entity_id": f"{entity_type}-{entity_index:02d}",
                        "entity_type": entity_type,
                        "metric_id": metric_id,
                        "period": period,
                        "series_id": (
                            f"{entity_type}-{entity_index:02d}-{metric_id}"
                        ),
                        "source_url": "https://fred.stlouisfed.org/",
                        "unit": "Percent",
                        "value": float(entity_index + metric_index),
                    }
                )
    return PreparedRpsPanel(
        periods=(period,),
        period_rows={period: tuple(rows)},
        subgroup_records=(),
        definition_id="sha256:" + "1" * 64,
        taxonomy_version="sha256:" + "2" * 64,
        series_count=131,
        observation_count=131,
    )


def test_observatory_wrapper_hash_binds_bounded_public_view(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    output_dir = tmp_path / "candidate"
    output_dir.mkdir()
    source_id = "rps-genai-tracker-fred-release-6"
    base_candidate: dict[str, Any] = {
        "schema_version": 1,
        "release_id": "synthetic-rps",
        "release_type": "baseline",
        "data_mode": "derived_only",
        "created_at": "2026-09-03T00:00:00Z",
        "supersedes_release_id": None,
        "sources": [
            {
                "source_id": source_id,
                "source_vintage_id": "sha256:" + "a" * 64,
            }
        ],
        "artifacts": [],
        "diagnostics": [],
        "claims": [],
        "build": {
            "builder_id": "rps-published-aggregate-construct-window-release-v3",
            "builder_commit": "0" * 40,
            "deterministic": True,
            "input_sha256": {},
            "output_sha256": {},
        },
        "candidate_scope": "synthetic base",
        "source_input_bytes_publication": False,
    }

    def fake_base_builder(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return base_candidate

    prepared = SimpleNamespace(
        analysis_panel=_panel(),
        source_periods=("2026-Q2",),
    )

    monkeypatch.setattr(
        "genai_at_work.rps_release_public.build_rps_release_candidate_complete_history",
        fake_base_builder,
    )
    monkeypatch.setattr(
        "genai_at_work.rps_release_public.prepare_rps_source_history",
        lambda *args, **kwargs: prepared,
    )

    candidate = build_rps_observatory_release_candidate(
        {},
        _canonical_manifest(),
        {},
        {},
        _contract(),
        output_dir=output_dir,
        release_id="synthetic-rps",
        builder_commit="0" * 40,
    )

    assert candidate["build"]["builder_id"] == BUILDER_ID
    assert candidate["build"]["output_sha256"][PUBLIC_VIEW_ARTIFACT_ID]
    artifact = candidate["artifacts"][0]
    assert artifact["artifact_id"] == PUBLIC_VIEW_ARTIFACT_ID
    assert artifact["path"] == PUBLIC_VIEW_ARTIFACT_PATH
    assert artifact["evidence_class"] == 1

    view_path = output_dir / PUBLIC_VIEW_ARTIFACT_PATH
    view = json.loads(view_path.read_text())
    assert view["national_complete_periods"] == ["2026-Q2"]
    assert view["latest_subgroup_period"] == "2026-Q2"
    assert len(view["industry_latest"]) == 60
    assert len(view["occupation_latest"]) == 66
    assert {row["entity_name"] for row in view["national_history"]} == {"Employed Adults"}
    assert all(row["entity_name"].startswith("Industry ") for row in view["industry_latest"])
    assert all(row["entity_name"].startswith("Occupation ") for row in view["occupation_latest"])
    assert view["historical_subgroup_panel_included"] is False

    manifest = json.loads((output_dir / "release.json").read_text())
    assert manifest["build"]["builder_id"] == BUILDER_ID
    assert manifest["artifacts"][0]["artifact_id"] == PUBLIC_VIEW_ARTIFACT_ID
