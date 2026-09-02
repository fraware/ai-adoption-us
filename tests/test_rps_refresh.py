from __future__ import annotations

import copy
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import pytest

from genai_at_work.rps_refresh import (
    RpsRefreshError,
    build_refresh_snapshot,
    compare_refresh_snapshots,
    summarize_refresh_candidate,
)


class FakeRpsClient:
    def __init__(self) -> None:
        self.release_rows = [
            {
                "id": "RPSGENAIUSAGESHAREWORK",
                "title": "Generative Artificial Intelligence, Adoption Rate for Work: Employed Adults",
                "frequency": "Quarterly",
                "units": "Percent",
                "seasonal_adjustment": "Not Seasonally Adjusted",
                "observation_start": "2024-08-01",
                "observation_end": "2026-05-01",
                "last_updated": "2026-08-04 10:00:00-05",
            },
            {
                "id": "RPSGENAIUSAGESHAREIND1",
                "title": "Generative Artificial Intelligence, Adoption Rate for Work: Information",
                "frequency": "Quarterly",
                "units": "Percent",
                "seasonal_adjustment": "Not Seasonally Adjusted",
                "observation_start": "2024-08-01",
                "observation_end": "2026-05-01",
                "last_updated": "2026-08-04 10:00:00-05",
            },
            {
                "id": "RPSGENAIUSAGESHAREOCC1",
                "title": "Generative Artificial Intelligence, Adoption Rate for Work: Management Occupations",
                "frequency": "Quarterly",
                "units": "Percent",
                "seasonal_adjustment": "Not Seasonally Adjusted",
                "observation_start": "2024-08-01",
                "observation_end": "2026-05-01",
                "last_updated": "2026-08-04 10:00:00-05",
            },
            {
                "id": "RPSGENAIUSAGESHAREALL",
                "title": "Generative Artificial Intelligence, Adoption Rate Overall: Working-Age Adults",
                "frequency": "Quarterly",
                "units": "Percent",
                "seasonal_adjustment": "Not Seasonally Adjusted",
                "observation_start": "2024-08-01",
                "observation_end": "2026-05-01",
                "last_updated": "2026-08-04 10:00:00-05",
            },
        ]
        self.observation_calls: list[str] = []
        self.notes = "Published aggregate RPS test series."

    def iter_release_series(
        self, release_id: int, page_size: int = 1000
    ) -> Iterator[dict[str, Any]]:
        assert release_id == 6
        assert page_size == 1000
        yield from copy.deepcopy(self.release_rows)

    def series_metadata(self, series_id: str) -> dict[str, Any]:
        row = next(row for row in self.release_rows if row["id"] == series_id)
        return {**copy.deepcopy(row), "notes": self.notes}

    def series_tags(self, series_id: str) -> list[dict[str, Any]]:
        assert any(row["id"] == series_id for row in self.release_rows)
        return [{"name": "Copyrighted: Citation Required"}]

    def series_observations(self, series_id: str) -> list[dict[str, Any]]:
        self.observation_calls.append(series_id)
        values = {
            "RPSGENAIUSAGESHAREWORK": "50.0",
            "RPSGENAIUSAGESHAREIND1": "70.0",
            "RPSGENAIUSAGESHAREOCC1": "60.0",
        }
        return [
            {
                "date": "2026-05-01",
                "value": values[series_id],
                "realtime_start": "2026-08-04",
                "realtime_end": "9999-12-31",
            }
        ]


def _manifest() -> dict[str, Any]:
    return {
        "series_count": 3,
        "series": [
            {
                "series_id": "RPSGENAIUSAGESHAREWORK",
                "metric_id": "adoption_work",
                "entity_id": "us",
                "entity_type": "national",
                "entity_name": "Employed Adults",
            },
            {
                "series_id": "RPSGENAIUSAGESHAREIND1",
                "metric_id": "adoption_work",
                "entity_id": "information",
                "entity_type": "industry",
                "entity_name": "Information",
            },
            {
                "series_id": "RPSGENAIUSAGESHAREOCC1",
                "metric_id": "adoption_work",
                "entity_id": "management-occupations",
                "entity_type": "occupation",
                "entity_name": "Management Occupations",
            },
        ],
    }


