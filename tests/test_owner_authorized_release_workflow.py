from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_owner_authorization_is_one_shot_and_does_not_waive_release_gates() -> None:
    authorization = read("data/registry/release1_owner_authorization.json")

    assert '"first_release_only": true' in authorization
    assert '"automated_release_review_authorized": true' in authorization
    assert '"human_review_required": false' in authorization
    assert '"formal_github_release_tag": "v1.0.0"' in authorization
    assert '"active": true' in authorization


def test_owner_authorized_workflow_is_bound_to_successful_canonical_candidate_review() -> None:
    workflow = read(".github/workflows/observatory-owner-authorized-release.yml")

    assert 'workflows: ["Observatory candidate review"]' in workflow
    assert "github.event.workflow_run.conclusion == 'success'" in workflow
    assert "github.event.workflow_run.event == 'push'" in workflow
    assert "github.event.workflow_run.head_branch == 'main'" in workflow
    assert "github.event.workflow_run.head_repository.full_name == github.repository" in workflow
    assert "registry.get('current_release_id')" in workflow
    assert "OWNER_RELEASE_AUTHORIZED=0" not in workflow
    assert "OWNER_RELEASE_AUTHORIZED={value}" in workflow


def test_owner_authorized_workflow_preserves_exact_identity_and_rights_contracts() -> None:
    workflow = read(".github/workflows/observatory-owner-authorized-release.yml")

    assert "observatory-candidate-review-${REVIEW_RUN_ID}-${CANDIDATE_SHA}" in workflow
    assert "summary.get('gate_status') != 'BLOCKED_REVIEW_REQUIRED'" in workflow
    assert "summary.get('rps_repository_binding_status') != 'pass'" in workflow
    assert "summary.get('source_input_bytes_included') is not False" in workflow
    assert "scripts/rehydrate_observatory_v1_candidate.py" in workflow
    assert "identity.get('status') != 'REHYDRATED_EXACT_CANDIDATE'" in workflow
    assert "human_review_performed': False" in workflow
    assert "review_mode': 'owner_authorized_automated_release_review'" in workflow
    assert "scripts/promote_rehydrated_observatory_v1.py" in workflow
    assert "scripts/validate_observatory_publication_commit.py --commit HEAD" in workflow
    assert "git rev-parse origin/main" in workflow
    assert "Private RPS source bytes published: false" in workflow


def test_formal_release_occurs_only_after_exact_pages_deployment_and_live_audit() -> None:
    workflow = read(".github/workflows/observatory-owner-authorized-release.yml")

    assert "GitHub Pages Release 1" in workflow
    assert "Build and audit GitHub Pages artifact" in workflow
    assert "Deploy GitHub Pages" in workflow
    assert "Audit deployed Release 1 origin" in workflow
    assert "gh release create \"$tag\"" in workflow
    assert "--target \"$PUBLICATION_SHA\"" in workflow
    assert "Formal release $tag already exists; refusing to overwrite it." in workflow
