"""CPS composition primitives for occupation-adjusted RPS analysis.

The module is deliberately independent of pandas/polars. It supports the official
2026 Basic Monthly CPS fixed-width public-use records for live research execution,
while retaining a small headered-CSV reader for deterministic unit fixtures.
Crosswalks are versioned, month weights are equal within a quarter, and unsupported
composition cells fail closed when coverage falls below the configured threshold.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import urllib.request
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

REQUIRED_COLUMNS = {
    "PRTAGE",
    "PREMPNOT",
    "PEMLR",
    "PWSSWGT",
    "PRDTIND1",
    "PRDTOCC1",
    "PEHRACT1",
    "PEHRUSL1",
}
DEFAULT_COVERAGE_GATE = 0.98
WEIGHT_IMPLIED_DECIMALS = 4

# Official 2026 Basic CPS public-use fixed-width locations, converted from the
# Census 1-based inclusive record-layout locations to Python 0-based slices.
# Source: 2026_Basic_CPS_Public_Use_Record_Layout_plus_IO_Code_list.txt.
FIXED_WIDTH_FIELDS_2026: dict[str, tuple[int, int]] = {
    "PRTAGE": (121, 123),       # 122-123
    "PEMLR": (179, 181),        # 180-181
    "PEHRUSL1": (217, 219),     # 218-219
    "PEHRACT1": (242, 244),     # 243-244
    "PREMPNOT": (392, 394),     # 393-394
    "PRDTIND1": (471, 473),     # 472-473
    "PRDTOCC1": (475, 477),     # 476-477
    "PWSSWGT": (612, 622),      # 613-622
}
FIXED_WIDTH_MIN_RECORD_LENGTH_2026 = max(end for _, end in FIXED_WIDTH_FIELDS_2026.values())


class UnavailableQuarter(ValueError):
    pass


@dataclass(frozen=True)
class CPSPerson:
    month: str
    industry_id: str
    industry_index: int
    occupation_id: str | None
    occupation_index: int | None
    worker_weight: float
    actual_hours: float | None
    usual_hours: float | None


@dataclass(frozen=True)
class IndustryComposition:
    industry_id: str
    industry_index: int
    worker_coverage: float
    actual_hours_valid_worker_coverage: float
    actual_hours_mapping_coverage: float | None
    usual_hours_valid_worker_coverage: float
    usual_hours_mapping_coverage: float | None
    worker_weights: dict[str, float] | None
    actual_hour_weights: dict[str, float] | None
    usual_hour_weights: dict[str, float] | None
    worker_suppressed: bool
    actual_hours_suppressed: bool
    usual_hours_suppressed: bool


@dataclass
class _IndustryStats:
    industry_index: int
    worker_total: float = 0.0
    worker_mapped: float = 0.0
    worker_occ: dict[str, float] = field(default_factory=dict)
    actual_valid_worker: float = 0.0
    actual_total_hours: float = 0.0
    actual_mapped_hours: float = 0.0
    actual_occ: dict[str, float] = field(default_factory=dict)
    usual_valid_worker: float = 0.0
    usual_total_hours: float = 0.0
    usual_mapped_hours: float = 0.0
    usual_occ: dict[str, float] = field(default_factory=dict)


def _parse_int(value: object) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def _parse_float(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _required_int(value: object, *, field: str) -> int:
    parsed = _parse_int(value)
    if parsed is None:
        raise ValueError(f"{field} must be integer-compatible, got {value!r}")
    return parsed


def parse_final_weight(value: object) -> float | None:
    """Decode PWSSWGT, which the 2026 CPS dictionary defines with four implied decimals."""
    raw = _parse_float(value)
    if raw is None or raw <= 0:
        return None
    return float(raw / (10**WEIGHT_IMPLIED_DECIMALS))


def load_crosswalks(
    registry_dir: Path,
) -> tuple[dict[int, dict[str, object]], dict[int, dict[str, object]]]:
    industry_doc = json.loads((registry_dir / "cps_industry_crosswalk_v2.json").read_text())
    occupation_doc = json.loads((registry_dir / "cps_occupation_crosswalk_v1.json").read_text())

    industry: dict[int, dict[str, object]] = {}
    for entry in industry_doc["entries"]:
        for code in entry["cps_codes"]:
            if int(code) in industry:
                raise ValueError(f"duplicate CPS industry code {code}")
            industry[int(code)] = entry
    expected_industry = set(industry_doc["civilian_codes_expected"])
    if set(industry) != expected_industry:
        raise ValueError("industry crosswalk does not cover civilian PRDTIND1 codes exactly once")

    occupation = {int(entry["cps_code"]): entry for entry in occupation_doc["entries"]}
    expected_occupation = set(occupation_doc["civilian_codes_expected"])
    if set(occupation) != expected_occupation:
        raise ValueError("occupation crosswalk does not cover civilian PRDTOCC1 codes exactly once")
    return industry, occupation


def quarter_months(year: int, quarter: int, registry_dir: Path) -> tuple[str, ...]:
    doc = json.loads((registry_dir / "cps_quarter_availability.json").read_text())
    key = f"{year}-Q{quarter}"
    if key in doc.get("unavailable", {}):
        raise UnavailableQuarter(doc["unavailable"][key]["reason"])
    try:
        months = doc["quarter_months"][str(quarter)]
    except KeyError as exc:
        raise ValueError(f"unsupported quarter: {quarter}") from exc
    return tuple(str(m) for m in months)


def _validate_month(month: str) -> str:
    normalized = month.lower()
    if normalized not in {
        "jan",
        "feb",
        "mar",
        "apr",
        "may",
        "jun",
        "jul",
        "aug",
        "sep",
        "oct",
        "nov",
        "dec",
    }:
        raise ValueError(f"unsupported month abbreviation: {month}")
    return normalized


def official_month_filename(year: int, month: str) -> str:
    """Return the Census CSV filename retained for fixture/backward compatibility."""
    month = _validate_month(month)
    return f"{month}{str(year)[-2:]}pub.csv"


def official_month_url(year: int, month: str) -> str:
    return (
        f"https://www2.census.gov/programs-surveys/cps/datasets/{year}/basic/"
        f"{official_month_filename(year, month)}"
    )


def official_fixed_width_filename(year: int, month: str) -> str:
    """Return the compressed official fixed-width Basic CPS public-use filename."""
    month = _validate_month(month)
    return f"{month}{str(year)[-2:]}pub.dat.gz"


def official_fixed_width_url(year: int, month: str) -> str:
    return (
        f"https://www2.census.gov/programs-surveys/cps/datasets/{year}/basic/"
        f"{official_fixed_width_filename(year, month)}"
    )


def official_record_layout_url(year: int) -> str:
    if year != 2026:
        raise ValueError("live fixed-width ingestion is currently pinned to the audited 2026 layout")
    return (
        "https://www2.census.gov/programs-surveys/cps/datasets/2026/basic/"
        "2026_Basic_CPS_Public_Use_Record_Layout_plus_IO_Code_list.txt"
    )


def decode_person(
    row: Mapping[str, object],
    *,
    month: str,
    month_factor: float,
    industry_crosswalk: Mapping[int, Mapping[str, object]],
    occupation_crosswalk: Mapping[int, Mapping[str, object]],
) -> CPSPerson | None:
    age = _parse_int(row.get("PRTAGE"))
    if age is None or not 18 <= age <= 64:
        return None
    if _parse_int(row.get("PREMPNOT")) != 1:
        return None

    base_weight = parse_final_weight(row.get("PWSSWGT"))
    if base_weight is None:
        return None
    worker_weight = base_weight * month_factor

    industry_code = _parse_int(row.get("PRDTIND1"))
    industry = industry_crosswalk.get(industry_code) if industry_code is not None else None
    if industry is None:
        return None

    occupation_code = _parse_int(row.get("PRDTOCC1"))
    occupation = occupation_crosswalk.get(occupation_code) if occupation_code is not None else None

    pemlr = _parse_int(row.get("PEMLR"))
    actual_raw = _parse_float(row.get("PEHRACT1"))
    if pemlr == 2:
        actual_hours = 0.0
    elif pemlr == 1 and actual_raw is not None and 0 <= actual_raw <= 99:
        actual_hours = actual_raw
    else:
        actual_hours = None

    usual_raw = _parse_float(row.get("PEHRUSL1"))
    usual_hours = usual_raw if usual_raw is not None and 0 <= usual_raw <= 99 else None

    return CPSPerson(
        month=month,
        industry_id=str(industry["entity_id"]),
        industry_index=_required_int(industry["entity_index"], field="industry.entity_index"),
        occupation_id=str(occupation["entity_id"]) if occupation is not None else None,
        occupation_index=(
            _required_int(occupation["entity_index"], field="occupation.entity_index")
            if occupation is not None
            else None
        ),
        worker_weight=worker_weight,
        actual_hours=actual_hours,
        usual_hours=usual_hours,
    )


def decode_fixed_width_record_2026(record: str) -> dict[str, str]:
    """Extract the project-required variables from one official 2026 fixed-width record."""
    record = record.rstrip("\r\n")
    if len(record) < FIXED_WIDTH_MIN_RECORD_LENGTH_2026:
        raise ValueError(
            "2026 CPS fixed-width record is shorter than the required 622-character prefix: "
            f"{len(record)}"
        )
    return {
        name: record[start:end]
        for name, (start, end) in FIXED_WIDTH_FIELDS_2026.items()
    }


def _normalized(numerators: Mapping[str, float], denominator: float) -> dict[str, float] | None:
    if denominator <= 0:
        return None
    values = {k: v / denominator for k, v in numerators.items() if v >= 0}
    total = sum(values.values())
    if abs(total - 1.0) > 1e-10:
        raise ValueError(f"normalized composition weights do not sum to one: {total}")
    return values


def build_composition(
    people: Iterable[CPSPerson],
    *,
    coverage_gate: float = DEFAULT_COVERAGE_GATE,
) -> list[IndustryComposition]:
    if not 0 < coverage_gate <= 1:
        raise ValueError("coverage_gate must be in (0, 1]")

    stats: dict[str, _IndustryStats] = {}
    for person in people:
        s = stats.setdefault(person.industry_id, _IndustryStats(person.industry_index))
        if s.industry_index != person.industry_index:
            raise ValueError(f"conflicting industry index for {person.industry_id}")

        w = person.worker_weight
        s.worker_total += w
        if person.occupation_id is not None:
            s.worker_mapped += w
            s.worker_occ[person.occupation_id] = s.worker_occ.get(person.occupation_id, 0.0) + w

        if person.actual_hours is not None:
            s.actual_valid_worker += w
            hours = w * person.actual_hours
            s.actual_total_hours += hours
            if person.occupation_id is not None:
                s.actual_mapped_hours += hours
                s.actual_occ[person.occupation_id] = s.actual_occ.get(person.occupation_id, 0.0) + hours

        if person.usual_hours is not None:
            s.usual_valid_worker += w
            hours = w * person.usual_hours
            s.usual_total_hours += hours
            if person.occupation_id is not None:
                s.usual_mapped_hours += hours
                s.usual_occ[person.occupation_id] = s.usual_occ.get(person.occupation_id, 0.0) + hours

    out: list[IndustryComposition] = []
    for industry_id, s in stats.items():
        worker_total = s.worker_total
        worker_mapped = s.worker_mapped
        actual_valid_worker = s.actual_valid_worker
        actual_total_hours = s.actual_total_hours
        actual_mapped_hours = s.actual_mapped_hours
        usual_valid_worker = s.usual_valid_worker
        usual_total_hours = s.usual_total_hours
        usual_mapped_hours = s.usual_mapped_hours

        worker_coverage = worker_mapped / worker_total if worker_total > 0 else 0.0
        actual_valid_worker_coverage = actual_valid_worker / worker_total if worker_total > 0 else 0.0
        usual_valid_worker_coverage = usual_valid_worker / worker_total if worker_total > 0 else 0.0
        actual_mapping_coverage = (
            actual_mapped_hours / actual_total_hours if actual_total_hours > 0 else None
        )
        usual_mapping_coverage = usual_mapped_hours / usual_total_hours if usual_total_hours > 0 else None

        worker_suppressed = worker_coverage < coverage_gate
        actual_suppressed = (
            actual_valid_worker_coverage < coverage_gate
            or actual_mapping_coverage is None
            or actual_mapping_coverage < coverage_gate
        )
        usual_suppressed = (
            usual_valid_worker_coverage < coverage_gate
            or usual_mapping_coverage is None
            or usual_mapping_coverage < coverage_gate
        )

        out.append(
            IndustryComposition(
                industry_id=industry_id,
                industry_index=s.industry_index,
                worker_coverage=worker_coverage,
                actual_hours_valid_worker_coverage=actual_valid_worker_coverage,
                actual_hours_mapping_coverage=actual_mapping_coverage,
                usual_hours_valid_worker_coverage=usual_valid_worker_coverage,
                usual_hours_mapping_coverage=usual_mapping_coverage,
                worker_weights=None if worker_suppressed else _normalized(s.worker_occ, worker_mapped),
                actual_hour_weights=(
                    None
                    if actual_suppressed
                    else _normalized(s.actual_occ, actual_mapped_hours)
                ),
                usual_hour_weights=(
                    None
                    if usual_suppressed
                    else _normalized(s.usual_occ, usual_mapped_hours)
                ),
                worker_suppressed=worker_suppressed,
                actual_hours_suppressed=actual_suppressed,
                usual_hours_suppressed=usual_suppressed,
            )
        )
    return sorted(out, key=lambda x: x.industry_index)


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()


def read_quarter_csvs(
    input_dir: Path,
    *,
    year: int,
    quarter: int,
    registry_dir: Path,
) -> tuple[list[CPSPerson], list[dict[str, object]]]:
    """Read headered CSV fixtures.

    The official Census 2026 live-ingestion path is `read_quarter_fixed_width_gz`.
    This reader remains useful for small deterministic tests and explicit converted
    CSV inputs that include variable-name headers.
    """
    months = quarter_months(year, quarter, registry_dir)
    industry, occupation = load_crosswalks(registry_dir)
    month_factor = 1.0 / len(months)
    people: list[CPSPerson] = []
    provenance: list[dict[str, object]] = []

    for month in months:
        filename = official_month_filename(year, month)
        path = input_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"missing official CPS input: {path}")
        digest = _sha256_file(path)
        with path.open(newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
            if missing:
                raise ValueError(f"{filename} is missing required CPS columns: {sorted(missing)}")
            row_count = 0
            in_scope_count = 0
            for row in reader:
                row_count += 1
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
                "source_url": official_month_url(year, month),
                "sha256": digest,
                "rows_read": row_count,
                "in_scope_rows": in_scope_count,
                "month_factor": month_factor,
                "input_format": "headered_csv",
            }
        )
    return people, provenance


def read_quarter_fixed_width_gz(
    input_dir: Path,
    *,
    year: int,
    quarter: int,
    registry_dir: Path,
) -> tuple[list[CPSPerson], list[dict[str, object]]]:
    """Read the official compressed fixed-width Basic CPS files for 2026."""
    if year != 2026:
        raise ValueError("live fixed-width ingestion is currently pinned to the audited 2026 layout")

    months = quarter_months(year, quarter, registry_dir)
    industry, occupation = load_crosswalks(registry_dir)
    month_factor = 1.0 / len(months)
    people: list[CPSPerson] = []
    provenance: list[dict[str, object]] = []

    for month in months:
        filename = official_fixed_width_filename(year, month)
        path = input_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"missing official CPS fixed-width input: {path}")
        digest = _sha256_file(path)
        row_count = 0
        in_scope_count = 0
        with gzip.open(path, mode="rt", encoding="ascii", newline="") as handle:
            for line in handle:
                row_count += 1
                try:
                    row = decode_fixed_width_record_2026(line)
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
                "source_url": official_fixed_width_url(year, month),
                "record_layout_url": official_record_layout_url(year),
                "sha256": digest,
                "rows_read": row_count,
                "in_scope_rows": in_scope_count,
                "month_factor": month_factor,
                "input_format": "official_fixed_width_gzip",
            }
        )
    return people, provenance


def _download_url(url: str, destination: Path) -> dict[str, object]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    hasher = hashlib.sha256()
    try:
        with urllib.request.urlopen(url, timeout=60) as response, destination.open("wb") as out:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
                hasher.update(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return {"source_url": url, "path": str(destination), "sha256": hasher.hexdigest()}


def download_official_month(year: int, month: str, destination: Path) -> dict[str, object]:
    """Download the Census CSV distribution file.

    This is retained for compatibility. Live 2026 ingestion uses the fixed-width gzip
    file because its record layout is explicit and independently auditable.
    """
    return _download_url(official_month_url(year, month), destination)


def download_official_fixed_width_month(
    year: int,
    month: str,
    destination: Path,
) -> dict[str, object]:
    """Download one official compressed fixed-width Basic CPS public-use file."""
    if year != 2026:
        raise ValueError("live fixed-width ingestion is currently pinned to the audited 2026 layout")
    return _download_url(official_fixed_width_url(year, month), destination)
