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

    candidates = [
        "540000",
        "54----",
        "23----",
        "31--33",
        "44--45",
        "48--49",
        "56----",
        "56--57",
        "99-100",
        "999000",
    ]
    ids = []
    for industry in candidates:
        ids.append(series_id(industry))
        ids.append(series_id(industry, "110000"))

    response = requests.post(
        API_URL,
        json={"seriesid": ids, "startyear": "2025", "endyear": "2025"},
        timeout=60,
        headers={"User-Agent": "genai-at-work-research/0.1 source-validation"},
    )
    response.raise_for_status()
    payload = response.json()
    results = []
    for series in payload.get("Results", {}).get("series", []):
        data = series.get("data", [])
        results.append(
            {
                "series_id": series.get("seriesID"),
                "has_data": bool(data),
                "data": data,
            }
        )

    output = {
        "status": payload.get("status"),
        "messages": payload.get("message", []),
        "candidate_industry_codes": candidates,
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"resolved": [r["series_id"] for r in results if r["has_data"]]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
