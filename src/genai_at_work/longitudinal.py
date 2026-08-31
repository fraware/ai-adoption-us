"""Deterministic longitudinal diagnostics for the private RPS subgroup audit.

No network access occurs here. This module operates on an explicitly supplied private audit fixture.
It intentionally uses only the Python standard library so the research validation surface remains small.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from itertools import combinations
from math import isfinite, sqrt

METRIC_MAP = {
    "adoption_work": "A",
    "assisted_hours_share": "H",
    "reported_time_savings_share": "S",
}
REQUIRED_PERIODS = ("2025-Q2", "2025-Q3", "2025-Q4", "2026-Q1", "2026-Q2")
REQUIRED_ENTITY_COUNTS = {"industry": 20, "occupation": 22}


@dataclass(frozen=True)
class AuditRecord:
    entity_type: str
    entity_id: str
    entity_index: int
    metric_id: str
    period: str
    value: float
    series_id: str
    audit_scope: str
    rights_status: str


def _mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs)


def pearson(x: Sequence[float], y: Sequence[float]) -> float:
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("Pearson correlation requires equal-length vectors with n>=2")
    mx, my = _mean(x), _mean(y)
    dx = [v - mx for v in x]
    dy = [v - my for v in y]
    den = sqrt(sum(v * v for v in dx) * sum(v * v for v in dy))
    if den == 0:
        raise ValueError("Pearson correlation is undefined for a constant vector")
    return sum(a * b for a, b in zip(dx, dy, strict=True)) / den


def ranks(values: Sequence[float]) -> list[float]:
    """Average ranks, 1-based, with deterministic handling of ties."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    out = [0.0] * len(values)
    pos = 0
    while pos < len(order):
        end = pos + 1
        while end < len(order) and values[order[end]] == values[order[pos]]:
            end += 1
        avg_rank = (pos + 1 + end) / 2.0
        for j in range(pos, end):
            out[order[j]] = avg_rank
        pos = end
    return out


def spearman(x: Sequence[float], y: Sequence[float]) -> float:
    return pearson(ranks(x), ranks(y))


def r2_single(y: Sequence[float], x: Sequence[float]) -> float:
    r = pearson(x, y)
    return r * r


def _solve_3x3(a: list[list[float]], b: list[float]) -> list[float]:
    aug = [[*row, rhs] for row, rhs in zip(a, b, strict=True)]
    n = 3
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(aug[r][col]))
        if abs(aug[pivot][col]) < 1e-15:
            raise ValueError("Singular design matrix")
        aug[col], aug[pivot] = aug[pivot], aug[col]
        scale = aug[col][col]
        aug[col] = [v / scale for v in aug[col]]
        for row in range(n):
            if row == col:
                continue
            factor = aug[row][col]
            aug[row] = [v - factor * w for v, w in zip(aug[row], aug[col], strict=True)]
    return [aug[i][-1] for i in range(n)]


def r2_two(y: Sequence[float], x1: Sequence[float], x2: Sequence[float]) -> float:
    if not (len(y) == len(x1) == len(x2)) or len(y) < 3:
        raise ValueError("Two-predictor regression requires equal-length vectors with n>=3")
    n = float(len(y))
    sx1, sx2 = sum(x1), sum(x2)
    sx1x1 = sum(v * v for v in x1)
    sx2x2 = sum(v * v for v in x2)
    sx1x2 = sum(a * b for a, b in zip(x1, x2, strict=True))
    sy = sum(y)
    sx1y = sum(a * b for a, b in zip(x1, y, strict=True))
    sx2y = sum(a * b for a, b in zip(x2, y, strict=True))
    beta = _solve_3x3(
        [[n, sx1, sx2], [sx1, sx1x1, sx1x2], [sx2, sx1x2, sx2x2]],
        [sy, sx1y, sx2y],
    )
    fitted = [beta[0] + beta[1] * a + beta[2] * b for a, b in zip(x1, x2, strict=True)]
    my = _mean(y)
    sst = sum((v - my) ** 2 for v in y)
    sse = sum((v - f) ** 2 for v, f in zip(y, fitted, strict=True))
    return 1.0 - sse / sst


