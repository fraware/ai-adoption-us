#!/usr/bin/env python3
"""Build rights-safe CPS/RPS composition residual evidence from a private RPS snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from genai_at_work.composition_snapshot import build_composition_residual_evidence
from genai_at_work.rps_release import prepare_rps_panel

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "registry" / "rps_source_series_manifest.json"
SCOPE_PATH = ROOT / "data" / "registry" / "rps_provider_catalog_scope.json"
DEFAULT_TIERS_PATH = (
    ROOT
    / "data"
    / "derived"
    / "composition"
    / "composition-evidence-v1"
    / "industry_evidence_tiers.json"
)


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise SystemExit(f"Expected JSON object at {path}")
    return {str(key): item for key, item in value.items()}


def _load_array(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text())
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise SystemExit(f"Expected JSON object array at {path}")
    return [{str(key): item for key, item in row.items()} for row in value]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _composition_arg(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("--composition must use PERIOD=PATH, e.g. 2026-Q2=data/...json")
    period, path = value.split("=", 1)
    if not period or not path:
        raise argparse.ArgumentTypeError("--composition requires non-empty PERIOD and PATH")
    return period, Path(path)


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-snapshot", type=Path, required=True)
    parser.add_argument(
        "--composition",
        action="append",
        type=_composition_arg,
        required=True,
        help="Repeatable PERIOD=PATH CPS composition input.",
    )
    parser.add_argument(
        "--evidence-tiers",
        type=Path,
        default=DEFAULT_TIERS_PATH,
        help="Versioned composition-basis evidence tier registry.",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    if not args.source_snapshot.is_file():
        raise SystemExit(f"Source snapshot does not exist: {args.source_snapshot}")
    if not args.evidence_tiers.is_file():
        raise SystemExit(f"Evidence tiers do not exist: {args.evidence_tiers}")
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise SystemExit(f"Output directory must be new or empty: {args.output_dir}")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    composition_paths: dict[str, Path] = {}
    for period, path in args.composition:
        if period in composition_paths:
            raise SystemExit(f"Duplicate --composition period: {period}")
        if not path.is_file():
            raise SystemExit(f"Composition input does not exist: {path}")
        composition_paths[period] = path

    snapshot = _load_object(args.source_snapshot)
    canonical_manifest = _load_object(MANIFEST_PATH)
    provider_scope = _load_object(SCOPE_PATH)
    panel = prepare_rps_panel(snapshot, canonical_manifest, provider_scope)
    compositions = {period: _load_object(path) for period, path in composition_paths.items()}
    evidence_tiers = _load_array(args.evidence_tiers)
    evidence = build_composition_residual_evidence(
        panel,
        compositions,
        evidence_tiers=evidence_tiers,
    )

    _write(args.output_dir / "composition_residual_evidence.json", evidence)
    _write(args.output_dir / "primary_residuals.json", evidence["primary_residuals"])
    _write(args.output_dir / "usual_hours_sensitivity.json", evidence["usual_hours_sensitivity"])
    _write(
        args.output_dir / "leave_one_occupation_out_influence.json",
        evidence["leave_one_occupation_out_influence"],
    )
    _write(args.output_dir / "cross_period_persistence.json", evidence["cross_period_persistence"])
    _write(args.output_dir / "validation_checks.json", evidence["validation"])

    source_content = snapshot.get("content_sha256")
    if not isinstance(source_content, str) or not source_content:
        raise SystemExit("Validated source snapshot is missing content_sha256")
    input_manifest = {
        "schema_version": 1,
        "artifact_type": "rps_cps_composition_residual_input_manifest",
        "source_content_sha256": source_content,
        "source_snapshot_file_sha256": _sha256(args.source_snapshot),
        "source_snapshot_published": False,
        "source_definition_id": panel.definition_id,
        "source_taxonomy_version": panel.taxonomy_version,
        "canonical_manifest_sha256": _sha256(MANIFEST_PATH),
        "provider_scope_sha256": _sha256(SCOPE_PATH),
        "composition_inputs": {
            period: {"path": str(path), "sha256": _sha256(path)}
            for period, path in sorted(composition_paths.items())
        },
        "evidence_tiers": {
            "path": str(args.evidence_tiers),
            "sha256": _sha256(args.evidence_tiers),
        },
        "public_raw_rps_observations_included": False,
        "interpretation_boundary": (
            "Occupation-adjusted industry-context residuals are descriptive standardization gaps, not organizational or productivity effects."
        ),
    }
    _write(args.output_dir / "input_manifest.json", input_manifest)

    print(
        json.dumps(
            {
                "periods": evidence["periods"],
                "primary_rows": len(evidence["primary_residuals"]),
                "usual_hours_sensitivity_rows": len(evidence["usual_hours_sensitivity"]),
                "influence_rows": len(evidence["leave_one_occupation_out_influence"]),
                "persistence_rows": len(evidence["cross_period_persistence"]),
                "validation_status": evidence["validation"]["status"],
                "source_content_sha256": source_content,
                "public_raw_rps_observations_included": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
