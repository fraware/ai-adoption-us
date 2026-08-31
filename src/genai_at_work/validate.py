"""Scientific and structural validation rules for publishable RPS data."""

from __future__ import annotations

from collections import defaultdict

from genai_at_work.models import Observation, SeriesMetadata


class ValidationError(RuntimeError):
    """Raised when data violate a publication invariant."""


ALLOWED_METRICS = {
    "adoption_overall",
    "adoption_work",
    "work_use_last_week",
    "work_use_daily",
    "assisted_hours_share",
    "reported_time_savings_share",
}


def validate_metadata(rows: list[SeriesMetadata]) -> None:
    """Fail on unit/frequency drift and duplicate source IDs."""

    seen: set[str] = set()
    for row in rows:
        if row.series_id in seen:
            raise ValidationError(f"Duplicate series ID: {row.series_id}")
        seen.add(row.series_id)
        if row.metric_id not in ALLOWED_METRICS:
            raise ValidationError(f"Unsupported metric: {row.metric_id}")
        if row.frequency != "Quarterly":
            raise ValidationError(f"Unexpected frequency for {row.series_id}: {row.frequency}")
        if row.unit != "Percent":
            raise ValidationError(f"Unexpected units for {row.series_id}: {row.unit}")
        if row.seasonal_adjustment != "Not Seasonally Adjusted":
            raise ValidationError(
                f"Unexpected seasonal adjustment for {row.series_id}: {row.seasonal_adjustment}"
            )


def validate_observations(rows: list[Observation]) -> None:
    """Check ranges, uniqueness, and logically nested national work-use measures."""

    keys: set[tuple[str, object]] = set()
    for row in rows:
        key = (row.series_id, row.date)
        if key in keys:
            raise ValidationError(f"Duplicate observation: {key}")
        keys.add(key)
        if not 0.0 <= row.value <= 100.0:
            raise ValidationError(f"Percentage out of range: {row.series_id} {row.date}={row.value}")

    by_period: dict[str, dict[str, float]] = defaultdict(dict)
    for row in rows:
        if row.entity_id == "us":
            by_period[row.period][row.metric_id] = row.value

    for period, metrics in by_period.items():
        adoption = metrics.get("adoption_work")
        last_week = metrics.get("work_use_last_week")
        daily = metrics.get("work_use_daily")
        if adoption is not None and last_week is not None and last_week > adoption + 1e-9:
            raise ValidationError(f"Last-week work use exceeds work adoption in {period}")
        if last_week is not None and daily is not None and daily > last_week + 1e-9:
            raise ValidationError(f"Daily work use exceeds last-week work use in {period}")
