#!/usr/bin/env python3
"""Archive an exact RPS source snapshot into an immutable private-vintage root."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from genai_at_work.private_vintage import PrivateVintageError, archive_rps_private_vintage

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ROOT = ROOT / "data" / "audit" / "private"


def _assert_private_archive_boundary(archive_root: Path) -> None:
    resolved = archive_root.resolve()
    repository = ROOT.resolve()
    try:
        resolved.relative_to(repository)
    except ValueError:
        return
    try:
        resolved.relative_to(PRIVATE_ROOT.resolve())
    except ValueError as exc:
        raise SystemExit(
            "Repository-local RPS private-vintage archives may only be written under "
            "data/audit/private/. Use an external operator-controlled private mount otherwise."
        ) from exc


def _builder_commit() -> str:
    try:
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        if status.strip():
            raise SystemExit(
                "Refusing to archive an RPS vintage from a dirty Git working tree. "
                "Commit or remove all changes first."
            )
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except subprocess.CalledProcessError as exc:
        raise SystemExit("Could not resolve a clean Git builder commit") from exc
    if len(commit) not in {40, 64}:
        raise SystemExit(f"Unexpected Git commit identity: {commit!r}")
    return commit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-snapshot",
        type=Path,
        required=True,
        help="Exact private rps_source_snapshot.json to archive.",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help=(
            "Operator-controlled private archive root. Repository-local roots must be under "
            "data/audit/private/."
        ),
    )
    parser.add_argument(
        "--previous-snapshot",
        type=Path,
        help=(
            "Optional prior archived/private RPS snapshot. When supplied, the archive retains "
            "the exact private revision/new-wave diff against it."
        ),
    )
    args = parser.parse_args()

    if not args.source_snapshot.is_file():
        raise SystemExit(f"Source snapshot does not exist: {args.source_snapshot}")
    if args.previous_snapshot is not None and not args.previous_snapshot.is_file():
        raise SystemExit(f"Previous snapshot does not exist: {args.previous_snapshot}")
    _assert_private_archive_boundary(args.archive_root)

    try:
        package_dir, manifest = archive_rps_private_vintage(
            args.source_snapshot,
            args.archive_root,
            builder_commit=_builder_commit(),
            previous_snapshot_path=args.previous_snapshot,
        )
    except PrivateVintageError as exc:
        raise SystemExit(str(exc)) from exc

    comparison = manifest["comparison"]
    summary = {
        "archive_event_id": manifest["archive_event_id"],
        "package_dir": str(package_dir.resolve()),
        "source_id": manifest["source_id"],
        "source_content_sha256": manifest["source_content_sha256"],
        "source_snapshot_sha256": manifest["source_snapshot_sha256"],
        "retrieved_at": manifest["retrieved_at"],
        "revision_status": comparison["revision_status"],
        "previous_snapshot_sha256": comparison["previous_snapshot_sha256"],
        "builder_commit": manifest["builder_commit"],
        "storage_scope": manifest["rights"]["storage_scope"],
        "public_archive": manifest["public_archive"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
