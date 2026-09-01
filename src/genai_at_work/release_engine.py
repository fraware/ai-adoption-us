"""Fail-closed governance for immutable, versioned observatory releases.

Source-specific pipelines prepare candidate packages. This module verifies their
source bytes, deterministic build manifest, derived artifacts, diagnostics, and
public claims; compares them with the current frozen release; and validates the
review evidence required before promotion. Source input bytes are never copied
into the public release archive by this system.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

ALLOWED_DATA_MODES = {"derived_only", "rights_cleared_direct"}
ALLOWED_RELEASE_TYPES = {"baseline", "new_wave", "revision", "mixed"}
ALLOWED_REVISION_STATUS = {"unchanged", "new_wave", "revision", "mixed"}
ALLOWED_STORAGE_SCOPES = {"transient", "private", "public"}
ALLOWED_PUBLICATION_SCOPES = {"none", "derived_only", "source_and_derived"}
ALLOWED_REDISTRIBUTION_SCOPES = {"none", "derived_only", "source_and_derived"}
REQUIRED_DIAGNOSTIC_CLASSES = {
    "stability",
    "influence",
    "regression_contract",
    "suppression_coverage",
}


def load_json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def stage_fingerprint(value: Mapping[str, Any]) -> str:
    return canonical_digest(value)


def _string(mapping: Mapping[str, Any], key: str, context: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}.{key} must be a non-empty string")
    return value


def _mapping(mapping: Mapping[str, Any], key: str, context: str) -> Mapping[str, Any]:
    value = mapping.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"{context}.{key} must be an object")
    return value


def _rows(mapping: Mapping[str, Any], key: str, context: str) -> list[Mapping[str, Any]]:
    value = mapping.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(row, Mapping) for row in value):
        raise ValueError(f"{context}.{key} must be a non-empty list of objects")
    return list(value)


def _strings(mapping: Mapping[str, Any], key: str, context: str) -> list[str]:
    value = mapping.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{context}.{key} must be a non-empty list of strings")
    if len(set(value)) != len(value):
        raise ValueError(f"{context}.{key} contains duplicates")
    return list(value)


def _digest(value: object, context: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{context} must be a 64-character SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{context} must be hexadecimal") from exc
    return value.lower()


def _safe_relative(root: Path, relative: str, *, required_prefix: str) -> Path:
    posix = PurePosixPath(relative)
    if posix.is_absolute() or ".." in posix.parts or not posix.parts:
        raise ValueError(f"Unsafe candidate path: {relative!r}")
    if posix.parts[0] != required_prefix:
        raise ValueError(f"Candidate path {relative!r} must live under {required_prefix}/")
    root_resolved = root.resolve()
    resolved = (root / Path(*posix.parts)).resolve()
    if root_resolved not in resolved.parents:
        raise ValueError(f"Candidate path escapes package root: {relative!r}")
    return resolved


def _by_id(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, Mapping[str, Any]]:
    return {str(row[key]): row for row in rows}


def _stable_digest(mapping: Mapping[str, Any], keys: Sequence[str]) -> str:
    return canonical_digest({key: mapping.get(key) for key in keys})


def _source_objects(source: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    objects = source.get("objects")
    if not isinstance(objects, list):
        return {}
    return {
        str(row["object_id"]): row
        for row in objects
        if isinstance(row, Mapping) and isinstance(row.get("object_id"), str)
    }


def validate_release_manifest(manifest: Mapping[str, Any], candidate_root: Path) -> None:
    """Validate schema, package namespaces, bytes, and build provenance."""
    if manifest.get("schema_version") != 1:
        raise ValueError("release.schema_version must equal 1")
    _string(manifest, "release_id", "release")
    release_type = _string(manifest, "release_type", "release")
    if release_type not in ALLOWED_RELEASE_TYPES:
        raise ValueError(f"Unsupported release_type: {release_type}")
    data_mode = _string(manifest, "data_mode", "release")
    if data_mode not in ALLOWED_DATA_MODES:
        raise ValueError(f"Unsupported data_mode: {data_mode}")
    _string(manifest, "created_at", "release")
    supersedes = manifest.get("supersedes_release_id")
    if supersedes is not None and (not isinstance(supersedes, str) or not supersedes):
        raise ValueError("release.supersedes_release_id must be null or a non-empty string")

    source_ids: set[str] = set()
    input_hashes: dict[str, str] = {}
    for index, source in enumerate(_rows(manifest, "sources", "release")):
        context = f"sources[{index}]"
        source_id = _string(source, "source_id", context)
        if source_id in source_ids:
            raise ValueError(f"Duplicate source_id: {source_id}")
        source_ids.add(source_id)
        for key in ("provider", "dataset", "source_vintage_id", "retrieved_at", "instrument_version", "definition_id"):
            _string(source, key, context)
        revision_status = _string(source, "revision_status", context)
        if revision_status not in ALLOWED_REVISION_STATUS:
            raise ValueError(f"Unsupported revision_status for {source_id}: {revision_status}")
        _strings(source, "reference_periods", context)

        taxonomy = _mapping(source, "taxonomy_versions", context)
        if not taxonomy or not all(isinstance(k, str) and k and isinstance(v, str) and v for k, v in taxonomy.items()):
            raise ValueError(f"{context}.taxonomy_versions must map names to non-empty versions")

        rights = _mapping(source, "rights", context)
        status = _string(rights, "status", f"{context}.rights")
        storage = _string(rights, "storage_scope", f"{context}.rights")
        publication = _string(rights, "publication_scope", f"{context}.rights")
        redistribution = _string(rights, "redistribution_scope", f"{context}.rights")
        if status not in {"approved", "unresolved", "denied"}:
            raise ValueError(f"Unsupported rights status for {source_id}: {status}")
        if storage not in ALLOWED_STORAGE_SCOPES:
            raise ValueError(f"Unsupported storage scope for {source_id}: {storage}")
        if publication not in ALLOWED_PUBLICATION_SCOPES:
            raise ValueError(f"Unsupported publication scope for {source_id}: {publication}")
        if redistribution not in ALLOWED_REDISTRIBUTION_SCOPES:
            raise ValueError(f"Unsupported redistribution scope for {source_id}: {redistribution}")

        coverage = _mapping(source, "coverage", context)
        if _string(coverage, "status", f"{context}.coverage") not in {"pass", "fail"}:
            raise ValueError(f"Unsupported coverage status for {source_id}")
        required = coverage.get("required_units")
        observed = coverage.get("observed_units")
        if not isinstance(required, int) or isinstance(required, bool) or required < 1:
            raise ValueError(f"{context}.coverage.required_units must be a positive integer")
        if not isinstance(observed, int) or isinstance(observed, bool) or observed < 0:
            raise ValueError(f"{context}.coverage.observed_units must be a non-negative integer")

        object_ids: set[str] = set()
        for object_index, source_object in enumerate(_rows(source, "objects", context)):
            object_context = f"{context}.objects[{object_index}]"
            object_id = _string(source_object, "object_id", object_context)
            if object_id in object_ids:
                raise ValueError(f"Duplicate object_id within {source_id}: {object_id}")
            object_ids.add(object_id)
            _string(source_object, "locator", object_context)
            local_path = _string(source_object, "local_path", object_context)
            expected_sha = _digest(source_object.get("sha256"), f"{object_context}.sha256")
            expected_size = source_object.get("size_bytes")
            if not isinstance(expected_size, int) or isinstance(expected_size, bool) or expected_size < 0:
                raise ValueError(f"{object_context}.size_bytes must be a non-negative integer")
            path = _safe_relative(candidate_root, local_path, required_prefix="inputs")
            if not path.is_file():
                raise ValueError(f"Candidate source input is missing: {local_path}")
            if path.stat().st_size != expected_size:
                raise ValueError(f"Candidate source input size mismatch: {local_path}")
            if sha256_file(path) != expected_sha:
                raise ValueError(f"Candidate source input checksum mismatch: {local_path}")
            key = f"{source_id}:{object_id}"
            if key in input_hashes:
                raise ValueError(f"Duplicate source object key: {key}")
            input_hashes[key] = expected_sha

    artifact_ids: set[str] = set()
    output_hashes: dict[str, str] = {}
    for index, artifact in enumerate(_rows(manifest, "artifacts", "release")):
        context = f"artifacts[{index}]"
        artifact_id = _string(artifact, "artifact_id", context)
        if artifact_id in artifact_ids:
            raise ValueError(f"Duplicate artifact_id: {artifact_id}")
        artifact_ids.add(artifact_id)
        relative = _string(artifact, "path", context)
        path = _safe_relative(candidate_root, relative, required_prefix="artifacts")
        if not path.is_file():
            raise ValueError(f"Candidate artifact is missing: {relative}")
        expected_sha = _digest(artifact.get("sha256"), f"{context}.sha256")
        expected_size = artifact.get("size_bytes")
        if not isinstance(expected_size, int) or isinstance(expected_size, bool) or expected_size < 0:
            raise ValueError(f"{context}.size_bytes must be a non-negative integer")
        if path.stat().st_size != expected_size:
            raise ValueError(f"Candidate artifact size mismatch: {relative}")
        if sha256_file(path) != expected_sha:
            raise ValueError(f"Candidate artifact checksum mismatch: {relative}")
        evidence_class = artifact.get("evidence_class")
        if not isinstance(evidence_class, int) or isinstance(evidence_class, bool) or evidence_class not in range(1, 6):
            raise ValueError(f"{context}.evidence_class must be an integer from 1 to 5")
        unknown_sources = sorted(set(_strings(artifact, "source_ids", context)) - source_ids)
        if unknown_sources:
            raise ValueError(f"{context} references unknown sources: {unknown_sources}")
        output_hashes[artifact_id] = expected_sha

    diagnostic_ids: set[str] = set()
    diagnostic_classes: set[str] = set()
    for index, diagnostic in enumerate(_rows(manifest, "diagnostics", "release")):
        context = f"diagnostics[{index}]"
        diagnostic_id = _string(diagnostic, "diagnostic_id", context)
        if diagnostic_id in diagnostic_ids:
            raise ValueError(f"Duplicate diagnostic_id: {diagnostic_id}")
        diagnostic_ids.add(diagnostic_id)
        diagnostic_class = _string(diagnostic, "diagnostic_class", context)
        if diagnostic_class not in REQUIRED_DIAGNOSTIC_CLASSES:
            raise ValueError(f"Unsupported diagnostic_class: {diagnostic_class}")
        diagnostic_classes.add(diagnostic_class)
        if _string(diagnostic, "status", context) not in {"pass", "fail"}:
            raise ValueError(f"Unsupported diagnostic status: {diagnostic_id}")
        _digest(diagnostic.get("value_digest"), f"{context}.value_digest")
    missing_classes = sorted(REQUIRED_DIAGNOSTIC_CLASSES - diagnostic_classes)
    if missing_classes:
        raise ValueError(f"Release diagnostics are missing required classes: {missing_classes}")

    claim_ids: set[str] = set()
    for index, claim in enumerate(_rows(manifest, "claims", "release")):
        context = f"claims[{index}]"
        claim_id = _string(claim, "claim_id", context)
        if claim_id in claim_ids:
            raise ValueError(f"Duplicate claim_id: {claim_id}")
        claim_ids.add(claim_id)
        _strings(claim, "surfaces", context)
        unknown_artifacts = sorted(set(_strings(claim, "artifact_ids", context)) - artifact_ids)
        if unknown_artifacts:
            raise ValueError(f"{context} references unknown artifacts: {unknown_artifacts}")
        _digest(claim.get("value_digest"), f"{context}.value_digest")
        _string(claim, "value_summary", context)
        _string(claim, "truth_state", context)
        _string(claim, "interpretation_boundary", context)
        evidence_class = claim.get("evidence_class")
        if not isinstance(evidence_class, int) or isinstance(evidence_class, bool) or evidence_class not in range(1, 6):
            raise ValueError(f"{context}.evidence_class must be an integer from 1 to 5")

    build = _mapping(manifest, "build", "release")
    _string(build, "builder_id", "release.build")
    _string(build, "builder_commit", "release.build")
    if build.get("deterministic") is not True:
        raise ValueError("release.build.deterministic must be true")
    declared_inputs = {str(k): str(v) for k, v in _mapping(build, "input_sha256", "release.build").items()}
    declared_outputs = {str(k): str(v) for k, v in _mapping(build, "output_sha256", "release.build").items()}
    if declared_inputs != input_hashes:
        raise ValueError("release.build.input_sha256 must exactly cover every verified source object")
    if declared_outputs != output_hashes:
        raise ValueError("release.build.output_sha256 must exactly cover every verified artifact")


def diff_releases(previous: Mapping[str, Any] | None, candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Produce auditable diffs and fail-closed contract violations."""
    new_sources = _by_id(_rows(candidate, "sources", "release"), "source_id")
    new_artifacts = _by_id(_rows(candidate, "artifacts", "release"), "artifact_id")
    new_diagnostics = _by_id(_rows(candidate, "diagnostics", "release"), "diagnostic_id")
    new_claims = _by_id(_rows(candidate, "claims", "release"), "claim_id")
    old_sources: dict[str, Mapping[str, Any]] = {}
    old_artifacts: dict[str, Mapping[str, Any]] = {}
    old_diagnostics: dict[str, Mapping[str, Any]] = {}
    old_claims: dict[str, Mapping[str, Any]] = {}
    if previous is not None:
        old_sources = _by_id(_rows(previous, "sources", "release"), "source_id")
        old_artifacts = _by_id(_rows(previous, "artifacts", "release"), "artifact_id")
        old_diagnostics = _by_id(_rows(previous, "diagnostics", "release"), "diagnostic_id")
        old_claims = _by_id(_rows(previous, "claims", "release"), "claim_id")

    failures: list[dict[str, str]] = []
    if previous is None and candidate.get("release_type") != "baseline":
        failures.append({"code": "FIRST_RELEASE_NOT_BASELINE", "scope": "release"})
    if previous is not None and candidate.get("release_type") == "baseline":
        failures.append({"code": "BASELINE_REUSE", "scope": "release"})
    if previous is not None and previous.get("data_mode") != candidate.get("data_mode"):
        failures.append({"code": "DATA_MODE_CHANGE", "scope": "release"})

    source_changes: list[dict[str, Any]] = []
    has_new_wave_change = False
    has_revision_change = False
    for source_id in sorted(old_sources.keys() | new_sources.keys()):
        old = old_sources.get(source_id)
        new = new_sources.get(source_id)
        if old is None and new is not None:
            has_new_wave_change = True
            source_changes.append(
                {
                    "source_id": source_id,
                    "change": "added",
                    "old_source_vintage_id": None,
                    "new_source_vintage_id": new.get("source_vintage_id"),
                }
            )
            continue
        if new is None and old is not None:
            source_changes.append(
                {
                    "source_id": source_id,
                    "change": "removed",
                    "old_source_vintage_id": old.get("source_vintage_id"),
                    "new_source_vintage_id": None,
                }
            )
            failures.append({"code": "MISSING_SOURCE", "source_id": source_id})
            continue
        if old is None or new is None:
            continue
        if _stable_digest(old, ("rights",)) != _stable_digest(new, ("rights",)):
            failures.append({"code": "RIGHTS_CHANGE", "source_id": source_id})
        if _stable_digest(old, ("instrument_version", "definition_id", "taxonomy_versions")) != _stable_digest(
            new, ("instrument_version", "definition_id", "taxonomy_versions")
        ):
            failures.append({"code": "DEFINITION_CHANGE", "source_id": source_id})
        old_periods = {str(v) for v in old.get("reference_periods", [])}
        new_periods = {str(v) for v in new.get("reference_periods", [])}
        added_periods = sorted(new_periods - old_periods)
        removed_periods = sorted(old_periods - new_periods)
        if added_periods:
            has_new_wave_change = True
        if removed_periods:
            failures.append({"code": "MISSING_PERIOD", "source_id": source_id})
        old_objects = _source_objects(old)
        new_objects = _source_objects(new)
        added_objects = sorted(new_objects.keys() - old_objects.keys())
        removed_objects = sorted(old_objects.keys() - new_objects.keys())
        modified_objects = sorted(
            object_id
            for object_id in old_objects.keys() & new_objects.keys()
            if old_objects[object_id].get("sha256") != new_objects[object_id].get("sha256")
        )
        if added_objects:
            has_new_wave_change = True
        if modified_objects:
            has_revision_change = True
        if removed_objects:
            failures.append({"code": "MISSING_SOURCE_OBJECT", "source_id": source_id})
        changed = bool(added_periods or removed_periods or added_objects or removed_objects or modified_objects)
        if changed:
            source_changes.append(
                {
                    "source_id": source_id,
                    "change": "modified",
                    "old_source_vintage_id": old.get("source_vintage_id"),
                    "new_source_vintage_id": new.get("source_vintage_id"),
                    "added_periods": added_periods,
                    "removed_periods": removed_periods,
                    "added_objects": added_objects,
                    "removed_objects": removed_objects,
                    "modified_objects": modified_objects,
                }
            )
            if new.get("source_vintage_id") == old.get("source_vintage_id"):
                failures.append({"code": "SOURCE_VINTAGE_ID_NOT_ADVANCED", "source_id": source_id})
            if new.get("revision_status") == "unchanged":
                failures.append({"code": "REVISION_STATUS_MISMATCH", "source_id": source_id})

    release_type = candidate.get("release_type")
    if previous is not None and release_type == "new_wave" and has_revision_change:
        failures.append({"code": "RELEASE_TYPE_MISMATCH", "scope": "release"})
    if previous is not None and release_type == "revision" and has_new_wave_change:
        failures.append({"code": "RELEASE_TYPE_MISMATCH", "scope": "release"})
    if previous is not None and release_type == "new_wave" and not has_new_wave_change:
        failures.append({"code": "RELEASE_TYPE_MISMATCH", "scope": "release"})

    artifact_changes: list[dict[str, Any]] = []
    changed_artifacts: set[str] = set()
    artifact_fields = ("sha256", "path", "evidence_class", "source_ids")
    for artifact_id in sorted(old_artifacts.keys() | new_artifacts.keys()):
        old = old_artifacts.get(artifact_id)
        new = new_artifacts.get(artifact_id)
        if old is None:
            change = "added"
        elif new is None:
            change = "removed"
        elif _stable_digest(old, artifact_fields) != _stable_digest(new, artifact_fields):
            change = "modified"
        else:
            continue
        changed_artifacts.add(artifact_id)
        artifact_changes.append(
            {
                "artifact_id": artifact_id,
                "change": change,
                "old_sha256": old.get("sha256") if old else None,
                "new_sha256": new.get("sha256") if new else None,
            }
        )

    diagnostic_changes: list[dict[str, Any]] = []
    changed_diagnostics: set[str] = set()
    diagnostic_fields = ("status", "value_digest", "diagnostic_class")
    for diagnostic_id in sorted(old_diagnostics.keys() | new_diagnostics.keys()):
        old = old_diagnostics.get(diagnostic_id)
        new = new_diagnostics.get(diagnostic_id)
        if old is None:
            change = "added"
        elif new is None:
            change = "removed"
        elif _stable_digest(old, diagnostic_fields) != _stable_digest(new, diagnostic_fields):
            change = "modified"
        else:
            continue
        changed_diagnostics.add(diagnostic_id)
        diagnostic_changes.append(
            {
                "diagnostic_id": diagnostic_id,
                "change": change,
                "old_status": old.get("status") if old else None,
                "new_status": new.get("status") if new else None,
                "old_value_digest": old.get("value_digest") if old else None,
                "new_value_digest": new.get("value_digest") if new else None,
            }
        )

    claim_changes: list[dict[str, Any]] = []
    affected_claims: set[str] = set()
    claim_fields = (
        "value_digest",
        "value_summary",
        "truth_state",
        "artifact_ids",
        "evidence_class",
        "interpretation_boundary",
        "surfaces",
    )
    for claim_id in sorted(old_claims.keys() | new_claims.keys()):
        old = old_claims.get(claim_id)
        new = new_claims.get(claim_id)
        if old is None:
            change = "added"
        elif new is None:
            change = "removed"
        elif _stable_digest(old, claim_fields) != _stable_digest(new, claim_fields):
            change = "modified"
        else:
            change = "unchanged"
        refs: set[str] = set()
        surfaces: set[str] = set()
        if old is not None:
            refs.update(str(v) for v in old.get("artifact_ids", []))
            surfaces.update(str(v) for v in old.get("surfaces", []))
        if new is not None:
            refs.update(str(v) for v in new.get("artifact_ids", []))
            surfaces.update(str(v) for v in new.get("surfaces", []))
        dependency_changed = bool(refs & changed_artifacts)
        if change != "unchanged" or dependency_changed:
            affected_claims.add(claim_id)
            claim_changes.append(
                {
                    "claim_id": claim_id,
                    "change": change,
                    "artifact_dependency_changed": dependency_changed,
                    "surfaces": sorted(surfaces),
                    "old_value_summary": old.get("value_summary") if old else None,
                    "new_value_summary": new.get("value_summary") if new else None,
                    "old_truth_state": old.get("truth_state") if old else None,
                    "new_truth_state": new.get("truth_state") if new else None,
                }
            )

    return {
        "source_changes": source_changes,
        "artifact_changes": artifact_changes,
        "diagnostic_changes": diagnostic_changes,
        "claim_changes": claim_changes,
        "contract_failures": failures,
        "changed_source_ids": sorted(str(row["source_id"]) for row in source_changes),
        "changed_artifact_ids": sorted(changed_artifacts),
        "changed_diagnostic_ids": sorted(changed_diagnostics),
        "affected_claim_ids": sorted(affected_claims),
    }


