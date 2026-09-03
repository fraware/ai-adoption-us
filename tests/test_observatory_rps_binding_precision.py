from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from genai_at_work.observatory_rps_bindings import (
    BINDINGS_REPOSITORY_PATH,
    ObservatoryRpsBindingError,
    _validate_value_binding,
)
from genai_at_work.release_engine import load_json_object

ROOT = Path(__file__).parents[1]
CHECKPOINT = ROOT / "data/registry/rps_industry_adoption_q2_2026_v1.json"
BINDINGS = ROOT / BINDINGS_REPOSITORY_PATH


def _binding() -> dict[str, Any]:
    bindings = load_json_object(BINDINGS)
    rows = bindings["source_value_bindings"]
    assert isinstance(rows, list) and len(rows) == 1 and isinstance(rows[0], dict)
    return deepcopy(rows[0])


def _source_candidate(tmp_path: Path, *, delta: float) -> dict[str, Any]:
    checkpoint = load_json_object(CHECKPOINT)
    rows = checkpoint["rows"]
    assert isinstance(rows, list)
    records = [
        {
            "period": "2026-Q2",
            "entity_type": "industry",
            "entity_id": f"industry-{index:02d}",
            "metric_id": "adoption_work",
            "series_id": row["series_id"],
            "value": float(row["value_pct"]) + delta,
        }
        for index, row in enumerate(rows, start=1)
        if isinstance(row, dict)
    ]
    relative = "inputs/rps/2026-Q2.json"
    source_path = tmp_path / relative
    source_path.parent.mkdir(parents=True)
    source_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "period": "2026-Q2",
                "records": records,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    return {
        "objects": [
            {
                "object_id": "2026-q2",
                "local_path": relative,
            }
        ]
    }


def test_sub_checkpoint_precision_difference_is_same_analytical_input(
    tmp_path: Path,
) -> None:
    binding = _binding()
    assert binding["checkpoint_decimal_places"] == 5
    source = _source_candidate(tmp_path, delta=0.000001)

    decimal_places = _validate_value_binding(
        binding,
        repo_root=ROOT,
        candidate_root=tmp_path,
        source=source,
    )

    assert decimal_places == 5


def test_change_that_alters_five_decimal_checkpoint_fails_closed(
    tmp_path: Path,
) -> None:
    source = _source_candidate(tmp_path, delta=0.00001)
    with pytest.raises(
        ObservatoryRpsBindingError,
        match="changed for 20 series at 5 decimal places",
    ):
        _validate_value_binding(
            _binding(),
            repo_root=ROOT,
            candidate_root=tmp_path,
            source=source,
        )


def test_precision_must_be_explicit_and_bounded(tmp_path: Path) -> None:
    source = _source_candidate(tmp_path, delta=0.0)
    missing = _binding()
    missing.pop("checkpoint_decimal_places")
    with pytest.raises(ObservatoryRpsBindingError, match="checkpoint_decimal_places"):
        _validate_value_binding(
            missing,
            repo_root=ROOT,
            candidate_root=tmp_path,
            source=source,
        )

    invalid = _binding()
    invalid["checkpoint_decimal_places"] = 13
    with pytest.raises(ObservatoryRpsBindingError, match="checkpoint_decimal_places"):
        _validate_value_binding(
            invalid,
            repo_root=ROOT,
            candidate_root=tmp_path,
            source=source,
        )
