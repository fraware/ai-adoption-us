#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from genai_at_work.revision_gate import (
    DERIVED_ARTIFACTS,
    affected_claims,
    diff_artifacts,
    diff_fixture_records,
    fixture_records,
    load_json,
    sha256_file,
    stage_fingerprint,
    validate_review_attestation,
    validate_source_vintage,
    verify_current_fixture,
)

ROOT = Path(__file__).parents[1]


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _archive_current(
    current_fixture: Path,
    canonical_derived: Path,
    registry: dict[str, Any],
    archive_root: Path,
) -> Path:
    freeze_id = str(registry["freeze_id"])
    target = archive_root / freeze_id
    target.mkdir(parents=True, exist_ok=True)
    fixture_target = target / "rps_subgroup_5q_audit.json"
    if fixture_target.exists():
        if sha256_file(fixture_target) != str(registry["fixture_sha256"]):
            raise SystemExit("Private archive already contains a different fixture under the frozen ID")
    else:
        shutil.copy2(current_fixture, fixture_target)
    derived_target = target / "derived"
    derived_target.mkdir(exist_ok=True)
    for name in DERIVED_ARTIFACTS:
        source = canonical_derived / name
        target_file = derived_target / name
        if not source.is_file():
            raise SystemExit(f"Current canonical derived artifact is missing: {name}")
        if target_file.exists() and sha256_file(target_file) != sha256_file(source):
            raise SystemExit(f"Private archive already contains a conflicting derived artifact: {name}")
        if not target_file.exists():
            shutil.copy2(source, target_file)
    _write_json(target / "freeze_registry_snapshot.json", registry)
    return target


def _base_private_env(candidate_fixture: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["RPS_PRIVATE_FIXTURE"] = str(candidate_fixture)
    env["RPS_REVISION_CANDIDATE"] = "1"
    return env


def _run_builder(candidate_fixture: Path, output_dir: Path, checkpoint_date: str) -> None:
    env = _base_private_env(candidate_fixture)
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "build_longitudinal.py"),
            "--fixture",
            str(candidate_fixture),
            "--output-dir",
            str(output_dir),
            "--checkpoint-date",
            checkpoint_date,
        ],
        cwd=ROOT,
        env=env,
        check=True,
    )


def _run_candidate_private_suite(candidate_fixture: Path, staging_dir: Path) -> dict[str, Any]:
    env = _base_private_env(candidate_fixture)
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/test_longitudinal.py"],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    result: dict[str, Any] = {
        "returncode": completed.returncode,
        "all_applicable_tests_passed": completed.returncode == 0,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "candidate_fixture_sha256": sha256_file(candidate_fixture),
        "scope_note": (
            "The candidate runs the fixture-present longitudinal analytical suite. "
            "Only the same-freeze byte-for-byte canonical reproduction assertion is skipped, "
            "because a separately staged revision is expected to be compared through artifact_diff.json instead."
        ),
    }
    _write_json(staging_dir / "private_suite.private.json", result)
    return result


