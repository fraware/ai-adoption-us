from __future__ import annotations

from csv import DictReader
from hashlib import sha256
from json import loads
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "data" / "derived" / "composition" / "oews-rps-adoption-2026-09-02"


def _rows(name: str) -> list[dict[str, str]]:
    with (EVIDENCE / name).open(newline="") as handle:
        return list(DictReader(handle))


def _json(name: str) -> object:
    return loads((EVIDENCE / name).read_text())


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def test_live_oews_rps_evidence_is_bound_to_canonical_source_identity() -> None:
    manifest = _json("input_manifest.json")
    provenance = _json("provenance.json")
    assert isinstance(manifest, dict)
    assert isinstance(provenance, dict)
    assert manifest["source_content_sha256"] == (
        "fe8bffa7cacd029cc23e2ba7e310d925e8c05322f6d53bd89e8234f02e825b73"
    )
    assert manifest["source_snapshot_file_sha256"] == (
        "66b3ffbaebf43c3c8434556eec9329a232d8f17483ba3a613e6b00d214af3f74"
    )
    assert manifest["source_snapshot_published"] is False
    assert manifest["public_raw_rps_observations_included"] is False
    assert provenance["live_validation"]["github_run_id"] == "33687737639"
    assert provenance["live_validation"]["github_sha"] == (
        "3fb2cff4a9b1cbc2f340c8db00328efaa2c30130"
    )
    assert provenance["live_validation"]["workflow_status"] == "success"
    assert provenance["rights_boundary"]["raw_rps_snapshot_committed"] is False
    assert provenance["rights_boundary"]["bulk_source_mirror_created"] is False


def test_primary_counterfactual_table_has_exact_primary_scope() -> None:
    rows = _rows("primary_counterfactuals.csv")
    assert len(rows) == 34
    for period in ("2025-Q2", "2026-Q2"):
        period_rows = [row for row in rows if row["period"] == period]
        assert len(period_rows) == 17
        assert {int(row["industry_index"]) for row in period_rows} == set(range(2, 19))
        assert sum(row["point_identified"] == "True" for row in period_rows) == 14
        assert sum(row["point_identified"] == "False" for row in period_rows) == 3
        assert all(row["residual_sign_identification"] in {"positive", "negative"} for row in period_rows)


def test_primary_cps_oews_direction_result_and_disagreements_are_pinned() -> None:
    rows = _rows("primary_cps_oews_comparison.csv")
    assert len(rows) == 34
    disagreements = [row for row in rows if row["direction_agreement"] == "False"]
    assert [(row["period"], row["industry_id"]) for row in disagreements] == [
        ("2025-Q2", "arts-entertainment-and-recreation"),
        ("2026-Q2", "educational-services"),
    ]
    for period in ("2025-Q2", "2026-Q2"):
        period_rows = [row for row in rows if row["period"] == period]
        assert sum(row["direction_agreement"] == "True" for row in period_rows) == 16
        assert sum(row["direction_agreement"] == "False" for row in period_rows) == 1
        assert all(row["oews_residual_sign_identification"] != "contains_zero" for row in period_rows)


def test_summary_preserves_rank_and_partial_identification_diagnostics() -> None:
    summary = _json("summary.json")
    assert isinstance(summary, list)
    by_period = {row["period"]: row for row in summary}
    assert by_period["2025-Q2"]["exact_residual_rank_spearman"] == 0.832967032967033
    assert by_period["2026-Q2"]["exact_residual_rank_spearman"] == 0.9692307692307692
    assert by_period["2025-Q2"]["maximum_partial_residual_interval_width"] == (
        0.06223176256413865
    )
    assert by_period["2026-Q2"]["maximum_partial_residual_interval_width"] == (
        0.027044085730338452
    )
    assert all(row["supported_primary_count"] == 17 for row in summary)
    assert all(row["partially_identified_primary_count"] == 3 for row in summary)


def test_validation_retains_full_live_output_counts_without_raw_snapshot() -> None:
    validation = _json("validation_checks.json")
    assert isinstance(validation, dict)
    assert validation == {
        "comparison_row_count": 40,
        "counterfactual_row_count": 40,
        "interpretation": "independent-source descriptive robustness; not causal inference",
        "partially_identified_row_count": 8,
        "periods": ["2025-Q2", "2026-Q2"],
        "point_identified_row_count": 32,
        "raw_rps_snapshot_published": False,
        "status": "pass",
        "unsupported_comparison_row_count": 0,
        "unsupported_counterfactual_row_count": 0,
    }
    assert not (EVIDENCE / "rps_source_snapshot.json").exists()


def test_canonical_primary_table_hashes_match_provenance() -> None:
    provenance = _json("provenance.json")
    assert isinstance(provenance, dict)
    subset = provenance["canonical_public_subset"]
    assert _sha256(EVIDENCE / "primary_counterfactuals.csv") == subset[
        "primary_counterfactuals_sha256"
    ]
    assert _sha256(EVIDENCE / "primary_cps_oews_comparison.csv") == subset[
        "primary_comparison_sha256"
    ]
