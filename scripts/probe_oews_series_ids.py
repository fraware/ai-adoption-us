#!/usr/bin/env python3
"""Resolve OEWS sector-level series-ID encoding through the sanctioned BLS API."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import requests

API_URL = "https://api.bls.gov/publicAPI/v1/timeseries/data/"


def series_id(industry: str, occupation: str = "000000", datatype: str = "01") -> str:
    if len(industry) != 6 or len(occupation) != 6 or len(datatype) != 2:
        raise ValueError("invalid OEWS series component width")
    return f"OEUN0000000{industry}{occupation}{datatype}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    # BLS sector identifiers use half-open interval notation for NAICS sectors:
    # 54--55 means sector 54, 31--34 means sectors 31-33, etc. Sector 99 uses
    # the legacy OEWS 99-100 token. These candidates cover the project's 20
    # industry groups in canonical order.
    candidates = [
        "11--12",
        "21--22",
        "23--24",
        "31--34",
        "42--43",
        "44--46",
        "48--50",
        "22--23",
        "51--52",
        "52--53",
        "53--54",
        "54--55",
        "55--56",
        "56--57",
        "61--62",
        "62--63",
        "71--72",
        "72--73",
        "81--82",
        "99-100",
    ]
    ids = [series_id(industry) for industry in candidates]

    response = requests.post(
        API_URL,
        json={"seriesid": ids, "startyear": "2025", "endyear": "2025"},
        timeout=60,
        headers={"User-Agent": "genai-at-work-research/0.1 source-validation"},
    )
    response.raise_for_status()
    payload = response.json()
    results = []
    for industry, series in zip(candidates, payload.get("Results", {}).get("series", []), strict=True):
        data = series.get("data", [])
        results.append(
            {
                "industry_code": industry,
                "series_id": series.get("seriesID"),
                "has_data": bool(data),
                "data": data,
            }
        )

    output = {
        "status": payload.get("status"),
        "messages": payload.get("message", []),
        "candidate_industry_codes": candidates,
        "all_candidates_resolved": all(result["has_data"] for result in results),
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "resolved_count": sum(1 for result in results if result["has_data"]),
                "total_candidates": len(results),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
