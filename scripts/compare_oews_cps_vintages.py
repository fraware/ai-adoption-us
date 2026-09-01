#!/usr/bin/env python3
"""Compare one saved OEWS composition artifact with two CPS quarter vintages.

The script is deliberately offline with respect to BLS: it consumes the already-frozen
May-2025 OEWS aggregate composition artifact and compares it with Q2-2025 and Q2-2026
CPS worker-share compositions. It also computes partial-identification L1 bounds for
industries with unpublished OEWS occupation cells.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from genai_at_work.oews import (
    OewsCompositionRow,
    compare_cps_oews_worker_composition,
    cosine_similarity,
    median,
    spearman_rank_correlation,
)
from genai_at_work.oews_partial import l1_identification_bounds


def _load_json(path: Path) -> dict[str, Any]:
    raw: object = json.loads(path.read_text())
    if not isinstance(raw, dict):
        raise ValueError(f"expected JSON object in {path}")
    return {str(key): value for key, value in raw.items()}


def _oews_rows(payload: dict[str, Any]) -> list[OewsCompositionRow]:
    raw_rows = payload.get("industries")
    if not isinstance(raw_rows, list):
        raise ValueError("OEWS composition industries must be a list")
    rows: list[OewsCompositionRow] = []
    for raw in raw_rows:
        if not isinstance(raw, dict):
            raise ValueError("OEWS composition row must be an object")
        occupation_employment_raw = raw.get("occupation_employment")
        if not isinstance(occupation_employment_raw, dict):
            raise ValueError("OEWS row occupation_employment must be an object")
        worker_weights_raw = raw.get("worker_weights")
        worker_weights = None
        if isinstance(worker_weights_raw, dict):
            worker_weights = {
                str(key): float(value) for key, value in worker_weights_raw.items()
            }
        rows.append(
            OewsCompositionRow(
                industry_index=int(raw["industry_index"]),
                industry_id=str(raw["industry_id"]),
                industry_name=str(raw["industry_name"]),
                oews_industry_code=str(raw["oews_industry_code"]),
                comparability=str(raw["comparability"]),
                comparability_reason=(
                    str(raw["comparability_reason"])
                    if raw.get("comparability_reason") is not None
                    else None
                ),
                total_employment=(
                    float(raw["total_employment"])
                    if raw.get("total_employment") is not None
                    else None
                ),
                observed_major_group_employment=float(
                    raw["observed_major_group_employment"]
                ),
                raw_sum_to_total_ratio=(
                    float(raw["raw_sum_to_total_ratio"])
                    if raw.get("raw_sum_to_total_ratio") is not None
                    else None
                ),
                coverage=float(raw["coverage"]),
                supported=bool(raw["supported"]),
                missing_occupations=tuple(
                    str(value) for value in raw.get("missing_occupations", [])
                ),
                occupation_employment={
                    str(key): (float(value) if value is not None else None)
                    for key, value in occupation_employment_raw.items()
                },
                worker_weights=worker_weights,
            )
        )
    return rows


def _cps_industries(payload: dict[str, Any]) -> list[dict[str, Any]]:
    raw_rows = payload.get("industries")
    if not isinstance(raw_rows, list):
        raise ValueError("CPS composition industries must be a list")
    rows: list[dict[str, Any]] = []
    for raw in raw_rows:
        if not isinstance(raw, dict):
            raise ValueError("CPS composition row must be an object")
        rows.append({str(key): value for key, value in raw.items()})
    return rows


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"cannot write empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _comparison_rows(rows: list[Any]) -> list[dict[str, Any]]:
    return [asdict(row) for row in rows]


def _bound_rows(rows: list[Any]) -> list[dict[str, Any]]:
    serialized: list[dict[str, Any]] = []
    for row in rows:
        document = asdict(row)
        document["missing_occupations"] = ";".join(row.missing_occupations)
        serialized.append(document)
    return serialized


def _period_summary(
    *,
    period: str,
    comparisons: list[Any],
    bounds: list[Any],
) -> dict[str, Any]:
    primary_exact = [
        row
        for row in comparisons
        if row.comparability == "primary" and row.l1_distance is not None
    ]
    primary_bounds = [
        row
        for row in bounds
        if row.comparability == "primary" and row.bounds_supported
    ]
    primary_incomplete_bounds = [row for row in primary_bounds if not row.point_identified]
    l1_values = [float(row.l1_distance) for row in primary_exact]
    cosine_values = [
        float(row.cosine_similarity)
        for row in primary_exact
        if row.cosine_similarity is not None
    ]
    spearman_values = [
        float(row.spearman_rank_correlation)
        for row in primary_exact
        if row.spearman_rank_correlation is not None
    ]
    lower_values = [
        float(row.l1_lower_bound)
        for row in primary_bounds
        if row.l1_lower_bound is not None
    ]
    upper_values = [
        float(row.l1_upper_bound)
        for row in primary_bounds
        if row.l1_upper_bound is not None
    ]
    bound_widths = [
        float(row.l1_bound_width)
        for row in primary_incomplete_bounds
        if row.l1_bound_width is not None
    ]
    residual_shares = [
        float(row.residual_unpublished_mass_share)
        for row in primary_incomplete_bounds
        if row.residual_unpublished_mass_share is not None
    ]
    top_agreements = sum(row.top_occupation_agreement is True for row in primary_exact)
    return {
        "period": period,
        "primary_industry_count": sum(
            row.comparability == "primary" for row in comparisons
        ),
        "primary_exact_comparison_count": len(primary_exact),
        "primary_bound_supported_count": len(primary_bounds),
        "primary_partially_identified_count": len(primary_incomplete_bounds),
        "median_exact_l1_distance": median(l1_values),
        "median_exact_cosine_similarity": median(cosine_values),
        "median_exact_spearman_rank_correlation": median(spearman_values),
        "exact_top_occupation_agreement_count": top_agreements,
        "exact_top_occupation_agreement_rate": (
            top_agreements / len(primary_exact) if primary_exact else None
        ),
        "median_primary_l1_lower_bound": median(lower_values),
        "median_primary_l1_upper_bound": median(upper_values),
        "maximum_partial_l1_bound_width": max(bound_widths, default=0.0),
        "maximum_residual_unpublished_mass_share": max(residual_shares, default=0.0),
    }


def _canonical_weights(
    row: dict[str, Any], occupation_ids: list[str]
) -> dict[str, float] | None:
    raw = row.get("worker_weights")
    if not isinstance(raw, dict):
        return None
    values = {str(key): float(value) for key, value in raw.items()}
    return {occupation_id: values.get(occupation_id, 0.0) for occupation_id in occupation_ids}


def _cps_vintage_stability(
    *,
    cps_2025: list[dict[str, Any]],
    cps_2026: list[dict[str, Any]],
    oews_rows: list[OewsCompositionRow],
    occupation_ids: list[str],
) -> list[dict[str, Any]]:
    by_2025 = {str(row["industry_id"]): row for row in cps_2025}
    by_2026 = {str(row["industry_id"]): row for row in cps_2026}
    comparability = {row.industry_id: row.comparability for row in oews_rows}
    names = {row.industry_id: row.industry_name for row in oews_rows}
    indices = {row.industry_id: row.industry_index for row in oews_rows}
    results: list[dict[str, Any]] = []

    for industry_id in sorted(indices, key=indices.__getitem__):
        row_2025 = by_2025.get(industry_id)
        row_2026 = by_2026.get(industry_id)
        weights_2025 = (
            _canonical_weights(row_2025, occupation_ids) if row_2025 is not None else None
        )
        weights_2026 = (
            _canonical_weights(row_2026, occupation_ids) if row_2026 is not None else None
        )
        if weights_2025 is None or weights_2026 is None:
            results.append(
                {
                    "industry_index": indices[industry_id],
                    "industry_id": industry_id,
                    "industry_name": names[industry_id],
                    "comparability": comparability[industry_id],
                    "supported": False,
                    "l1_distance": None,
                    "cosine_similarity": None,
                    "spearman_rank_correlation": None,
                    "top_occupation_agreement": None,
                    "cps_2025_top_occupation": None,
                    "cps_2026_top_occupation": None,
                }
            )
            continue
        vector_2025 = [weights_2025[key] for key in occupation_ids]
        vector_2026 = [weights_2026[key] for key in occupation_ids]
        top_2025 = max(occupation_ids, key=weights_2025.__getitem__)
        top_2026 = max(occupation_ids, key=weights_2026.__getitem__)
        results.append(
            {
                "industry_index": indices[industry_id],
                "industry_id": industry_id,
                "industry_name": names[industry_id],
                "comparability": comparability[industry_id],
                "supported": True,
                "l1_distance": sum(
                    abs(left - right)
                    for left, right in zip(vector_2025, vector_2026, strict=True)
                ),
                "cosine_similarity": cosine_similarity(vector_2025, vector_2026),
                "spearman_rank_correlation": spearman_rank_correlation(
                    vector_2025, vector_2026
                ),
                "top_occupation_agreement": top_2025 == top_2026,
                "cps_2025_top_occupation": top_2025,
                "cps_2026_top_occupation": top_2026,
            }
        )
    return results


def _same_industry_exact_deltas(
    comparisons_2025: list[Any], comparisons_2026: list[Any]
) -> list[dict[str, Any]]:
    by_2025 = {row.industry_id: row for row in comparisons_2025}
    results: list[dict[str, Any]] = []
    for row_2026 in comparisons_2026:
        row_2025 = by_2025.get(row_2026.industry_id)
        if (
            row_2025 is None
            or row_2025.comparability != "primary"
            or row_2025.l1_distance is None
            or row_2026.l1_distance is None
        ):
            continue
        delta = float(row_2026.l1_distance) - float(row_2025.l1_distance)
        results.append(
            {
                "industry_index": row_2026.industry_index,
                "industry_id": row_2026.industry_id,
                "industry_name": row_2026.industry_name,
                "l1_q2_2025": row_2025.l1_distance,
                "l1_q2_2026": row_2026.l1_distance,
                "l1_2026_minus_2025": delta,
                "q2_2025_closer_to_may_2025_oews": delta > 0,
            }
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oews-composition", type=Path, required=True)
    parser.add_argument("--cps-2025", type=Path, required=True)
    parser.add_argument("--cps-2026", type=Path, required=True)
    parser.add_argument("--occupation-crosswalk", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--validation-report", type=Path, required=True)
    parser.add_argument("--source-build-commit", required=True)
    args = parser.parse_args()

    oews_payload = _load_json(args.oews_composition)
    cps_2025_payload = _load_json(args.cps_2025)
    cps_2026_payload = _load_json(args.cps_2026)
    occupation_crosswalk = _load_json(args.occupation_crosswalk)
    occupation_entries = occupation_crosswalk.get("entries")
    if not isinstance(occupation_entries, list):
        raise ValueError("occupation crosswalk entries must be a list")
    occupation_ids = [str(row["entity_id"]) for row in occupation_entries]

    oews_rows = _oews_rows(oews_payload)
    cps_2025 = _cps_industries(cps_2025_payload)
    cps_2026 = _cps_industries(cps_2026_payload)

    comparisons_2025 = compare_cps_oews_worker_composition(
        oews_rows, cps_2025, occupation_ids=occupation_ids
    )
    comparisons_2026 = compare_cps_oews_worker_composition(
        oews_rows, cps_2026, occupation_ids=occupation_ids
    )
    bounds_2025 = l1_identification_bounds(
        oews_rows, cps_2025, occupation_ids=occupation_ids
    )
    bounds_2026 = l1_identification_bounds(
        oews_rows, cps_2026, occupation_ids=occupation_ids
    )
    cps_stability = _cps_vintage_stability(
        cps_2025=cps_2025,
        cps_2026=cps_2026,
        oews_rows=oews_rows,
        occupation_ids=occupation_ids,
    )
    exact_deltas = _same_industry_exact_deltas(comparisons_2025, comparisons_2026)

    summary_2025 = _period_summary(
        period=str(cps_2025_payload.get("period", "2025-Q2")),
        comparisons=comparisons_2025,
        bounds=bounds_2025,
    )
    summary_2026 = _period_summary(
        period=str(cps_2026_payload.get("period", "2026-Q2")),
        comparisons=comparisons_2026,
        bounds=bounds_2026,
    )
    primary_cps_stability = [
        row
        for row in cps_stability
        if row["comparability"] == "primary" and row["supported"]
    ]
    stability_l1 = [float(row["l1_distance"]) for row in primary_cps_stability]
    stability_cosine = [
        float(row["cosine_similarity"])
        for row in primary_cps_stability
        if row["cosine_similarity"] is not None
    ]
    stability_spearman = [
        float(row["spearman_rank_correlation"])
        for row in primary_cps_stability
        if row["spearman_rank_correlation"] is not None
    ]
    stability_top = sum(
        row["top_occupation_agreement"] is True for row in primary_cps_stability
    )
    delta_values = [float(row["l1_2026_minus_2025"]) for row in exact_deltas]
    generated_at = datetime.now(UTC).isoformat()

    summary = {
        "status": "OEWS partial-identification and CPS vintage robustness executed",
        "generated_at_utc": generated_at,
        "source_build_commit": args.source_build_commit,
        "oews_period": "May 2025",
        "occupation_count": len(occupation_ids),
        "cps_2025": summary_2025,
        "cps_2026": summary_2026,
        "cps_q2_2025_vs_q2_2026_primary": {
            "supported_industry_count": len(primary_cps_stability),
            "median_l1_distance": median(stability_l1),
            "median_cosine_similarity": median(stability_cosine),
            "median_spearman_rank_correlation": median(stability_spearman),
            "top_occupation_agreement_count": stability_top,
            "top_occupation_agreement_rate": (
                stability_top / len(primary_cps_stability)
                if primary_cps_stability
                else None
            ),
        },
        "same_exact_industry_vintage_deltas": {
            "industry_count": len(exact_deltas),
            "median_l1_2026_minus_2025": median(delta_values),
            "q2_2025_closer_count": sum(
                bool(row["q2_2025_closer_to_may_2025_oews"])
                for row in exact_deltas
            ),
        },
        "identification_boundary": (
            "Partial L1 intervals condition on published OEWS all-occupations totals and "
            "published major-group employment counts. They identify only the effect of "
            "allocating unpublished OEWS occupation-cell mass; they do not include source "
            "sampling/model uncertainty or published-value rounding uncertainty."
        ),
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(
        args.output_dir / "oews_vs_cps_q2_2025_exact.csv",
        _comparison_rows(comparisons_2025),
    )
    _write_csv(
        args.output_dir / "oews_vs_cps_q2_2026_exact.csv",
        _comparison_rows(comparisons_2026),
    )
    _write_csv(
        args.output_dir / "oews_vs_cps_q2_2025_l1_bounds.csv",
        _bound_rows(bounds_2025),
    )
    _write_csv(
        args.output_dir / "oews_vs_cps_q2_2026_l1_bounds.csv",
        _bound_rows(bounds_2026),
    )
    _write_csv(args.output_dir / "cps_q2_2025_vs_q2_2026.csv", cps_stability)
    _write_csv(args.output_dir / "exact_vintage_l1_deltas.csv", exact_deltas)
    (args.output_dir / "validation_checks.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )

    report = f"""# May 2025 OEWS cross-source and CPS-vintage robustness