def normalize_records(raw_records: Iterable[Mapping[str, object]]) -> list[AuditRecord]:
    records: list[AuditRecord] = []
    for raw in raw_records:
        rec = AuditRecord(
            entity_type=str(raw["entity_type"]),
            entity_id=str(raw["entity_id"]),
            entity_index=int(raw["entity_index"]),
            metric_id=str(raw["metric_id"]),
            period=str(raw["period"]),
            value=float(raw["value"]),
            series_id=str(raw["series_id"]),
            audit_scope=str(raw["audit_scope"]),
            rights_status=str(raw["rights_status"]),
        )
        records.append(rec)
    return records


def validate_private_fixture(records: Sequence[AuditRecord]) -> dict[str, bool]:
    keys = {(r.entity_type, r.entity_id, r.metric_id, r.period) for r in records}
    entities = {(r.entity_type, r.entity_id) for r in records}
    series = {r.series_id for r in records}
    periods = {r.period for r in records}
    checks = {
        "rows_630": len(records) == 630,
        "unique_keys_630": len(keys) == 630,
        "entities_42": len(entities) == 42,
        "series_126": len(series) == 126,
        "periods_exact": periods == set(REQUIRED_PERIODS),
        "metrics_exact": {r.metric_id for r in records} == set(METRIC_MAP),
        "values_finite_0_100": all(isfinite(r.value) and 0 <= r.value <= 100 for r in records),
        "all_private": all(r.audit_scope == "private_research_only" for r in records),
        "rights_marked": all(r.rights_status == "Copyrighted: Citation Required" for r in records),
    }
    for entity_type, expected in REQUIRED_ENTITY_COUNTS.items():
        actual = {r.entity_id for r in records if r.entity_type == entity_type}
        checks[f"{entity_type}_entities_{expected}"] = len(actual) == expected
    return checks


def _wide(records: Sequence[AuditRecord], entity_type: str, period: str) -> list[dict[str, float | str | int]]:
    by_entity: dict[str, dict[str, float | str | int]] = {}
    for r in records:
        if r.entity_type != entity_type or r.period != period:
            continue
        row = by_entity.setdefault(r.entity_id, {"entity_id": r.entity_id, "entity_index": r.entity_index})
        row[METRIC_MAP[r.metric_id]] = r.value
    out = list(by_entity.values())
    out.sort(key=lambda row: int(row["entity_index"]))
    if len(out) != REQUIRED_ENTITY_COUNTS[entity_type]:
        raise ValueError(f"Incomplete {entity_type} panel for {period}: {len(out)} rows")
    if any(not all(m in row for m in ("A", "H", "S")) for row in out):
        raise ValueError(f"Incomplete A/H/S panel for {entity_type} {period}")
    return out


def quarter_diagnostic(records: Sequence[AuditRecord], entity_type: str, period: str) -> dict[str, float | int | str]:
    rows = _wide(records, entity_type, period)
    a = [float(r["A"]) for r in rows]
    h = [float(r["H"]) for r in rows]
    s = [float(r["S"]) for r in rows]
    r2_sa = r2_single(s, a)
    r2_sh = r2_single(s, h)
    r2_sah = r2_two(s, a, h)
    loo_diffs: list[float] = []
    for omitted in range(len(rows)):
        aa = a[:omitted] + a[omitted + 1 :]
        hh = h[:omitted] + h[omitted + 1 :]
        ss = s[:omitted] + s[omitted + 1 :]
        loo_diffs.append(r2_single(ss, hh) - r2_single(ss, aa))
    return {
        "entity_type": entity_type,
        "period": period,
        "n": len(rows),
        "r_A_H": pearson(a, h),
        "spearman_A_H": spearman(a, h),
        "r2_H_A": r2_single(h, a),
        "r2_S_A": r2_sa,
        "r2_S_H": r2_sh,
        "r2_S_A_H": r2_sah,
        "increment_H_given_A": r2_sah - r2_sa,
        "increment_A_given_H": r2_sah - r2_sh,
        "loo_H_beats_A": sum(d > 0 for d in loo_diffs),
        "loo_A_beats_H": sum(d < 0 for d in loo_diffs),
        "loo_H_minus_A_min": min(loo_diffs),
        "loo_H_minus_A_max": max(loo_diffs),
    }


def all_quarter_diagnostics(records: Sequence[AuditRecord]) -> list[dict[str, float | int | str]]:
    return [
        quarter_diagnostic(records, entity_type, period)
        for entity_type in ("industry", "occupation")
        for period in REQUIRED_PERIODS
    ]


