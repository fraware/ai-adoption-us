from __future__ import annotations

import importlib.util
import json
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any


def _release_script() -> ModuleType:
    path = Path(__file__).parents[1] / "scripts/observatory_release.py"
    spec = importlib.util.spec_from_file_location("observatory_release_script", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load release script at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_stage_identity_does_not_depend_on_runner_filesystem_path(tmp_path: Path) -> None:
    stage_payload = _release_script()._stage_payload
    assert callable(stage_payload)
    build_stage: Callable[..., dict[str, Any]] = stage_payload

    manifest = {
        "schema_version": 1,
        "release_id": "observatory-v1-review-1",
        "data_mode": "derived_only",
    }
    first = tmp_path / "runner-a" / "release.json"
    second = tmp_path / "runner-b" / "release.json"
    first.parent.mkdir()
    second.parent.mkdir()
    payload = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    first.write_text(payload)
    second.write_text(payload)

    registry = {
        "current_release_id": None,
        "current_release_manifest_sha256": None,
    }
    release_diff = {"changed_source_ids": ["rps"]}
    review = {"review_type": "synthetic"}

    first_stage = build_stage(
        registry,
        first,
        manifest,
        release_diff,
        review,
        "BLOCKED_REVIEW_REQUIRED",
    )
    second_stage = build_stage(
        registry,
        second,
        manifest,
        release_diff,
        review,
        "BLOCKED_REVIEW_REQUIRED",
    )

    assert first_stage == second_stage
    assert first_stage["schema_version"] == 2
    assert "candidate_manifest_path" not in first_stage
    assert first_stage["candidate_manifest_sha256"]
    assert first_stage["candidate_manifest_digest"]
