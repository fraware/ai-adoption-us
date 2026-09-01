#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path
from typing import Any

from genai_at_work.release_engine import (
    canonical_digest,
    candidate_gate_failures,
    diff_releases,
    gate_status,
    load_json_object,
    review_package,
    sanitized_public_manifest,
    sha256_file,
    stage_fingerprint,
    validate_release_manifest,
    validate_review_attestation,
)

ROOT = Path(__file__).parents[1]


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(temp, path)


def _registry_current(registry: dict[str, Any]) -> str | None:
    value = registry.get("current_release_id")
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise SystemExit("Release registry current_release_id must be null or a non-empty string")
    return value


def _load_previous(registry: dict[str, Any], releases_root: Path) -> dict[str, Any] | None:
    current = _registry_current(registry)
    if current is None:
        return None
    manifest_path = releases_root / current / "release_manifest.json"
    if not manifest_path.is_file():
        raise SystemExit(f"Registered current release manifest is missing: {manifest_path}")
    previous = load_json_object(manifest_path)
    expected = registry.get("current_release_manifest_sha256")
    actual = sha256_file(manifest_path)
    if not isinstance(expected, str) or actual != expected:
        raise SystemExit("Registered current release manifest checksum mismatch")
    if previous.get("release_id") != current:
        raise SystemExit("Registered current release ID does not match its manifest")
    return previous


def _validate_supersession(candidate: dict[str, Any], registry: dict[str, Any]) -> None:
    current = _registry_current(registry)
    supersedes = candidate.get("supersedes_release_id")
    if current is None:
        if supersedes is not None:
            raise SystemExit("First promoted release must use supersedes_release_id=null")
    elif supersedes != current:
        raise SystemExit(f"Candidate must explicitly supersede current release {current!r}")
    releases = registry.get("releases", [])
    if not isinstance(releases, list):
        raise SystemExit("Release registry releases must be a list")
    known_ids = {str(row.get("release_id")) for row in releases if isinstance(row, dict)}
    release_id = str(candidate.get("release_id", ""))
    if release_id == current or release_id in known_ids:
        raise SystemExit(f"Release ID is already frozen and cannot be reused: {release_id}")


def _has_changes(diff: dict[str, Any]) -> bool:
    return any(
        bool(diff.get(key))
        for key in ("source_changes", "artifact_changes", "diagnostic_changes", "claim_changes")
    )


def _stage_payload(
    *,
    registry: dict[str, Any],
    candidate_manifest_path: Path,
    candidate_manifest_sha256: str,
    candidate: dict[str, Any],
    release_diff: dict[str, Any],
    status: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": 1,
        "registry_current_release_id": _registry_current(registry),
        "registry_current_manifest_sha256": registry.get("current_release_manifest_sha256"),
        "candidate_release_id": candidate["release_id"],
        "candidate_manifest_path": str(candidate_manifest_path.resolve()),
        "candidate_manifest_sha256": candidate_manifest_sha256,
        "candidate_manifest_digest": canonical_digest(candidate),
        "release_diff_digest": canonical_digest(release_diff),
        "gate_status": status,
    }
    payload["stage_id"] = stage_fingerprint(payload)
    return payload


def stage(args: argparse.Namespace) -> int:
    if args.staging_dir.exists():
        raise SystemExit(f"Staging directory already exists; use a new immutable path: {args.staging_dir}")
    registry = load_json_object(args.registry)
    candidate = load_json_object(args.candidate_manifest)
    validate_release_manifest(candidate, args.candidate_root)
    _validate_supersession(candidate, registry)
    previous = _load_previous(registry, args.releases_root)
    release_diff = diff_releases(previous, candidate)
    failures = candidate_gate_failures(candidate, release_diff)
    status = gate_status(failures, _has_changes(release_diff))
    candidate_sha = sha256_file(args.candidate_manifest)
    stage_manifest = _stage_payload(
        registry=registry,
        candidate_manifest_path=args.candidate_manifest,
        candidate_manifest_sha256=candidate_sha,
        candidate=candidate,
        release_diff=release_diff,
        status=status,
    )
    args.staging_dir.mkdir(parents=True)
    _write_json(args.staging_dir / "stage_manifest.json", stage_manifest)
    _write_json(args.staging_dir / "release_diff.json", release_diff)
    _write_json(args.staging_dir / "review_package.json", review_package(candidate, release_diff))
    _write_json(
        args.staging_dir / "publication_gate.json",
        {
            "stage_id": stage_manifest["stage_id"],
            "status": status,
            "failures": failures,
            "promotion_requires_review": status == "BLOCKED_REVIEW_REQUIRED",
            "source_input_bytes_publishable_by_this_engine": False,
        },
    )
    print(json.dumps({"stage_id": stage_manifest["stage_id"], "status": status}, indent=2))
    return 0


def _recompute_stage(
    *,
    args: argparse.Namespace,
    registry: dict[str, Any],
    candidate: dict[str, Any],
    release_diff: dict[str, Any],
    status: str,
) -> dict[str, Any]:
    return _stage_payload(
        registry=registry,
        candidate_manifest_path=args.candidate_manifest,
        candidate_manifest_sha256=sha256_file(args.candidate_manifest),
        candidate=candidate,
        release_diff=release_diff,
        status=status,
    )


