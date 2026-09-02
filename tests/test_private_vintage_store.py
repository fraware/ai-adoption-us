from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from genai_at_work.private_vintage import PrivateVintageError, sha256_file
from genai_at_work.private_vintage_store import store_rps_private_vintage
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


def _write(path: Path, value: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    return path


def test_store_uses_exclusive_lock_and_cleans_it_after_success(tmp_path: Path) -> None:
    source = _write(tmp_path / "source.json", _snapshot())
    archive_root = tmp_path / "vault"
    package, manifest = store_rps_private_vintage(
        source,
        archive_root,
        builder_commit=BUILDER_COMMIT,
    )

    lock = package.parent / f".{sha256_file(source)}.lock"
    assert not lock.exists()
    assert manifest["archive_event_id"] == sha256_file(source)
    assert package.stat().st_mode & 0o077 == 0
    for path in package.iterdir():
        if path.is_file():
            assert path.stat().st_mode & 0o077 == 0


def test_store_fails_closed_on_stale_or_competing_lock(tmp_path: Path) -> None:
    source = _write(tmp_path / "source.json", _snapshot())
    snapshot_sha = sha256_file(source)
    source_root = tmp_path / "vault" / "rps-genai-tracker-fred-release-6"
    source_root.mkdir(parents=True)
    lock = source_root / f".{snapshot_sha}.lock"
    lock.write_text("stale-lock\n")

    with pytest.raises(PrivateVintageError, match="locked by another or interrupted writer"):
        store_rps_private_vintage(
            source,
            tmp_path / "vault",
            builder_commit=BUILDER_COMMIT,
        )
    assert lock.exists()


def test_existing_event_cannot_be_rebound_to_different_previous_snapshot(tmp_path: Path) -> None:
    current = _write(tmp_path / "current.json", _snapshot())
    package, manifest = store_rps_private_vintage(
        current,
        tmp_path / "vault",
        builder_commit=BUILDER_COMMIT,
    )
    assert manifest["comparison"]["previous_snapshot_sha256"] is None

    previous_snapshot = copy.deepcopy(_snapshot(retrieved_at="2026-08-01T12:00:00Z"))
    previous = _write(tmp_path / "previous.json", previous_snapshot)
    assert sha256_file(previous) != sha256_file(current)

    with pytest.raises(PrivateVintageError, match="already bound to a different previous snapshot"):
        store_rps_private_vintage(
            current,
            tmp_path / "vault",
            builder_commit=BUILDER_COMMIT,
            previous_snapshot_path=previous,
        )
    assert package.is_dir()


def test_existing_event_is_idempotent_when_previous_binding_matches(tmp_path: Path) -> None:
    previous = _write(tmp_path / "previous.json", _snapshot(retrieved_at="2026-09-01T12:00:00Z"))
    current_snapshot = _snapshot(retrieved_at="2026-09-02T12:00:00Z")
    current = _write(tmp_path / "current.json", current_snapshot)

    first_package, first_manifest = store_rps_private_vintage(
        current,
        tmp_path / "vault",
        builder_commit=BUILDER_COMMIT,
        previous_snapshot_path=previous,
    )
    second_package, second_manifest = store_rps_private_vintage(
        current,
        tmp_path / "vault",
        builder_commit="f" * 40,
        previous_snapshot_path=previous,
    )

    assert second_package == first_package
    assert second_manifest == first_manifest
    assert first_manifest["comparison"]["previous_snapshot_sha256"] == sha256_file(previous)
    assert first_manifest["builder_commit"] == BUILDER_COMMIT
