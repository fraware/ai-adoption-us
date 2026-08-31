"""Normalization helpers for source observations."""

from __future__ import annotations

from datetime import UTC, date, datetime

from genai_at_work.models import Observation, SeriesMetadata


class ObservationError(ValueError):
    """Raised when a source observation cannot be represented canonically."""


def quarter_label(value: date) -> str:
    """Convert a quarterly observation date to `YYYY-QN`."""

    quarter = ((value.month - 1) // 3) + 1
    return f"{value.year}-Q{quarter}"


def normalize_observations(
    metadata: SeriesMetadata, raw_rows: list[dict[str, str]], ingested_at: datetime | None = None
) -> list[Observation]:
    """Normalize FRED rows, excluding missing (`.`) observations without imputing them."""

    timestamp = ingested_at or datetime.now(UTC)
    observations: list[Observation] = []
    for row in raw_rows:
        raw_value = row.get("value")
        if raw_value is None or raw_value in (".", ""):
            continue
        obs_date = date.fromisoformat(row["date"])
        try:
            value = float(raw_value)
        except (TypeError, ValueError) as exc:
            raise ObservationError(
                f"Non-numeric FRED value {raw_value!r} for {metadata.series_id} on {obs_date}"
            ) from exc

        observations.append(
            Observation(
                series_id=metadata.series_id,
                metric_id=metadata.metric_id,
                entity_id=metadata.entity_id,
                entity_type=metadata.entity_type,
                date=obs_date,
                period=quarter_label(obs_date),
                value=value,
                unit=metadata.unit,
                realtime_start=(
                    date.fromisoformat(row["realtime_start"]) if row.get("realtime_start") else None
                ),
                realtime_end=(
                    date.fromisoformat(row["realtime_end"]) if row.get("realtime_end") else None
                ),
                ingested_at_utc=timestamp,
                source_last_updated=metadata.last_updated,
            )
        )
    return observations
