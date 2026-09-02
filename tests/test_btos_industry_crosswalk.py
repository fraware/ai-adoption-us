from __future__ import annotations

from json import loads
from pathlib import Path

REGISTRY = Path(__file__).parents[1] / "data" / "registry"
BTOS = REGISTRY / "btos_rps_industry_crosswalk_v1.json"
RPS = REGISTRY / "cps_industry_crosswalk_v2.json"


def _load(path: Path) -> dict[str, object]:
    return loads(path.read_text())


def test_crosswalk_uses_exact_canonical_rps20_entities() -> None:
    btos_entries = _load(BTOS)["entries"]
    rps_entries = _load(RPS)["entries"]

    assert len(btos_entries) == 20
    assert len(rps_entries) == 20
    assert [
        (row["entity_index"], row["entity_id"], row["entity_name"])
        for row in btos_entries
    ] == [
        (row["entity_index"], row["entity_id"], row["entity_name"])
        for row in rps_entries
    ]


def test_btos_sector_codes_are_unique_and_complete_for_in_scope_sector_set() -> None:
    entries = _load(BTOS)["entries"]
    mapped = [row for row in entries if row["mapping_status"] == "mapped"]
    codes = [row["btos_sector_code"] for row in mapped]

    assert len(mapped) == 19
    assert len(codes) == len(set(codes))
    assert set(codes) == {
        "11",
        "21",
        "22",
        "23",
        "31-33",
        "42",
        "44-45",
        "48-49",
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
    }


def test_public_administration_has_no_btos_counterpart() -> None:
    entries = _load(BTOS)["entries"]
    public_admin = next(row for row in entries if row["entity_id"] == "public-administration")

    assert public_admin["entity_index"] == 20
    assert public_admin["btos_sector_code"] is None
    assert public_admin["mapping_status"] == "unsupported"
    assert public_admin["comparability"] == "excluded"
    assert "NAICS 92" in public_admin["reason"]
    assert "no BTOS sector estimate may be imputed" in public_admin["reason"]


def test_limited_comparability_universes_are_explicit() -> None:
    entries = _load(BTOS)["entries"]
    limited = {row["entity_id"]: row["reason"] for row in entries if row["comparability"] == "limited"}

    assert set(limited) == {
        "agriculture-forestry-fishing-and-hunting",
        "transportation-and-warehousing",
        "finance-and-insurance",
        "other-services-except-public-administration",
    }
    assert "111 and 112" in limited["agriculture-forestry-fishing-and-hunting"]
    assert "482" in limited["transportation-and-warehousing"]
    assert "491" in limited["transportation-and-warehousing"]
    assert "521" in limited["finance-and-insurance"]
    assert "525" in limited["finance-and-insurance"]
    assert "813" in limited["other-services-except-public-administration"]
    assert "814" in limited["other-services-except-public-administration"]


def test_unclassified_btos_businesses_are_fail_closed() -> None:
    special = _load(BTOS)["source_special_codes"]

    assert len(special) == 1
    xx = special[0]
    assert xx["btos_sector_code"] == "XX"
    assert xx["mapping_status"] == "unsupported"
    assert xx["target_entity_id"] is None
    assert "Never redistribute" in xx["rule"]


def test_summary_and_use_rules_preserve_cross_source_boundary() -> None:
    registry = _load(BTOS)
    summary = registry["summary"]
    rules = " ".join(registry["required_use_rules"])

    assert summary == {
        "rps_industries": 20,
        "btos_sector_mapped": 19,
        "primary_comparability": 15,
        "limited_comparability": 4,
        "excluded_no_btos_counterpart": 1,
    }
    assert "do not use fuzzy label matching" in rules
    assert "Do not redistribute BTOS XX" in rules
    assert "Do not produce a BTOS-RPS comparison for Public Administration" in rules
    assert "productivity" in rules
    assert "causal effect" in rules
