"""Compose the complete Observatory v1 baseline from reviewed component evidence.

The RPS component is supplied as a private release-engine candidate because its
``inputs/`` namespace contains authorized published aggregate source observations
that must never be committed to the public repository. CPS, OEWS, and BTOS source
identities and derived evidence are rights-safe, versioned repository artifacts.

This module only composes a candidate. It never stages, attests, or promotes one.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path, PurePosixPath
from typing import Any

from genai_at_work.release_engine import (
    canonical_digest,
    load_json_object,
    sha256_file,
    validate_release_manifest,
)

V1_CONTRACT_REPOSITORY_PATH = "data/registry/observatory_v1_baseline_contract.json"

REQUIRED_COMPONENTS = {
    "rps_longitudinal",
    "cps_composition",
    "oews_robustness",
    "btos_triangulation",
}
REQUIRED_RPS_ARTIFACT_IDS = {
    "rps-longitudinal-diagnostics",
    "rps-quarter-diagnostics",
    "rps-rank-stability",
    "rps-longitudinal-validation",
}
REQUIRED_RPS_BUILDER_ID = "rps-published-aggregate-construct-window-release-v3"
REQUIRED_RPS_METRICS = {
    "adoption_work",
    "assisted_hours_share",
    "reported_time_savings_share",
}
REQUIRED_GLOBAL_GATE_IDS = {
    "cps-q2-2025-composition",
    "cps-q2-2026-composition",
    "cps-residual-contract",
    "oews-robustness-contract",
    "btos-cross-construct-governance",
    "cps-q4-2025-explicit-unavailability",
}
REQUIRED_GLOBAL_CLAIM_IDS = {
    "global-cps-q4-2025-unavailable",
    "global-industry-context-residual-descriptive-only",
    "global-oews-composition-robustness",
    "global-btos-rps-cross-construct-concordance",
    "global-cps-composition-design-interval-unsupported",
}
_ALLOWED_DIAGNOSTIC_CLASSES = {
    "stability",
    "influence",
    "regression_contract",
    "suppression_coverage",
}
_RELEASE_ID_RE = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")
_OBJECT_ID_RE = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")
_COMMIT_RE = re.compile(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}")


class ObservatoryBaselineError(ValueError):
    """Raised when the v1 global-baseline contract cannot be satisfied."""


def _mapping(value: object, context: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ObservatoryBaselineError(f"{context} must be an object")
    return {str(key): item for key, item in value.items()}


def _rows(value: object, context: str) -> list[dict[str, Any]]:
    if (
        not isinstance(value, list)
        or not value
        or not all(isinstance(item, Mapping) for item in value)
    ):
        raise ObservatoryBaselineError(f"{context} must be a non-empty list of objects")
    return [{str(key): item for key, item in row.items()} for row in value]


def _strings(value: object, context: str) -> list[str]:
    if (
        not isinstance(value, list)
        or not value
        or not all(isinstance(item, str) and item for item in value)
    ):
        raise ObservatoryBaselineError(f"{context} must be a non-empty list of strings")
    if len(set(value)) != len(value):
        raise ObservatoryBaselineError(f"{context} contains duplicates")
    return list(value)


def _string(mapping: Mapping[str, Any], key: str, context: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ObservatoryBaselineError(f"{context}.{key} must be a non-empty string")
    return value


def _repo_path(repo_root: Path, relative: str) -> Path:
    posix = PurePosixPath(relative)
    if posix.is_absolute() or not posix.parts or ".." in posix.parts:
        raise ObservatoryBaselineError(
            f"Unsafe repository path in baseline contract: {relative!r}"
        )
    root = repo_root.resolve()
    path = (root / Path(*posix.parts)).resolve()
    if root not in path.parents:
        raise ObservatoryBaselineError(
            f"Repository path escapes project root: {relative!r}"
        )
    if not path.is_file():
        raise ObservatoryBaselineError(
            f"Required baseline file does not exist: {relative}"
        )
    return path


def _nested_value(value: object, dotted_path: str) -> object:
    current = value
    for part in dotted_path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            raise ObservatoryBaselineError(
                f"Validation field is missing: {dotted_path}"
            )
        current = current[part]
    return current


def _copy_exact(source: Path, destination: Path) -> tuple[str, int]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise ObservatoryBaselineError(f"Candidate path already exists: {destination}")
    shutil.copyfile(source, destination)
    return sha256_file(destination), destination.stat().st_size


def _repository_locator(builder_commit: str, repository_path: str) -> str:
    return (
        "https://raw.githubusercontent.com/fraware/ai-adoption-us/"
        f"{builder_commit}/{repository_path}"
    )


def _source_by_id(
    release: Mapping[str, Any], source_id: str
) -> Mapping[str, Any] | None:
    raw_sources = release.get("sources")
    if not isinstance(raw_sources, list):
        return None
    for source in raw_sources:
        if isinstance(source, Mapping) and source.get("source_id") == source_id:
            return source
    return None


def _artifact_hashes(release: Mapping[str, Any]) -> dict[str, str]:
    raw_artifacts = release.get("artifacts")
    if not isinstance(raw_artifacts, list):
        return {}
    return {
        str(row["artifact_id"]): str(row["sha256"])
        for row in raw_artifacts
        if isinstance(row, Mapping)
        and isinstance(row.get("artifact_id"), str)
        and isinstance(row.get("sha256"), str)
    }


def _object_hashes(source: Mapping[str, Any]) -> dict[str, str]:
    raw_objects = source.get("objects")
    if not isinstance(raw_objects, list):
        return {}
    return {
        str(row["object_id"]): str(row["sha256"])
        for row in raw_objects
        if isinstance(row, Mapping)
        and isinstance(row.get("object_id"), str)
        and isinstance(row.get("sha256"), str)
    }


def _source_revision_status(
    previous_release: Mapping[str, Any] | None,
    *,
    source_id: str,
    reference_periods: Sequence[str],
    objects: Sequence[Mapping[str, Any]],
) -> str:
    if previous_release is None:
        return "new_wave"
    previous = _source_by_id(previous_release, source_id)
    if previous is None:
        return "new_wave"

    old_periods = {str(item) for item in previous.get("reference_periods", [])}
    new_periods = {str(item) for item in reference_periods}
    old_objects = _object_hashes(previous)
    new_objects = {
        str(row["object_id"]): str(row["sha256"])
        for row in objects
        if isinstance(row.get("object_id"), str)
        and isinstance(row.get("sha256"), str)
    }

    added_periods = new_periods - old_periods
    removed_periods = old_periods - new_periods
    added_objects = new_objects.keys() - old_objects.keys()
    removed_objects = old_objects.keys() - new_objects.keys()
    modified_objects = {
        object_id
        for object_id in old_objects.keys() & new_objects.keys()
        if old_objects[object_id] != new_objects[object_id]
    }
    has_new_wave = bool(added_periods)
    has_revision = bool(
        removed_periods
        or removed_objects
        or modified_objects
        or (added_objects and not added_periods)
    )
    if has_new_wave and has_revision:
        return "mixed"
    if has_new_wave:
        return "new_wave"
    if has_revision:
        return "revision"
    return "unchanged"


def _release_type(
    previous_release: Mapping[str, Any] | None,
    *,
    sources: Sequence[Mapping[str, Any]],
    artifacts: Sequence[Mapping[str, Any]],
) -> str:
    if previous_release is None:
        return "baseline"
    statuses = {str(source["revision_status"]) for source in sources}
    has_new_wave = bool(statuses & {"new_wave", "mixed"})
    has_revision = bool(statuses & {"revision", "mixed"})
    previous_hashes = _artifact_hashes(previous_release)
    current_hashes = {
        str(row["artifact_id"]): str(row["sha256"]) for row in artifacts
    }
    has_derived_change = previous_hashes != current_hashes
    if (has_new_wave and has_revision) or "mixed" in statuses:
        return "mixed"
    if has_new_wave:
        return "new_wave"
    if has_revision or has_derived_change:
        return "revision"
    # A reproduced candidate still needs a schema-valid release type. The generic
    # diff classifies it as REPRODUCED_CURRENT_RELEASE because no content changed.
    return "revision"


def _verify_repository_builder_state(repo_root: Path, builder_commit: str) -> None:
    """Bind repository evidence bytes to a clean checkout of ``builder_commit``."""

    try:
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except subprocess.CalledProcessError as exc:
        raise ObservatoryBaselineError(
            "Could not verify repository state for global baseline composition"
        ) from exc
    if status.strip():
        raise ObservatoryBaselineError(
            "Refusing to compose a global baseline from a dirty repository checkout"
        )
    if head.lower() != builder_commit.lower():
        raise ObservatoryBaselineError(
            "builder_commit must equal the clean repository HEAD used for evidence bytes"
        )


def validate_v1_baseline_contract(
    contract: Mapping[str, Any], repo_root: Path
) -> None:
    """Validate the static v1 composition contract and repository evidence gates."""

    if contract.get("schema_version") != 1:
        raise ObservatoryBaselineError("baseline contract schema_version must equal 1")
    _string(contract, "contract_id", "contract")
    if contract.get("data_mode") != "derived_only":
        raise ObservatoryBaselineError(
            "Observatory v1 baseline must use data_mode=derived_only"
        )

    required_components = set(
        _strings(contract.get("required_components"), "required_components")
    )
    if required_components != REQUIRED_COMPONENTS:
        raise ObservatoryBaselineError(
            "Observatory v1 must require exactly RPS longitudinal, CPS composition, "
            "OEWS robustness, and BTOS triangulation components"
        )

    rps = _mapping(contract.get("rps_component"), "rps_component")
    if rps.get("component_id") != "rps_longitudinal":
        raise ObservatoryBaselineError(
            "rps_component.component_id must equal rps_longitudinal"
        )
    rps_source_id = _string(rps, "source_id", "rps_component")
    required_rps_artifacts = set(
        _strings(
            rps.get("required_artifact_ids"),
            "rps_component.required_artifact_ids",
        )
    )
    if required_rps_artifacts != REQUIRED_RPS_ARTIFACT_IDS:
        raise ObservatoryBaselineError(
            "RPS component must require the complete v3 longitudinal artifact set"
        )
    if rps.get("require_claims") is not True:
        raise ObservatoryBaselineError("RPS component must require claim traceability")
    if rps.get("require_source_input_bytes_publication_false") is not True:
        raise ObservatoryBaselineError(
            "RPS component must preserve the private source-byte boundary"
        )

    repository_sources = _rows(
        contract.get("repository_sources"), "repository_sources"
    )
    component_ids = {str(row.get("component_id")) for row in repository_sources}
    if component_ids != REQUIRED_COMPONENTS - {"rps_longitudinal"}:
        raise ObservatoryBaselineError(
            "Repository source contracts must cover CPS, OEWS, and BTOS exactly"
        )
    source_ids = {rps_source_id}
    for index, source in enumerate(repository_sources):
        context = f"repository_sources[{index}]"
        source_id = _string(source, "source_id", context)
        if source_id in source_ids:
            raise ObservatoryBaselineError(
                f"Duplicate baseline source_id: {source_id}"
            )
        source_ids.add(source_id)
        for key in (
            "provider",
            "dataset",
            "retrieved_at",
            "instrument_version",
            "definition_id",
        ):
            _string(source, key, context)
        _strings(source.get("reference_periods"), f"{context}.reference_periods")
        taxonomy = _mapping(
            source.get("taxonomy_versions"), f"{context}.taxonomy_versions"
        )
        if not taxonomy or not all(
            isinstance(key, str)
            and key
            and isinstance(value, str)
            and value
            for key, value in taxonomy.items()
        ):
            raise ObservatoryBaselineError(
                f"{context}.taxonomy_versions is invalid"
            )
        rights = _mapping(source.get("rights"), f"{context}.rights")
        if rights != {
            "status": "approved",
            "storage_scope": "public",
            "publication_scope": "derived_only",
            "redistribution_scope": "derived_only",
        }:
            raise ObservatoryBaselineError(
                f"{context}.rights must keep repository source evidence public "
                "but publication/redistribution derived-only"
            )
        coverage = _mapping(source.get("coverage"), f"{context}.coverage")
        required = coverage.get("required_units")
        observed = coverage.get("observed_units")
        if (
            coverage.get("status") != "pass"
            or not isinstance(required, int)
            or isinstance(required, bool)
            or required < 1
            or not isinstance(observed, int)
            or isinstance(observed, bool)
            or observed < required
        ):
            raise ObservatoryBaselineError(
                f"{context}.coverage must be complete and passing"
            )
        seen_objects: set[str] = set()
        for object_index, source_object in enumerate(
            _rows(source.get("objects"), f"{context}.objects")
        ):
            object_context = f"{context}.objects[{object_index}]"
            object_id = _string(source_object, "object_id", object_context)
            if _OBJECT_ID_RE.fullmatch(object_id) is None:
                raise ObservatoryBaselineError(
                    f"Unsafe source object_id: {object_id!r}"
                )
            if object_id in seen_objects:
                raise ObservatoryBaselineError(
                    f"Duplicate source object_id in {source_id}: {object_id}"
                )
            seen_objects.add(object_id)
            repository_path = _string(
                source_object, "repository_path", object_context
            )
            _repo_path(repo_root, repository_path)

    repository_artifacts = _rows(
        contract.get("repository_artifacts"), "repository_artifacts"
    )
    artifact_ids: set[str] = set(REQUIRED_RPS_ARTIFACT_IDS)
    artifact_components: set[str] = set()
    for index, artifact in enumerate(repository_artifacts):
        context = f"repository_artifacts[{index}]"
        artifact_id = _string(artifact, "artifact_id", context)
        if artifact_id in artifact_ids:
            raise ObservatoryBaselineError(
                f"Duplicate baseline artifact_id: {artifact_id}"
            )
        artifact_ids.add(artifact_id)
        component_id = _string(artifact, "component_id", context)
        if component_id not in REQUIRED_COMPONENTS - {"rps_longitudinal"}:
            raise ObservatoryBaselineError(
                f"Unknown repository artifact component: {component_id}"
            )
        artifact_components.add(component_id)
        repository_path = _string(artifact, "repository_path", context)
        _repo_path(repo_root, repository_path)
        evidence_class = artifact.get("evidence_class")
        if (
            not isinstance(evidence_class, int)
            or isinstance(evidence_class, bool)
            or evidence_class not in range(1, 6)
        ):
            raise ObservatoryBaselineError(
                f"{context}.evidence_class must be 1..5"
            )
        unknown_sources = (
            set(
                _strings(
                    artifact.get("source_ids"),
                    f"{context}.source_ids",
                )
            )
            - source_ids
        )
        if unknown_sources:
            raise ObservatoryBaselineError(
                f"{context} references unknown sources: {sorted(unknown_sources)}"
            )
    if artifact_components != REQUIRED_COMPONENTS - {"rps_longitudinal"}:
        raise ObservatoryBaselineError(
            "Every non-RPS v1 component must contribute release artifacts"
        )

    gates = _rows(contract.get("validation_gates"), "validation_gates")
    gate_ids: set[str] = set()
    for index, gate in enumerate(gates):
        context = f"validation_gates[{index}]"
        gate_id = _string(gate, "gate_id", context)
        if gate_id in gate_ids:
            raise ObservatoryBaselineError(
                f"Duplicate validation gate_id: {gate_id}"
            )
        gate_ids.add(gate_id)
        diagnostic_class = _string(gate, "diagnostic_class", context)
        if diagnostic_class not in _ALLOWED_DIAGNOSTIC_CLASSES:
            raise ObservatoryBaselineError(
                f"Unsupported diagnostic class: {diagnostic_class}"
            )
        repository_path = _string(gate, "repository_path", context)
        path = _repo_path(repo_root, repository_path)
        payload = load_json_object(path)
        expected = _mapping(gate.get("expected"), f"{context}.expected")
        if not expected:
            raise ObservatoryBaselineError(
                f"{context}.expected must not be empty"
            )
        for dotted_path, expected_value in expected.items():
            actual = _nested_value(payload, dotted_path)
            if actual != expected_value:
                raise ObservatoryBaselineError(
                    f"Validation gate {gate_id} failed at {dotted_path}: "
                    f"expected {expected_value!r}, observed {actual!r}"
                )
    if gate_ids != REQUIRED_GLOBAL_GATE_IDS:
        raise ObservatoryBaselineError(
            "V1 validation gate inventory does not match the required scientific gates"
        )

    claims = _rows(contract.get("global_claims"), "global_claims")
    claim_ids: set[str] = set()
    for index, claim in enumerate(claims):
        context = f"global_claims[{index}]"
        claim_id = _string(claim, "claim_id", context)
        if claim_id in claim_ids:
            raise ObservatoryBaselineError(
                f"Duplicate global claim_id: {claim_id}"
            )
        claim_ids.add(claim_id)
        _strings(claim.get("surfaces"), f"{context}.surfaces")
        references = set(
            _strings(claim.get("artifact_ids"), f"{context}.artifact_ids")
        )
        unknown_artifacts = references - artifact_ids
        if unknown_artifacts:
            raise ObservatoryBaselineError(
                f"{context} references unknown artifacts: {sorted(unknown_artifacts)}"
            )
        _string(claim, "value_summary", context)
        _string(claim, "truth_state", context)
        _string(claim, "interpretation_boundary", context)
        evidence_class = claim.get("evidence_class")
        if (
            not isinstance(evidence_class, int)
            or isinstance(evidence_class, bool)
            or evidence_class not in range(1, 6)
        ):
            raise ObservatoryBaselineError(
                f"{context}.evidence_class must be 1..5"
            )
    if claim_ids != REQUIRED_GLOBAL_CLAIM_IDS:
        raise ObservatoryBaselineError(
            "V1 global claim inventory does not match the required construct boundaries"
        )

    canonical_contract = load_json_object(
        _repo_path(repo_root, V1_CONTRACT_REPOSITORY_PATH)
    )
    if canonical_digest(contract) != canonical_digest(canonical_contract):
        raise ObservatoryBaselineError(
            "V1 composition must use the exact repository-pinned baseline contract"
        )


def _validate_rps_component(
    rps_candidate: Mapping[str, Any],
    rps_root: Path,
    contract: Mapping[str, Any],
) -> None:
    """Require the actual complete-history RPS v3 component, not a name-compatible stub."""

    validate_release_manifest(rps_candidate, rps_root)
    if rps_candidate.get("data_mode") != "derived_only":
        raise ObservatoryBaselineError("RPS component must use derived_only data mode")

    build = _mapping(rps_candidate.get("build"), "rps_candidate.build")
    if build.get("builder_id") != REQUIRED_RPS_BUILDER_ID:
        raise ObservatoryBaselineError(
            f"RPS component builder_id must equal {REQUIRED_RPS_BUILDER_ID!r}"
        )

    rps_contract = _mapping(contract.get("rps_component"), "rps_component")
    source_id = _string(rps_contract, "source_id", "rps_component")
    sources = rps_candidate.get("sources")
    if (
        not isinstance(sources, list)
        or len(sources) != 1
        or not isinstance(sources[0], Mapping)
    ):
        raise ObservatoryBaselineError(
            "Global v1 composer requires exactly one RPS source component"
        )
    source = sources[0]
    if source.get("source_id") != source_id:
        raise ObservatoryBaselineError(
            "RPS candidate source_id does not match the v1 contract"
        )

    coverage = _mapping(source.get("coverage"), "rps_candidate.source.coverage")
    if (
        coverage.get("status") != "pass"
        or coverage.get("subgroup_series_count") != 126
        or coverage.get("national_series_count") != 5
    ):
        raise ObservatoryBaselineError(
            "RPS component must bind all 126 subgroup and five national source series"
        )
    required_units = coverage.get("required_units")
    observed_units = coverage.get("observed_units")
    full_source_units = coverage.get("full_source_observed_units")
    if (
        not isinstance(required_units, int)
        or isinstance(required_units, bool)
        or required_units < 1
        or observed_units != required_units
        or not isinstance(full_source_units, int)
        or isinstance(full_source_units, bool)
        or full_source_units < required_units
    ):
        raise ObservatoryBaselineError(
            "RPS component analytical and full-source coverage is incomplete"
        )

    analysis_periods = _strings(
        source.get("analysis_reference_periods"),
        "rps_candidate.source.analysis_reference_periods",
    )
    metric_periods = _mapping(
        source.get("analysis_metric_reference_periods"),
        "rps_candidate.source.analysis_metric_reference_periods",
    )
    if set(metric_periods) != REQUIRED_RPS_METRICS:
        raise ObservatoryBaselineError(
            "RPS component must bind the complete A/H/S construct family"
        )
    common = set(analysis_periods)
    for metric_id in REQUIRED_RPS_METRICS:
        periods = _strings(
            metric_periods.get(metric_id),
            f"rps_candidate.source.analysis_metric_reference_periods.{metric_id}",
        )
        common.intersection_update(periods)
    if common != set(analysis_periods):
        raise ObservatoryBaselineError(
            "RPS analysis_reference_periods must equal the common A/H/S complete window"
        )

    required_artifacts = set(
        _strings(
            rps_contract.get("required_artifact_ids"),
            "rps_component.required_artifact_ids",
        )
    )
    actual_artifacts = {
        str(row.get("artifact_id"))
        for row in rps_candidate.get("artifacts", [])
        if isinstance(row, Mapping)
    }
    if actual_artifacts != required_artifacts:
        raise ObservatoryBaselineError(
            "RPS v1 component artifact inventory must exactly match the reviewed v3 set"
        )
    if rps_contract.get("require_claims") is True:
        claims = rps_candidate.get("claims")
        if not isinstance(claims, list) or not claims:
            raise ObservatoryBaselineError(
                "RPS candidate has no traceable claims"
            )
    if (
        rps_contract.get("require_source_input_bytes_publication_false") is True
        and rps_candidate.get("source_input_bytes_publication") is not False
    ):
        raise ObservatoryBaselineError(
            "RPS candidate does not preserve the private source-byte boundary"
        )


def _compose_into(
    *,
    rps_candidate_root: Path,
    output_dir: Path,
    contract: Mapping[str, Any],
    repo_root: Path,
    release_id: str,
    builder_commit: str,
    previous_release: Mapping[str, Any] | None,
) -> dict[str, Any]:
    rps_manifest_path = rps_candidate_root / "release.json"
    if not rps_manifest_path.is_file():
        raise ObservatoryBaselineError(
            f"RPS component candidate has no release.json: {rps_candidate_root}"
        )
    rps_candidate = load_json_object(rps_manifest_path)
    _validate_rps_component(rps_candidate, rps_candidate_root, contract)

    sources: list[dict[str, Any]] = []
    artifacts: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    claims: list[dict[str, Any]] = []

    for raw_source in rps_candidate["sources"]:
        source = deepcopy(raw_source)
        for source_object in source["objects"]:
            relative = str(source_object["local_path"])
            source_path = rps_candidate_root / relative
            destination = output_dir / relative
            observed_sha, observed_size = _copy_exact(source_path, destination)
            if (
                observed_sha != source_object["sha256"]
                or observed_size != source_object["size_bytes"]
            ):
                raise ObservatoryBaselineError(
                    f"RPS source object changed during global composition: {relative}"
                )
        source["revision_status"] = _source_revision_status(
            previous_release,
            source_id=str(source["source_id"]),
            reference_periods=[str(value) for value in source["reference_periods"]],
            objects=source["objects"],
        )
        sources.append(source)

    for raw_artifact in rps_candidate["artifacts"]:
        artifact = deepcopy(raw_artifact)
        relative = str(artifact["path"])
        source_path = rps_candidate_root / relative
        destination = output_dir / relative
        observed_sha, observed_size = _copy_exact(source_path, destination)
        if (
            observed_sha != artifact["sha256"]
            or observed_size != artifact["size_bytes"]
        ):
            raise ObservatoryBaselineError(
                f"RPS artifact changed during global composition: {relative}"
            )
        artifacts.append(artifact)
    diagnostics.extend(deepcopy(rps_candidate["diagnostics"]))
    claims.extend(deepcopy(rps_candidate["claims"]))

    repository_sources = _rows(
        contract.get("repository_sources"), "repository_sources"
    )
    for source_spec in repository_sources:
        source_id = str(source_spec["source_id"])
        reference_periods = [
            str(item) for item in source_spec["reference_periods"]
        ]
        source_objects: list[dict[str, Any]] = []
        for object_spec in source_spec["objects"]:
            object_id = str(object_spec["object_id"])
            repository_path = str(object_spec["repository_path"])
            source_path = _repo_path(repo_root, repository_path)
            suffix = source_path.suffix or ".bin"
            relative = f"inputs/{source_id}/{object_id}{suffix}"
            sha256, size = _copy_exact(source_path, output_dir / relative)
            source_objects.append(
                {
                    "object_id": object_id,
                    "locator": _repository_locator(
                        builder_commit.lower(), repository_path
                    ),
                    "local_path": relative,
                    "sha256": sha256,
                    "size_bytes": size,
                }
            )
        source_vintage_id = "sha256:" + canonical_digest(
            {
                "source_id": source_id,
                "reference_periods": reference_periods,
                "definition_id": source_spec["definition_id"],
                "taxonomy_versions": source_spec["taxonomy_versions"],
                "objects": [
                    {
                        "object_id": row["object_id"],
                        "sha256": row["sha256"],
                    }
                    for row in source_objects
                ],
            }
        )
        sources.append(
            {
                "source_id": source_id,
                "provider": source_spec["provider"],
                "dataset": source_spec["dataset"],
                "source_vintage_id": source_vintage_id,
                "retrieved_at": source_spec["retrieved_at"],
                "revision_status": _source_revision_status(
                    previous_release,
                    source_id=source_id,
                    reference_periods=reference_periods,
                    objects=source_objects,
                ),
                "reference_periods": reference_periods,
                "instrument_version": source_spec["instrument_version"],
                "definition_id": source_spec["definition_id"],
                "taxonomy_versions": deepcopy(
                    source_spec["taxonomy_versions"]
                ),
                "rights": deepcopy(source_spec["rights"]),
                "coverage": deepcopy(source_spec["coverage"]),
                "objects": source_objects,
            }
        )

    for artifact_spec in _rows(
        contract.get("repository_artifacts"), "repository_artifacts"
    ):
        artifact_id = str(artifact_spec["artifact_id"])
        repository_path = str(artifact_spec["repository_path"])
        source_path = _repo_path(repo_root, repository_path)
        suffix = source_path.suffix or ".bin"
        relative = (
            f"artifacts/{artifact_spec['component_id']}/"
            f"{artifact_id}{suffix}"
        )
        sha256, size = _copy_exact(source_path, output_dir / relative)
        artifacts.append(
            {
                "artifact_id": artifact_id,
                "path": relative,
                "sha256": sha256,
                "size_bytes": size,
                "evidence_class": artifact_spec["evidence_class"],
                "source_ids": list(artifact_spec["source_ids"]),
            }
        )

    artifact_hashes = {
        str(row["artifact_id"]): str(row["sha256"]) for row in artifacts
    }
    for gate in _rows(contract.get("validation_gates"), "validation_gates"):
        repository_path = str(gate["repository_path"])
        gate_sha = sha256_file(_repo_path(repo_root, repository_path))
        diagnostics.append(
            {
                "diagnostic_id": f"global-{gate['gate_id']}",
                "diagnostic_class": gate["diagnostic_class"],
                "status": "pass",
                "value_digest": canonical_digest(
                    {
                        "gate_id": gate["gate_id"],
                        "repository_path": repository_path,
                        "sha256": gate_sha,
                        "expected": gate["expected"],
                    }
                ),
            }
        )

    existing_claim_ids = {str(row["claim_id"]) for row in claims}
    for claim_spec in _rows(contract.get("global_claims"), "global_claims"):
        claim_id = str(claim_spec["claim_id"])
        if claim_id in existing_claim_ids:
            raise ObservatoryBaselineError(
                f"Global claim collides with RPS claim: {claim_id}"
            )
        references = [str(item) for item in claim_spec["artifact_ids"]]
        claim_artifact_hashes = {
            artifact_id: artifact_hashes[artifact_id]
            for artifact_id in references
        }
        claims.append(
            {
                "claim_id": claim_id,
                "surfaces": list(claim_spec["surfaces"]),
                "artifact_ids": references,
                "value_digest": canonical_digest(
                    {
                        "value_summary": claim_spec["value_summary"],
                        "truth_state": claim_spec["truth_state"],
                        "artifact_sha256": claim_artifact_hashes,
                    }
                ),
                "value_summary": claim_spec["value_summary"],
                "truth_state": claim_spec["truth_state"],
                "evidence_class": claim_spec["evidence_class"],
                "interpretation_boundary": claim_spec[
                    "interpretation_boundary"
                ],
            }
        )
        existing_claim_ids.add(claim_id)

    release_type = _release_type(
        previous_release, sources=sources, artifacts=artifacts
    )
    supersedes_release_id = (
        previous_release.get("release_id")
        if previous_release is not None
        else None
    )
    if supersedes_release_id is not None and (
        not isinstance(supersedes_release_id, str)
        or not supersedes_release_id
    ):
        raise ObservatoryBaselineError(
            "Previous global release has an invalid release_id"
        )

    input_sha256 = {
        f"{source['source_id']}:{source_object['object_id']}": source_object[
            "sha256"
        ]
        for source in sources
        for source_object in source["objects"]
    }
    output_sha256 = {
        str(artifact["artifact_id"]): str(artifact["sha256"])
        for artifact in artifacts
    }
    candidate = {
        "schema_version": 1,
        "release_id": release_id,
        "release_type": release_type,
        "data_mode": "derived_only",
        "created_at": str(rps_candidate["created_at"]),
        "supersedes_release_id": supersedes_release_id,
        "sources": sources,
        "artifacts": artifacts,
        "diagnostics": diagnostics,
        "claims": claims,
        "build": {
            "builder_id": "observatory-v1-global-baseline-composer-v1",
            "builder_commit": builder_commit.lower(),
            "deterministic": True,
            "input_sha256": input_sha256,
            "output_sha256": output_sha256,
        },
        "component_builds": {
            "rps": {
                "builder_id": rps_candidate["build"]["builder_id"],
                "builder_commit": rps_candidate["build"]["builder_commit"],
            },
            "baseline_contract": {
                "repository_path": V1_CONTRACT_REPOSITORY_PATH,
                "canonical_digest": canonical_digest(contract),
                "file_sha256": sha256_file(
                    _repo_path(repo_root, V1_CONTRACT_REPOSITORY_PATH)
                ),
            },
        },
        "baseline_contract_id": contract["contract_id"],
        "candidate_scope": (
            "Complete Observatory v1 candidate: RPS longitudinal evidence, CPS "
            "composition and occupation-adjusted descriptive residuals, OEWS "
            "composition robustness, and BTOS cross-construct industry "
            "triangulation. Unsupported CPS design-based composition inference "
            "remains fail-closed. Promotion still requires exact-candidate "
            "scientific, editorial, source-rights, and CI review."
        ),
        "source_input_bytes_publication": False,
    }
    release_path = output_dir / "release.json"
    release_path.write_text(
        json.dumps(candidate, indent=2, sort_keys=True) + "\n"
    )
    validate_release_manifest(candidate, output_dir)
    return candidate


def compose_v1_global_baseline(
    *,
    rps_candidate_root: Path,
    output_dir: Path,
    contract: Mapping[str, Any],
    repo_root: Path,
    release_id: str,
    builder_commit: str,
    previous_release: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Compose and atomically validate a complete Observatory v1 candidate."""

    validate_v1_baseline_contract(contract, repo_root)
    if _RELEASE_ID_RE.fullmatch(release_id) is None:
        raise ObservatoryBaselineError(
            "release_id must be a lowercase immutable release slug"
        )
    if _COMMIT_RE.fullmatch(builder_commit) is None:
        raise ObservatoryBaselineError(
            "builder_commit must be a 40- or 64-character Git SHA"
        )
    _verify_repository_builder_state(repo_root, builder_commit)

    if output_dir.exists():
        raise ObservatoryBaselineError(
            f"Global candidate output directory must not already exist: {output_dir}"
        )
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_dir.with_name(f".{output_dir.name}.tmp")
    if temporary.exists():
        raise ObservatoryBaselineError(
            f"Stale temporary candidate directory exists: {temporary}"
        )
    temporary.mkdir()

    try:
        candidate = _compose_into(
            rps_candidate_root=rps_candidate_root,
            output_dir=temporary,
            contract=contract,
            repo_root=repo_root,
            release_id=release_id,
            builder_commit=builder_commit,
            previous_release=previous_release,
        )
        os.replace(temporary, output_dir)
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise
    return candidate
