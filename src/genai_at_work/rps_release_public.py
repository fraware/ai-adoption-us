"""Compose the RPS observatory component with its bounded public observation view.

The existing complete-history builder remains the validated source/longitudinal
kernel. This adapter adds the rights-bounded public observation artifact and
upgrades the component builder identity without changing the private source
history or longitudinal estimands.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from genai_at_work.rps_public_view import build_rps_public_observation_view
from genai_at_work.rps_release import _write_json
from genai_at_work.rps_release_complete import (
    build_rps_release_candidate_complete_history,
    prepare_rps_source_history,
)

PUBLIC_VIEW_ARTIFACT_ID = "rps-public-observation-view"
PUBLIC_VIEW_ARTIFACT_PATH = "artifacts/public/rps_public_observation_view.json"
BUILDER_ID = "rps-published-aggregate-observatory-release-v4"


def build_rps_observatory_release_candidate(
    snapshot: Mapping[str, Any],
    canonical_manifest: Mapping[str, Any],
    provider_scope: Mapping[str, Any],
    claim_inventory: Mapping[str, Any],
    public_view_contract: Mapping[str, Any],
    *,
    output_dir: Path,
    release_id: str,
    builder_commit: str,
    previous_release: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the complete RPS component used by the public observatory release.

    The returned manifest includes all v3 longitudinal artifacts plus one bounded
    public observation view. Source input bytes remain private and are never
    copied into the public artifact namespace.
    """

    candidate = build_rps_release_candidate_complete_history(
        snapshot,
        canonical_manifest,
        provider_scope,
        claim_inventory,
        output_dir=output_dir,
        release_id=release_id,
        builder_commit=builder_commit,
        previous_release=previous_release,
    )
    prepared = prepare_rps_source_history(snapshot, canonical_manifest, provider_scope)
    source = candidate["sources"][0]
    view = build_rps_public_observation_view(
        prepared.analysis_panel,
        source_id=str(source["source_id"]),
        source_vintage_id=str(source["source_vintage_id"]),
        source_reference_periods=prepared.source_periods,
        contract=public_view_contract,
    )
    view_sha256, view_size = _write_json(output_dir / PUBLIC_VIEW_ARTIFACT_PATH, view)

    artifacts = candidate.get("artifacts")
    build = candidate.get("build")
    if not isinstance(artifacts, list) or not isinstance(build, dict):
        raise ValueError("RPS base release candidate has an invalid manifest structure")
    output_hashes = build.get("output_sha256")
    if not isinstance(output_hashes, dict):
        raise ValueError("RPS base release candidate has invalid build.output_sha256")
    if any(
        isinstance(row, Mapping) and row.get("artifact_id") == PUBLIC_VIEW_ARTIFACT_ID
        for row in artifacts
    ):
        raise ValueError("RPS base release candidate already contains the public view artifact")

    artifacts.append(
        {
            "artifact_id": PUBLIC_VIEW_ARTIFACT_ID,
            "path": PUBLIC_VIEW_ARTIFACT_PATH,
            "sha256": view_sha256,
            "size_bytes": view_size,
            "evidence_class": 1,
            "source_ids": [str(source["source_id"])],
        }
    )
    output_hashes[PUBLIC_VIEW_ARTIFACT_ID] = view_sha256
    build["builder_id"] = BUILDER_ID
    candidate["candidate_scope"] = (
        "Complete RPS observatory component: private complete-history source inputs, "
        "reviewed longitudinal diagnostics, and the rights-bounded public observation "
        "projection defined by rps-public-observation-delivery-v1. Historical subgroup "
        "source observations remain private."
    )
    _write_json(output_dir / "release.json", candidate)
    return candidate
