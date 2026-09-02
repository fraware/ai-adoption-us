from __future__ import annotations

from copy import deepcopy

import pytest

from genai_at_work.rps_checkpoint import RpsCheckpointError, build_public_rps_source_checkpoint

CONTENT_SHA = "a" * 64
SNAPSHOT_SHA = "b" * 64
COMMIT = "0123456789abcdef0123456789abcdef01234567"
RUN_ID = "33683408001"
SOURCE_PERIODS = ["2024-Q3", "2024-Q4", "2025-Q1", "2025-Q2", "2026-Q2"]
JOINT_PERIODS = ["2024-Q4", "2025-Q1", "2025-Q2", "2026-Q2"]


def _source_summary() -> dict[str, object]:
    return {
        "candidate_type": "rps_published_aggregate_refresh",
        "source_id": "rps-genai-tracker-fred-release-6",
        "content_sha256": CONTENT_SHA,
        "private_snapshot_file_sha256": SNAPSHOT_SHA,
        "retrieved_at": "2026-09-02T21:00:00Z",
        "revision_status": "baseline",
        "promotion_state": "source-candidate-only",
        "public_raw_observations_included": False,
        "requires_release_review": True,
        "observation_count": 962,
        "inventory": {
            "provider_series_count": 137,
            "observatory_series_count": 131,
            "excluded_series_count": 6,
            "provider_inventory_status": "pass",
        },
    }


def _release() -> dict[str, object]:
    source_objects = [
        {
            "object_id": period.lower(),
            "locator": "https://fred.stlouisfed.org/release?rid=6",
            "local_path": f"inputs/rps/{period}.json",
            "sha256": f"{index + 1:064x}",
            "size_bytes": 1000 + index,
        }
        for index, period in enumerate(SOURCE_PERIODS)
    ]
    return {
        "schema_version": 1,
        "release_id": "rps-test",
        "release_type": "baseline",
        "data_mode": "derived_only",
        "source_input_bytes_publication": False,
        "sources": [
            {
                "source_id": "rps-genai-tracker-fred-release-6",
                "source_vintage_id": f"sha256:{CONTENT_SHA}",
                "reference_periods": SOURCE_PERIODS,
                "analysis_reference_periods": JOINT_PERIODS,
                "analysis_metric_reference_periods": {
                    "adoption_work": SOURCE_PERIODS,
                    "assisted_hours_share": JOINT_PERIODS,
                    "reported_time_savings_share": JOINT_PERIODS,
                },
                "definition_id": f"sha256:{'c' * 64}",
                "taxonomy_versions": {"rps_source_series_manifest": f"sha256:{'d' * 64}"},
                "rights": {
                    "status": "approved",
                    "storage_scope": "private",
                    "publication_scope": "derived_only",
                    "redistribution_scope": "derived_only",
                },
                "coverage": {
                    "status": "pass",
                    "required_units": 131 * len(JOINT_PERIODS),
                    "observed_units": 131 * len(JOINT_PERIODS),
                    "full_source_observed_units": 962,
                    "subgroup_series_count": 126,
                    "national_series_count": 5,
                },
                "objects": source_objects,
            }
        ],
        "build": {
            "builder_id": "rps-published-aggregate-construct-window-release-v3",
            "builder_commit": COMMIT,
            "deterministic": True,
            "input_sha256": {},
            "output_sha256": {},
        },
    }


def _build(
    summary: dict[str, object] | None = None,
    release: dict[str, object] | None = None,
) -> dict[str, object]:
    return build_public_rps_source_checkpoint(
        summary or _source_summary(),
        release or _release(),
        validation_run_id=RUN_ID,
        validation_commit=COMMIT,
    )


def test_checkpoint_contains_hashes_and_period_scope_but_no_source_rows() -> None:
    checkpoint = _build()
    assert checkpoint["checkpoint_state"] == "candidate_for_review"
    assert checkpoint["source_content_sha256"] == CONTENT_SHA
    assert checkpoint["source_snapshot_file_sha256"] == SNAPSHOT_SHA
    assert checkpoint["analysis_reference_periods"] == JOINT_PERIODS
    assert checkpoint["analysis_metric_reference_periods"] == {
        "adoption_work": SOURCE_PERIODS,
        "assisted_hours_share": JOINT_PERIODS,
        "reported_time_savings_share": JOINT_PERIODS,
    }
    assert len(checkpoint["source_objects"]) == len(SOURCE_PERIODS)
    serialized = repr(checkpoint)
    assert "local_path" not in serialized
    assert "records" not in serialized
    assert "observations" not in serialized
    assert checkpoint["rights_boundary"]["checkpoint_contains_observation_values"] is False
    assert checkpoint["rights_boundary"]["durable_private_raw_archive_attested"] is False
    assert checkpoint["requires_human_acceptance"] is True
    assert checkpoint["promotion_performed"] is False


def test_checkpoint_rejects_widened_publication_rights() -> None:
    release = deepcopy(_release())
    source = release["sources"][0]
    source["rights"]["publication_scope"] = "raw_public"
    with pytest.raises(RpsCheckpointError, match="publication_scope"):
        _build(release=release)


def test_checkpoint_rejects_source_identity_mismatch() -> None:
    release = deepcopy(_release())
    release["sources"][0]["source_vintage_id"] = f"sha256:{'e' * 64}"
    with pytest.raises(RpsCheckpointError, match="source_vintage_id"):
        _build(release=release)


def test_checkpoint_rejects_non_intersection_joint_periods() -> None:
    release = deepcopy(_release())
    release["sources"][0]["analysis_reference_periods"] = SOURCE_PERIODS
    release["sources"][0]["coverage"]["required_units"] = 131 * len(SOURCE_PERIODS)
    release["sources"][0]["coverage"]["observed_units"] = 131 * len(SOURCE_PERIODS)
    with pytest.raises(RpsCheckpointError, match="construct intersection"):
        _build(release=release)


def test_checkpoint_rejects_different_builder_commit() -> None:
    release = deepcopy(_release())
    release["build"]["builder_commit"] = "f" * 40
    with pytest.raises(RpsCheckpointError, match="validated GitHub commit"):
        _build(release=release)


def test_checkpoint_rejects_observation_bearing_output_field(monkeypatch: pytest.MonkeyPatch) -> None:
    from genai_at_work import rps_checkpoint

    original = rps_checkpoint._assert_no_forbidden_keys

    def inject_and_validate(value: object, *, context: str = "checkpoint") -> None:
        assert isinstance(value, dict)
        value["observations"] = []
        original(value, context=context)

    monkeypatch.setattr(rps_checkpoint, "_assert_no_forbidden_keys", inject_and_validate)
    with pytest.raises(RpsCheckpointError, match="forbidden source-data key"):
        _build()
