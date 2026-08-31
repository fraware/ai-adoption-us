#!/usr/bin/env python3
"""Create a deterministic rights-safe source export from the canonical private repository.

The export includes only Git-tracked files and explicitly excludes private audit material.
It is a source/publication package, not a redistribution of the underlying RPS observations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
import zipfile
from pathlib import Path

PRIVATE_PREFIXES = ("data/audit/private/",)
FORBIDDEN_NAMES = ("rps_subgroup_5q_audit",)
FIXED_ZIP_TIME = (2026, 8, 30, 0, 0, 0)


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def tracked_files(root: Path) -> list[str]:
    return [line for line in git(root, "ls-files").splitlines() if line]


def excluded(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in PRIVATE_PREFIXES)


def zip_bytes(zip_path: Path, archive_root: str, root: Path, files: list[str], provenance: dict[str, object]) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for rel in sorted(files):
            if excluded(rel):
                continue
            data = (root / rel).read_bytes()
            info = zipfile.ZipInfo(f"{archive_root}/{rel}", FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            mode = 0o100755 if ((root / rel).stat().st_mode & 0o111) else 0o100644
            info.external_attr = mode << 16
            zf.writestr(info, data)

        payload = (json.dumps(provenance, indent=2, sort_keys=True) + "\n").encode()
        info = zipfile.ZipInfo(f"{archive_root}/RELEASE_PROVENANCE.json", FIXED_ZIP_TIME)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        zf.writestr(info, payload)


def validate_zip(zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        bad = [n for n in names if "/data/audit/private/" in n or any(token in n for token in FORBIDDEN_NAMES)]
        if bad:
            raise SystemExit(f"rights-safe export contains forbidden private paths: {bad[:5]}")
        if not any(n.endswith("data/derived/longitudinal/longitudinal_diagnostics.json") for n in names):
            raise SystemExit("rights-safe export is missing the derived longitudinal diagnostics")
        if not any(n.endswith("data/registry/rps_source_series_manifest.json") for n in names):
            raise SystemExit("rights-safe export is missing the canonical source registry")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--allow-dirty", action="store_true")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    status = git(root, "status", "--porcelain")
    if status and not args.allow_dirty:
        raise SystemExit("refusing to export from a dirty Git working tree")

    head = git(root, "rev-parse", "HEAD")
    files = tracked_files(root)
    included = [p for p in files if not excluded(p)]
    excluded_files = [p for p in files if excluded(p)]
    provenance = {
        "archive_role": "rights_safe_release_candidate",
        "checkpoint_date": "2026-08-30",
        "source_commit": head,
        "tracked_files_included": len(included),
        "tracked_private_files_excluded": len(excluded_files),
        "private_prefixes_excluded": list(PRIVATE_PREFIXES),
        "data_mode_for_public_render": "derived_only",
        "raw_rps_observations_included": False,
        "genuine_next_build_verified": False,
    }

    out = Path(args.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as _:  # keeps failure cleanup explicit
        zip_bytes(out, "genai-at-work", root, files, provenance)
    validate_zip(out)
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    print(json.dumps({"path": str(out), "sha256": digest, **provenance}, indent=2))


if __name__ == "__main__":
    main()
