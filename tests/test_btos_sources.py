from __future__ import annotations

from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from genai_at_work.btos_sources import (
    BTOS_SOURCE_URLS,
    MAX_WORKBOOK_BYTES,
    download_btos_workbook,
    inspect_xlsx_bytes,
)


def _minimal_xlsx(*sheet_names: str) -> bytes:
    workbook_sheets = "".join(
        f'<sheet name="{name}" sheetId="{index}"/>'
        for index, name in enumerate(sheet_names, start=1)
    )
    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<sheets>{workbook_sheets}</sheets>"
        "</workbook>"
    )

    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?><Types '
            'xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>',
        )
        archive.writestr("xl/workbook.xml", workbook_xml)
        for index, _ in enumerate(sheet_names, start=1):
            archive.writestr(
                f"xl/worksheets/sheet{index}.xml",
                '<?xml version="1.0" encoding="UTF-8"?><worksheet '
                'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"/>',
            )
    return buffer.getvalue()


def test_fixed_source_urls_are_exact_official_census_workbooks() -> None:
    assert BTOS_SOURCE_URLS == {
        "national_core": "https://www.census.gov/hfp/btos/downloads/National.xlsx",
        "sector_core": "https://www.census.gov/hfp/btos/downloads/Sector.xlsx",
        "ai_supplement_2026": (
            "https://www.census.gov/hfp/btos/downloads/AI_Supplement_Table_2026.xlsx"
        ),
    }


def test_inspect_xlsx_bytes_returns_hash_size_and_sheet_inventory() -> None:
    data = _minimal_xlsx("National", "Metadata")
    inspection = inspect_xlsx_bytes(data)

    assert inspection.byte_size == len(data)
    assert len(inspection.sha256) == 64
    assert inspection.zip_entry_count == 4
    assert inspection.sheet_names == ("National", "Metadata")


def test_inspect_xlsx_bytes_rejects_non_xlsx_bytes() -> None:
    with pytest.raises(ValueError, match="valid XLSX/ZIP"):
        inspect_xlsx_bytes(b"not an xlsx")


def test_inspect_xlsx_bytes_rejects_missing_workbook_metadata() -> None:
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("xl/worksheets/sheet1.xml", "<worksheet/>")

    with pytest.raises(ValueError, match="missing required members"):
        inspect_xlsx_bytes(buffer.getvalue())


def test_inspect_xlsx_bytes_rejects_workbook_without_worksheets() -> None:
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0"?><workbook '
            'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<sheets><sheet name="Declared" sheetId="1"/></sheets></workbook>',
        )

    with pytest.raises(ValueError, match="no worksheet XML members"):
        inspect_xlsx_bytes(buffer.getvalue())


def test_download_rejects_unknown_source_key_before_network_access() -> None:
    with pytest.raises(ValueError, match="unsupported BTOS source key"):
        download_btos_workbook("arbitrary-user-url")


def test_max_workbook_size_is_bounded() -> None:
    assert MAX_WORKBOOK_BYTES == 100 * 1024 * 1024
