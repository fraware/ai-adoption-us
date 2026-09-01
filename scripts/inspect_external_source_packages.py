#!/usr/bin/env python3
"""Inspect external research source packages without retaining raw data.

This script is intentionally limited to source reconnaissance. It records transport
metadata, cryptographic identity, archive directories, and workbook schema previews.
It does not infer publication or redistribution rights from technical accessibility.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import openpyxl
import requests

OEWS_URL = "https://www.bls.gov/oes/special-requests/oesm25in4.zip"
RPS_REPLICATION_URL = (
    "https://services.informs.org/dataset/download.php?doi=mnsc.2025.02523"
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fetch(url: str, timeout: int = 90) -> tuple[requests.Response | None, str | None]:
    try:
        response = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers={"User-Agent": "genai-at-work-research/0.1 source-validation"},
        )
        return response, None
    except requests.RequestException as exc:
        return None, f"{type(exc).__name__}: {exc}"


def _safe_headers(response: requests.Response) -> dict[str, str | None]:
    return {
        "content_type": response.headers.get("content-type"),
        "content_length": response.headers.get("content-length"),
        "content_disposition": response.headers.get("content-disposition"),
        "last_modified": response.headers.get("last-modified"),
        "etag": response.headers.get("etag"),
    }


def inspect_oews(*, generated_at: str, source_build_commit: str) -> dict[str, Any]:
    response, error = _fetch(OEWS_URL)
    if response is None:
        raise RuntimeError(f"OEWS download failed: {error}")
    if response.status_code != 200:
        raise RuntimeError(f"OEWS returned HTTP {response.status_code}")

    payload = response.content
    if not zipfile.is_zipfile(io.BytesIO(payload)):
        raise RuntimeError("OEWS response is not a ZIP archive")

    entries: list[dict[str, Any]] = []
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        for info in archive.infolist():
            entry: dict[str, Any] = {
                "path": info.filename,
                "size_bytes": info.file_size,
                "compressed_size_bytes": info.compress_size,
            }
            if info.filename.lower().endswith(".xlsx"):
                workbook_bytes = archive.read(info.filename)
                workbook = openpyxl.load_workbook(
                    io.BytesIO(workbook_bytes), read_only=True, data_only=True
                )
                sheets: list[dict[str, Any]] = []
                for sheet in workbook.worksheets:
                    preview = [
                        [None if value is None else str(value) for value in row]
                        for row in sheet.iter_rows(min_row=1, max_row=6, values_only=True)
                    ]
                    sheets.append(
                        {
                            "name": sheet.title,
                            "max_row": sheet.max_row,
                            "max_column": sheet.max_column,
                            "first_six_rows": preview,
                        }
                    )
                entry["xlsx_sha256"] = _sha256(workbook_bytes)
                entry["sheets"] = sheets
                workbook.close()
            entries.append(entry)

    return {
        "status": "downloaded_and_schema_inspected",
        "provider": "U.S. Bureau of Labor Statistics",
        "dataset": (
            "May 2025 OEWS national industry-specific occupational employment "
            "and wage estimates"
        ),
        "source_url": OEWS_URL,
        "final_url": response.url,
        "http_status": response.status_code,
        "headers": _safe_headers(response),
        "archive_size_bytes": len(payload),
        "archive_sha256": _sha256(payload),
        "archive_entries": entries,
        "generated_at_utc": generated_at,
        "source_build_commit": source_build_commit,
        "raw_retained_in_repository": False,
    }


def inspect_rps(*, generated_at: str, source_build_commit: str) -> dict[str, Any]:
    response, error = _fetch(RPS_REPLICATION_URL)
    result: dict[str, Any] = {
        "provider_surface": "INFORMS Management Science replication-files endpoint",
        "article_doi": "10.1287/mnsc.2025.02523",
        "source_url": RPS_REPLICATION_URL,
        "generated_at_utc": generated_at,
        "source_build_commit": source_build_commit,
        "raw_retained_in_repository": False,
        "rights_conclusion": (
            "none; technical accessibility does not establish reuse or redistribution "
            "permission"
        ),
    }
    if response is None:
        result.update({"status": "request_error", "request_error": error})
        return result

    payload = response.content
    is_zip = zipfile.is_zipfile(io.BytesIO(payload))
    result.update(
        {
            "status": "http_response_received",
            "http_status": response.status_code,
            "final_url": response.url,
            "headers": _safe_headers(response),
            "response_size_bytes": len(payload),
            "response_sha256": _sha256(payload),
            "is_zip_archive": is_zip,
        }
    )
    if is_zip:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            result["archive_entries"] = [
                {
                    "path": info.filename,
                    "size_bytes": info.file_size,
                    "compressed_size_bytes": info.compress_size,
                }
                for info in archive.infolist()
            ]
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    generated_at = datetime.now(UTC).isoformat()
    source_build_commit = os.environ.get("SOURCE_BUILD_COMMIT", "unknown")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    oews = inspect_oews(
        generated_at=generated_at, source_build_commit=source_build_commit
    )
    rps = inspect_rps(generated_at=generated_at, source_build_commit=source_build_commit)

    (args.output_dir / "oews_may_2025_source_schema.json").write_text(
        json.dumps(oews, indent=2, sort_keys=True) + "\n"
    )
    (args.output_dir / "rps_replication_endpoint_probe.json").write_text(
        json.dumps(rps, indent=2, sort_keys=True) + "\n"
    )
    (args.output_dir / "README.md").write_text(
        "# Source-unlock reconnaissance - 2026-09-01\n\n"
        "The official May 2025 BLS national industry-specific OEWS package is "
        "inspected in memory and represented here only by source identity, hashes, "
        "archive structure, and workbook schema previews. Raw OEWS bytes are not "
        "retained in the repository.\n\n"
        "The INFORMS historical RPS replication-files endpoint is probed separately. "
        "Its result establishes technical accessibility only. No reuse, storage, or "
        "redistribution rights are inferred from a successful download.\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
