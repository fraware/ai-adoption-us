"""Typed models for canonical source metadata and observations."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class EntityType(StrEnum):
    NATIONAL = "national"
    INDUSTRY = "industry"
    OCCUPATION = "occupation"


class SeriesMetadata(BaseModel):
    """Metadata required to safely publish a source series."""

    series_id: str
    title: str
    metric_id: str
    entity_id: str
    entity_type: EntityType
    entity_name: str
    frequency: str
    unit: str
    seasonal_adjustment: str
    observation_start: date
    observation_end: date
    last_updated: str
    notes: str = ""
    notes_hash: str
    source_url: str
    copyright_status: str
    citation_text: str


class Observation(BaseModel):
    """A normalized latest-vintage RPS observation."""

    source: str = Field(default="fred_rps", frozen=True)
    series_id: str
    metric_id: str
    entity_id: str
    entity_type: EntityType
    date: date
    period: str
    value: float
    unit: str
    realtime_start: date | None = None
    realtime_end: date | None = None
    ingested_at_utc: datetime
    source_last_updated: str | None = None
