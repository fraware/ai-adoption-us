#!/usr/bin/env python3
"""Execute the canonical BTOS-RPS industry triangulation from pinned checkpoints."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from genai_at_work.btos_rps_triangulation import execute_v1

ROOT = Path(__file__).parents[1]
DEFAULT_BTOS = ROOT / "data" / "derived" / "btos" / "btos_core_ai_202611.json"
DEFAULT_RPS = ROOT / "data" / "registry" / "rps_industry_adoption_q2_2026_v1.json"
DEFAULT_CROSSWALK = ROOT / "data" / "registry" / "btos_rps_industry_crosswalk_v1.json"
DEFAULT_OUTPUT = ROOT / "data" / "derived" / "btos_rps" / "industry_triangulation_q2_2026_v1.json"
PUBLIC_PRODUCT_ROUTE = "/explore/industries"
PUBLICATION_VALIDATED_COMMIT = "75b94550be97c2e500db6c7b796330d0d8e90c40"


def _load(path: Path) -> dict[str, Any]:
    value: object = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object in {path}")
    return {str(key): cell for key, cell in value.items()}


def build_payload(
    btos_path: Path = DEFAULT_BTOS,
    rps_path: Path = DEFAULT_RPS,
    crosswalk_path: Path = DEFAULT_CROSSWALK,
) -> dict[str, Any]:
    btos = _load(btos_path)
    rps = _load(rps_path)
    crosswalk = _load(crosswalk_path)
    result = execute_v1(btos, rps, crosswalk)

    return {
        "schema_version": 1,
        "analysis_id": "btos-rps-industry-triangulation-q2-2026-v1",
        "executed_date": "2026-09-02",
        "protocol_id": "btos-rps-industry-triangulation-v1",
        "protocol_canonical_commit": "854db8d637e5f7896ef2f779692d9451d8971e55",
        "inputs": {
            "btos_checkpoint": str(btos_path.relative_to(ROOT)),
            "rps_checkpoint": str(rps_path.relative_to(ROOT)),
            "crosswalk": str(crosswalk_path.relative_to(ROOT)),
        },
        "constructs": {
            "btos": "percent of responding employer businesses reporting AI use in any business function in the last two weeks",
            "rps": "percent of employed adults aged 18-64 in the industry reporting use of Generative AI for their job",
            "interpretation": "Cross-source sector concordance only. The percentages have different units, denominators, technology scope, and reference periods and are not interchangeable.",
        },
        "primary": result["primary"],
        "expanded_sensitivity": result["expanded_sensitivity"],
        "exclusions": [
            {
                "entity_index": 1,
                "reason": "BTOS sector 11 suppressed in cycle 202611; no reconstruction or imputation.",
            },
            {
                "entity_index": 13,
                "reason": "BTOS sector 55 suppressed in cycle 202611; excluded from the primary statistic without reconstruction or cycle switching.",
            },
            {"entity_index": 20, "reason": "Public Administration has no BTOS counterpart."},
            {
                "source_key": "XX",
                "reason": "BTOS unclassified multi-sector businesses are not mapped or redistributed.",
            },
        ],
        "pairs": result["pairs"],
        "preanalysis_exposure_disclosure": "The canonical protocol records that two RPS industry observations (Information and Management of Companies and Enterprises) were inadvertently exposed during metadata verification before preregistration. The full industry vector and selected-cycle BTOS outcomes were not assembled together and no cross-source statistic was computed before the protocol was canonical.",
        "prohibited_interpretations": [
            "Do not interpret correlation as a causal effect.",
            "Do not call BTOS business AI use equivalent to RPS worker GenAI adoption.",
            "Do not calculate percentage-point gaps or calibration to an identity line from these non-commensurate measures.",
            "Do not interpret either measure as productivity.",
            "Do not report p-values or correlation confidence intervals without an approved survey-covariance design.",
        ],
        "public_product_status": "published",
        "public_product_route": PUBLIC_PRODUCT_ROUTE,
        "publication_validated_commit": PUBLICATION_VALIDATED_COMMIT,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    payload = build_payload()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