def candidate_gate_failures(candidate: Mapping[str, Any], release_diff: Mapping[str, Any]) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    existing = release_diff.get("contract_failures")
    if isinstance(existing, list):
        failures.extend({str(k): str(v) for k, v in row.items()} for row in existing if isinstance(row, Mapping))
    for source in _rows(candidate, "sources", "release"):
        source_id = str(source["source_id"])
        rights = _mapping(source, "rights", f"source {source_id}")
        if (
            rights.get("status") != "approved"
            or rights.get("publication_scope") == "none"
            or rights.get("redistribution_scope") == "none"
        ):
            failures.append({"code": "RIGHTS_UNRESOLVED", "source_id": source_id})
        coverage = _mapping(source, "coverage", f"source {source_id}")
        required = coverage.get("required_units")
        observed = coverage.get("observed_units")
        if coverage.get("status") != "pass" or not isinstance(required, int) or not isinstance(observed, int) or observed < required:
            failures.append({"code": "COVERAGE_FAILED", "source_id": source_id})
    for diagnostic in _rows(candidate, "diagnostics", "release"):
        if diagnostic.get("status") != "pass":
            failures.append({"code": "DIAGNOSTIC_FAILED", "diagnostic_id": str(diagnostic["diagnostic_id"])})
    return failures