## Status

This checkpoint separates two sources of disagreement in occupation composition: source-system differences between OEWS and CPS, and temporal movement between Q2 2025 and Q2 2026 CPS.

The OEWS source is held fixed at May 2025. No additional BLS request is made by this comparison step; it consumes the previously frozen OEWS aggregate artifact.

## Exact-vector comparison

For primary-comparability industries with all 22 OEWS major occupation groups published:

- OEWS vs Q2 2025 CPS median L1: **{summary_2025['median_exact_l1_distance']}**
- OEWS vs Q2 2025 CPS median cosine: **{summary_2025['median_exact_cosine_similarity']}**
- OEWS vs Q2 2025 CPS median Spearman: **{summary_2025['median_exact_spearman_rank_correlation']}**
- OEWS vs Q2 2026 CPS median L1: **{summary_2026['median_exact_l1_distance']}**
- OEWS vs Q2 2026 CPS median cosine: **{summary_2026['median_exact_cosine_similarity']}**
- OEWS vs Q2 2026 CPS median Spearman: **{summary_2026['median_exact_spearman_rank_correlation']}**

The exact same-industry L1 difference is defined as Q2-2026 L1 minus Q2-2025 L1. Its median is **{summary['same_exact_industry_vintage_deltas']['median_l1_2026_minus_2025']}** across **{summary['same_exact_industry_vintage_deltas']['industry_count']}** primary industries with exact OEWS vectors.

