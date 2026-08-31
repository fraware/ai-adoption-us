"""Classify FRED RPS release series into publication constructs and entities."""

from __future__ import annotations

import hashlib
import re
from datetime import date
from typing import Any

from genai_at_work.models import EntityType, SeriesMetadata

PREFIX = "Generative Artificial Intelligence, "

# The mapping is semantic rather than ID-pattern based because some assisted-hours series
# use opaque suffixes. Classification is checked against titles returned by the release API.
METRIC_PREFIXES: tuple[tuple[str, str], ...] = (
    ("Adoption Rate Overall: ", "adoption_overall"),
    ("Adoption Rate for Work: ", "adoption_work"),
    ("Use Last Week for Work: ", "work_use_last_week"),
    ("Daily Use for Work: ", "work_use_daily"),
    ("Work Hours Assisted: ", "assisted_hours_share"),
    ("Time Savings: ", "reported_time_savings_share"),
)

# These release constructs are known but intentionally outside the first public data model.
# They are surfaced in build reports so their exclusion remains explicit.
KNOWN_EXCLUDED_PREFIXES: tuple[str, ...] = (
    "Adoption Rate Outside of Work: ",
    "Use Last Week Overall: ",
    "Use Last Week Outside of Work: ",
    "Daily Use Overall: ",
    "Daily Use Outside of Work: ",
)


def is_known_excluded_title(title: str) -> bool:
    if not title.startswith(PREFIX):
        return False
    remainder = title[len(PREFIX):]
    return any(remainder.startswith(prefix) for prefix in KNOWN_EXCLUDED_PREFIXES)

NATIONAL_LABELS = {"Working-Age Adults", "Employed Adults"}


def slugify(value: str) -> str:
    """Create a stable URL/data identifier from a source display label."""

    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized


def parse_title(title: str, known_industries: set[str], known_occupations: set[str]) -> tuple[str, EntityType, str]:
    """Map a FRED title to metric, entity type, and entity display name.

    Industry and occupation labels are learned from the adoption series first. This avoids
    guessing entity type from opaque assisted-hours/time-savings series IDs.
    """

    if not title.startswith(PREFIX):
        raise ValueError(f"Not an RPS GenAI title: {title}")

    remainder = title[len(PREFIX) :]
    for source_prefix, metric_id in METRIC_PREFIXES:
        if remainder.startswith(source_prefix):
            entity_name = remainder[len(source_prefix) :].strip()
            if entity_name in NATIONAL_LABELS:
                return metric_id, EntityType.NATIONAL, entity_name
            if entity_name in known_industries:
                return metric_id, EntityType.INDUSTRY, entity_name
            if entity_name in known_occupations:
                return metric_id, EntityType.OCCUPATION, entity_name
            raise ValueError(f"Unclassified RPS entity label: {entity_name!r} in {title!r}")
    raise ValueError(f"Unsupported RPS metric title: {title}")


def learn_entity_labels(release_rows: list[dict[str, Any]]) -> tuple[set[str], set[str]]:
    """Learn industry and occupation labels from structured adoption-series IDs."""

    industries: set[str] = set()
    occupations: set[str] = set()
    marker = PREFIX + "Adoption Rate for Work: "
    for row in release_rows:
        title = str(row.get("title", ""))
        series_id = str(row.get("id", ""))
        if not title.startswith(marker):
            continue
        entity = title[len(marker) :].strip()
        if entity in NATIONAL_LABELS:
            continue
        if re.search(r"IND\d+$", series_id):
            industries.add(entity)
        elif re.search(r"OCC\d+$", series_id):
            occupations.add(entity)
    if not industries or not occupations:
        raise ValueError("Could not learn both industry and occupation label sets from RPS release.")
    return industries, occupations


def build_series_metadata(
    release_row: dict[str, Any],
    detail_row: dict[str, Any],
    tags: list[dict[str, Any]],
    known_industries: set[str],
    known_occupations: set[str],
) -> SeriesMetadata:
    """Normalize FRED metadata and detect source-definition changes through a notes hash."""

    metric_id, entity_type, entity_name = parse_title(
        str(release_row["title"]), known_industries, known_occupations
    )
    notes = str(detail_row.get("notes", ""))
    notes_hash = hashlib.sha256(notes.encode("utf-8")).hexdigest()
    series_id = str(release_row["id"])
    entity_id = "us" if entity_type is EntityType.NATIONAL else slugify(entity_name)

    tag_names = {str(tag.get("name", "")) for tag in tags}
    copyright_candidates = sorted(
        name for name in tag_names if name.startswith("Copyrighted:") or name.startswith("Public Domain:")
    )
    copyright_status = copyright_candidates[0] if copyright_candidates else "Unknown — review required"
    citation_text = (
        f"Bick, Alexander; Blandin, Adam; Deming, David, {release_row['title']} "
        f"[{series_id}], retrieved from FRED, Federal Reserve Bank of St. Louis."
    )

    return SeriesMetadata(
        series_id=series_id,
        title=str(release_row["title"]),
        metric_id=metric_id,
        entity_id=entity_id,
        entity_type=entity_type,
        entity_name=entity_name,
        frequency=str(release_row["frequency"]),
        unit=str(release_row["units"]),
        seasonal_adjustment=str(release_row["seasonal_adjustment"]),
        observation_start=date.fromisoformat(str(release_row["observation_start"])),
        observation_end=date.fromisoformat(str(release_row["observation_end"])),
        last_updated=str(release_row["last_updated"]),
        notes=notes,
        notes_hash=notes_hash,
        source_url=f"https://fred.stlouisfed.org/series/{series_id}",
        copyright_status=copyright_status,
        citation_text=citation_text,
    )
