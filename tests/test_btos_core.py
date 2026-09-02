from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZipFile

from genai_at_work.btos_core import (
    extract_cycle_dates,
    extract_national_response,
    extract_sector_responses,
    read_xlsx_sheet_rows,
)

ROOT = Path(__file__).parents[1]
SOURCE = ROOT / "data" / "registry" / "btos_core_ai_202617_source_v1.json"
CHECKPOINT = ROOT / "data" / "derived" / "btos" / "btos_core_ai_202617.json"
CROSSWALK = ROOT / "data" / "registry" / "btos_rps_industry_crosswalk_v1.json"


def _column_name(index: int) -> str:
    value = index + 1
    letters = ""
    while value:
        value, remainder = divmod(value - 1, 26)
        letters = chr(ord("A") + remainder) + letters
    return letters


def _sheet_xml(rows: list[list[str | None]]) -> str:
    rendered_rows = []
    for row_number, row in enumerate(rows, start=1):
        cells = []
        for column, value in enumerate(row):
            if value is None:
                continue
            reference = f"{_column_name(column)}{row_number}"
            cells.append(
                f'<c r="{reference}" t="inlineStr"><is><t>{escape(value)}</t></is></c>'
            )
        rendered_rows.append(f'<row r="{row_number}">{"".join(cells)}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(rendered_rows)}</sheetData></worksheet>'
    )


def _inline_xlsx(sheets: dict[str, list[list[str | None]]]) -> bytes:
    workbook_sheets = []
    relationships = []
    with BytesIO() as buffer:
        with ZipFile(buffer, "w") as archive:
            for index, (name, rows) in enumerate(sheets.items(), start=1):
                workbook_sheets.append(
                    f'<sheet name="{escape(name)}" sheetId="{index}" r:id="rId{index}"/>'
                )
                relationships.append(
                    '<Relationship '
                    f'Id="rId{index}" '
                    'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
                    f'Target="worksheets/sheet{index}.xml"/>'
                )
                archive.writestr(f"xl/worksheets/sheet{index}.xml", _sheet_xml(rows))
            archive.writestr(
                "xl/workbook.xml",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                f'<sheets>{"".join(workbook_sheets)}</sheets></workbook>',
            )
            archive.writestr(
                "xl/_rels/workbook.xml.rels",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                f'{"".join(relationships)}</Relationships>',
            )
        return buffer.getvalue()


def _national_fixture() -> bytes:
    question = "Synthetic AI use question"
    estimates = [
        ["Question ID", "Question", "Answer ID", "Answer", "202617"],
        ["7", question, "1", "Yes", "22.4%"],
        ["7", question, "2", "No", "68.2%"],
        ["7", question, "3", "Do not know", "9.4%"],
    ]
    standard_errors = [
        ["Question ID", "Question", "Answer ID", "Answer", "202617"],
        ["7", question, "1", "Yes", "0.36%"],
        ["7", question, "2", "No", "0.33%"],
        ["7", question, "3", "Do not know", "0.23%"],
    ]
    dates = [
        [
            "Sample Year",
            "Cycle",
            "Panel",
            "Smpdt",
            "Collection Start",
            "Col End",
            "Reference Period Start",
            "Ref End",
            "Publication Date",
        ],
        ["2", "1", "2", "202617", "46244", "46257", "46230", "46243", "46261"],
    ]
    return _inline_xlsx(
        {
            "Response Estimates": estimates,
            "Response Standard Errors": standard_errors,
            "Collection and Reference Dates": dates,
        }
    )


def test_extract_national_response_and_cycle_dates() -> None:
    data = _national_fixture()
    response = extract_national_response(data, cycle="202617", question_id=7, answer_id=1)
    dates = extract_cycle_dates(data, cycle="202617")

    assert response.question == "Synthetic AI use question"
    assert response.answer == "Yes"
    assert response.estimate_pct == 22.4
    assert response.standard_error_pp == 0.36
    assert response.suppression_code is None
    assert dates.collection_start.isoformat() == "2026-08-10"
    assert dates.collection_end.isoformat() == "2026-08-23"
    assert dates.reference_start.isoformat() == "2026-07-27"
    assert dates.reference_end.isoformat() == "2026-08-09"
    assert dates.publication_date.isoformat() == "2026-08-27"