def _rank_vector(records: Sequence[AuditRecord], entity_type: str, period: str, metric: str) -> list[float]:
    rows = _wide(records, entity_type, period)
    values = [float(r[metric]) for r in rows]
    return ranks(values)


def rank_stability(records: Sequence[AuditRecord], entity_type: str, metric: str) -> dict[str, float | str]:
    rank_by_period = {p: _rank_vector(records, entity_type, p, metric) for p in REQUIRED_PERIODS}
    pairwise = [spearman(rank_by_period[a], rank_by_period[b]) for a, b in combinations(REQUIRED_PERIODS, 2)]
    consecutive = [
        spearman(rank_by_period[REQUIRED_PERIODS[i]], rank_by_period[REQUIRED_PERIODS[i + 1]])
        for i in range(len(REQUIRED_PERIODS) - 1)
    ]
    ordered = sorted(pairwise)
    median_pairwise = (ordered[4] + ordered[5]) / 2
    ordered_consecutive = sorted(consecutive)
    median_consecutive = (ordered_consecutive[1] + ordered_consecutive[2]) / 2
    return {
        "metric": metric,
        "median_pairwise_rank_corr": median_pairwise,
        "min_pairwise": min(pairwise),
        "max_pairwise": max(pairwise),
        "median_consecutive": median_consecutive,
        "endpoint": spearman(rank_by_period[REQUIRED_PERIODS[0]], rank_by_period[REQUIRED_PERIODS[-1]]),
        "entity_type": entity_type,
    }


def all_rank_stability(records: Sequence[AuditRecord]) -> list[dict[str, float | str]]:
    return [rank_stability(records, et, metric) for et in ("industry", "occupation") for metric in ("A", "H", "S")]


def dominance_checks(records: Sequence[AuditRecord]) -> dict[str, bool | int]:
    qd = {(d["entity_type"], d["period"]): d for d in all_quarter_diagnostics(records)}
    ah_pearson = all(
        float(qd[("occupation", p)]["r_A_H"]) > float(qd[("industry", p)]["r_A_H"])
        for p in REQUIRED_PERIODS
    )
    ah_spearman = all(
        float(qd[("occupation", p)]["spearman_A_H"]) > float(qd[("industry", p)]["spearman_A_H"])
        for p in REQUIRED_PERIODS
    )
    occupation_a_beats_h = all(
        float(qd[("occupation", p)]["r2_S_A"]) > float(qd[("occupation", p)]["r2_S_H"])
        for p in REQUIRED_PERIODS
    )
    occupation_loo = sum(int(qd[("occupation", p)]["loo_A_beats_H"]) for p in REQUIRED_PERIODS)
    industry_h_waves = sum(
        float(qd[("industry", p)]["r2_S_H"]) > float(qd[("industry", p)]["r2_S_A"])
        for p in REQUIRED_PERIODS
    )

    pair_dominance: dict[tuple[str, str], tuple[int, int]] = {}
    for et in ("industry", "occupation"):
        rank_by_metric = {
            m: {p: _rank_vector(records, et, p, m) for p in REQUIRED_PERIODS}
            for m in ("A", "H", "S")
        }
        a_gt_h = a_gt_s = 0
        for p1, p2 in combinations(REQUIRED_PERIODS, 2):
            ca = spearman(rank_by_metric["A"][p1], rank_by_metric["A"][p2])
            ch = spearman(rank_by_metric["H"][p1], rank_by_metric["H"][p2])
            cs = spearman(rank_by_metric["S"][p1], rank_by_metric["S"][p2])
            a_gt_h += ca > ch
            a_gt_s += ca > cs
        pair_dominance[(et, "counts")] = (a_gt_h, a_gt_s)

    return {
        "occupation_AH_pearson_exceeds_industry_all_5": ah_pearson,
        "occupation_AH_spearman_exceeds_industry_all_5": ah_spearman,
        "occupation_A_beats_H_for_S_all_5": occupation_a_beats_h,
        "occupation_leave_one_out_A_beats_H": occupation_loo,
        "industry_H_beats_A_waves": industry_h_waves,
        "industry_adoption_rank_gt_H_pairs": pair_dominance[("industry", "counts")][0],
        "industry_adoption_rank_gt_S_pairs": pair_dominance[("industry", "counts")][1],
        "occupation_adoption_rank_gt_H_pairs": pair_dominance[("occupation", "counts")][0],
        "occupation_adoption_rank_gt_S_pairs": pair_dominance[("occupation", "counts")][1],
    }


