"""Audited 2025 Basic Monthly CPS fixed-width ingestion.

This module keeps the 2025 layout contract separate from the 2026 parser even though the
project-required field positions are identical. The positions are loaded from a versioned
registry derived from official Census documentation.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import urllib.request
from collections.abc import Mapping
from pathlib import Path

from genai_at_work.cps import (
    CPSPerson,
    decode_person,
    load_crosswalks,
    official_fixed_width_filename,
    official_fixed_width_url,
    quarter_months,
)

LAYOUT_FILENAME = "cps_fixed_width_layout_2025_v1.json"


def load_2025_layout(registry_dir: Path) -> tuple[dict[str, tuple[int, int]], str, str]:
    """Load 2025 Census locations as Python half-open slices."""

    raw = json.loads((registry_dir / LAYOUT_FILENAME).read_text())
    if raw.get("year") != 2025:
        raise ValueError("2025 CPS layout registry has unexpected year")
    fields_raw = raw.get("fields")
    if not isinstance(fields_raw, Mapping):
        raise ValueError("2025 CPS layout fields must be an object")
    fields: dict[str, tuple[int, int]] = {}
    for name, location in fields_raw.items():
        if not isinstance(location, Mapping):
            raise ValueError(f"invalid CPS layout entry for {name}")
        start = int(location["start"])
        end = int(location["end"])
        if start <= 0 or end < start:
            raise ValueError(f"invalid Census location for {name}: {start}-{end}")
        fields[str(name)] = (start - 1, end)
    required = {
        "PRTAGE",
        "PREMPNOT",
        "PEMLR",
        "PWSSWGT",
        "PRDTIND1",
        "PRDTOCC1",
        "PEHRACT1",
        "PEHRUSL1",
    }
    if set(fields) != required:
        raise ValueError("2025 CPS layout registry does not contain exactly required fields")
    return fields, str(raw["record_layout_url"]), str(raw["version"])


def decode_fixed_width_record_2025(
    record: str,
    *,
    fields: Mapping[str, tuple[int, int]],
) -> dict[str, str]:
    """Extract project-required variables from one 2025 Basic CPS record."""

    record = record.rstrip("\r\n")
    minimum_length = max(end for _, end in fields.values())
    if len(record) < minimum_length:
        raise ValueError(
            "2025 CPS fixed-width record is shorter than the required prefix: "
            f"{len(record)} < {minimum_length}"
        )
    return {name: record[start:end] for name, (start, end) in fields.items()}


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()


def download_official_fixed_width_month_2025(
    month: str,
    destination: Path,
) -> None:
    """Download one official 2025 Basic CPS fixed-width gzip file."""

    url = official_fixed_width_url(2025, month)
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(url, timeout=90) as response, destination.open("wb") as out:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        raise


def read_quarter_fixed_width_gz_2025(
    input_dir: Path,
    *,
    quarter: int,
    registry_dir: Path,
) -> tuple[list[CPSPerson], list[dict[str, object]]]:
    """Read an official 2025 Basic CPS quarter under the audited layout registry."""

    months = quarter_months(2025, quarter, registry_dir)
    industry, occupation = load_crosswalks(registry_dir)
    fields, layout_url, layout_version = load_2025_layout(registry_dir)
    month_factor = 1.0 / len(months)
    people: list[CPSPerson] = []
    provenance: list[dict[str, object]] = []

    for month in months:
        filename = official_fixed_width_filename(2025, month)
        path = input_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"missing official CPS fixed-width input: {path}")
        row_count = 0
        in_scope_count = 0
        with gzip.open(path, mode="rt", encoding="ascii", newline="") as handle:
            for line in handle:
                row_count += 1
                try:
                    row = decode_fixed_width_record_2025(line, fields=fields)
                except ValueError as exc:
                    raise ValueError(f"{filename} record {row_count}: {exc}") from exc
                person = decode_person(
                    row,
                    month=month,
                    month_factor=month_factor,
                    industry_crosswalk=industry,
                    occupation_crosswalk=occupation,
                )
                if person is not None:
                    people.append(person)
                    in_scope_count += 1
        provenance.append(
            {
                "month": month,
                "filename": filename,
                "source_url": official_fixed_width_url(2025, month),
                "record_layout_url": layout_url,
                "layout_version": layout_version,
                "sha256": _sha256_file(path),
                "rows_read": row_count,
                "in_scope_rows": in_scope_count,
                "month_factor": month_factor,
                "input_format": "official_fixed_width_gzip",
            }
        )
    return people, provenance