def test_extract_sector_responses_preserves_source_suppression() -> None:
    question = "Synthetic AI use question"
    data = _inline_xlsx(
        {
            "Response Estimates": [
                ["Sector", "Question ID", "Question", "Answer ID", "Answer", "202617"],
                ["11", "7", question, "1", "Yes", "S"],
                ["21", "7", question, "1", "Yes", "8.2%"],
            ],
            "Response Standard Errors": [
                ["Sector", "Question ID", "Question", "Answer ID", "Answer", "202617"],
                ["11", "7", question, "1", "Yes", "S"],
                ["21", "7", question, "1", "Yes", "2.46%"],
            ],
        }
    )

    rows = {row.sector_code: row for row in extract_sector_responses(data, cycle="202617", question_id=7, answer_id=1)}
    assert rows["11"].estimate_pct is None
    assert rows["11"].standard_error_pp is None
    assert rows["11"].suppression_code == "S"
    assert rows["21"].estimate_pct == 8.2
    assert rows["21"].standard_error_pp == 2.46
    assert rows["21"].suppression_code is None


def test_reader_supports_shared_strings() -> None:
    with BytesIO() as buffer:
        with ZipFile(buffer, "w") as archive:
            archive.writestr(
                "xl/sharedStrings.xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                '<si><t>Header</t></si><si><t>Value</t></si></sst>',
            )
            archive.writestr(
                "xl/workbook.xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                '<sheets><sheet name="Shared" sheetId="1" r:id="rId1"/></sheets></workbook>',
            )
            archive.writestr(
                "xl/_rels/workbook.xml.rels",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
                'Target="worksheets/sheet1.xml"/></Relationships>',
            )
            archive.writestr(
                "xl/worksheets/sheet1.xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                '<sheetData><row r="1"><c r="A1" t="s"><v>0</v></c>'
                '<c r="B1" t="s"><v>1</v></c></row></sheetData></worksheet>',
            )
        data = buffer.getvalue()

    assert read_xlsx_sheet_rows(data, "Shared") == (("Header", "Value"),)


def test_committed_checkpoint_preserves_source_and_measurement_boundaries() -> None:
    source = json.loads(SOURCE.read_text())
    checkpoint = json.loads(CHECKPOINT.read_text())
    crosswalk = json.loads(CROSSWALK.read_text())

    assert source["checkpoint_id"] == checkpoint["checkpoint_id"]
    assert source["cycle"] == "202617"
    assert source["question_id"] == 7
    assert source["answer_id"] == 1
    assert source["source_files"]["national"]["sha256"] == (
        "0db08921d1feaf2f1ee6516a4118424183941d5460d2330a9659cacbe1046dc7"
    )
    assert source["source_files"]["sector"]["sha256"] == (
        "d4e4ef99e958c66bc8b044489e36a6468f93307a1b8216f96e92dbdba8a44e78"
    )
    assert checkpoint["national"] == {
        "estimate_pct": 22.4,
        "standard_error_pp": 0.36,
        "suppression_code": None,
    }

    sectors = checkpoint["sectors"]
    assert len(sectors) == 20
    assert {row["btos_sector_code"] for row in sectors} == {
        "11",
        "21",
        "22",
        "23",
        "31",
        "42",
        "44",
        "48",
        "51",
        "52",
        "53",
        "54",
        "55",
        "56",
        "61",
        "62",
        "71",
        "72",
        "81",
        "XX",
    }
    suppressed = {row["btos_sector_code"] for row in sectors if row["suppression_code"] == "S"}
    assert suppressed == {"11", "55"}
    for row in sectors:
        if row["suppression_code"] == "S":
            assert row["estimate_pct"] is None
            assert row["standard_error_pp"] is None

    xx = next(row for row in sectors if row["btos_sector_code"] == "XX")
    assert xx["entity_id"] is None
    assert xx["comparability"] == "unclassified"
    assert checkpoint["unsupported_targets"] == [
        {
            "entity_index": 20,
            "entity_id": "public-administration",
            "entity_name": "Public Administration",
            "reason": "NAICS 92 Public Administration is outside the BTOS target population; no BTOS estimate is imputed.",
        }
    ]

    mapped = {
        row["btos_sector_code"]: row
        for row in crosswalk["entries"]
        if row["mapping_status"] == "mapped"
    }
    for row in sectors:
        if row["btos_sector_code"] == "XX":
            continue
        mapping = mapped[row["btos_sector_code"]]
        assert row["entity_id"] == mapping["entity_id"]
        assert row["naics_sector_span"] == mapping["naics_sector_span"]
        assert row["comparability"] == mapping["comparability"]

    assert source["raw_workbook_bytes_committed"] is False
    assert source["rps_values_included"] is False
    assert source["cross_source_statistics_included"] is False
    assert checkpoint["rps_values_included"] is False
    assert checkpoint["cross_source_statistics_included"] is False
