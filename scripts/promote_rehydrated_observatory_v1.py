#!/usr/bin/env python3
"""Promote only an exactly rehydrated, explicitly reviewed Observatory candidate.

This is the trusted promotion operator for Observatory v1. It validates the
rights-safe deterministic rehydration identity, requires the human attestation
to bind that identity digest, delegates the existing exact-stage/CI promotion
checks to ``observatory_release.py``, and atomically finalizes the immutable
release with a rehydration sidecar and review-record trace.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import observatory_release
from genai_at_work.release_engine import (
    canonical_digest,
    load_json_object,
    sha256_file,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "data" / "registry" / "observatory_release_registry.json"
DEFAULT_RELEASES_ROOT = ROOT / "data" / "releases"


class RehydratedPromotionError(RuntimeError):
    """Raised when exact rehydration is not bound into the promotion request."""


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _artifact_hashes(candidate: dict[str, Any]) -> dict[str, str]:
    artifacts = candidate.get("artifacts")
    if not isinstance(artifacts, list):
        raise RehydratedPromotionError("Candidate artifacts must be a list")
    result: dict[str, str] = {}
    for row in artifacts:
        if not isinstance(row, dict):
            raise RehydratedPromotionError("Candidate contains an invalid artifact row")
        artifact_id = row.get("artifact_id")
        digest = row.get("sha256")
        if not isinstance(artifact_id, str) or not isinstance(digest, str):
            raise RehydratedPromotionError("Candidate artifact identity is incomplete")
        result[artifact_id] = digest
    return result


def _source_vintages(candidate: dict[str, Any]) -> dict[str, str]:
    sources = candidate.get("sources")
    if not isinstance(sources, list):
        raise RehydratedPromotionError("Candidate sources must be a list")
    result: dict[str, str] = {}
    for row in sources:
        if not isinstance(row, dict):
            raise RehydratedPromotionError("Candidate contains an invalid source row")
        source_id = row.get("source_id")
        vintage = row.get("source_vintage_id")
        if not isinstance(source_id, str) or not isinstance(vintage, str):
            raise RehydratedPromotionError("Candidate source identity is incomplete")
        result[source_id] = vintage
    return result


def validate_rehydration_identity(
    identity: dict[str, Any],
    *,
    candidate: dict[str, Any],
    candidate_manifest: Path,
    staged_manifest: dict[str, Any],
) -> None:
    """Require a deterministic identity for this exact candidate and stage."""

    expected = {
        "schema_version": 1,
        "status": "REHYDRATED_EXACT_CANDIDATE",
        "release_id": candidate.get("release_id"),
        "candidate_commit": candidate.get("build", {}).get("builder_commit"),
        "candidate_manifest_sha256": sha256_file(candidate_manifest),
        "candidate_manifest_digest": canonical_digest(candidate),
        "stage_id": staged_manifest.get("stage_id"),
        "source_vintage_ids": _source_vintages(candidate),
        "artifact_sha256": _artifact_hashes(candidate),
        "source_input_bytes_included": False,
    }
    if identity != expected:
        raise RehydratedPromotionError(
            "Rehydration identity does not exactly match the candidate, source vintages, artifacts, and stage"
        )


def _rollback(
    *,
    registry: Path,
    registry_before: bytes,
    release_target: Path,
) -> None:
    if release_target.exists():
        shutil.rmtree(release_target)
    registry.write_bytes(registry_before)


def promote(args: argparse.Namespace) -> int:
    candidate = load_json_object(args.candidate_manifest)
    staged_manifest = load_json_object(args.staging_dir / "stage_manifest.json")
    identity = load_json_object(args.rehydration_identity)
    attestation = load_json_object(args.attestation)

    validate_rehydration_identity(
        identity,
        candidate=candidate,
        candidate_manifest=args.candidate_manifest,
        staged_manifest=staged_manifest,
    )
    identity_sha = sha256_file(args.rehydration_identity)
    if attestation.get("rehydration_identity_sha256") != identity_sha:
        raise RehydratedPromotionError(
            "Human review attestation is not bound to this exact rehydration identity"
        )

    release_id = candidate.get("release_id")
    if not isinstance(release_id, str) or not release_id:
        raise RehydratedPromotionError("Candidate release_id is invalid")
    release_target = args.releases_root / release_id
    registry_before = args.registry.read_bytes()

    delegated = argparse.Namespace(
        candidate_manifest=args.candidate_manifest,
        candidate_root=args.candidate_root,
        registry=args.registry,
        releases_root=args.releases_root,
        staging_dir=args.staging_dir,
        attestation=args.attestation,
    )
    observatory_release.promote(delegated)

    try:
        if not release_target.is_dir():
            raise RehydratedPromotionError("Delegated promotion did not create the release directory")
        destination_identity = release_target / "rehydration_identity.json"
        if destination_identity.exists():
            raise RehydratedPromotionError("Release already contains a rehydration identity sidecar")
        shutil.copyfile(args.rehydration_identity, destination_identity)
        if sha256_file(destination_identity) != identity_sha:
            raise RehydratedPromotionError("Copied rehydration identity checksum mismatch")

        review_record_path = release_target / "review_record.json"
        review_record = load_json_object(review_record_path)
        review_record["rehydration_status"] = "REHYDRATED_EXACT_CANDIDATE"
        review_record["rehydration_identity_sha256"] = identity_sha
        review_record["source_rehydrated_before_promotion"] = True
        _write_json(review_record_path, review_record)

        registry = load_json_object(args.registry)
        releases = registry.get("releases")
        if not isinstance(releases, list) or not releases:
            raise RehydratedPromotionError("Release registry did not record the promotion")
        matches = [
            row
            for row in releases
            if isinstance(row, dict) and row.get("release_id") == release_id
        ]
        if len(matches) != 1:
            raise RehydratedPromotionError("Release registry must contain exactly one promoted release row")
        matches[0]["rehydration_status"] = "REHYDRATED_EXACT_CANDIDATE"
        matches[0]["rehydration_identity_sha256"] = identity_sha
        _write_json(args.registry, registry)
    except Exception:
        _rollback(
            registry=args.registry,
            registry_before=registry_before,
            release_target=release_target,
        )
        raise

    print(
        json.dumps(
            {
                "release_id": release_id,
                "rehydration_identity_sha256": identity_sha,
                "status": "PROMOTED_AFTER_EXACT_REHYDRATION_AND_EXPLICIT_REVIEW",
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-manifest", type=Path, required=True)
    parser.add_argument("--candidate-root", type=Path, required=True)
    parser.add_argument("--staging-dir", type=Path, required=True)
    parser.add_argument("--attestation", type=Path, required=True)
    parser.add_argument("--rehydration-identity", type=Path, required=True)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--releases-root", type=Path, default=DEFAULT_RELEASES_ROOT)
    return parser


def main() -> int:
    args = parser().parse_args()
    try:
        return promote(args)
    except (RehydratedPromotionError, ValueError) as exc:
        raise SystemExit(f"Rehydrated Observatory promotion blocked: {exc}") from exc


if __name__ == "__main__":
    raise SystemExit(main())
