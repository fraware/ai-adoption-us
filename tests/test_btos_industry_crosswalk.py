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


def test_btos_sector_codes_are_exact_source_file_keys() -> None:
    registry = _load(BTOS)
    entries = registry["entries"]
    mapped = [row for row in entries if row["mapping_status"] == "mapped"]
    codes = [row["btos_sector_code"] for row in mapped]

    expected = {
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
    }
    assert len(mapped) == 19
    assert len(codes) == len(set(codes))
    assert set(codes) == expected

    contract = registry["source_key_contract"]
    assert contract["source_file"] == "Sector.xlsx"
    assert contract["source_sha256"] == (
        "d4e4ef99e958c66bc8b044489e36a6468f93307a1b8216f96e92dbdba8a44e78"
    )
    assert set(contract["observed_sector_keys"]) == expected | {"XX"}
    assert "exact value stored" in contract["rule"]


def test_naics_span_labels_are_not_source_join_keys() -> None:
    entries = _load(BTOS)["entries"]
    by_entity = {row["entity_id"]: row for row in entries}

    assert by_entity["manufacturing"]["btos_sector_code"] == "31"
    assert by_entity["manufacturing"]["naics_sector_span"] == "31-33"
    assert by_entity["retail-trade"]["btos_sector_code"] == "44"
    assert by_entity["retail-trade"]["naics_sector_span"] == "44-45"
    assert by_entity["transportation-and-warehousing"]["btos_sector_code"] == "48"
    assert by_entity["transportation-and-warehousing"]["naics_sector_span"] == "48-49"

    rules = " ".join(_load(BTOS)["required_use_rules"])
    assert "do not join on naics_sector_span" in rules


def test_public_administration_has_no_btos_counterpart() -> None:
    entries = _load(BTOS)["entries"]
    public_admin = next(row for row in entries if row["entity_id"] == "public-administration")

    assert public_admin["entity_index"] == 20
    assert public_admin["btos_sector_code"] is None
    assert public_admin["naics_sector_span"] == "92"
    assert public_admin["mapping_status"] == "unsupported"
    assert public_admin["comparability"] == "excluded"
    assert "NAICS 92" in public_admin["reason"]
    assert "no BTOS sector estimate may be imputed" in public_admin["reason"]


def test_limited_comparability_universes_are_explicit() -> None:
    entries = _load(BTOS)["entries"]
    limited = {
        row["entity_id"]: row["reason"]
        for row in entries
        if row["comparability"] == "limited"
    }

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
    assert xx["naics_sector_span"] is None
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
    assert "do not join on naics_sector_span" in rules
    assert "fuzzy label matching" in rules
    assert "Do not redistribute BTOS XX" in rules
    assert "Do not produce a BTOS-RPS comparison for Public Administration" in rules
    assert "productivity" in rules
    assert "causal effect" in rules