def stage(args: argparse.Namespace) -> int:
    registry = load_json(args.registry)
    source_vintage = load_json(args.source_vintage)
    claim_inventory = load_json(args.claim_inventory)
    validate_source_vintage(source_vintage, registry)
    current_fixture = args.current_fixture.resolve()
    candidate_fixture = args.candidate_fixture.resolve()
    if current_fixture == candidate_fixture:
        raise SystemExit("Candidate fixture must be staged at a separate path; never overwrite the current freeze first")
    current_sha = verify_current_fixture(current_fixture, registry)
    current_records = fixture_records(current_fixture)
    candidate_records = fixture_records(candidate_fixture)
    candidate_sha = sha256_file(candidate_fixture)
    archive_dir = _archive_current(current_fixture, args.canonical_derived, registry, args.private_archive_root)
    if args.staging_dir.exists():
        raise SystemExit(f"Staging directory already exists; use a new immutable staging path: {args.staging_dir}")
    derived_dir = args.staging_dir / "derived"
    derived_dir.mkdir(parents=True)
    private_suite = _run_candidate_private_suite(candidate_fixture, args.staging_dir)
    _run_builder(candidate_fixture, derived_dir, str(source_vintage["checkpoint_date"]))
    validation = load_json(derived_dir / "validation_checks.json")
    fixture_diff = diff_fixture_records(current_records, candidate_records)
    artifact_diff = diff_artifacts(args.canonical_derived, derived_dir)
    has_artifact_changes = int(artifact_diff["changed_artifact_count"]) > 0
    claims = affected_claims(claim_inventory, has_artifact_changes)
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "current_freeze_id": registry["freeze_id"],
        "current_fixture_sha256": current_sha,
        "candidate_fixture_sha256": candidate_sha,
        "source_vintage": source_vintage,
        "private_archive_dir": str(archive_dir),
        "fixture_changed_cell_count": fixture_diff["changed_cell_count"],
        "changed_artifact_count": artifact_diff["changed_artifact_count"],
        "private_suite_all_applicable_tests_passed": private_suite["all_applicable_tests_passed"] is True,
        "publication_validation_all_passed": validation.get("all_passed") is True,
    }
    stage_id = stage_fingerprint(manifest)
    manifest["stage_id"] = stage_id
    if private_suite["all_applicable_tests_passed"] is not True:
        status = "BLOCKED_PRIVATE_SUITE_FAILED"
    elif validation.get("all_passed") is not True:
        status = "BLOCKED_DIAGNOSTICS_FAILED"
    elif candidate_sha == current_sha and not has_artifact_changes:
        status = "REPRODUCED_CURRENT_FREEZE"
    else:
        status = "BLOCKED_REVIEW_REQUIRED"
    _write_json(args.staging_dir / "stage_manifest.json", manifest)
    _write_json(args.staging_dir / "fixture_diff.private.json", fixture_diff)
    _write_json(args.staging_dir / "artifact_diff.json", artifact_diff)
    _write_json(args.staging_dir / "claim_review.json", {"claims": claims})
    _write_json(
        args.staging_dir / "publication_gate.json",
        {
            "stage_id": stage_id,
            "status": status,
            "promotion_allowed_without_review": status == "REPRODUCED_CURRENT_FREEZE",
            "note": (
                "Private suite output and cell-level diff remain in staging and must not be committed "
                "to the public repository."
            ),
        },
    )
    print(json.dumps({"stage_id": stage_id, "status": status}, indent=2))
    return 0


