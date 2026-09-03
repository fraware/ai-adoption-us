"""Bind repository-derived Observatory evidence to the candidate RPS vintage.

The global Observatory candidate combines a private, live RPS component with
reviewed repository artifacts that were derived from RPS earlier in the research
pipeline. This module prevents those two evidence paths from silently referring
to different RPS vintages. Every repository artifact that declares an RPS source
must have exactly one registered binding, and every binding is checked before the
global candidate is composed.
"""

from __future__ import annotations

import json
import math
import os
import shutil
from collections.abc import Mapping
from copy import deepcopy
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path, PurePosixPath
from typing import Any

from genai_at_work.observatory_baseline import compose_v1_global_baseline
from genai_at_work.release_engine import (
    canonical_digest,
    load_json_object,
    validate_release_manifest,
)

BINDINGS_REPOSITORY_PATH = (
    "data/registry/observatory_v1_rps_repository_bindings.json"
)
BINDING_DIAGNOSTIC_ID = "global-rps-repository-source-binding"


class ObservatoryRpsBindingError(ValueError):
    """Raised when repository RPS evidence is not bound to the candidate vintage."""


def _rows(value: object, context: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not all(isinstance(row, Mapping) for row in value):
        raise ObservatoryRpsBindingError(f"{context} must be a list of objects")
    return [{str(key): item for key, item in row.items()} for row in value]


def _strings(value: object, context: str) -> list[str]:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise ObservatoryRpsBindingError(f"{context} must be a list of strings")
    if len(set(value)) != len(value):
        raise ObservatoryRpsBindingError(f"{context} contains duplicates")
    return list(value)


def _string(mapping: Mapping[str, Any], key: str, context: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ObservatoryRpsBindingError(f"{context}.{key} must be a non-empty string")
    return value


def _digest(value: object, context: str) -> str:
    if not isinstance(value, str):
        raise ObservatoryRpsBindingError(f"{context} must be a SHA-256 digest")
    normalized = value.removeprefix("sha256:").lower()
    if len(normalized) != 64:
        raise ObservatoryRpsBindingError(f"{context} must be a 64-character SHA-256 digest")
    try:
        int(normalized, 16)
    except ValueError as exc:
        raise ObservatoryRpsBindingError(f"{context} must be hexadecimal") from exc
    return normalized


def _nested_value(value: object, dotted_path: str, context: str) -> object:
    current = value
    for part in dotted_path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            raise ObservatoryRpsBindingError(
                f"{context} is missing registered field {dotted_path!r}"
            )
        current = current[part]
    return current


def _repo_path(repo_root: Path, relative: str) -> Path:
    posix = PurePosixPath(relative)
    if posix.is_absolute() or not posix.parts or ".." in posix.parts:
        raise ObservatoryRpsBindingError(f"Unsafe repository binding path: {relative!r}")
    root = repo_root.resolve()
    path = (root / Path(*posix.parts)).resolve()
    if root not in path.parents or not path.is_file():
        raise ObservatoryRpsBindingError(
            f"Registered repository binding file is unavailable: {relative}"
        )
    return path


def _candidate_input_path(candidate_root: Path, relative: str) -> Path:
    posix = PurePosixPath(relative)
    if (
        posix.is_absolute()
        or not posix.parts
        or posix.parts[0] != "inputs"
        or ".." in posix.parts
    ):
        raise ObservatoryRpsBindingError(f"Unsafe RPS candidate input path: {relative!r}")
    root = candidate_root.resolve()
    path = (root / Path(*posix.parts)).resolve()
    if root not in path.parents or not path.is_file():
        raise ObservatoryRpsBindingError(
            f"Registered RPS candidate input is unavailable: {relative}"
        )
    return path


def _rps_source(
    rps_candidate: Mapping[str, Any], source_id: str
) -> dict[str, Any]:
    sources = _rows(rps_candidate.get("sources"), "rps_candidate.sources")
    matches = [row for row in sources if row.get("source_id") == source_id]
    if len(matches) != 1:
        raise ObservatoryRpsBindingError(
            f"RPS candidate must contain exactly one source {source_id!r}"
        )
    return matches[0]


def _required_repository_artifacts(
    baseline_contract: Mapping[str, Any], source_id: str
) -> set[str]:
    required: set[str] = set()
    for index, artifact in enumerate(
        _rows(baseline_contract.get("repository_artifacts"), "repository_artifacts")
    ):
        context = f"repository_artifacts[{index}]"
        artifact_id = _string(artifact, "artifact_id", context)
        source_ids = _strings(artifact.get("source_ids"), f"{context}.source_ids")
        if source_id in source_ids:
            required.add(artifact_id)
    if not required:
        raise ObservatoryRpsBindingError(
            "Observatory baseline has no repository artifacts that depend on RPS"
        )
    return required


def _binding_artifact_inventory(bindings: Mapping[str, Any]) -> tuple[set[str], list[str]]:
    covered: set[str] = set()
    binding_ids: list[str] = []
    for family in ("source_vintage_bindings", "source_value_bindings"):
        for index, binding in enumerate(_rows(bindings.get(family), family)):
            context = f"{family}[{index}]"
            binding_id = _string(binding, "binding_id", context)
            if binding_id in binding_ids:
                raise ObservatoryRpsBindingError(
                    f"Duplicate RPS repository binding_id: {binding_id}"
                )
            binding_ids.append(binding_id)
            for artifact_id in _strings(
                binding.get("artifact_ids"), f"{context}.artifact_ids"
            ):
                if artifact_id in covered:
                    raise ObservatoryRpsBindingError(
                        f"RPS repository artifact has multiple bindings: {artifact_id}"
                    )
                covered.add(artifact_id)
    return covered, binding_ids


def _candidate_period_records(
    source: Mapping[str, Any],
    candidate_root: Path,
    *,
    period: str,
) -> list[dict[str, Any]]:
    objects = _rows(source.get("objects"), "rps_candidate.source.objects")
    matches: list[list[dict[str, Any]]] = []
    for index, source_object in enumerate(objects):
        context = f"rps_candidate.source.objects[{index}]"
        relative = _string(source_object, "local_path", context)
        payload = load_json_object(_candidate_input_path(candidate_root, relative))
        if payload.get("period") != period:
            continue
        rows = _rows(payload.get("records"), f"{context}.records")
        matches.append(rows)
    if len(matches) != 1:
        raise ObservatoryRpsBindingError(
            f"RPS candidate must contain exactly one source object for period {period}"
        )
    return matches[0]


def _finite_number(value: object, context: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ObservatoryRpsBindingError(f"{context} must be numeric")
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ObservatoryRpsBindingError(f"{context} must be finite")
    return numeric


def _decimal_number(value: object, context: str) -> Decimal:
    numeric = _finite_number(value, context)
    try:
        return Decimal(str(numeric))
    except InvalidOperation as exc:
        raise ObservatoryRpsBindingError(f"{context} is not a valid decimal") from exc


def _validate_value_binding(
    binding: Mapping[str, Any],
    *,
    repo_root: Path,
    candidate_root: Path,
    source: Mapping[str, Any],
) -> int:
    binding_id = _string(binding, "binding_id", "source_value_binding")
    repository_path = _string(
        binding, "repository_path", f"source_value_binding.{binding_id}"
    )
    candidate_period = _string(
        binding, "candidate_period", f"source_value_binding.{binding_id}"
    )
    checkpoint_period = _string(
        binding, "checkpoint_period", f"source_value_binding.{binding_id}"
    )
    entity_type = _string(
        binding, "entity_type", f"source_value_binding.{binding_id}"
    )
    metric_id = _string(binding, "metric_id", f"source_value_binding.{binding_id}")
    expected_rows = binding.get("expected_rows")
    if (
        not isinstance(expected_rows, int)
        or isinstance(expected_rows, bool)
        or expected_rows < 1
    ):
        raise ObservatoryRpsBindingError(
            f"source_value_binding.{binding_id}.expected_rows must be positive"
        )
    decimal_places = binding.get("checkpoint_decimal_places")
    if (
        not isinstance(decimal_places, int)
        or isinstance(decimal_places, bool)
        or not 0 <= decimal_places <= 12
    ):
        raise ObservatoryRpsBindingError(
            f"source_value_binding.{binding_id}.checkpoint_decimal_places must be an integer from 0 to 12"
        )
    quantum = Decimal(1).scaleb(-decimal_places)

    candidate_rows = [
        row
        for row in _candidate_period_records(
            source, candidate_root, period=candidate_period
        )
        if row.get("period") == candidate_period
        and row.get("entity_type") == entity_type
        and row.get("metric_id") == metric_id
    ]
    if len(candidate_rows) != expected_rows:
        raise ObservatoryRpsBindingError(
            f"RPS value binding {binding_id} expected {expected_rows} candidate rows, "
            f"observed {len(candidate_rows)}"
        )
    candidate_values: dict[str, Decimal] = {}
    for index, row in enumerate(candidate_rows):
        series_id = _string(row, "series_id", f"{binding_id}.candidate_rows[{index}]")
        if series_id in candidate_values:
            raise ObservatoryRpsBindingError(
                f"RPS value binding {binding_id} has duplicate candidate series {series_id}"
            )
        candidate_values[series_id] = _decimal_number(
            row.get("value"), f"{binding_id}.candidate_rows[{index}].value"
        )

    checkpoint = load_json_object(_repo_path(repo_root, repository_path))
    if checkpoint.get("period") != checkpoint_period:
        raise ObservatoryRpsBindingError(
            f"RPS value binding {binding_id} checkpoint period changed"
        )
    if checkpoint.get("metric_id") != metric_id:
        raise ObservatoryRpsBindingError(
            f"RPS value binding {binding_id} checkpoint metric changed"
        )
    checkpoint_rows = _rows(checkpoint.get("rows"), f"{binding_id}.checkpoint.rows")
    if len(checkpoint_rows) != expected_rows:
        raise ObservatoryRpsBindingError(
            f"RPS value binding {binding_id} expected {expected_rows} checkpoint rows, "
            f"observed {len(checkpoint_rows)}"
        )
    checkpoint_values: dict[str, Decimal] = {}
    for index, row in enumerate(checkpoint_rows):
        series_id = _string(row, "series_id", f"{binding_id}.checkpoint.rows[{index}]")
        if series_id in checkpoint_values:
            raise ObservatoryRpsBindingError(
                f"RPS value binding {binding_id} has duplicate checkpoint series {series_id}"
            )
        value = _decimal_number(
            row.get("value_pct"), f"{binding_id}.checkpoint.rows[{index}].value_pct"
        )
        quantized = value.quantize(quantum, rounding=ROUND_HALF_UP)
        if quantized != value:
            raise ObservatoryRpsBindingError(
                f"RPS value binding {binding_id} checkpoint series {series_id} exceeds declared precision"
            )
        checkpoint_values[series_id] = quantized

    if set(candidate_values) != set(checkpoint_values):
        raise ObservatoryRpsBindingError(
            f"RPS value binding {binding_id} series inventory changed"
        )
    mismatches = [
        series_id
        for series_id in sorted(candidate_values)
        if candidate_values[series_id].quantize(quantum, rounding=ROUND_HALF_UP)
        != checkpoint_values[series_id]
    ]
    if mismatches:
        raise ObservatoryRpsBindingError(
            f"RPS value binding {binding_id} changed for {len(mismatches)} series at {decimal_places} decimal places"
        )
    return decimal_places


def validate_rps_repository_bindings(
    rps_candidate: Mapping[str, Any],
    *,
    rps_candidate_root: Path,
    baseline_contract: Mapping[str, Any],
    bindings: Mapping[str, Any],
    repo_root: Path,
) -> dict[str, Any]:
    """Require exact RPS-vintage consistency for repository-derived evidence."""

    validate_release_manifest(rps_candidate, rps_candidate_root)
    if bindings.get("schema_version") != 1:
        raise ObservatoryRpsBindingError("RPS repository bindings schema_version must equal 1")
    binding_id = _string(bindings, "binding_id", "bindings")
    source_id = _string(bindings, "source_id", "bindings")

    source = _rps_source(rps_candidate, source_id)
    source_vintage = _string(source, "source_vintage_id", "rps_candidate.source")
    source_digest = _digest(source_vintage, "rps_candidate.source.source_vintage_id")

    required_artifacts = _required_repository_artifacts(baseline_contract, source_id)
    covered_artifacts, binding_ids = _binding_artifact_inventory(bindings)
    if covered_artifacts != required_artifacts:
        missing = sorted(required_artifacts - covered_artifacts)
        extra = sorted(covered_artifacts - required_artifacts)
        raise ObservatoryRpsBindingError(
            "RPS repository binding coverage must exactly match RPS-dependent baseline "
            f"artifacts; missing={missing}, extra={extra}"
        )

    for index, binding in enumerate(
        _rows(bindings.get("source_vintage_bindings"), "source_vintage_bindings")
    ):
        context = f"source_vintage_bindings[{index}]"
        registered_id = _string(binding, "binding_id", context)
        repository_path = _string(binding, "repository_path", context)
        digest_field = _string(binding, "digest_field", context)
        provenance = load_json_object(_repo_path(repo_root, repository_path))
        observed = _digest(
            _nested_value(provenance, digest_field, registered_id),
            f"{registered_id}.{digest_field}",
        )
        if observed != source_digest:
            raise ObservatoryRpsBindingError(
                f"RPS source vintage mismatch for repository binding {registered_id}"
            )

    value_binding_decimal_places: dict[str, int] = {}
    for binding in _rows(bindings.get("source_value_bindings"), "source_value_bindings"):
        registered_id = _string(binding, "binding_id", "source_value_binding")
        value_binding_decimal_places[registered_id] = _validate_value_binding(
            binding,
            repo_root=repo_root,
            candidate_root=rps_candidate_root,
            source=source,
        )

    canonical_bindings = load_json_object(
        _repo_path(repo_root, BINDINGS_REPOSITORY_PATH)
    )
    if canonical_digest(bindings) != canonical_digest(canonical_bindings):
        raise ObservatoryRpsBindingError(
            "RPS repository binding validation must use the exact repository-pinned registry"
        )

    return {
        "schema_version": 1,
        "binding_id": binding_id,
        "source_id": source_id,
        "source_vintage_id": f"sha256:{source_digest}",
        "status": "pass",
        "binding_ids": sorted(binding_ids),
        "covered_artifact_ids": sorted(covered_artifacts),
        "value_binding_decimal_places": value_binding_decimal_places,
    }


def _write_release_manifest(path: Path, candidate: Mapping[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def compose_v1_global_baseline_bound(
    *,
    rps_candidate_root: Path,
    output_dir: Path,
    contract: Mapping[str, Any],
    bindings: Mapping[str, Any],
    repo_root: Path,
    release_id: str,
    builder_commit: str,
    previous_release: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Compose a global candidate only after RPS-dependent evidence is vintage-bound."""

    rps_manifest_path = rps_candidate_root / "release.json"
    if not rps_manifest_path.is_file():
        raise ObservatoryRpsBindingError(
            f"RPS component candidate has no release.json: {rps_candidate_root}"
        )
    rps_candidate = load_json_object(rps_manifest_path)
    binding_summary = validate_rps_repository_bindings(
        rps_candidate,
        rps_candidate_root=rps_candidate_root,
        baseline_contract=contract,
        bindings=bindings,
        repo_root=repo_root,
    )

    candidate = compose_v1_global_baseline(
        rps_candidate_root=rps_candidate_root,
        output_dir=output_dir,
        contract=contract,
        repo_root=repo_root,
        release_id=release_id,
        builder_commit=builder_commit,
        previous_release=previous_release,
    )
    try:
        enriched = deepcopy(candidate)
        diagnostics = enriched.get("diagnostics")
        component_builds = enriched.get("component_builds")
        if not isinstance(diagnostics, list) or not isinstance(component_builds, dict):
            raise ObservatoryRpsBindingError(
                "Global candidate is missing diagnostics or component_builds"
            )
        if any(
            isinstance(row, Mapping)
            and row.get("diagnostic_id") == BINDING_DIAGNOSTIC_ID
            for row in diagnostics
        ):
            raise ObservatoryRpsBindingError(
                f"Global candidate already contains diagnostic {BINDING_DIAGNOSTIC_ID}"
            )
        diagnostics.append(
            {
                "diagnostic_id": BINDING_DIAGNOSTIC_ID,
                "diagnostic_class": "regression_contract",
                "status": "pass",
                "value_digest": canonical_digest(binding_summary),
            }
        )
        component_builds["rps_repository_bindings"] = {
            "repository_path": BINDINGS_REPOSITORY_PATH,
            "binding_id": binding_summary["binding_id"],
            "canonical_digest": canonical_digest(bindings),
            "status": "pass",
            "source_vintage_id": binding_summary["source_vintage_id"],
        }
        _write_release_manifest(output_dir / "release.json", enriched)
        validate_release_manifest(enriched, output_dir)
    except Exception:
        if output_dir.exists():
            shutil.rmtree(output_dir)
        raise
    return enriched
