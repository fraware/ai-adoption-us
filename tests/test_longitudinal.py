from __future__ import annotations

import json
from pathlib import Path

import pytest

from genai_at_work.longitudinal import (
    all_quarter_diagnostics,
    all_rank_stability,
    dominance_checks,
    normalize_records,
    pearson,
    r2_single,
    r2_two,
    ranks,
    spearman,
    validate_private_fixture,
)

FIXTURE = Path(__file__).parents[1] / "data" / "audit" / "private" / "rps_subgroup_5q_audit.json"


def records():
    if not FIXTURE.exists():
        pytest.skip("private RPS audit fixture is intentionally absent from the rights-safe release")
    return normalize_records(json.loads(FIXTURE.read_text())["records"])


def test_ranks_average_ties():
    assert ranks([10, 20, 20, 40]) == [1.0, 2.5, 2.5, 4.0]


def test_correlations_simple():
    assert pearson([1, 2, 3], [2, 4, 6]) == pytest.approx(1.0)
    assert spearman([3, 1, 2], [30, 10, 20]) == pytest.approx(1.0)
    assert r2_single([2, 4, 6], [1, 2, 3]) == pytest.approx(1.0)


def test_two_predictor_r2_exact_plane():
    x1 = [0, 1, 0, 1, 2]
    x2 = [0, 0, 1, 1, 1]
    y = [1 + 2*a + 3*b for a, b in zip(x1, x2, strict=True)]
    assert r2_two(y, x1, x2) == pytest.approx(1.0)


def test_private_fixture_contract():
    checks = validate_private_fixture(records())
    assert all(checks.values()), checks


def test_q2_2026_industry_regressions_reproduce_phase3():
    q = {(d["entity_type"], d["period"]): d for d in all_quarter_diagnostics(records())}
    d = q[("industry", "2026-Q2")]
    assert d["r2_H_A"] == pytest.approx(0.5720649640229158, abs=1e-12)
    assert d["r2_S_A"] == pytest.approx(0.6743621529087418, abs=1e-12)
    assert d["r2_S_H"] == pytest.approx(0.729350702198649, abs=1e-12)
    assert d["r2_S_A_H"] == pytest.approx(0.8011260611502208, abs=1e-12)


def test_q2_2026_occupation_regressions_reproduce_audit():
    q = {(d["entity_type"], d["period"]): d for d in all_quarter_diagnostics(records())}
    d = q[("occupation", "2026-Q2")]
    assert d["r_A_H"] == pytest.approx(0.8858499234250853, abs=1e-12)
    assert d["r2_S_A"] == pytest.approx(0.7930128060122963, abs=1e-12)
    assert d["r2_S_H"] == pytest.approx(0.662969766905623, abs=1e-12)
    assert d["r2_S_A_H"] == pytest.approx(0.7960024716488292, abs=1e-12)


def test_longitudinal_dominance_contract():
    d = dominance_checks(records())
    assert d["occupation_AH_pearson_exceeds_industry_all_5"] is True
    assert d["occupation_AH_spearman_exceeds_industry_all_5"] is True
    assert d["occupation_A_beats_H_for_S_all_5"] is True
    assert d["occupation_leave_one_out_A_beats_H"] == 110
    assert d["industry_H_beats_A_waves"] == 3
    assert d["industry_adoption_rank_gt_H_pairs"] == 10
    assert d["occupation_adoption_rank_gt_H_pairs"] == 10
    assert d["industry_adoption_rank_gt_S_pairs"] == 10
    assert d["occupation_adoption_rank_gt_S_pairs"] == 10


def test_rank_stability_medians_reproduce_checkpoint():
    x = {(d["entity_type"], d["metric"]): d for d in all_rank_stability(records())}
    assert x[("industry", "A")]["median_pairwise_rank_corr"] == pytest.approx(0.850375939849624, abs=1e-12)
    assert x[("industry", "H")]["median_pairwise_rank_corr"] == pytest.approx(0.6135338345864662, abs=1e-12)
    assert x[("occupation", "A")]["median_pairwise_rank_corr"] == pytest.approx(0.8729531338226991, abs=1e-12)
    assert x[("occupation", "H")]["median_pairwise_rank_corr"] == pytest.approx(0.6075663466967816, abs=1e-12)


def test_builder_reproduces_committed_derived_artifacts_byte_for_byte(tmp_path):
    import os
    import subprocess
    import sys

    if not FIXTURE.exists():
        pytest.skip("private RPS audit fixture is intentionally absent from the rights-safe release")
    root = FIXTURE.parents[3]
    out = tmp_path / "derived"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "build_longitudinal.py"),
            "--fixture", str(FIXTURE),
            "--output-dir", str(out),
            "--checkpoint-date", "2026-08-30",
        ],
        cwd=root,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    canonical = root / "data" / "derived" / "longitudinal"
    for name in (
        "longitudinal_diagnostics.json",
        "validation_checks.json",
        "quarter_diagnostics.csv",
        "rank_stability.csv",
    ):
        assert (out / name).read_bytes() == (canonical / name).read_bytes(), name
