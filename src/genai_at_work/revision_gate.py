"""Fail-closed governance helpers for private RPS fixture revisions."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from genai_at_work.longitudinal import AuditRecord, normalize_records, validate_private_fixture

DERIVED_ARTIFACTS = (
    "longitudinal_diagnostics.json",
    "validation_checks.json",
    "quarter_diagnostics.csv",
    "rank_stability.csv",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return value


def fixture_records(path: Path) -> list[AuditRecord]:
    payload = load_json(path)
    raw = payload.get("records")
    if not isinstance(raw, list):
        raise ValueError("Private fixture must contain a records list")
    records = normalize_records(raw)
    checks = validate_private_fixture(records)
    failed = sorted(key for key, passed in checks.items() if not passed)
    if failed:
        raise ValueError(f"Private fixture contract failed: {failed}")
    return records


def verify_current_fixture(path: Path, registry: Mapping[str, Any]) -> str:
    actual = sha256_file(path)
    expected = str(registry.get("fixture_sha256", ""))
    if not expected or actual != expected:
        raise ValueError(
            "Current private fixture does not match the frozen registry; "
            f"expected {expected or '<missing>'}, found {actual}"
        )
    fixture_records(path)
    return actual


def validate_source_vintage(source_vintage: Mapping[str, Any], registry: Mapping[str, Any]) -> None:
    required = (
        "source_vintage_id",
        "new_freeze_id",
        "retrieved_at",
        "checkpoint_date",
        "rights_status",
        "definitions_status",
    )
    missing = [key for key in required if not source_vintage.get(key)]
    if missing:
        raise ValueError(f"Source-vintage record missing required fields: {missing}")
    if source_vintage["new_freeze_id"] == registry.get("freeze_id"):
        raise ValueError("A revised source must receive a new freeze ID; silent freeze reuse is forbidden")
    contract = registry.get("contract")
    if not isinstance(contract, Mapping):
        raise ValueError("Freeze registry is missing contract metadata")
    expected_rights = str(contract.get("rights_status", ""))
    if source_vintage["rights_status"] != expected_rights:
        raise ValueError("Rights status changed; publication gate remains blocked pending a new rights decision")
    if source_vintage["definitions_status"] != "unchanged":
        raise ValueError("Construct or definition changes require a new measurement specification before publication")


def _record_key(record: AuditRecord) -> tuple[str, str, str, str]:
    return (record.entity_type, record.entity_id, record.metric_id, record.period)


def diff_fixture_records(current: Sequence[AuditRecord], candidate: Sequence[AuditRecord]) -> dict[str, Any]:
    old = {_record_key(record): record for record in current}
    new = {_record_key(record): record for record in candidate}
    changed: list[dict[str, Any]] = []
    for key in sorted(old.keys() | new.keys()):
        before = old.get(key)
        after = new.get(key)
        if before is None:
            changed.append({"key": list(key), "change": "added", "new_value": after.value if after else None})
        elif after is None:
            changed.append({"key": list(key), "change": "removed", "old_value": before.value})
        elif before.value != after.value or before.series_id != after.series_id:
            changed.append(
                {
                    "key": list(key),
                    "change": "modified",
                    "old_value": before.value,
                    "new_value": after.value,
                    "delta": after.value - before.value,
                    "old_series_id": before.series_id,
                    "new_series_id": after.series_id,
                }
            )
    return {"changed_cell_count": len(changed), "changes": changed}


def diff_artifacts(canonical_dir: Path, candidate_dir: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for name in DERIVED_ARTIFACTS:
        current = canonical_dir / name
        candidate = candidate_dir / name
        if not current.is_file() or not candidate.is_file():
            raise ValueError(f"Missing derived artifact required by revision gate: {name}")
        old_sha = sha256_file(current)
        new_sha = sha256_file(candidate)
        rows.append({"artifact": name, "old_sha256": old_sha, "new_sha256": new_sha, "changed": old_sha != new_sha})
    return {"changed_artifact_count": sum(bool(row["changed"]) for row in rows), "artifacts": rows}


def affected_claims(claim_inventory: Mapping[str, Any], artifacts_changed: bool) -> list[dict[str, Any]]:
    raw_claims = claim_inventory.get("claims")
    if not isinstance(raw_claims, list):
        raise ValueError("Claim inventory must contain a claims list")
    claims: list[dict[str, Any]] = []
    for raw in raw_claims:
        if not isinstance(raw, Mapping):
            raise ValueError("Each claim inventory entry must be an object")
        claims.append(
            {
                "claim_id": str(raw.get("claim_id", "")),
                "surface": str(raw.get("surface", "")),
                "review_status": "PENDING" if artifacts_changed else "NOT_AFFECTED",
            }
        )
    return claims


def stage_fingerprint(manifest: Mapping[str, Any]) -> str:
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(canonical).hexdigest()


def validate_review_attestation(
    attestation: Mapping[str, Any],
    *,
    stage_id: str,
    candidate_fixture_sha256: str,
    artifact_diff: Mapping[str, Any],
    affected: Sequence[Mapping[str, Any]],
) -> None:
    required_true = ("rights_reviewed", "definitions_reviewed", "all_affected_claims_reviewed")
    if attestation.get("stage_id") != stage_id:
        raise ValueError("Review attestation is not bound to this exact staged revision")
    if attestation.get("candidate_fixture_sha256") != candidate_fixture_sha256:
        raise ValueError("Review attestation candidate-fixture checksum mismatch")
    if not attestation.get("reviewer") or not attestation.get("reviewed_at"):
        raise ValueError("Review attestation requires reviewer and reviewed_at")
    if any(attestation.get(key) is not True for key in required_true):
        raise ValueError("Review attestation is incomplete")
    expected_hashes = {
        str(row["artifact"]): str(row["new_sha256"])
        for row in artifact_diff.get("artifacts", [])
        if isinstance(row, Mapping)
    }
    if attestation.get("artifact_sha256") != expected_hashes:
        raise ValueError("Review attestation artifact hashes do not match staged outputs")
    expected_claims = sorted(
        str(row["claim_id"])
        for row in affected
        if isinstance(row, Mapping) and row.get("review_status") == "PENDING"
    )
    reviewed_claims = attestation.get("reviewed_claim_ids")
    if not isinstance(reviewed_claims, list) or sorted(str(value) for value in reviewed_claims) != expected_claims:
        raise ValueError("Review attestation does not cover every affected public claim")
