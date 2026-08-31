#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from genai_at_work.composition import composition_residuals
from genai_at_work.cps import IndustryComposition


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--composition", type=Path, required=True)
    parser.add_argument("--rps-private-fixture", type=Path, required=True)
    parser.add_argument("--period", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--hours-basis", choices=("actual", "usual"), default="actual")
    args = parser.parse_args()

    composition_doc = json.loads(args.composition.read_text())
    rps_doc = json.loads(args.rps_private_fixture.read_text())
    compositions = [IndustryComposition(**row) for row in composition_doc["industries"]]

    results = {}
    for metric_id in ("adoption_work", "assisted_hours_share", "reported_time_savings_share"):
        rows = composition_residuals(
            compositions,
            rps_doc["records"],
            period=args.period,
            metric_id=metric_id,
            hours_basis=args.hours_basis,
        )
        results[metric_id] = [asdict(row) for row in rows]

    payload = {
        "status": "occupation-adjusted descriptive industry-context residuals; not causal effects",
        "period": args.period,
        "hours_basis": args.hours_basis,
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({metric: len(rows) for metric, rows in results.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
