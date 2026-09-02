"""Fail-closed acquisition primitives for official BTOS workbook sources."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

BTOS_SOURCE_URLS: dict[str, str] = {
    "national_core": "https://www.census.gov/hfp/btos/downloads/National.xlsx",
    "sector_core": "https://www.census.gov/hfp/btos/downloads/Sector.xlsx",
    "ai_supplement_2026": "https://www.census.gov/hfp/btos/downloads/AI_Supplement_Table_2026.xlsx",
}
ALLOWED_CENSUS_HOSTS = {"www.census.gov", "www2.census.gov"}
MAX_WORKBOOK_BYTES = 100 * 1024 * 1024
_XLSX_MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


@dataclass(frozen=True)
class WorkbookInspection:
    byte_size: int
    sha256: str
    zip_entry_count: int
    sheet_names: tuple[str, ...]


@dataclass(frozen=True)
class DownloadedWorkbook:
    source_key: str
    source_url: str
    final_url: str
    content_type: str | None
    data: bytes
    inspection: WorkbookInspection


def _validate_census_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_CENSUS_HOSTS:
        raise ValueError(f"BTOS source URL is outside the allowed Census hosts: {url}")


def inspect_xlsx_bytes(data: bytes) -> WorkbookInspection:
    """Validate basic XLSX structure and return immutable byte-level evidence."""
    if not data:
        raise ValueError("BTOS workbook is empty")
    if len(data) > MAX_WORKBOOK_BYTES:
        raise ValueError(f"BTOS workbook exceeds {MAX_WORKBOOK_BYTES} bytes")

    try:
        with ZipFile(BytesIO(data)) as archive:
            names = set(archive.namelist())
            required = {"[Content_Types].xml", "xl/workbook.xml"}
            missing = sorted(required - names)
            if missing:
                raise ValueError(f"BTOS XLSX is missing required members: {missing}")

            worksheet_members = sorted(
                name
                for name in names
                if name.startswith("xl/worksheets/") and name.endswith(".xml")
            )
            if not worksheet_members:
                raise ValueError("BTOS XLSX contains no worksheet XML members")

            root = ElementTree.fromstring(archive.read("xl/workbook.xml"))
            sheets = root.findall(f"{{{_XLSX_MAIN_NS}}}sheets/{{{_XLSX_MAIN_NS}}}sheet")
            sheet_names = tuple(
                name
                for sheet in sheets
                if (name := sheet.attrib.get("name")) is not None and name.strip()
            )
            if not sheet_names:
                raise ValueError("BTOS XLSX workbook metadata contains no named sheets")
    except BadZipFile as exc:
        raise ValueError("BTOS source is not a valid XLSX/ZIP container") from exc
    except ElementTree.ParseError as exc:
        raise ValueError("BTOS workbook XML is malformed") from exc

    return WorkbookInspection(
        byte_size=len(data),
        sha256=sha256(data).hexdigest(),
        zip_entry_count=len(names),
        sheet_names=sheet_names,
    )


def download_btos_workbook(source_key: str, *, timeout_seconds: float = 60.0) -> DownloadedWorkbook:
    """Download one fixed official BTOS workbook and fail closed on redirects/structure."""
    try:
        source_url = BTOS_SOURCE_URLS[source_key]
    except KeyError as exc:
        raise ValueError(f"unsupported BTOS source key: {source_key}") from exc

    _validate_census_url(source_url)
    request = Request(
        source_url,
        headers={"User-Agent": "ai-adoption-us-source-probe/1.0 (+public statistical reproducibility)"},
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        final_url = response.geturl()
        _validate_census_url(final_url)
        content_type = response.headers.get_content_type()
        data = response.read(MAX_WORKBOOK_BYTES + 1)

    if len(data) > MAX_WORKBOOK_BYTES:
        raise ValueError(f"BTOS workbook exceeds {MAX_WORKBOOK_BYTES} bytes")

    inspection = inspect_xlsx_bytes(data)
    return DownloadedWorkbook(
        source_key=source_key,
        source_url=source_url,
        final_url=final_url,
        content_type=content_type,
        data=data,
        inspection=inspection,
    )
