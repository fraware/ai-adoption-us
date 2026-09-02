from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from genai_at_work.private_vintage import (
    DIFF_NAME,
    MANIFEST_NAME,
    SNAPSHOT_NAME,
    PrivateVintageError,
    archive_rps_private_vintage,
    sha256_file,
    verify_rps_private_vintage,
)
from genai_at_work.rps_release import snapshot_content_sha256

BUILDER_COMMIT = "0123456789abcdef0123456789abcdef01234567"


def _snapshot(*, retrieved_at: str = "2026-09-02T12:00:00Z") -> dict[str, Any]:
    snapshot: dict[str, Any] = {
        "schema_version": 1,
        "snapshot_type": "rps_published_aggregate_refresh",
        "source_id": "rps-genai-tracker-fred-release-6",
        "provider": "Synthetic FRED/ALFRED RPS distribution",
        "provider_release_id": 6,
        "retrieved_at": retrieved_at,
        "rights": {
            "status": "approved",
            "scope": "published aggregate project use",
            "decision_ref": "docs/source-rights/RPS_SOURCE_DECISION.md",
            "public_bulk_redistribution_approved": False,
        },
        "inventory": {
            "provider_series_count": 2,
            "observatory_series_count": 1,
            "excluded_series_count": 1,
            "provider_inventory_status": "pass",
        },
        "observation_count": 1,
        "series": [
            {
                "series_id": "RPSGENAIUSAGESHAREWORK",
                "title": "Synthetic RPS work adoption",
                "metric_id": "adoption_work",
                "entity_id": "us",
                "entity_type": "national",
                "entity_name": "Employed Adults",
                "frequency": "Quarterly",
                "unit": "Percent",
                "seasonal_adjustment": "Not Seasonally Adjusted",
                "observation_start": "2026-05-01",
                "observation_end": "2026-05-01",
                "last_updated": "2026-08-04 10:00:00-05",
                "notes_hash": "a" * 64,
                "source_url": "https://fred.stlouisfed.org/series/RPSGENAIUSAGESHAREWORK",
                "copyright_status": "Copyrighted: Citation Required",
                "citation_text": "Synthetic test citation.",
                "observations": [
                    {
                        "date": "2026-05-01",
                        "period": "2026-Q2",
                        "value": 50.0,
                        "unit": "Percent",
                        "realtime_start": retrieved_at[:10],
                        "realtime_end": retrieved_at[:10],
                        "source_last_updated": "2026-08-04 10:00:00-05",
                    }
                ],
            }
        ],
        "excluded_series": [
            {
                "series_id": "RPSGENAIUSAGESHAREALL",
                "title": "Synthetic excluded national construct",
                "construct": "Adoption Rate Overall",
                "reason": "Outside the work-focused observatory scope.",
                "observations_retrieved": False,
            }
        ],
    }
    snapshot["content_sha256"] = snapshot_content_sha256(snapshot)
    return snapshot


