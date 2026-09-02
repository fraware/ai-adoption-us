from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

from genai_at_work.btos_sources import BTOS_SOURCE_URLS, download_btos_workbook


def _filename(url: str) -> str:
    name = Path(urlparse(url).path).name
    if not name:
        raise ValueError(f"BTOS source URL has no filename: {url}")
    return name


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe fixed official BTOS workbook sources.")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, object]] = []
    errors: list[dict[str, str]] = []
    retrieved_at = datetime.now(UTC).isoformat()

    for source_key, source_url in BTOS_SOURCE_URLS.items():
        try:
            downloaded = download_btos_workbook(source_key)
            filename = _filename(source_url)
            (output_dir / filename).write_bytes(downloaded.data)
            records.append(
                {
                    "source_key": source_key,
                    "source_url": downloaded.source_url,
                    "final_url": downloaded.final_url,
                    "filename": filename,
                    "content_type": downloaded.content_type,
                    "byte_size": downloaded.inspection.byte_size,
                    "sha256": downloaded.inspection.sha256,
                    "zip_entry_count": downloaded.inspection.zip_entry_count,
                    "sheet_names": list(downloaded.inspection.sheet_names),
                }
            )
        except Exception as exc:  # noqa: BLE001 - evidence manifest must capture source failures
            errors.append(
                {
                    "source_key": source_key,
                    "source_url": source_url,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )

    manifest = {
        "schema_version": 1,
        "retrieved_at_utc": retrieved_at,
        "source_owner": "U.S. Census Bureau",
        "complete": not errors and len(records) == len(BTOS_SOURCE_URLS),
        "files": records,
        "errors": errors,
        "provenance_note": (
            "Workbook bytes are workflow evidence only. A source vintage becomes canonical in the "
            "observatory only after its manifest/hash is reviewed and committed through the normal "
            "release process."
        ),
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    if errors:
        for error in errors:
            print(
                f"BTOS source probe failed for {error['source_key']}: "
                f"{error['error_type']}: {error['error']}"
            )
        return 1

    for record in records:
        print(
            f"{record['source_key']}: {record['byte_size']} bytes "
            f"sha256={record['sha256']} sheets={record['sheet_names']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