def rank_stability_detail(records: Sequence[AuditRecord], entity_type: str, metric: str) -> dict[str, object]:
    """Return the publication-facing stability object, including consecutive pair detail."""
    rank_by_period = {p: _rank_vector(records, entity_type, p, metric) for p in REQUIRED_PERIODS}
    pairwise = [
        spearman(rank_by_period[a], rank_by_period[b])
        for a, b in combinations(REQUIRED_PERIODS, 2)
    ]
    consecutive = [
        [
            REQUIRED_PERIODS[i],
            REQUIRED_PERIODS[i + 1],
            spearman(rank_by_period[REQUIRED_PERIODS[i]], rank_by_period[REQUIRED_PERIODS[i + 1]]),
        ]
        for i in range(len(REQUIRED_PERIODS) - 1)
    ]
    ordered = sorted(pairwise)
    median_pairwise = (ordered[4] + ordered[5]) / 2
    return {
        "consecutive": consecutive,
        "endpoint": spearman(rank_by_period[REQUIRED_PERIODS[0]], rank_by_period[REQUIRED_PERIODS[-1]]),
        "max_pairwise": max(pairwise),
        "median_pairwise": median_pairwise,
        "min_pairwise": min(pairwise),
    }


def all_rank_stability_detail(records: Sequence[AuditRecord]) -> dict[str, dict[str, dict[str, object]]]:
    return {
        entity_type: {
            metric: rank_stability_detail(records, entity_type, metric)
            for metric in ("A", "H", "S")
        }
        for entity_type in ("industry", "occupation")
    }


def rank_stability_dominance(records: Sequence[AuditRecord]) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for entity_type in ("industry", "occupation"):
        rank_by_metric = {
            metric: {period: _rank_vector(records, entity_type, period, metric) for period in REQUIRED_PERIODS}
            for metric in ("A", "H", "S")
        }
        a_gt_h = a_gt_s = s_gt_h = 0
        pairs = list(combinations(REQUIRED_PERIODS, 2))
        for p1, p2 in pairs:
            ca = spearman(rank_by_metric["A"][p1], rank_by_metric["A"][p2])
            ch = spearman(rank_by_metric["H"][p1], rank_by_metric["H"][p2])
            cs = spearman(rank_by_metric["S"][p1], rank_by_metric["S"][p2])
            a_gt_h += int(ca > ch)
            a_gt_s += int(ca > cs)
            s_gt_h += int(cs > ch)
        out[entity_type] = {
            "adoption_rank_corr_gt_assisted_hours_rank_corr": a_gt_h,
            "adoption_rank_corr_gt_reported_savings_rank_corr": a_gt_s,
            "quarter_pairs": len(pairs),
            "reported_savings_rank_corr_gt_assisted_hours_rank_corr": s_gt_h,
        }
    return out


def nested_quarter_diagnostics(records: Sequence[AuditRecord]) -> dict[str, dict[str, dict[str, float | int]]]:
    nested: dict[str, dict[str, dict[str, float | int]]] = {"industry": {}, "occupation": {}}
    for row in all_quarter_diagnostics(records):
        entity_type = str(row["entity_type"])
        period = str(row["period"])
        nested[entity_type][period] = {
            str(key): value
            for key, value in row.items()
            if key not in {"entity_type", "period"}
        }
    return nested


def cross_level_comparison(records: Sequence[AuditRecord]) -> dict[str, dict[str, float]]:
    qd = nested_quarter_diagnostics(records)
    out: dict[str, dict[str, float]] = {}
    for period in REQUIRED_PERIODS:
        industry = qd["industry"][period]
        occupation = qd["occupation"][period]
        out[period] = {
            "industry_H_minus_A_for_S_r2": float(industry["r2_S_H"]) - float(industry["r2_S_A"]),
            "industry_incremental_H_given_A_r2": float(industry["increment_H_given_A"]),
            "occupation_A_minus_H_for_S_r2": float(occupation["r2_S_A"]) - float(occupation["r2_S_H"]),
            "occupation_incremental_H_given_A_r2": float(occupation["increment_H_given_A"]),
            "occupation_minus_industry_pearson_A_H": float(occupation["r_A_H"]) - float(industry["r_A_H"]),
            "occupation_minus_industry_spearman_A_H": float(occupation["spearman_A_H"]) - float(industry["spearman_A_H"]),
        }
    return out
