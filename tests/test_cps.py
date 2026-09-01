from __future__ import annotations

import csv
import gzip
import json
from pathlib import Path

import pytest

from genai_at_work.cps import (
    FIXED_WIDTH_FIELDS_2026,
    CPSPerson,
    UnavailableQuarter,
    build_composition,
    decode_fixed_width_record_2026,
    decode_person,
    load_crosswalks,
    official_fixed_width_filename,
    official_fixed_width_url,
    official_month_filename,
    official_month_url,
    parse_final_weight,
    quarter_months,
    read_quarter_csvs,
    read_quarter_fixed_width_gz,
)

ROOT = Path(__file__).parents[1]
REGISTRY = ROOT / "data" / "registry"


def test_crosswalks_are_exact_and_use_corrected_industry_ordering():
    industry, occupation = load_crosswalks(REGISTRY)
    assert set(industry) == set(range(1, 52))
    assert set(occupation) == set(range(1, 23))
    assert industry[4]["entity_index"] == 3
    assert industry[4]["entity_id"] == "construction"
    assert industry[23]["entity_index"] == 7
    assert industry[23]["entity_id"] == "transportation-and-warehousing"
    assert industry[24]["entity_index"] == 8
    assert industry[24]["entity_id"] == "utilities"
    assert occupation[1]["entity_id"] == "management-occupations"
    assert occupation[22]["entity_id"] == "transportation-and-material-moving-occupations"


def test_final_weight_has_four_implied_decimals():
    assert parse_final_weight("123456") == pytest.approx(12.3456)
    assert parse_final_weight("10000") == pytest.approx(1.0)
    assert parse_final_weight("0") is None
    assert parse_final_weight("") is None


def _row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "PRTAGE": "35",
        "PREMPNOT": "1",
        "PEMLR": "1",
        "PWSSWGT": "10000",
        "PRDTIND1": "25",
        "PRDTOCC1": "3",
        "PEHRACT1": "40",
        "PEHRUSL1": "40",
    }
    row.update(overrides)
    return row


def test_decode_person_applies_population_and_hours_rules():
    industry, occupation = load_crosswalks(REGISTRY)
    person = decode_person(
        _row(),
        month="apr",
        month_factor=1 / 3,
        industry_crosswalk=industry,
        occupation_crosswalk=occupation,
    )
    assert person is not None
    assert person.industry_id == "information"
    assert person.occupation_id == "computer-and-mathematical-occupations"
    assert person.worker_weight == pytest.approx(1 / 3)
    assert person.actual_hours == 40

    absent = decode_person(
        _row(PEMLR="2", PEHRACT1="-1"),
        month="apr",
        month_factor=1 / 3,
        industry_crosswalk=industry,
        occupation_crosswalk=occupation,
    )
    assert absent is not None
    assert absent.actual_hours == 0.0

    invalid_hours = decode_person(
        _row(PEMLR="1", PEHRACT1="-1", PEHRUSL1="-4"),
        month="apr",
        month_factor=1 / 3,
        industry_crosswalk=industry,
        occupation_crosswalk=occupation,
    )
    assert invalid_hours is not None
    assert invalid_hours.actual_hours is None
    assert invalid_hours.usual_hours is None

    assert decode_person(
        _row(PRTAGE="17"),
        month="apr",
        month_factor=1 / 3,
        industry_crosswalk=industry,
        occupation_crosswalk=occupation,
    ) is None
    assert decode_person(
        _row(PREMPNOT="2"),
        month="apr",
        month_factor=1 / 3,
        industry_crosswalk=industry,
        occupation_crosswalk=occupation,
    ) is None


def test_worker_and_hour_weights_use_different_denominators():
    people = [
        CPSPerson("apr", "information", 9, "management-occupations", 1, 1.0, 10.0, 20.0),
        CPSPerson(
            "apr",
            "information",
            9,
            "computer-and-mathematical-occupations",
            3,
            1.0,
            30.0,
            40.0,
        ),
    ]
    result = build_composition(people)[0]
    assert result.worker_suppressed is False
    assert result.actual_hours_suppressed is False
    assert result.worker_weights == {
        "management-occupations": pytest.approx(0.5),
        "computer-and-mathematical-occupations": pytest.approx(0.5),
    }
    assert result.actual_hour_weights == {
        "management-occupations": pytest.approx(0.25),
        "computer-and-mathematical-occupations": pytest.approx(0.75),
    }
    assert result.usual_hour_weights == {
        "management-occupations": pytest.approx(1 / 3),
        "computer-and-mathematical-occupations": pytest.approx(2 / 3),
    }


def test_coverage_gate_suppresses_instead_of_silently_renormalizing():
    people = [
        CPSPerson("apr", "information", 9, "management-occupations", 1, 97.0, 40.0, 40.0),
        CPSPerson("apr", "information", 9, None, None, 3.0, 40.0, 40.0),
    ]
    result = build_composition(people, coverage_gate=0.98)[0]
    assert result.worker_coverage == pytest.approx(0.97)
    assert result.worker_suppressed is True
    assert result.worker_weights is None
    assert result.actual_hours_mapping_coverage == pytest.approx(0.97)
    assert result.actual_hours_suppressed is True
    assert result.actual_hour_weights is None


def test_invalid_actual_hours_trigger_hour_gate_but_not_worker_gate():
    people = [
        CPSPerson("apr", "information", 9, "management-occupations", 1, 97.0, 40.0, 40.0),
        CPSPerson(
            "apr",
            "information",
            9,
            "computer-and-mathematical-occupations",
            3,
            3.0,
            None,
            40.0,
        ),
    ]
    result = build_composition(people, coverage_gate=0.98)[0]
    assert result.worker_suppressed is False
    assert result.actual_hours_valid_worker_coverage == pytest.approx(0.97)
    assert result.actual_hours_suppressed is True
    assert result.usual_hours_suppressed is False