## Partial identification for unpublished OEWS cells

All primary industries with a coherent published-total residual receive an L1 interval. Complete OEWS vectors have zero-width intervals. Incomplete vectors allow the residual unpublished employment mass to be allocated arbitrarily across the missing canonical occupations.

- Q2 2025 CPS median primary L1 lower bound: **{summary_2025['median_primary_l1_lower_bound']}**
- Q2 2025 CPS median primary L1 upper bound: **{summary_2025['median_primary_l1_upper_bound']}**
- Q2 2026 CPS median primary L1 lower bound: **{summary_2026['median_primary_l1_lower_bound']}**
- Q2 2026 CPS median primary L1 upper bound: **{summary_2026['median_primary_l1_upper_bound']}**
- maximum unresolved OEWS mass share among partially identified primary industries: **{max(summary_2025['maximum_residual_unpublished_mass_share'], summary_2026['maximum_residual_unpublished_mass_share'])}**

These intervals address unpublished-cell allocation only. They do not represent confidence intervals and do not absorb OEWS model uncertainty, CPS sampling uncertainty, or published-value rounding uncertainty.

## CPS temporal stability

Across primary-comparability industries, Q2 2025 versus Q2 2026 CPS worker-share composition has:

- median L1 distance: **{summary['cps_q2_2025_vs_q2_2026_primary']['median_l1_distance']}**
- median cosine similarity: **{summary['cps_q2_2025_vs_q2_2026_primary']['median_cosine_similarity']}**
- median Spearman rank correlation: **{summary['cps_q2_2025_vs_q2_2026_primary']['median_spearman_rank_correlation']}**

## Scientific boundary

This analysis strengthens or weakens the claim that the CPS occupation-composition layer is structurally reasonable across an independent employer-side source and nearby vintages. It does not identify an RPS industry-context effect. That gate remains closed until an authorized compatible RPS occupation vintage is available.
"""
    args.validation_report.parent.mkdir(parents=True, exist_ok=True)
    args.validation_report.write_text(report)

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