def promote(args: argparse.Namespace) -> int:
    registry = load_json(args.registry)
    manifest = load_json(args.staging_dir / "stage_manifest.json")
    artifact_diff = load_json(args.staging_dir / "artifact_diff.json")
    claim_review = load_json(args.staging_dir / "claim_review.json")
    gate = load_json(args.staging_dir / "publication_gate.json")
    if gate.get("status") != "BLOCKED_REVIEW_REQUIRED":
        raise SystemExit(f"Promotion requires a changed, diagnostically valid staged revision; found {gate.get('status')}")
    if manifest.get("private_suite_all_applicable_tests_passed") is not True:
        raise SystemExit("Staged candidate private suite did not pass; promotion remains blocked")
    if manifest.get("publication_validation_all_passed") is not True:
        raise SystemExit("Staged candidate publication diagnostics did not pass; promotion remains blocked")
    current_sha = verify_current_fixture(args.current_fixture, registry)
    if current_sha != manifest.get("current_fixture_sha256"):
        raise SystemExit("Current private fixture changed after staging; restage against the new baseline")
    candidate_sha = sha256_file(args.candidate_fixture)
    if candidate_sha != manifest.get("candidate_fixture_sha256"):
        raise SystemExit("Candidate private fixture changed after staging")
    current_stage_payload = {key: value for key, value in manifest.items() if key != "stage_id"}
    stage_id = stage_fingerprint(current_stage_payload)
    if stage_id != manifest.get("stage_id"):
        raise SystemExit("Staged revision manifest fingerprint mismatch")
    staged_artifact_diff = diff_artifacts(args.canonical_derived, args.staging_dir / "derived")
    if staged_artifact_diff != artifact_diff:
        raise SystemExit("Staged derived artifacts changed after review package creation")
    claims = claim_review.get("claims")
    if not isinstance(claims, list):
        raise SystemExit("Invalid claim-review package")
    attestation = load_json(args.attestation)
    validate_review_attestation(
        attestation,
        stage_id=stage_id,
        candidate_fixture_sha256=candidate_sha,
        artifact_diff=artifact_diff,
        affected=claims,
    )
    source_vintage = manifest.get("source_vintage")
    if not isinstance(source_vintage, dict) or not source_vintage.get("new_freeze_id"):
        raise SystemExit("Source-vintage record must provide new_freeze_id before promotion")
    _archive_current(args.current_fixture, args.canonical_derived, registry, args.private_archive_root)
    shutil.copy2(args.candidate_fixture, args.current_fixture)
    for name in DERIVED_ARTIFACTS:
        shutil.copy2(args.staging_dir / "derived" / name, args.canonical_derived / name)
    new_registry = dict(registry)
    new_registry.update(
        {
            "previous_freeze_id": registry["freeze_id"],
            "previous_fixture_sha256": registry["fixture_sha256"],
            "freeze_id": source_vintage["new_freeze_id"],
            "checkpoint_date": source_vintage["checkpoint_date"],
            "fixture_sha256": candidate_sha,
            "source_vintage_id": source_vintage["source_vintage_id"],
        }
    )
    _write_json(args.registry, new_registry)
    public_record = {
        "schema_version": 1,
        "stage_id": stage_id,
        "previous_freeze_id": registry["freeze_id"],
        "new_freeze_id": source_vintage["new_freeze_id"],
        "previous_fixture_sha256": registry["fixture_sha256"],
        "new_fixture_sha256": candidate_sha,
        "changed_cell_count": manifest["fixture_changed_cell_count"],
        "changed_artifact_count": manifest["changed_artifact_count"],
        "private_suite_all_applicable_tests_passed": True,
        "publication_validation_all_passed": True,
        "reviewed_at": attestation["reviewed_at"],
        "reviewer": attestation["reviewer"],
        "source_vintage_id": source_vintage["source_vintage_id"],
        "rights_status": source_vintage["rights_status"],
        "definitions_status": source_vintage["definitions_status"],
        "status": "PROMOTED_AFTER_EXPLICIT_REVIEW",
        "privacy_note": "Raw fixture, private suite output, and cell-level revision diff remain private.",
    }
    _write_json(args.validation_record, public_record)
    print(json.dumps(public_record, indent=2, sort_keys=True))
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Stage or promote a private RPS fixture revision without silent overwrite")
    sub = p.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--current-fixture", type=Path, default=ROOT / "data/audit/private/rps_subgroup_5q_audit.json")
    common.add_argument("--registry", type=Path, default=ROOT / "data/registry/private_fixture_freeze.json")
    common.add_argument("--claim-inventory", type=Path, default=ROOT / "data/registry/longitudinal_claim_inventory.json")
    common.add_argument("--canonical-derived", type=Path, default=ROOT / "data/derived/longitudinal")
    common.add_argument("--private-archive-root", type=Path, required=True)
    common.add_argument("--candidate-fixture", type=Path, required=True)
    stage_parser = sub.add_parser("stage", parents=[common])
    stage_parser.add_argument("--source-vintage", type=Path, required=True)
    stage_parser.add_argument("--staging-dir", type=Path, required=True)
    promote_parser = sub.add_parser("promote", parents=[common])
    promote_parser.add_argument("--staging-dir", type=Path, required=True)
    promote_parser.add_argument("--attestation", type=Path, required=True)
    promote_parser.add_argument("--validation-record", type=Path, required=True)
    return p


def main() -> int:
    args = parser().parse_args()
    return stage(args) if args.command == "stage" else promote(args)


if __name__ == "__main__":
    raise SystemExit(main())