def _scope() -> dict[str, Any]:
    return {
        "provider_release_id": 6,
        "provider_release_series_count": 4,
        "observatory_registry_series_count": 3,
        "intentionally_excluded_national_series": [
            {
                "series_id": "RPSGENAIUSAGESHAREALL",
                "construct": "Adoption Rate Overall",
                "reason": "Outside the work-focused observatory scope.",
            }
        ],
    }


def _snapshot(client: FakeRpsClient | None = None) -> dict[str, Any]:
    return build_refresh_snapshot(
        client or FakeRpsClient(),
        _manifest(),
        _scope(),
        retrieved_at=datetime(2026, 9, 2, 12, 0, tzinfo=UTC),
    )


def test_refresh_requires_exact_provider_inventory_and_skips_excluded_observations() -> None:
    client = FakeRpsClient()
    snapshot = _snapshot(client)

    assert snapshot["inventory"] == {
        "provider_series_count": 4,
        "observatory_series_count": 3,
        "excluded_series_count": 1,
        "provider_inventory_status": "pass",
    }
    assert snapshot["observation_count"] == 3
    assert snapshot["rights"]["status"] == "approved"
    assert snapshot["rights"]["public_bulk_redistribution_approved"] is False
    assert set(client.observation_calls) == {
        "RPSGENAIUSAGESHAREWORK",
        "RPSGENAIUSAGESHAREIND1",
        "RPSGENAIUSAGESHAREOCC1",
    }
    assert "RPSGENAIUSAGESHAREALL" not in client.observation_calls
    assert snapshot["excluded_series"][0]["observations_retrieved"] is False
    assert len(snapshot["content_sha256"]) == 64


def test_refresh_fails_closed_on_provider_inventory_drift() -> None:
    client = FakeRpsClient()
    client.release_rows.pop()
    with pytest.raises(RpsRefreshError, match="Provider release inventory drift"):
        build_refresh_snapshot(client, _manifest(), _scope())


def test_refresh_fails_closed_on_canonical_entity_identity_drift() -> None:
    manifest = _manifest()
    manifest["series"][1]["entity_name"] = "Wrong Industry"
    with pytest.raises(RpsRefreshError, match="Canonical manifest identity drift"):
        build_refresh_snapshot(FakeRpsClient(), manifest, _scope())


def test_snapshot_comparison_distinguishes_new_wave_revision_and_mixed() -> None:
    previous = _snapshot()

    new_wave = copy.deepcopy(previous)
    new_wave["series"][0]["observations"].append(
        {
            "date": "2026-08-01",
            "period": "2026-Q3",
            "value": 55.0,
            "unit": "Percent",
            "realtime_start": "2026-11-01",
            "realtime_end": "9999-12-31",
            "source_last_updated": "2026-11-01 10:00:00-06",
        }
    )
    new_wave["content_sha256"] = "a" * 64
    assert compare_refresh_snapshots(previous, new_wave)["revision_status"] == "new_wave"

    revision = copy.deepcopy(previous)
    revision["series"][1]["observations"][0]["value"] = 71.0
    revision["content_sha256"] = "b" * 64
    revision_diff = compare_refresh_snapshots(previous, revision)
    assert revision_diff["revision_status"] == "revision"
    assert revision_diff["counts"]["revised_observations"] == 1

    mixed = copy.deepcopy(new_wave)
    mixed["series"][2]["notes_hash"] = "f" * 64
    mixed["content_sha256"] = "c" * 64
    mixed_diff = compare_refresh_snapshots(previous, mixed)
    assert mixed_diff["revision_status"] == "mixed"
    assert mixed_diff["counts"]["definition_changes"] == 1
    assert mixed_diff["requires_release_review"] is True


def test_review_summary_excludes_raw_source_rows() -> None:
    snapshot = _snapshot()
    summary = summarize_refresh_candidate(
        snapshot,
        snapshot_file_sha256="d" * 64,
    )

    assert summary["revision_status"] == "baseline"
    assert summary["promotion_state"] == "source-candidate-only"
    assert summary["public_raw_observations_included"] is False
    assert summary["snapshot_file_sha256"] == "d" * 64
    assert summary["inventory"]["observatory_series_count"] == 3
    assert "series" not in summary
    assert "excluded_series" not in summary
