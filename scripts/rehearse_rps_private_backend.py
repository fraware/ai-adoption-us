#!/usr/bin/env python3
"""Write and independently verify an RPS private-vintage backend challenge.

This command produces source-byte-free review evidence. A successful rehearsal
does not independently prove the truth of the reviewed backend configuration;
it cryptographically binds write/read/recovery evidence to that exact private
configuration-attestation file.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from genai_at_work.private_backend_config import PrivateBackendConfigurationError
from genai_at_work.private_vintage import PrivateVintageError
from genai_at_work.private_vintage_backend import (
    load_backend_challenge,
    verify_backend_challenge,
    write_backend_challenge,
)

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ROOT = ROOT / "data" / "audit" / "private"


def _assert_repository_private_boundary(path: Path, *, label: str) -> None:
    """Reject repository-local sensitive paths outside the ignored private boundary."""

    resolved = path.resolve()
    repository = ROOT.resolve()
    try:
        resolved.relative_to(repository)
    except ValueError:
        return
    try:
        resolved.relative_to(PRIVATE_ROOT.resolve())
    except ValueError as exc:
        raise SystemExit(
            f"Repository-local {label} may only exist under data/audit/private/. "
            "Use an external operator-controlled private path otherwise."
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
        help="Write one immutable private-vintage event and emit a bound challenge.",
    )
    write_parser.add_argument("--source-snapshot", type=Path, required=True)
    write_parser.add_argument("--backend-root", type=Path, required=True)
    write_parser.add_argument("--configuration-evidence", type=Path, required=True)
    write_parser.add_argument("--challenge-out", type=Path, required=True)
    write_parser.add_argument("--previous-snapshot", type=Path)

    verify_parser = subparsers.add_parser(
        "verify",
        help="Read back the challenged event against the same exact configuration evidence.",
    )
    verify_parser.add_argument("--challenge", type=Path, required=True)
    verify_parser.add_argument("--backend-root", type=Path, required=True)
    verify_parser.add_argument("--configuration-evidence", type=Path, required=True)
    verify_parser.add_argument("--evidence-out", type=Path, required=True)

    args = parser.parse_args()
    _assert_repository_private_boundary(args.backend_root, label="private-backend roots")
    _assert_repository_private_boundary(
        args.configuration_evidence,
        label="backend configuration evidence",
    )

    try:
        if args.command == "write":
            if not args.source_snapshot.is_file():
                raise SystemExit(
                    f"Source snapshot does not exist: {args.source_snapshot}"
                )
            if not args.configuration_evidence.is_file():
                raise SystemExit(
                    "Backend configuration evidence does not exist: "
                    f"{args.configuration_evidence}"
                )
            if (
                args.previous_snapshot is not None
                and not args.previous_snapshot.is_file()
            ):
                raise SystemExit(
                    f"Previous snapshot does not exist: {args.previous_snapshot}"
                )
            _assert_repository_private_boundary(
                args.source_snapshot,
                label="RPS source snapshots",
            )
            if args.previous_snapshot is not None:
                _assert_repository_private_boundary(
                    args.previous_snapshot,
                    label="RPS predecessor snapshots",
                )
            _assert_repository_private_boundary(
                args.challenge_out,
                label="backend review evidence",
            )
            challenge = write_backend_challenge(
                args.source_snapshot,
                args.backend_root,
                configuration_evidence_path=args.configuration_evidence,
                builder_commit=_builder_commit(),
                previous_snapshot_path=args.previous_snapshot,
            )
            _write_new_json(args.challenge_out, challenge)
            print(json.dumps(challenge, indent=2, sort_keys=True))
            return 0

        if not args.challenge.is_file():
            raise SystemExit(f"Backend challenge does not exist: {args.challenge}")
        if not args.configuration_evidence.is_file():
            raise SystemExit(
                "Backend configuration evidence does not exist: "
                f"{args.configuration_evidence}"
            )
        _assert_repository_private_boundary(
            args.challenge,
            label="backend review evidence",
        )
        _assert_repository_private_boundary(
            args.evidence_out,
            label="backend review evidence",
        )
        challenge = load_backend_challenge(args.challenge)
        evidence = verify_backend_challenge(
            challenge,
            args.backend_root,
            configuration_evidence_path=args.configuration_evidence,
            verification_builder_commit=_builder_commit(),
        )
        _write_new_json(args.evidence_out, evidence)
        print(json.dumps(evidence, indent=2, sort_keys=True))
        return 0
    except (PrivateVintageError, PrivateBackendConfigurationError) as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    raise SystemExit(main())
