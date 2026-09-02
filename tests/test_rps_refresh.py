from __future__ import annotations

import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

from genai_at_work.rps_refresh import RpsRefreshError, build_refresh_candidate

ROOT = Path(__file__).parents[1]
MANIFEST = ROOT / "data" / "registry" / "rps_source_series_manifest.json"
SCOPE = ROOT / "data" / "registry" / "rps_provider_catalog_scope.json"
CHECKPOINT = ROOT / "data" / "registry" / "rps_industry_adoption_q2_2026_v1.json"
WORKFLOW = ROOT / ".github" / "workflows" / "rps-source-watch.yml"


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text())
    assert isinstance(value, dict)
    return value


def _baseline_inputs() -> tuple[
    dict[str, object],
    dict[str, object],
    dict[str, object],
    list[dict[str, object]],
    dict[str, list[dict[str, object]]],
]:
    manifest = _load(MANIFEST)
    scope = _load(SCOPE)
    checkpoint = _load(CHECKPOINT)
    series = manifest["series"]
    excluded = scope["intentionally_excluded_national_series"]
    assert isinstance(series, list)
    assert isinstance(excluded, list)

    release_rows: list[dict[str, object]] = []
    observations: dict[str, list[dict[str, object]]] = {}
    pinned = {
        row["series_id"]: row["value_pct"]
        for row in checkpoint["rows"]
        if isinstance(row, dict)
    }

    for row in series:
        assert isinstance(row, dict)
        series_id = str(row["series_id"])
        release_rows.append(
            {
                "id": series_id,
                "last_updated": "2026-08-04 00:00:00-05",
                "observation_end": "2026-04-01",
            }
        )
        value = pinned.get(series_id, 10.0)
        observations[series_id] = [
            {
                "date": "2026-04-01",
                "value": str(value),
                "realtime_start": "2026-08-04",
                "realtime_end": "9999-12-31",
            }
        ]

    for row in excluded:
        assert isinstance(row, dict)
        release_rows.append(
            {
                "id": str(row["series_id"]),
                "last_updated": "2026-08-04 00:00:00-05",
                "observation_end": "2026-04-01",
            }
        )

    assert len(release_rows) == 137
    assert len(observations) == 131
    return manifest, scope, checkpoint, release_rows, observations


def _candidate(
    release_rows: list[dict[str, object]],
    observations: dict[str, list[dict[str, object]]],
) -> dict[str, object]:
    manifest, scope, checkpoint, _, _ = _baseline_inputs()
    return build_refresh_candidate(
        manifest=manifest,
        provider_scope=scope,
        canonical_checkpoint=checkpoint,
        release_rows=release_rows,
        observations_by_series=observations,
        retrieved_at="2026-09-02T12:00:00+00:00",
    )


def test_baseline_refresh_candidate_is_noncanonical_and_detects_no_change() -> None:
    _, _, _, release_rows, observations = _baseline_inputs()
    candidate = _candidate(release_rows, observations)
    q2 = candidate["canonical_q2_industry_adoption_check"]
    catalog = candidate["catalog"]

    assert candidate["status"] == "no-provider-change-detected"
    assert candidate["candidate_is_canonical"] is False
    assert candidate["candidate_is_publication_ready"] is False
    assert candidate["automatic_repository_write"] is False
    assert candidate["full_history_included"] is False
    assert candidate["review_reasons"] == []
    assert candidate["supported_series_with_newer_observation_than_q2_baseline"] == 0
    assert len(candidate["supported_series_latest"]) == 131
    assert catalog["observed_provider_series_count"] == 137
    assert catalog["catalog_added_ids"] == []
    assert catalog["catalog_removed_ids"] == []
    assert q2["pinned_series_count"] == 20
    assert q2["unchanged"] == 20
    assert q2["revised"] == 0
    assert q2["missing"] == 0


def test_new_wave_is_review_required_without_changing_canonical_checkpoint() -> None:
    _, _, checkpoint, release_rows, observations = _baseline_inputs()
    first = checkpoint["rows"][0]
    assert isinstance(first, dict)
    series_id = str(first["series_id"])
    observations[series_id].append(
        {
            "date": "2026-07-01",
            "value": "35.0",
            "realtime_start": "2026-11-01",
            "realtime_end": "9999-12-31",
        }
    )
    candidate = _candidate(release_rows, observations)

    assert candidate["status"] == "new-wave-review-required"
    assert candidate["review_reasons"] == ["newer-supported-observations-available"]
    assert candidate["supported_series_with_newer_observation_than_q2_baseline"] == 1
    assert candidate["candidate_is_canonical"] is False


def test_revision_of_pinned_q2_value_is_fail_closed_provider_drift() -> None:
    _, _, checkpoint, release_rows, observations = _baseline_inputs()
    first = checkpoint["rows"][0]
    assert isinstance(first, dict)
    series_id = str(first["series_id"])
    observations[series_id][0]["value"] = "999.0"
    candidate = _candidate(release_rows, observations)
    q2 = candidate["canonical_q2_industry_adoption_check"]

    assert candidate["status"] == "review-required-provider-drift"
    assert "canonical-q2-industry-values-revised" in candidate["review_reasons"]
    assert q2["revised"] == 1
    assert q2["unchanged"] == 19


def test_catalog_drift_is_reported_without_accepting_new_series() -> None:
    _, _, _, release_rows, observations = _baseline_inputs()
    release_rows.append({"id": "RPSUNREGISTERED", "last_updated": "", "observation_end": ""})
    candidate = _candidate(release_rows, observations)
    catalog = candidate["catalog"]

    assert candidate["status"] == "review-required-provider-drift"
    assert "provider-catalog-drift" in candidate["review_reasons"]
    assert catalog["catalog_added_ids"] == ["RPSUNREGISTERED"]
    assert len(candidate["supported_series_latest"]) == 131


def test_missing_supported_observation_payload_fails_closed() -> None:
    _, _, _, release_rows, observations = _baseline_inputs()
    observations.pop(next(iter(observations)))
    with pytest.raises(RpsRefreshError, match="Observation payloads missing"):
        _candidate(release_rows, observations)


def test_probe_refuses_canonical_or_public_output_paths_before_network_access() -> None:
    output = ROOT / "data" / "registry" / "forbidden-rps-refresh.json"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "probe_rps_aggregate_sources.py"),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src"), "FRED_API_KEY": ""},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "Refusing to write source-watch evidence" in result.stderr
    assert not output.exists()


def test_workflow_is_read_only_review_evidence_with_explicit_scheduled_probe() -> None:
    text = WORKFLOW.read_text()
    assert "schedule:" in text
    assert "cron: '17 11 * * 1'" in text
    assert "workflow_dispatch:" in text
    assert "permissions:\n  contents: read" in text
    assert "secrets.FRED_API_KEY" in text
    assert "continue-on-error: true" in text
    assert "runner.temp" in text
    assert "retention-days: 14" in text
    assert "contents: write" not in text
    assert "git push" not in text
    assert "create-pull-request" not in text