def gate_status(failures: Sequence[Mapping[str, str]], has_changes: bool) -> str:
    codes = {str(row.get("code", "")) for row in failures}
    if codes & {"RIGHTS_CHANGE", "RIGHTS_UNRESOLVED"}:
        return "BLOCKED_RIGHTS"
    if "DEFINITION_CHANGE" in codes:
        return "BLOCKED_DEFINITION_CHANGE"
    if "DATA_MODE_CHANGE" in codes:
        return "BLOCKED_DATA_MODE_CHANGE"
    if codes & {"MISSING_SOURCE", "MISSING_PERIOD", "MISSING_SOURCE_OBJECT"}:
        return "BLOCKED_MISSING_SERIES"
    if "COVERAGE_FAILED" in codes:
        return "BLOCKED_COVERAGE"
    if "DIAGNOSTIC_FAILED" in codes:
        return "BLOCKED_DIAGNOSTICS"
    if codes & {"REVISION_STATUS_MISMATCH", "SOURCE_VINTAGE_ID_NOT_ADVANCED", "RELEASE_TYPE_MISMATCH"}:
        return "BLOCKED_REVISION_STATUS"
    if failures:
        return "BLOCKED_CONTRACT"
    return "BLOCKED_REVIEW_REQUIRED" if has_changes else "REPRODUCED_CURRENT_RELEASE"


