"""Versioned, fail-closed observatory release governance.

This module does not fetch data. Source-specific pipelines prepare a candidate
release package with locally verifiable source inputs and deterministic derived
artifacts. The release engine validates, diffs, reviews, and immutably promotes
that package without copying source input bytes into the public release archive.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

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


def _require_string(mapping: Mapping[str, Any], key: str, context: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}.{key} must be a non-empty string")
    return value


def _require_mapping(mapping: Mapping[str, Any], key: str, context: str) -> Mapping[str, Any]:
    value = mapping.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"{context}.{key} must be an object")
    return value


def _require_mapping_list(mapping: Mapping[str, Any], key: str, context: str) -> list[Mapping[str, Any]]:
    value = mapping.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(row, Mapping) for row in value):
        raise ValueError(f"{context}.{key} must be a non-empty list of objects")
    return list(value)


def _require_string_list(mapping: Mapping[str, Any], key: str, context: str) -> list[str]:
    value = mapping.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{context}.{key} must be a non-empty list of strings")
    if len(set(value)) != len(value):
        raise ValueError(f"{context}.{key} contains duplicate values")
    return list(value)


def _safe_candidate_path(root: Path, relative: str) -> Path:
    posix = PurePosixPath(relative)
    if posix.is_absolute() or ".." in posix.parts or not posix.parts:
        raise ValueError(f"Candidate path must be safe and relative: {relative!r}")
    root_resolved = root.resolve()
    resolved = (root / Path(*posix.parts)).resolve()
    if resolved != root_resolved and root_resolved not in resolved.parents:
        raise ValueError(f"Candidate path escapes package root: {relative!r}")
    return resolved


def _validate_hex_digest(value: object, *, context: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{context} must be a 64-character SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{context} must be hexadecimal") from exc
    return value.lower()


def _source_object_key(source_id: str, object_id: str) -> str:
    return f"{source_id}:{object_id}"


def validate_release_manifest(manifest: Mapping[str, Any], candidate_root: Path) -> None:
    if manifest.get("schema_version") != 1:
        raise ValueError("release manifest schema_version must equal 1")
    _require_string(manifest, "release_id", "release")
    release_type = _require_string(manifest, "release_type", "release")
    if release_type not in ALLOWED_RELEASE_TYPES:
        raise ValueError(f"Unsupported release_type: {release_type}")
    _require_string(manifest, "created_at", "release")
    supersedes = manifest.get("supersedes_release_id")
    if supersedes is not None and (not isinstance(supersedes, str) or not supersedes):
        raise ValueError("release.supersedes_release_id must be null or a non-empty string")

    sources = _require_mapping_list(manifest, "sources", "release")
    source_ids: set[str] = set()
    source_object_hashes: dict[str, str] = {}
    for index, source in enumerate(sources):
        context = f"sources[{index}]"
        source_id = _require_string(source, "source_id", context)
        if source_id in source_ids:
            raise ValueError(f"Duplicate source_id: {source_id}")
        source_ids.add(source_id)
        for key in (
            "provider",
            "dataset",
            "source_vintage_id",
            "retrieved_at",
            "instrument_version",
            "definition_id",
        ):
            _require_string(source, key, context)
        revision_status = _require_string(source, "revision_status", context)
        if revision_status not in ALLOWED_REVISION_STATUS:
            raise ValueError(f"Unsupported revision_status for {source_id}: {revision_status}")
        _require_string_list(source, "reference_periods", context)
        taxonomy = _require_mapping(source, "taxonomy_versions", context)
        if not taxonomy or not all(isinstance(k, str) and k and isinstance(v, str) and v for k, v in taxonomy.items()):
            raise ValueError(f"{context}.taxonomy_versions must map non-empty names to versions")

        rights = _require_mapping(source, "rights", context)
        rights_status = _require_string(rights, "status", f"{context}.rights")
        if rights_status not in {"approved", "unresolved", "denied"}:
            raise ValueError(f"Unsupported rights status for {source_id}: {rights_status}")
        storage_scope = _require_string(rights, "storage_scope", f"{context}.rights")
        publication_scope = _require_string(rights, "publication_scope", f"{context}.rights")
        redistribution_scope = _require_string(rights, "redistribution_scope", f"{context}.rights")
        if storage_scope not in ALLOWED_STORAGE_SCOPES:
            raise ValueError(f"Unsupported storage_scope for {source_id}: {storage_scope}")
        if publication_scope not in ALLOWED_PUBLICATION_SCOPES:
            raise ValueError(f"Unsupported publication_scope for {source_id}: {publication_scope}")
        if redistribution_scope not in ALLOWED_REDISTRIBUTION_SCOPES:
            raise ValueError(f"Unsupported redistribution_scope for {source_id}: {redistribution_scope}")

        coverage = _require_mapping(source, "coverage", context)
        coverage_status = _require_string(coverage, "status", f"{context}.coverage")
        if coverage_status not in {"pass", "fail"}:
            raise ValueError(f"Unsupported coverage status for {source_id}: {coverage_status}")
        required_units = coverage.get("required_units")
        observed_units = coverage.get("observed_units")
        if not isinstance(required_units, int) or isinstance(required_units, bool) or required_units < 1:
            raise ValueError(f"{context}.coverage.required_units must be a positive integer")
        if not isinstance(observed_units, int) or isinstance(observed_units, bool) or observed_units < 0:
            raise ValueError(f"{context}.coverage.observed_units must be a non-negative integer")

        objects = _require_mapping_list(source, "objects", context)
        object_ids: set[str] = set()
        for object_index, source_object in enumerate(objects):
            object_context = f"{context}.objects[{object_index}]"
            object_id = _require_string(source_object, "object_id", object_context)
            if object_id in object_ids:
                raise ValueError(f"Duplicate object_id within {source_id}: {object_id}")
            object_ids.add(object_id)
            _require_string(source_object, "locator", object_context)
            local_path = _require_string(source_object, "local_path", object_context)
            expected_sha = _validate_hex_digest(source_object.get("sha256"), context=f"{object_context}.sha256")
            expected_size = source_object.get("size_bytes")
            if not isinstance(expected_size, int) or isinstance(expected_size, bool) or expected_size < 0:
                raise ValueError(f"{object_context}.size_bytes must be a non-negative integer")
            source_path = _safe_candidate_path(candidate_root, local_path)
            if not source_path.is_file():
                raise ValueError(f"Candidate source input is missing: {local_path}")
            if source_path.stat().st_size != expected_size:
                raise ValueError(f"Candidate source input size mismatch: {local_path}")
            if sha256_file(source_path) != expected_sha:
                raise ValueError(f"Candidate source input checksum mismatch: {local_path}")
            global_key = _source_object_key(source_id, object_id)
            if global_key in source_object_hashes:
                raise ValueError(f"Duplicate source object key: {global_key}")
            source_object_hashes[global_key] = expected_sha

    artifacts = _require_mapping_list(manifest, "artifacts", "release")
    artifact_ids: set[str] = set()
    artifact_hashes: dict[str, str] = {}
    for index, artifact in enumerate(artifacts):
        context = f"artifacts[{index}]"
        artifact_id = _require_string(artifact, "artifact_id", context)
        if artifact_id in artifact_ids:
            raise ValueError(f"Duplicate artifact_id: {artifact_id}")
        artifact_ids.add(artifact_id)
        relative_path = _require_string(artifact, "path", context)
        artifact_path = _safe_candidate_path(candidate_root, relative_path)
        if not artifact_path.is_file():
            raise ValueError(f"Candidate artifact is missing: {relative_path}")
        expected_sha = _validate_hex_digest(artifact.get("sha256"), context=f"{context}.sha256")
        expected_size = artifact.get("size_bytes")
        if not isinstance(expected_size, int) or isinstance(expected_size, bool) or expected_size < 0:
            raise ValueError(f"{context}.size_bytes must be a non-negative integer")
        if artifact_path.stat().st_size != expected_size:
            raise ValueError(f"Candidate artifact size mismatch: {relative_path}")
        if sha256_file(artifact_path) != expected_sha:
            raise ValueError(f"Candidate artifact checksum mismatch: {relative_path}")
        evidence_class = artifact.get("evidence_class")
        if not isinstance(evidence_class, int) or isinstance(evidence_class, bool) or evidence_class not in range(1, 6):
            raise ValueError(f"{context}.evidence_class must be an integer from 1 to 5")
        source_refs = _require_string_list(artifact, "source_ids", context)
        unknown_sources = sorted(set(source_refs) - source_ids)
        if unknown_sources:
            raise ValueError(f"{context} references unknown sources: {unknown_sources}")
        artifact_hashes[artifact_id] = expected_sha

    diagnostics = _require_mapping_list(manifest, "diagnostics", "release")
    diagnostic_ids: set[str] = set()
    for index, diagnostic in enumerate(diagnostics):
        context = f"diagnostics[{index}]"
        diagnostic_id = _require_string(diagnostic, "diagnostic_id", context)
        if diagnostic_id in diagnostic_ids:
            raise ValueError(f"Duplicate diagnostic_id: {diagnostic_id}")
        diagnostic_ids.add(diagnostic_id)
        diagnostic_class = _require_string(diagnostic, "diagnostic_class", context)
        if diagnostic_class not in REQUIRED_DIAGNOSTIC_CLASSES:
            raise ValueError(f"Unsupported diagnostic_class: {diagnostic_class}")
        status = _require_string(diagnostic, "status", context)
        if status not in {"pass", "fail"}:
            raise ValueError(f"Unsupported diagnostic status: {status}")
        _validate_hex_digest(diagnostic.get("value_digest"), context=f"{context}.value_digest")
    observed_classes = {str(row["diagnostic_class"]) for row in diagnostics}
    if observed_classes != REQUIRED_DIAGNOSTIC_CLASSES:
        missing = sorted(REQUIRED_DIAGNOSTIC_CLASSES - observed_classes)
        raise ValueError(f"Release diagnostics are missing required classes: {missing}")

    claims = _require_mapping_list(manifest, "claims", "release")
    claim_ids: set[str] = set()
    for index, claim in enumerate(claims):
        context = f"claims[{index}]"
        claim_id = _require_string(claim, "claim_id", context)
        if claim_id in claim_ids:
            raise ValueError(f"Duplicate claim_id: {claim_id}")
        claim_ids.add(claim_id)
        _require_string_list(claim, "surfaces", context)
        artifact_refs = _require_string_list(claim, "artifact_ids", context)
        unknown_artifacts = sorted(set(artifact_refs) - artifact_ids)
        if unknown_artifacts:
            raise ValueError(f"{context} references unknown artifacts: {unknown_artifacts}")
        _validate_hex_digest(claim.get("value_digest"), context=f"{context}.value_digest")
        _require_string(claim, "truth_state", context)
        _require_string(claim, "interpretation_boundary", context)
        evidence_class = claim.get("evidence_class")
        if not isinstance(evidence_class, int) or isinstance(evidence_class, bool) or evidence_class not in range(1, 6):
            raise ValueError(f"{context}.evidence_class must be an integer from 1 to 5")

    build = _require_mapping(manifest, "build", "release")
    _require_string(build, "builder_id", "release.build")
    _require_string(build, "builder_commit", "release.build")
    if build.get("deterministic") is not True:
        raise ValueError("release.build.deterministic must be true")
    input_hashes = _require_mapping(build, "input_sha256", "release.build")
    output_hashes = _require_mapping(build, "output_sha256", "release.build")
    normalized_inputs = {str(key): str(value) for key, value in input_hashes.items()}
    normalized_outputs = {str(key): str(value) for key, value in output_hashes.items()}
    if normalized_inputs != source_object_hashes:
        raise ValueError("release.build.input_sha256 must exactly cover every verified source object")
    if normalized_outputs != artifact_hashes:
        raise ValueError("release.build.output_sha256 must exactly cover every verified artifact")


def _by_id(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, Mapping[str, Any]]:
    return {str(row[key]): row for row in rows}


def _source_objects(source: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    rows = source.get("objects")
    if not isinstance(rows, list):
        return {}
    return {str(row["object_id"]): row for row in rows if isinstance(row, Mapping) and "object_id" in row}


def _stable_fields_digest(mapping: Mapping[str, Any], keys: Sequence[str]) -> str:
    return canonical_digest({key: mapping.get(key) for key in keys})


def diff_releases(previous: Mapping[str, Any] | None, candidate: Mapping[str, Any]) -> dict[str, Any]:
    candidate_sources = _by_id(_require_mapping_list(candidate, "sources", "release"), "source_id")
    candidate_artifacts = _by_id(_require_mapping_list(candidate, "artifacts", "release"), "artifact_id")
    candidate_diagnostics = _by_id(_require_mapping_list(candidate, "diagnostics", "release"), "diagnostic_id")
    candidate_claims = _by_id(_require_mapping_list(candidate, "claims", "release"), "claim_id")

    previous_sources: dict[str, Mapping[str, Any]] = {}
    previous_artifacts: dict[str, Mapping[str, Any]] = {}
    previous_diagnostics: dict[str, Mapping[str, Any]] = {}
    previous_claims: dict[str, Mapping[str, Any]] = {}
    if previous is not None:
        previous_sources = _by_id(_require_mapping_list(previous, "sources", "release"), "source_id")
        previous_artifacts = _by_id(_require_mapping_list(previous, "artifacts", "release"), "artifact_id")
        previous_diagnostics = _by_id(_require_mapping_list(previous, "diagnostics", "release"), "diagnostic_id")
        previous_claims = _by_id(_require_mapping_list(previous, "claims", "release"), "claim_id")

    contract_failures: list[dict[str, str]] = []
    source_changes: list[dict[str, Any]] = []
    for source_id in sorted(previous_sources.keys() | candidate_sources.keys()):
        old = previous_sources.get(source_id)
        new = candidate_sources.get(source_id)
        if old is None and new is not None:
            source_changes.append({"source_id": source_id, "change": "added"})
            continue
        if new is None and old is not None:
            source_changes.append({"source_id": source_id, "change": "removed"})
            contract_failures.append({"code": "MISSING_SOURCE", "source_id": source_id})
            continue
        if old is None or new is None:
            continue
        rights_fields = ("rights",)
        definition_fields = ("instrument_version", "definition_id", "taxonomy_versions")
        if _stable_fields_digest(old, rights_fields) != _stable_fields_digest(new, rights_fields):
            contract_failures.append({"code": "RIGHTS_CHANGE", "source_id": source_id})
        if _stable_fields_digest(old, definition_fields) != _stable_fields_digest(new, definition_fields):
            contract_failures.append({"code": "DEFINITION_CHANGE", "source_id": source_id})
        old_periods = set(str(v) for v in old.get("reference_periods", []))
        new_periods = set(str(v) for v in new.get("reference_periods", []))
        removed_periods = sorted(old_periods - new_periods)
        added_periods = sorted(new_periods - old_periods)
        if removed_periods:
            contract_failures.append({"code": "MISSING_PERIOD", "source_id": source_id})
        old_objects = _source_objects(old)
        new_objects = _source_objects(new)
        removed_objects = sorted(old_objects.keys() - new_objects.keys())
        added_objects = sorted(new_objects.keys() - old_objects.keys())
        modified_objects = sorted(
            object_id
            for object_id in old_objects.keys() & new_objects.keys()
            if old_objects[object_id].get("sha256") != new_objects[object_id].get("sha256")
        )
        if removed_objects:
            contract_failures.append({"code": "MISSING_SOURCE_OBJECT", "source_id": source_id})
        changed = bool(removed_periods or added_periods or removed_objects or added_objects or modified_objects)
        if changed:
            source_changes.append(
                {
                    "source_id": source_id,
                    "change": "modified",
                    "added_periods": added_periods,
                    "removed_periods": removed_periods,
                    "added_objects": added_objects,
                    "removed_objects": removed_objects,
                    "modified_objects": modified_objects,
                }
            )
            if new.get("revision_status") == "unchanged":
                contract_failures.append({"code": "REVISION_STATUS_MISMATCH", "source_id": source_id})

    artifact_changes: list[dict[str, Any]] = []
    changed_artifact_ids: set[str] = set()
    for artifact_id in sorted(previous_artifacts.keys() | candidate_artifacts.keys()):
        old = previous_artifacts.get(artifact_id)
        new = candidate_artifacts.get(artifact_id)
        if old is None:
            change = "added"
        elif new is None:
            change = "removed"
        elif _stable_fields_digest(old, ("sha256", "path", "evidence_class", "source_ids")) != _stable_fields_digest(
            new, ("sha256", "path", "evidence_class", "source_ids")
        ):
            change = "modified"
        else:
            continue
        changed_artifact_ids.add(artifact_id)
        artifact_changes.append(
            {
                "artifact_id": artifact_id,
                "change": change,
                "old_sha256": old.get("sha256") if old else None,
                "new_sha256": new.get("sha256") if new else None,
            }
        )

    diagnostic_changes: list[dict[str, Any]] = []
    changed_diagnostic_ids: set[str] = set()
    for diagnostic_id in sorted(previous_diagnostics.keys() | candidate_diagnostics.keys()):
        old = previous_diagnostics.get(diagnostic_id)
        new = candidate_diagnostics.get(diagnostic_id)
        if old is None:
            change = "added"
        elif new is None:
            change = "removed"
        elif _stable_fields_digest(old, ("status", "value_digest", "diagnostic_class")) != _stable_fields_digest(
            new, ("status", "value_digest", "diagnostic_class")
        ):
            change = "modified"
        else:
            continue
        changed_diagnostic_ids.add(diagnostic_id)
        diagnostic_changes.append({"diagnostic_id": diagnostic_id, "change": change})

    claim_changes: list[dict[str, Any]] = []
    affected_claim_ids: set[str] = set()
    all_claim_ids = previous_claims.keys() | candidate_claims.keys()
    claim_fields = ("value_digest", "truth_state", "artifact_ids", "evidence_class", "interpretation_boundary", "surfaces")
    for claim_id in sorted(all_claim_ids):
        old = previous_claims.get(claim_id)
        new = candidate_claims.get(claim_id)
        if old is None:
            change = "added"
        elif new is None:
            change = "removed"
        elif _stable_fields_digest(old, claim_fields) != _stable_fields_digest(new, claim_fields):
            change = "modified"
        else:
            change = "unchanged"
        refs: set[str] = set()
        if old is not None:
            refs.update(str(v) for v in old.get("artifact_ids", []))
        if new is not None:
            refs.update(str(v) for v in new.get("artifact_ids", []))
        if change != "unchanged" or refs & changed_artifact_ids:
            affected_claim_ids.add(claim_id)
            claim_changes.append({"claim_id": claim_id, "change": change, "artifact_dependency_changed": bool(refs & changed_artifact_ids)})

    return {
        "source_changes": source_changes,
        "artifact_changes": artifact_changes,
        "diagnostic_changes": diagnostic_changes,
        "claim_changes": claim_changes,
        "contract_failures": contract_failures,
        "changed_source_ids": sorted(str(row["source_id"]) for row in source_changes),
        "changed_artifact_ids": sorted(changed_artifact_ids),
        "changed_diagnostic_ids": sorted(changed_diagnostic_ids),
        "affected_claim_ids": sorted(affected_claim_ids),
    }


def candidate_gate_failures(candidate: Mapping[str, Any], release_diff: Mapping[str, Any]) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    raw_contract = release_diff.get("contract_failures")
    if isinstance(raw_contract, list):
        failures.extend(dict(row) for row in raw_contract if isinstance(row, Mapping))
    for source in _require_mapping_list(candidate, "sources", "release"):
        source_id = str(source["source_id"])
        rights = _require_mapping(source, "rights", f"source {source_id}")
        if rights.get("status") != "approved" or rights.get("publication_scope") == "none":
            failures.append({"code": "RIGHTS_UNRESOLVED", "source_id": source_id})
        coverage = _require_mapping(source, "coverage", f"source {source_id}")
        required = coverage.get("required_units")
        observed = coverage.get("observed_units")
        if coverage.get("status") != "pass" or not isinstance(required, int) or not isinstance(observed, int) or observed < required:
            failures.append({"code": "COVERAGE_FAILED", "source_id": source_id})
    for diagnostic in _require_mapping_list(candidate, "diagnostics", "release"):
        if diagnostic.get("status") != "pass":
            failures.append({"code": "DIAGNOSTIC_FAILED", "diagnostic_id": str(diagnostic["diagnostic_id"])})
    return failures


def gate_status(failures: Sequence[Mapping[str, str]], has_changes: bool) -> str:
    codes = {str(row.get("code", "")) for row in failures}
    if codes & {"RIGHTS_CHANGE", "RIGHTS_UNRESOLVED"}:
        return "BLOCKED_RIGHTS"
    if "DEFINITION_CHANGE" in codes:
        return "BLOCKED_DEFINITION_CHANGE"
    if codes & {"MISSING_SOURCE", "MISSING_PERIOD", "MISSING_SOURCE_OBJECT"}:
        return "BLOCKED_MISSING_SERIES"
    if "COVERAGE_FAILED" in codes:
        return "BLOCKED_COVERAGE"
    if "DIAGNOSTIC_FAILED" in codes:
        return "BLOCKED_DIAGNOSTICS"
    if "REVISION_STATUS_MISMATCH" in codes:
        return "BLOCKED_REVISION_STATUS"
    if failures:
        return "BLOCKED_CONTRACT"
    return "BLOCKED_REVIEW_REQUIRED" if has_changes else "REPRODUCED_CURRENT_RELEASE"


def review_package(candidate: Mapping[str, Any], release_diff: Mapping[str, Any]) -> dict[str, Any]:
    claims = _by_id(_require_mapping_list(candidate, "claims", "release"), "claim_id")
    affected: list[dict[str, Any]] = []
    for claim_id in release_diff.get("affected_claim_ids", []):
        claim = claims.get(str(claim_id))
        affected.append(
            {
                "claim_id": str(claim_id),
                "surfaces": list(claim.get("surfaces", [])) if claim else [],
                "review_status": "PENDING",
                "removed_from_candidate": claim is None,
            }
        )
    return {
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
    if attestation.get("stage_id") != stage_id:
        raise ValueError("Review attestation is not bound to this staged release")
    if attestation.get("release_id") != candidate.get("release_id"):
        raise ValueError("Review attestation release_id mismatch")
    if attestation.get("candidate_manifest_sha256") != candidate_manifest_sha256:
        raise ValueError("Review attestation candidate-manifest checksum mismatch")
    if not attestation.get("reviewer") or not attestation.get("reviewed_at"):
        raise ValueError("Review attestation requires reviewer and reviewed_at")
    for key in ("scientific_reviewed", "editorial_reviewed", "source_rights_reviewed"):
        if attestation.get(key) is not True:
            raise ValueError(f"Review attestation requires {key}=true")
    artifact_hashes = {
        str(row["artifact_id"]): str(row["sha256"])
        for row in _require_mapping_list(candidate, "artifacts", "release")
    }
    if attestation.get("artifact_sha256") != artifact_hashes:
        raise ValueError("Review attestation artifact hashes do not match the candidate release")
    expected_sources = sorted(str(v) for v in release_diff.get("changed_source_ids", []))
    expected_diagnostics = sorted(str(v) for v in release_diff.get("changed_diagnostic_ids", []))
    expected_claims = sorted(str(v) for v in release_diff.get("affected_claim_ids", []))
    for key, expected in (
        ("reviewed_source_ids", expected_sources),
        ("reviewed_diagnostic_ids", expected_diagnostics),
        ("reviewed_claim_ids", expected_claims),
    ):
        actual = attestation.get(key)
        if not isinstance(actual, list) or sorted(str(v) for v in actual) != expected:
            raise ValueError(f"Review attestation {key} does not exactly cover the staged changes")


def sanitized_public_manifest(candidate: Mapping[str, Any]) -> dict[str, Any]:
    public = json.loads(json.dumps(candidate))
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
