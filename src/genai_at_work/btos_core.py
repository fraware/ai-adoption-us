"""Source-native extraction for pinned BTOS core AI checkpoints."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from io import BytesIO
from posixpath import join as posix_join
from posixpath import normpath
from typing import cast
from xml.etree import ElementTree
from zipfile import ZipFile

_MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_OFFICE_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_PACKAGE_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
_EXCEL_EPOCH = date(1899, 12, 30)


@dataclass(frozen=True)
class BTOSResponseEstimate:
    question_id: int
    answer_id: int
    question: str
    answer: str
    estimate_pct: float | None
    standard_error_pp: float | None
    suppression_code: str | None
    sector_code: str | None = None


@dataclass(frozen=True)
class BTOSCycleDates:
    cycle: str
    collection_start: date
    collection_end: date
    reference_start: date
    reference_end: date
    publication_date: date


def _column_index(cell_reference: str) -> int:
    letters = "".join(character for character in cell_reference if character.isalpha())
    if not letters:
        raise ValueError(f"XLSX cell reference has no column letters: {cell_reference!r}")
    index = 0
    for character in letters.upper():
        index = index * 26 + (ord(character) - ord("A") + 1)
    return index - 1


def _shared_strings(archive: ZipFile) -> tuple[str, ...]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return ()
    root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
    values: list[str] = []
    for item in root.findall(f"{{{_MAIN_NS}}}si"):
        values.append("".join(node.text or "" for node in item.iter(f"{{{_MAIN_NS}}}t")))
    return tuple(values)


def _sheet_path(archive: ZipFile, sheet_name: str) -> str:
    workbook = ElementTree.fromstring(archive.read("xl/workbook.xml"))
    relationships = ElementTree.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    relationship_targets = {
        relation.attrib["Id"]: relation.attrib["Target"]
        for relation in relationships.findall(f"{{{_PACKAGE_REL_NS}}}Relationship")
    }

    for sheet in workbook.findall(f"{{{_MAIN_NS}}}sheets/{{{_MAIN_NS}}}sheet"):
        if sheet.attrib.get("name") != sheet_name:
            continue
        relationship_id = sheet.attrib.get(f"{{{_OFFICE_REL_NS}}}id")
        if relationship_id is None or relationship_id not in relationship_targets:
            raise ValueError(f"XLSX sheet {sheet_name!r} has no resolvable relationship")
        target = relationship_targets[relationship_id]
        if target.startswith("/"):
            return normpath(target.lstrip("/"))
        if target.startswith("xl/"):
            return normpath(target)
        return normpath(posix_join("xl", target))
    raise ValueError(f"XLSX workbook does not contain sheet {sheet_name!r}")


def _cell_value(cell: ElementTree.Element, shared: tuple[str, ...]) -> str | None:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        inline = cell.find(f"{{{_MAIN_NS}}}is")
        if inline is None:
            return ""
        return "".join(node.text or "" for node in inline.iter(f"{{{_MAIN_NS}}}t"))

    value_node = cell.find(f"{{{_MAIN_NS}}}v")
    if value_node is None or value_node.text is None:
        return None
    raw_value = value_node.text
    if cell_type == "s":
        index = int(raw_value)
        try:
            return shared[index]
        except IndexError as exc:
            raise ValueError(f"XLSX shared-string index out of range: {index}") from exc
    if cell_type == "b":
        return "TRUE" if raw_value == "1" else "FALSE"
    return raw_value


def read_xlsx_sheet_rows(data: bytes, sheet_name: str) -> tuple[tuple[str | None, ...], ...]:
    """Read the raw displayed cell values from one XLSX sheet using only the stdlib."""
    with ZipFile(BytesIO(data)) as archive:
        shared = _shared_strings(archive)
        path = _sheet_path(archive, sheet_name)
        root = ElementTree.fromstring(archive.read(path))

        rows: list[tuple[str | None, ...]] = []
        for row in root.findall(f".//{{{_MAIN_NS}}}sheetData/{{{_MAIN_NS}}}row"):
            indexed_values: dict[int, str | None] = {}
            for cell in row.findall(f"{{{_MAIN_NS}}}c"):
                reference = cell.attrib.get("r")
                if reference is None:
                    raise ValueError(f"XLSX sheet {sheet_name!r} contains a cell without a reference")
                indexed_values[_column_index(reference)] = _cell_value(cell, shared)
            if not indexed_values:
                rows.append(())
                continue
            width = max(indexed_values) + 1
            rows.append(tuple(indexed_values.get(index) for index in range(width)))
    if not rows:
        raise ValueError(f"XLSX sheet {sheet_name!r} contains no rows")
    return tuple(rows)


def _require_cell(row: tuple[str | None, ...], index: int, label: str) -> str:
    if index >= len(row) or row[index] is None:
        raise ValueError(f"BTOS workbook row is missing {label}")
    return cast(str, row[index])


def _cycle_column(header: tuple[str | None, ...], cycle: str) -> int:
    matches = [index for index, value in enumerate(header) if value == cycle]
    if len(matches) != 1:
        raise ValueError(f"BTOS workbook expected one column for cycle {cycle}, found {len(matches)}")
    return matches[0]


def _parse_percent_cell(raw: str, *, label: str) -> tuple[float | None, str | None]:
    if raw == "S":
        return None, "S"
    if not raw.endswith("%"):
        raise ValueError(f"BTOS {label} is neither a percentage nor suppression code S: {raw!r}")
    try:
        value = float(raw[:-1])
    except ValueError as exc:
        raise ValueError(f"BTOS {label} has an invalid percentage: {raw!r}") from exc
    if not 0.0 <= value <= 100.0:
        raise ValueError(f"BTOS {label} percentage is outside [0, 100]: {value}")
    return value, None


def _matching_national_row(
    rows: tuple[tuple[str | None, ...], ...],
    *,
    cycle: str,
    question_id: int,
    answer_id: int,
) -> tuple[str, str, str]:
    header = rows[0]
    cycle_index = _cycle_column(header, cycle)
    matches: list[tuple[str, str, str]] = []
    for row in rows[1:]:
        if len(row) <= cycle_index:
            continue
        if row[0] != str(question_id) or row[2] != str(answer_id):
            continue
        matches.append(
            (
                _require_cell(row, 1, "question text"),
                _require_cell(row, 3, "answer text"),
                _require_cell(row, cycle_index, f"cycle {cycle} value"),
            )
        )
    if len(matches) != 1:
        raise ValueError(
            "BTOS national workbook expected one matching response row for "
            f"question {question_id}, answer {answer_id}, cycle {cycle}; found {len(matches)}"
        )
    return matches[0]


def extract_national_response(
    data: bytes,
    *,
    cycle: str,
    question_id: int,
    answer_id: int,
) -> BTOSResponseEstimate:
    estimates = read_xlsx_sheet_rows(data, "Response Estimates")
    standard_errors = read_xlsx_sheet_rows(data, "Response Standard Errors")
    question, answer, estimate_raw = _matching_national_row(
        estimates, cycle=cycle, question_id=question_id, answer_id=answer_id
    )
    se_question, se_answer, se_raw = _matching_national_row(
        standard_errors, cycle=cycle, question_id=question_id, answer_id=answer_id
    )
    if (se_question, se_answer) != (question, answer):
        raise ValueError("BTOS national estimate and standard-error row identities differ")

    estimate, estimate_suppression = _parse_percent_cell(estimate_raw, label="national estimate")
    standard_error, se_suppression = _parse_percent_cell(se_raw, label="national standard error")
    if estimate_suppression != se_suppression:
        raise ValueError("BTOS national estimate and standard error have inconsistent suppression")
    return BTOSResponseEstimate(
        question_id=question_id,
        answer_id=answer_id,
        question=question,
        answer=answer,
        estimate_pct=estimate,
        standard_error_pp=standard_error,
        suppression_code=estimate_suppression,
    )


def _sector_rows(
    rows: tuple[tuple[str | None, ...], ...],
    *,
    cycle: str,
    question_id: int,
    answer_id: int,
) -> dict[str, tuple[str, str, str]]:
    header = rows[0]
    cycle_index = _cycle_column(header, cycle)
    matches: dict[str, tuple[str, str, str]] = {}
    for row in rows[1:]:
        if len(row) <= cycle_index:
            continue
        if row[1] != str(question_id) or row[3] != str(answer_id):
            continue
        sector = _require_cell(row, 0, "sector code")
        if sector in matches:
            raise ValueError(f"BTOS sector workbook has duplicate source key {sector!r}")
        matches[sector] = (
            _require_cell(row, 2, "question text"),
            _require_cell(row, 4, "answer text"),
            _require_cell(row, cycle_index, f"cycle {cycle} value"),
        )
    if not matches:
        raise ValueError(
            f"BTOS sector workbook has no rows for question {question_id}, answer {answer_id}, cycle {cycle}"
        )
    return matches


def extract_sector_responses(
    data: bytes,
    *,
    cycle: str,
    question_id: int,
    answer_id: int,
) -> tuple[BTOSResponseEstimate, ...]:
    estimate_rows = _sector_rows(
        read_xlsx_sheet_rows(data, "Response Estimates"),
        cycle=cycle,
        question_id=question_id,
        answer_id=answer_id,
    )
    se_rows = _sector_rows(
        read_xlsx_sheet_rows(data, "Response Standard Errors"),
        cycle=cycle,
        question_id=question_id,
        answer_id=answer_id,
    )
    if set(estimate_rows) != set(se_rows):
        raise ValueError("BTOS sector estimate and standard-error source-key sets differ")

    results: list[BTOSResponseEstimate] = []
    for sector, (question, answer, estimate_raw) in estimate_rows.items():
        se_question, se_answer, se_raw = se_rows[sector]
        if (se_question, se_answer) != (question, answer):
            raise ValueError(f"BTOS sector {sector} estimate and standard-error row identities differ")
        estimate, estimate_suppression = _parse_percent_cell(
            estimate_raw, label=f"sector {sector} estimate"
        )
        standard_error, se_suppression = _parse_percent_cell(
            se_raw, label=f"sector {sector} standard error"
        )
        if estimate_suppression != se_suppression:
            raise ValueError(f"BTOS sector {sector} estimate and standard error suppressions differ")
        results.append(
            BTOSResponseEstimate(
                question_id=question_id,
                answer_id=answer_id,
                question=question,
                answer=answer,
                estimate_pct=estimate,
                standard_error_pp=standard_error,
                suppression_code=estimate_suppression,
                sector_code=sector,
            )
        )
    return tuple(results)


def _excel_serial_date(raw: str, *, label: str) -> date:
    try:
        numeric = float(raw)
    except ValueError as exc:
        raise ValueError(f"BTOS {label} has an invalid Excel date serial: {raw!r}") from exc
    integer = int(numeric)
    if numeric != integer:
        raise ValueError(f"BTOS {label} Excel date serial is not a whole day: {raw!r}")
    return _EXCEL_EPOCH + timedelta(days=integer)


def extract_cycle_dates(data: bytes, *, cycle: str) -> BTOSCycleDates:
    rows = read_xlsx_sheet_rows(data, "Collection and Reference Dates")
    header = rows[0]
    required_headers = (
        "Smpdt",
        "Collection Start",
        "Col End",
        "Reference Period Start",
        "Ref End",
        "Publication Date",
    )
    header_map = {value: index for index, value in enumerate(header) if value is not None}
    missing = [name for name in required_headers if name not in header_map]
    if missing:
        raise ValueError(f"BTOS collection/reference sheet is missing columns: {missing}")

    sample_date_index = header_map["Smpdt"]
    matches = [
        row for row in rows[1:] if len(row) > sample_date_index and row[sample_date_index] == cycle
    ]
    if len(matches) != 1:
        raise ValueError(f"BTOS expected one collection/reference row for cycle {cycle}, found {len(matches)}")
    row = matches[0]

    def raw(name: str) -> str:
        return _require_cell(row, header_map[name], name)

    return BTOSCycleDates(
        cycle=cycle,
        collection_start=_excel_serial_date(raw("Collection Start"), label="collection start"),
        collection_end=_excel_serial_date(raw("Col End"), label="collection end"),
        reference_start=_excel_serial_date(raw("Reference Period Start"), label="reference start"),
        reference_end=_excel_serial_date(raw("Ref End"), label="reference end"),
        publication_date=_excel_serial_date(raw("Publication Date"), label="publication date"),
    )