def _write_snapshot(path: Path, snapshot: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n")
    return path


def test_archive_installs_exact_immutable_baseline_and_is_idempotent(tmp_path: Path) -> None:
    source = _write_snapshot(tmp_path / "source.json", _snapshot())
    archive_root = tmp_path / "vault"

    package, manifest = archive_rps_private_vintage(
        source,
        archive_root,
        builder_commit=BUILDER_COMMIT,
    )

    source_sha = sha256_file(source)
    assert package == archive_root / "rps-genai-tracker-fred-release-6" / source_sha
    assert {path.name for path in package.iterdir()} == {MANIFEST_NAME, SNAPSHOT_NAME}
    assert (package / SNAPSHOT_NAME).read_bytes() == source.read_bytes()
    assert manifest["archive_event_id"] == source_sha
    assert manifest["source_snapshot_sha256"] == source_sha
    assert manifest["source_content_sha256"] == _snapshot()["content_sha256"]
    assert manifest["comparison"]["revision_status"] == "baseline"
    assert manifest["rights"]["storage_scope"] == "private"
    assert manifest["public_archive"] is False
    assert verify_rps_private_vintage(package) == manifest

    repeated_package, repeated_manifest = archive_rps_private_vintage(
        source,
        archive_root,
        builder_commit=BUILDER_COMMIT,
    )
    assert repeated_package == package
    assert repeated_manifest == manifest


def test_transport_envelope_creates_distinct_event_with_same_scientific_identity(
    tmp_path: Path,
) -> None:
    first_snapshot = _snapshot(retrieved_at="2026-09-02T12:00:00Z")
    second_snapshot = _snapshot(retrieved_at="2026-09-03T12:00:00Z")
    assert first_snapshot["content_sha256"] == second_snapshot["content_sha256"]

    first_path = _write_snapshot(tmp_path / "first.json", first_snapshot)
    second_path = _write_snapshot(tmp_path / "second.json", second_snapshot)
    assert sha256_file(first_path) != sha256_file(second_path)

    first_package, first_manifest = archive_rps_private_vintage(
        first_path,
        tmp_path / "vault",
        builder_commit=BUILDER_COMMIT,
    )
    second_package, second_manifest = archive_rps_private_vintage(
        second_path,
        tmp_path / "vault",
        builder_commit=BUILDER_COMMIT,
        previous_snapshot_path=first_path,
    )

    assert first_package != second_package
    assert first_manifest["source_content_sha256"] == second_manifest["source_content_sha256"]
    assert second_manifest["comparison"]["revision_status"] == "unchanged"
    assert second_manifest["comparison"]["previous_snapshot_sha256"] == sha256_file(first_path)
    assert (second_package / DIFF_NAME).is_file()
    diff = json.loads((second_package / DIFF_NAME).read_text())
    assert diff["revision_status"] == "unchanged"
    assert diff["counts"] == {
        "new_observations": 0,
        "revised_observations": 0,
        "removed_observations": 0,
        "definition_changes": 0,
    }


def test_archive_retains_private_new_wave_diff_bound_to_exact_previous_snapshot(
    tmp_path: Path,
) -> None:
    previous = _snapshot()
    current = copy.deepcopy(previous)
    current["retrieved_at"] = "2026-12-02T12:00:00Z"
    current["series"][0]["observation_end"] = "2026-08-01"
    current["series"][0]["last_updated"] = "2026-11-04 10:00:00-06"
    current["series"][0]["observations"].append(
        {
            "date": "2026-08-01",
            "period": "2026-Q3",
            "value": 53.0,
            "unit": "Percent",
            "realtime_start": "2026-12-02",
            "realtime_end": "2026-12-02",
            "source_last_updated": "2026-11-04 10:00:00-06",
        }
    )
    current["observation_count"] = 2
    current["content_sha256"] = snapshot_content_sha256(current)

    previous_path = _write_snapshot(tmp_path / "previous.json", previous)
    current_path = _write_snapshot(tmp_path / "current.json", current)
    package, manifest = archive_rps_private_vintage(
        current_path,
        tmp_path / "vault",
        builder_commit=BUILDER_COMMIT,
        previous_snapshot_path=previous_path,
    )

    assert manifest["comparison"]["revision_status"] == "new_wave"
    assert manifest["comparison"]["previous_snapshot_sha256"] == sha256_file(previous_path)
    diff = json.loads((package / DIFF_NAME).read_text())
    assert diff["revision_status"] == "new_wave"
    assert diff["counts"]["new_observations"] == 1
    assert diff["current_content_sha256"] == current["content_sha256"]
    assert verify_rps_private_vintage(package)["archive_event_id"] == sha256_file(current_path)


def test_archive_fails_closed_on_tamper_rights_and_corrupt_existing_package(tmp_path: Path) -> None:
    source_snapshot = _snapshot()
    source = _write_snapshot(tmp_path / "source.json", source_snapshot)

    tampered = copy.deepcopy(source_snapshot)
    tampered["series"][0]["observations"][0]["value"] = 99.0
    tampered_path = _write_snapshot(tmp_path / "tampered.json", tampered)
    with pytest.raises(PrivateVintageError, match="scientific content hash mismatch"):
        archive_rps_private_vintage(
            tampered_path,
            tmp_path / "tampered-vault",
            builder_commit=BUILDER_COMMIT,
        )

    unresolved = _snapshot()
    unresolved["rights"]["status"] = "unresolved"
    unresolved["content_sha256"] = snapshot_content_sha256(unresolved)
    unresolved_path = _write_snapshot(tmp_path / "unresolved.json", unresolved)
    with pytest.raises(PrivateVintageError, match="rights-approved"):
        archive_rps_private_vintage(
            unresolved_path,
            tmp_path / "rights-vault",
            builder_commit=BUILDER_COMMIT,
        )

    package, _ = archive_rps_private_vintage(
        source,
        tmp_path / "vault",
        builder_commit=BUILDER_COMMIT,
    )
    (package / SNAPSHOT_NAME).write_text("{}\n")
    with pytest.raises(PrivateVintageError, match="byte identity mismatch"):
        verify_rps_private_vintage(package)
    with pytest.raises(PrivateVintageError, match="byte identity mismatch"):
        archive_rps_private_vintage(
            source,
            tmp_path / "vault",
            builder_commit=BUILDER_COMMIT,
        )
