import json
from pathlib import Path

ROOT = Path(__file__).parents[1]


def manifest():
    return json.loads((ROOT / "data" / "registry" / "rps_source_series_manifest.json").read_text())


def test_canonical_source_manifest_cardinality_and_uniqueness():
    data = manifest()
    rows = data["series"]
    assert data["series_count"] == 131
    assert data["entity_type_counts"] == {"national": 5, "industry": 60, "occupation": 66}
    assert len(rows) == 131
    assert len({row["series_id"] for row in rows}) == 131


def test_national_work_series_are_exact_and_overall_use_is_outside_core_manifest():
    rows = manifest()["series"]
    national = {r["metric_id"]: r["series_id"] for r in rows if r["entity_type"] == "national"}
    assert national == {
        "adoption_work": "RPSGENAIUSAGESHAREWORK",
        "work_use_last_week": "RPSGENAIUSAGESHARELWWORK",
        "work_use_daily": "RPSGENAIUSAGESHAREEDLWWOR",
        "assisted_hours_share": "RPSGENAIASSISTWRKHRSALL",
        "reported_time_savings_share": "RPSGENAITSALL",
    }
    assert "RPSGENAIUSAGESHAREALL" not in {r["series_id"] for r in rows}


def test_every_source_series_has_canonical_entity_identity():
    rows = manifest()["series"]
    assert all(row.get("entity_id") for row in rows)
    assert len({(row["entity_type"], row["entity_id"], row["metric_id"]) for row in rows}) == 131
    industries = [row for row in rows if row["entity_type"] == "industry"]
    assert {row["entity_id"] for row in industries if row["entity_index"] == 8} == {"utilities"}
