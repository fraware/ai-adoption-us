from __future__ import annotations

from pathlib import Path

from genai_at_work.cps_historical import (
    decode_fixed_width_record_2025,
    load_2025_layout,
)


def _registry_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "registry"


def test_2025_layout_registry_matches_audited_locations() -> None:
    fields, layout_url, version = load_2025_layout(_registry_dir())
    assert version == "cps-basic-fixed-width-2025-v1"
    assert layout_url.endswith(
        "/2025/basic/2025_Basic_CPS_Public_Use_Record_Layout_plus_IO_Code_list.txt"
    )
    assert fields == {
        "PRTAGE": (121, 123),
        "PEMLR": (179, 181),
        "PEHRUSL1": (217, 219),
        "PEHRACT1": (242, 244),
        "PREMPNOT": (392, 394),
        "PRDTIND1": (471, 473),
        "PRDTOCC1": (475, 477),
        "PWSSWGT": (612, 622),
    }


def test_decode_2025_fixed_width_record_uses_registry_slices() -> None:
    fields, _, _ = load_2025_layout(_registry_dir())
    record = [" "] * 700
    expected = {
        "PRTAGE": "42",
        "PEMLR": "01",
        "PEHRUSL1": "40",
        "PEHRACT1": "38",
        "PREMPNOT": "01",
        "PRDTIND1": "36",
        "PRDTOCC1": "03",
        "PWSSWGT": "0012345678",
    }
    for name, value in expected.items():
        start, end = fields[name]
        assert len(value) == end - start
        record[start:end] = value

    decoded = decode_fixed_width_record_2025("".join(record), fields=fields)
    assert decoded == expected