def review_package(candidate: Mapping[str, Any], release_diff: Mapping[str, Any]) -> dict[str, Any]:
    change_by_claim = {
        str(row["claim_id"]): row
        for row in release_diff.get("claim_changes", [])
        if isinstance(row, Mapping) and "claim_id" in row
    }
    affected: list[dict[str, Any]] = []
    for raw_id in release_diff.get("affected_claim_ids", []):
        claim_id = str(raw_id)
        change = change_by_claim.get(claim_id, {})
        affected.append(
            {
                "claim_id": claim_id,
                "surfaces": list(change.get("surfaces", [])),
                "old_value_summary": change.get("old_value_summary"),
                "new_value_summary": change.get("new_value_summary"),
                "old_truth_state": change.get("old_truth_state"),
                "new_truth_state": change.get("new_truth_state"),
                "review_status": "PENDING",
            }
        )
    return {
        "data_mode": candidate.get("data_mode"),
        "changed_source_ids": list(release_diff.get("changed_source_ids", [])),
        "changed_diagnostic_ids": list(release_diff.get("changed_diagnostic_ids", [])),
        "affected_claims": affected,
    }


def validate_review_attestation(
    attestation: Mapping[str, Any],
    *,
    stage_id: str,
    candidate_manifest_sha256: str,
    candidate: Mapping[str, Any],
    release_diff: Mapping[str, Any],
) -> None:
    """Require exact scientific/editorial/rights/CI review binding."""
    if attestation.get("stage_id") != stage_id:
        raise ValueError("Review attestation is not bound to this staged release")
    if attestation.get("release_id") != candidate.get("release_id"):
        raise ValueError("Review attestation release_id mismatch")
    if attestation.get("candidate_manifest_sha256") != candidate_manifest_sha256:
        raise ValueError("Review attestation candidate-manifest checksum mismatch")
    if not attestation.get("reviewer") or not attestation.get("reviewed_at"):
        raise ValueError("Review attestation requires reviewer and reviewed_at")
    for key in ("scientific_reviewed", "editorial_reviewed", "source_rights_reviewed", "ci_passed"):
        if attestation.get(key) is not True:
            raise ValueError(f"Review attestation requires {key}=true")
    if not isinstance(attestation.get("candidate_commit"), str) or not attestation.get("candidate_commit"):
        raise ValueError("Review attestation requires candidate_commit")
    ci_run_ids = attestation.get("ci_run_ids")
    if not isinstance(ci_run_ids, list) or not ci_run_ids or not all(isinstance(v, int) and not isinstance(v, bool) and v > 0 for v in ci_run_ids):
        raise ValueError("Review attestation requires one or more positive integer ci_run_ids")
    expected_artifacts = {
        str(row["artifact_id"]): str(row["sha256"])
        for row in _rows(candidate, "artifacts", "release")
    }
    if attestation.get("artifact_sha256") != expected_artifacts:
        raise ValueError("Review attestation artifact hashes do not match the candidate release")
    exact_lists = (
        ("reviewed_source_ids", release_diff.get("changed_source_ids", [])),
        ("reviewed_diagnostic_ids", release_diff.get("changed_diagnostic_ids", [])),
        ("reviewed_claim_ids", release_diff.get("affected_claim_ids", [])),
    )
    for key, raw_expected in exact_lists:
        expected = sorted(str(v) for v in raw_expected)
        actual = attestation.get(key)
        if not isinstance(actual, list) or sorted(str(v) for v in actual) != expected:
            raise ValueError(f"Review attestation {key} does not exactly cover the staged changes")


def sanitized_public_manifest(candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Remove local source paths while retaining identity and provenance."""
    public: dict[str, Any] = json.loads(json.dumps(candidate))
    sources = public.get("sources")
    if isinstance(sources, list):
        for source in sources:
            if not isinstance(source, dict):
                continue
            objects = source.get("objects")
            if isinstance(objects, list):
                for source_object in objects:
                    if isinstance(source_object, dict):
                        source_object.pop("local_path", None)
    public["source_input_bytes_included"] = False
    return public