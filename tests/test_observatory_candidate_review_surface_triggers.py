from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/observatory-candidate-review.yml"
INVENTORY = ROOT / "data/registry/longitudinal_claim_inventory.json"


def test_candidate_review_workflow_tracks_every_governed_claim_surface() -> None:
    """A governed surface change must automatically produce a new review candidate."""

    workflow = WORKFLOW.read_text(encoding="utf-8")
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    claims = inventory.get("claims")
    assert isinstance(claims, list) and claims

    assert "data/registry/longitudinal_claim_inventory.json" in workflow
    surfaces = []
    for row in claims:
        assert isinstance(row, dict)
        surface = row.get("surface")
        assert isinstance(surface, str) and surface
        surfaces.append(surface)
        assert f"- '{surface}'" in workflow

    assert len(surfaces) == len(set(surfaces))