def _copy_public_artifacts(candidate: dict[str, Any], candidate_root: Path, release_dir: Path) -> dict[str, Any]:
    public = sanitized_public_manifest(candidate)
    public_artifacts = public.get("artifacts")
    candidate_artifacts = candidate.get("artifacts")
    if not isinstance(public_artifacts, list) or not isinstance(candidate_artifacts, list):
        raise SystemExit("Invalid artifact manifest during promotion")
    for public_artifact, candidate_artifact in zip(public_artifacts, candidate_artifacts, strict=True):
        if not isinstance(public_artifact, dict) or not isinstance(candidate_artifact, dict):
            raise SystemExit("Invalid artifact entry during promotion")
        rel = Path(str(candidate_artifact["path"]))
        source = candidate_root / rel
        destination_rel = Path("artifacts") / rel
        destination = release_dir / destination_rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        if sha256_file(destination) != str(candidate_artifact["sha256"]):
            raise SystemExit(f"Copied release artifact checksum mismatch: {candidate_artifact['artifact_id']}")
        public_artifact["path"] = destination_rel.as_posix()
    return public


def promote(args: argparse.Namespace) -> int:
    registry = load_json_object(args.registry)
    candidate = load_json_object(args.candidate_manifest)
    validate_release_manifest(candidate, args.candidate_root)
    _validate_supersession(candidate, registry)
    previous = _load_previous(registry, args.releases_root)
    release_diff = diff_releases(previous, candidate)
    failures = candidate_gate_failures(candidate, release_diff)
    status = gate_status(failures, _has_changes(release_diff))
    if status != "BLOCKED_REVIEW_REQUIRED":
        raise SystemExit(f"Promotion requires a valid changed release awaiting review; found {status}")

    staged_manifest = load_json_object(args.staging_dir / "stage_manifest.json")
    staged_diff = load_json_object(args.staging_dir / "release_diff.json")
    staged_gate = load_json_object(args.staging_dir / "publication_gate.json")
    if staged_gate.get("status") != "BLOCKED_REVIEW_REQUIRED":
        raise SystemExit("Staged publication gate is not review-promotable")
    recomputed_stage = _recompute_stage(
        args=args,
        registry=registry,
        candidate=candidate,
        release_diff=release_diff,
        status=status,
    )
    if recomputed_stage != staged_manifest:
        raise SystemExit("Release candidate, registry, or staged fingerprint changed after staging")
    if release_diff != staged_diff:
        raise SystemExit("Release diff changed after staging")

    candidate_manifest_sha = sha256_file(args.candidate_manifest)
    attestation = load_json_object(args.attestation)
    validate_review_attestation(
        attestation,
        stage_id=str(staged_manifest["stage_id"]),
        candidate_manifest_sha256=candidate_manifest_sha,
        candidate=candidate,
        release_diff=release_diff,
    )

    release_id = str(candidate["release_id"])
    target = args.releases_root / release_id
    if target.exists():
        raise SystemExit(f"Immutable release directory already exists: {target}")
    temporary = args.releases_root / f".{release_id}.tmp"
    if temporary.exists():
        raise SystemExit(f"Temporary release directory already exists: {temporary}")
    temporary.mkdir(parents=True)
    try:
        public_manifest = _copy_public_artifacts(candidate, args.candidate_root, temporary)
        public_manifest["release_status"] = "PROMOTED_AFTER_EXPLICIT_REVIEW"
        public_manifest["promoted_at"] = attestation["reviewed_at"]
        public_manifest["reviewer"] = attestation["reviewer"]
        _write_json(temporary / "release_manifest.json", public_manifest)
        _write_json(temporary / "release_diff.json", release_diff)
        public_review = {
            "stage_id": staged_manifest["stage_id"],
            "release_id": release_id,
            "reviewer": attestation["reviewer"],
            "reviewed_at": attestation["reviewed_at"],
            "scientific_reviewed": True,
            "editorial_reviewed": True,
            "source_rights_reviewed": True,
            "reviewed_source_ids": attestation["reviewed_source_ids"],
            "reviewed_diagnostic_ids": attestation["reviewed_diagnostic_ids"],
            "reviewed_claim_ids": attestation["reviewed_claim_ids"],
            "source_input_bytes_included": False,
        }
        _write_json(temporary / "review_record.json", public_review)
        os.replace(temporary, target)
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise

    public_manifest_path = target / "release_manifest.json"
    public_manifest_sha = sha256_file(public_manifest_path)
    releases = registry.get("releases", [])
    if not isinstance(releases, list):
        raise SystemExit("Release registry releases must be a list")
    updated = dict(registry)
    updated["current_release_id"] = release_id
    updated["current_release_manifest_sha256"] = public_manifest_sha
    updated["releases"] = [
        *releases,
        {
            "release_id": release_id,
            "manifest_sha256": public_manifest_sha,
            "promoted_at": attestation["reviewed_at"],
            "supersedes_release_id": candidate.get("supersedes_release_id"),
        },
    ]
    _write_json(args.registry, updated)
    result = {
        "release_id": release_id,
        "release_manifest_sha256": public_manifest_sha,
        "release_directory": str(target),
        "source_input_bytes_included": False,
        "status": "PROMOTED_AFTER_EXPLICIT_REVIEW",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Stage and promote immutable observatory releases")
    sub = p.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--candidate-manifest", type=Path, required=True)
    common.add_argument("--candidate-root", type=Path, required=True)
    common.add_argument(
        "--registry",
        type=Path,
        default=ROOT / "data/registry/observatory_release_registry.json",
    )
    common.add_argument("--releases-root", type=Path, default=ROOT / "data/releases")
    common.add_argument("--staging-dir", type=Path, required=True)
    sub.add_parser("stage", parents=[common])
    promote_parser = sub.add_parser("promote", parents=[common])
    promote_parser.add_argument("--attestation", type=Path, required=True)
    return p


def main() -> int:
    args = parser().parse_args()
    return stage(args) if args.command == "stage" else promote(args)


if __name__ == "__main__":
    raise SystemExit(main())
