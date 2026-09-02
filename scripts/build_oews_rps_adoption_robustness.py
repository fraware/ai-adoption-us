#!/usr/bin/env python3
"""Build rights-safe OEWS-weighted RPS adoption robustness from a private RPS snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from genai_at_work.oews import OewsCompositionRow
from genai_at_work.oews_rps import (
    OewsRpsError,
    adoption_counterfactual_bounds,
    compare_cps_oews_adoption_residuals,
    summarize_cps_oews_adoption_comparison,
)
from genai_at_work.rps_release import snapshot_content_sha256
from genai_at_work.rps_release_complete import prepare_rps_source_history


def _load_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise OewsRpsError(f"could not read {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise OewsRpsError(f"{label} must be a JSON object: {path}")
    return {str(key): item for key, item in value.items()}


def _load_rows(path: Path, *, label: str) -> list[dict[str, Any]]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise OewsRpsError(f"could not read {label} {path}: {exc}") from exc
    if not isinstance(value, list):
        raise OewsRpsError(f"{label} must be a JSON array: {path}")
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise OewsRpsError(f"{label}[{index}] must be an object")
        rows.append({str(key): cell for key, cell in item.items()})
    return rows


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _oews_rows(payload: dict[str, Any]) -> list[OewsCompositionRow]:
    raw_rows = payload.get("industries")
    if not isinstance(raw_rows, list):
        raise OewsRpsError("OEWS composition industries must be a list")
    rows: list[OewsCompositionRow] = []
    for index, raw in enumerate(raw_rows):
        if not isinstance(raw, dict):
            raise OewsRpsError(f"OEWS composition industries[{index}] must be an object")
        occupation_employment_raw = raw.get("occupation_employment")
        if not isinstance(occupation_employment_raw, dict):
            raise OewsRpsError("OEWS occupation_employment must be an object")
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
                observed_major_group_employment=float(raw["observed_major_group_employment"]),
                raw_sum_to_total_ratio=(
                    float(raw["raw_sum_to_total_ratio"])
                    if raw.get("raw_sum_to_total_ratio") is not None
                    else None
                ),
                coverage=float(raw["coverage"]),
                supported=bool(raw["supported"]),
                missing_occupations=tuple(str(value) for value in raw.get("missing_occupations", [])),
                occupation_employment={
                    str(key): (float(value) if value is not None else None)
                    for key, value in occupation_employment_raw.items()
                },
                worker_weights=worker_weights,
            )
        )
    rows.sort(key=lambda row: row.industry_index)
    if len(rows) != 20 or [row.industry_index for row in rows] != list(range(1, 21)):
        raise OewsRpsError("OEWS composition must contain canonical industry indices 1..20")
    return rows


def _occupation_ids(payload: dict[str, Any]) -> list[str]:
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise OewsRpsError("OEWS occupation crosswalk entries must be a list")
    indexed: list[tuple[int, str]] = []
    for index, raw in enumerate(entries):
        if not isinstance(raw, dict):
            raise OewsRpsError(f"occupation crosswalk entry {index} must be an object")
        entity_index = raw.get("entity_index")
        entity_id = raw.get("entity_id")
        if isinstance(entity_index, bool) or not isinstance(entity_index, int):
            raise OewsRpsError("occupation crosswalk entity_index must be an integer")
        if not isinstance(entity_id, str) or not entity_id:
            raise OewsRpsError("occupation crosswalk entity_id must be a non-empty string")
        indexed.append((entity_index, entity_id))
    indexed.sort()
    if [index for index, _ in indexed] != list(range(1, 23)):
        raise OewsRpsError("occupation crosswalk must contain canonical indices 1..22")
    ids = [entity_id for _, entity_id in indexed]
    if len(set(ids)) != 22:
        raise OewsRpsError("occupation crosswalk entity ids must be unique")
    return ids


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-snapshot", type=Path, required=True)
    parser.add_argument("--canonical-manifest", type=Path, required=True)
    parser.add_argument("--provider-scope", type=Path, required=True)
    parser.add_argument("--oews-composition", type=Path, required=True)
    parser.add_argument("--occupation-crosswalk", type=Path, required=True)
    parser.add_argument("--cps-primary-residuals", type=Path, required=True)
    parser.add_argument("--period", action="append", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir: Path = args.output_dir
    if output_dir.exists() and any(output_dir.iterdir()):
        raise SystemExit(f"output directory must be new or empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        snapshot = _load_object(args.source_snapshot, label="RPS source snapshot")
        declared_content_sha = snapshot.get("content_sha256")
        recomputed_content_sha = snapshot_content_sha256(snapshot)
        if declared_content_sha != recomputed_content_sha:
            raise OewsRpsError("RPS source snapshot scientific content hash does not verify")
        manifest = _load_object(args.canonical_manifest, label="RPS canonical manifest")
        scope = _load_object(args.provider_scope, label="RPS provider scope")
        prepared = prepare_rps_source_history(snapshot, manifest, scope)
        panel = prepared.analysis_panel
        oews_payload = _load_object(args.oews_composition, label="OEWS composition")
        oews_rows = _oews_rows(oews_payload)
        occupation_crosswalk = _load_object(
            args.occupation_crosswalk, label="OEWS occupation crosswalk"
        )
        occupation_ids = _occupation_ids(occupation_crosswalk)
        cps_rows = _load_rows(args.cps_primary_residuals, label="CPS primary residuals")

        periods = tuple(dict.fromkeys(str(value) for value in args.period))
        if not periods:
            raise OewsRpsError("at least one period is required")
        unavailable = [period for period in periods if period not in panel.periods]
        if unavailable:
            raise OewsRpsError(
                f"requested periods are unavailable in the complete RPS A/H/S panel: {unavailable!r}"
            )

        bound_documents: list[dict[str, Any]] = []
        comparison_documents: list[dict[str, Any]] = []
        summaries: list[dict[str, Any]] = []
        for period in periods:
            bounds = adoption_counterfactual_bounds(
                oews_rows,
                panel.subgroup_records,
                period=period,
                occupation_ids=occupation_ids,
            )
            comparisons = compare_cps_oews_adoption_residuals(
                cps_rows,
                bounds,
                period=period,
            )
            bound_documents.extend(asdict(row) for row in bounds)
            comparison_documents.extend(asdict(row) for row in comparisons)
            summaries.append(summarize_cps_oews_adoption_comparison(comparisons, period=period))

        expected_rows = 20 * len(periods)
        if len(bound_documents) != expected_rows or len(comparison_documents) != expected_rows:
            raise OewsRpsError("OEWS/RPS robustness output does not contain 20 industries per period")
        unsupported_bounds = sum(not bool(row["supported"]) for row in bound_documents)
        unsupported_comparisons = sum(
            not (bool(row["cps_supported"]) and bool(row["oews_supported"]))
            for row in comparison_documents
        )

        input_manifest = {
            "schema_version": 1,
            "artifact_type": "oews_rps_adoption_robustness_input_manifest",
            "source_content_sha256": recomputed_content_sha,
            "source_snapshot_file_sha256": _sha256(args.source_snapshot),
            "source_snapshot_published": False,
            "source_series_count": panel.series_count,
            "source_observation_count": panel.observation_count,
            "rps_analysis_periods": list(panel.periods),
            "requested_periods": list(periods),
            "canonical_manifest_sha256": _sha256(args.canonical_manifest),
            "provider_scope_sha256": _sha256(args.provider_scope),
            "oews_composition_sha256": _sha256(args.oews_composition),
            "occupation_crosswalk_sha256": _sha256(args.occupation_crosswalk),
            "cps_primary_residuals_sha256": _sha256(args.cps_primary_residuals),
            "public_raw_rps_observations_included": False,
            "interpretation_boundary": (
                "OEWS is an independent establishment-side occupation-composition robustness "
                "source. Missing OEWS occupation cells are partially identified, not zero-imputed. "
                "CPS and OEWS residuals are never averaged."
            ),
        }
        validation = {
            "status": "pass" if unsupported_bounds == 0 and unsupported_comparisons == 0 else "pass_with_unsupported_rows",
            "periods": list(periods),
            "counterfactual_row_count": len(bound_documents),
            "comparison_row_count": len(comparison_documents),
            "unsupported_counterfactual_row_count": unsupported_bounds,
            "unsupported_comparison_row_count": unsupported_comparisons,
            "point_identified_row_count": sum(bool(row["point_identified"]) for row in bound_documents),
            "partially_identified_row_count": sum(
                bool(row["supported"]) and not bool(row["point_identified"])
                for row in bound_documents
            ),
            "raw_rps_snapshot_published": False,
            "interpretation": "independent-source descriptive robustness; not causal inference",
        }

        _write_json(output_dir / "oews_rps_adoption_counterfactuals.json", bound_documents)
        _write_json(output_dir / "cps_oews_adoption_comparison.json", comparison_documents)
        _write_json(output_dir / "summary.json", summaries)
        _write_json(output_dir / "input_manifest.json", input_manifest)
        _write_json(output_dir / "validation_checks.json", validation)

        print(
            json.dumps(
                {
                    "status": validation["status"],
                    "periods": list(periods),
                    "counterfactual_rows": len(bound_documents),
                    "comparison_rows": len(comparison_documents),
                    "point_identified_rows": validation["point_identified_row_count"],
                    "partially_identified_rows": validation["partially_identified_row_count"],
                    "unsupported_counterfactual_rows": unsupported_bounds,
                    "source_content_sha256": recomputed_content_sha,
                    "public_raw_rps_observations_included": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
    except OewsRpsError as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
