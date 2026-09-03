#!/usr/bin/env python3
"""Write and independently verify an RPS private-vintage backend challenge.

This command produces rights-safe cryptographic evidence only. A successful
rehearsal does not by itself prove that the supplied backend is durable,
operator-controlled, or correctly access-controlled; those infrastructure facts
must be supported by the separately reviewed configuration evidence reference.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from genai_at_work.private_vintage import PrivateVintageError
from genai_at_work.private_vintage_backend import (
    load_backend_challenge,
    verify_backend_challenge,
    write_backend_challenge,
)

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ROOT = ROOT / "data" / "audit" / "private"


def _assert_private_backend_boundary(backend_root: Path) -> None:
    resolved = backend_root.resolve()
    repository = ROOT.resolve()
    try:
        resolved.relative_to(repository)
    except ValueError:
        return
    try:
        resolved.relative_to(PRIVATE_ROOT.resolve())
    except ValueError as exc:
        raise SystemExit(
            "Repository-local private-backend roots may only be written under "
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
                "Refusing to generate backend-conformance evidence from a dirty Git working tree."
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


def _write_new_json(path: Path, value: dict[str, Any]) -> None:
    if path.exists():
        raise SystemExit(f"Evidence output must be new and absent: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    write_parser = subparsers.add_parser(
        "write",
        help="Write one immutable private-vintage event and emit a rights-safe challenge.",
    )
    write_parser.add_argument("--source-snapshot", type=Path, required=True)
    write_parser.add_argument("--backend-root", type=Path, required=True)
    write_parser.add_argument("--backend-id", required=True)
    write_parser.add_argument("--configuration-evidence-ref", required=True)
    write_parser.add_argument("--challenge-out", type=Path, required=True)
    write_parser.add_argument("--previous-snapshot", type=Path)

    verify_parser = subparsers.add_parser(
        "verify",
        help="Read back the exact challenged event and emit rights-safe verification evidence.",
    )
    verify_parser.add_argument("--challenge", type=Path, required=True)
    verify_parser.add_argument("--backend-root", type=Path, required=True)
    verify_parser.add_argument("--evidence-out", type=Path, required=True)

    args = parser.parse_args()
    _assert_private_backend_boundary(args.backend_root)

    try:
        if args.command == "write":
            if not args.source_snapshot.is_file():
                raise SystemExit(
                    f"Source snapshot does not exist: {args.source_snapshot}"
                )
            if (
                args.previous_snapshot is not None
                and not args.previous_snapshot.is_file()
            ):
                raise SystemExit(
                    f"Previous snapshot does not exist: {args.previous_snapshot}"
                )
            challenge = write_backend_challenge(
                args.source_snapshot,
                args.backend_root,
                backend_id=args.backend_id,
                configuration_evidence_ref=args.configuration_evidence_ref,
                builder_commit=_builder_commit(),
                previous_snapshot_path=args.previous_snapshot,
            )
            _write_new_json(args.challenge_out, challenge)
            print(json.dumps(challenge, indent=2, sort_keys=True))
            return 0

        challenge = load_backend_challenge(args.challenge)
        evidence = verify_backend_challenge(challenge, args.backend_root)
        evidence["verification_builder_commit"] = _builder_commit()
        _write_new_json(args.evidence_out, evidence)
        print(json.dumps(evidence, indent=2, sort_keys=True))
        return 0
    except PrivateVintageError as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    raise SystemExit(main())
