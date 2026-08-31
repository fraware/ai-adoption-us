from __future__ import annotations

from datetime import UTC, date, datetime

from genai_at_work.models import EntityType, SeriesMetadata
from genai_at_work.normalize import normalize_observations, quarter_label


def _metadata() -> SeriesMetadata:
    return SeriesMetadata(
        series_id="TEST",
        title="test",
        metric_id="adoption_work",
        entity_id="us",
        entity_type=EntityType.NATIONAL,
        entity_name="Employed Adults",
        frequency="Quarterly",
        unit="Percent",
        seasonal_adjustment="Not Seasonally Adjusted",
        observation_start=date(2026, 1, 1),
        observation_end=date(2026, 4, 1),
        last_updated="2026-08-04 11:08:00-05",
        notes="",
        notes_hash="0" * 64,
        source_url="https://example.test",
        copyright_status="Copyrighted: Citation Required",
        citation_text="test citation",
    )


def test_quarter_label() -> None:
    assert quarter_label(date(2026, 4, 1)) == "2026-Q2"


def test_missing_fred_values_are_not_imputed() -> None:
    rows = normalize_observations(
        _metadata(),
        [
            {"date": "2026-01-01", "value": "."},
            {
                "date": "2026-04-01",
                "value": "45.2",
                "realtime_start": "2026-08-28",
                "realtime_end": "2026-08-28",
            },
        ],
        ingested_at=datetime(2026, 8, 28, tzinfo=UTC),
    )
    assert len(rows) == 1
    assert rows[0].value == 45.2
