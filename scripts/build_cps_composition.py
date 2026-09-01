#!/usr/bin/env python3
"""Build CPS occupation-composition weights from official public-use files."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from genai_at_work.cps import (
    build_composition,
    download_official_fixed_width_month,
    official_fixed_width_filename,
    quarter_months,
    read_quarter_fixed_width_gz,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--quarter", type=int, choices=(1, 2, 3, 4), required=True)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--download-missing", action="store_true")
    parser.add_argument("--coverage-gate", type=float, default=0.98)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    registry = root / "data" / "registry"
    try:
        months = quarter_months(args.year, args.quarter, registry)
    except Exception as exc:
        raise SystemExit(f"CPS quarter unavailable or invalid: {exc}") from exc

    if args.year != 2026:
        raise SystemExit(
            "CPS composition build blocked: authoritative fixed-width ingestion is currently "
            "pinned to the audited 2026 Census record layout"
        )

    if args.download_missing:
        for month in months:
            path = args.input_dir / official_fixed_width_filename(args.year, month)
            if not path.exists():
                try:
                    download_official_fixed_width_month(args.year, month, path)
                except Exception as exc:
                    raise SystemExit(f"failed to download {month} {args.year} CPS: {exc}") from exc

    try:
        people, provenance = read_quarter_fixed_width_gz(
            args.input_dir,
            year=args.year,
            quarter=args.quarter,
            registry_dir=registry,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise SystemExit(f"CPS composition build blocked: {exc}") from exc

    composition = build_composition(people, coverage_gate=args.coverage_gate)
    payload = {
        "status": "derived CPS composition; not public RPS observation data",
        "year": args.year,
        "quarter": args.quarter,
        "months": list(months),
        "input_format": "official_fixed_width_gzip",
        "coverage_gate": args.coverage_gate,
        "sample_rows": len(people),
        "provenance": provenance,
        "industries": [asdict(row) for row in composition],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"sample_rows": len(people), "industries": len(composition)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