def test_quarter_availability_and_official_paths():
    assert quarter_months(2026, 2, REGISTRY) == ("apr", "may", "jun")
    with pytest.raises(UnavailableQuarter, match="October 2025"):
        quarter_months(2025, 4, REGISTRY)
    assert official_month_filename(2026, "apr") == "apr26pub.csv"
    assert official_month_url(2026, "jun").endswith("/2026/basic/jun26pub.csv")
    assert official_fixed_width_filename(2026, "apr") == "apr26pub.dat.gz"
    assert official_fixed_width_url(2026, "jun").endswith("/2026/basic/jun26pub.dat.gz")


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_read_quarter_csvs_applies_equal_month_factors_and_records_provenance(
    tmp_path: Path,
):
    for month in ("apr", "may", "jun"):
        _write_csv(tmp_path / f"{month}26pub.csv", [_row()])
    people, provenance = read_quarter_csvs(
        tmp_path,
        year=2026,
        quarter=2,
        registry_dir=REGISTRY,
    )
    assert len(people) == 3
    assert all(p.worker_weight == pytest.approx(1 / 3) for p in people)
    assert [p["month"] for p in provenance] == ["apr", "may", "jun"]
    assert all(p["month_factor"] == pytest.approx(1 / 3) for p in provenance)
    assert all(len(str(p["sha256"])) == 64 for p in provenance)


def test_read_quarter_csvs_fails_on_missing_month(tmp_path: Path):
    _write_csv(tmp_path / "apr26pub.csv", [_row()])
    _write_csv(tmp_path / "may26pub.csv", [_row()])
    with pytest.raises(FileNotFoundError, match=r"jun26pub\.csv"):
        read_quarter_csvs(tmp_path, year=2026, quarter=2, registry_dir=REGISTRY)


def _fixed_width_record(**overrides: object) -> str:
    values: dict[str, object] = {
        "PRTAGE": 35,
        "PREMPNOT": 1,
        "PEMLR": 1,
        "PWSSWGT": 10000,
        "PRDTIND1": 25,
        "PRDTOCC1": 3,
        "PEHRACT1": 40,
        "PEHRUSL1": 40,
    }
    values.update(overrides)
    chars = [" "] * 950
    for name, value in values.items():
        start, end = FIXED_WIDTH_FIELDS_2026[name]
        width = end - start
        text = str(value).rjust(width)
        if len(text) != width:
            raise AssertionError(f"fixture value {value!r} does not fit {name} width {width}")
        chars[start:end] = text
    return "".join(chars) + "\n"


def test_fixed_width_2026_locations_decode_required_fields():
    row = decode_fixed_width_record_2026(_fixed_width_record())
    assert row["PRTAGE"].strip() == "35"
    assert row["PREMPNOT"].strip() == "1"
    assert row["PEMLR"].strip() == "1"
    assert row["PWSSWGT"].strip() == "10000"
    assert row["PRDTIND1"].strip() == "25"
    assert row["PRDTOCC1"].strip() == "3"
    assert row["PEHRACT1"].strip() == "40"
    assert row["PEHRUSL1"].strip() == "40"


def test_read_official_fixed_width_quarter_applies_equal_month_factors(tmp_path: Path):
    for month in ("apr", "may", "jun"):
        with gzip.open(tmp_path / f"{month}26pub.dat.gz", "wt", encoding="ascii") as handle:
            handle.write(_fixed_width_record())
    people, provenance = read_quarter_fixed_width_gz(
        tmp_path,
        year=2026,
        quarter=2,
        registry_dir=REGISTRY,
    )
    assert len(people) == 3
    assert all(person.worker_weight == pytest.approx(1 / 3) for person in people)
    assert all(item["input_format"] == "official_fixed_width_gzip" for item in provenance)
    assert all(len(str(item["sha256"])) == 64 for item in provenance)


def test_fixed_width_reader_rejects_non_2026_layout(tmp_path: Path):
    with pytest.raises(ValueError, match="pinned to the audited 2026 layout"):
        read_quarter_fixed_width_gz(
            tmp_path,
            year=2024,
            quarter=2,
            registry_dir=REGISTRY,
        )


def test_suppressed_weights_serialize_as_json_null():
    result = build_composition(
        [CPSPerson("apr", "information", 9, None, None, 1.0, 40.0, 40.0)]
    )[0]
    payload = json.dumps(result.__dict__)
    assert '"worker_weights": null' in payload
    assert '"actual_hour_weights": null' in payload


def test_cli_q4_2025_fails_cleanly_before_file_access(tmp_path: Path):
    import os
    import subprocess
    import sys

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_cps_composition.py"),
            "--year",
            "2025",
            "--quarter",
            "4",
            "--input-dir",
            str(tmp_path),
            "--output",
            str(tmp_path / "out.json"),
        ],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
    )
    assert proc.returncode != 0
    assert "CPS quarter unavailable or invalid" in proc.stderr
    assert "October 2025" in proc.stderr
    assert "Traceback" not in proc.stderr


def test_cli_missing_q2_file_fails_cleanly(tmp_path: Path):
    import os
    import subprocess
    import sys

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_cps_composition.py"),
            "--year",
            "2026",
            "--quarter",
            "2",
            "--input-dir",
            str(tmp_path),
            "--output",
            str(tmp_path / "out.json"),
        ],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
    )
    assert proc.returncode != 0
    assert "CPS composition build blocked" in proc.stderr
    assert "apr26pub.csv" in proc.stderr
    assert "Traceback" not in proc.stderr
