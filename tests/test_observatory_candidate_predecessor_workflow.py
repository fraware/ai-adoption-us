from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/observatory-candidate-review.yml"


def test_candidate_workflow_verifies_and_propagates_promoted_predecessor() -> None:
    """Future waves/revisions must explicitly supersede the current reviewed release."""

    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "Resolve and verify current promoted predecessor" in workflow
    assert "current_release_manifest_sha256" in workflow
    assert "Current promoted release manifest checksum mismatch" in workflow
    assert "Current predecessor is not an explicitly reviewed promoted release" in workflow
    assert "PREVIOUS_RELEASE_MANIFEST=" in workflow
    assert workflow.count('args+=(--previous-release-manifest "$PREVIOUS_RELEASE_MANIFEST")') == 2
    assert "scripts/prepare_rps_observatory_candidate.py \"${args[@]}\"" in workflow
    assert "scripts/prepare_observatory_v1_candidate.py \"${args[@]}\"" in workflow
