from pathlib import Path

import pytest

from scripts import publish_release1 as publication


def test_local_release_contract_requires_only_formal_tag_unchecked(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "RELEASE1_NOTES.md").write_text("Release 1\n", encoding="utf-8")
    (docs / "RELEASE_CHECKLIST.md").write_text(
        "- [x] deployment audited\n"
        "- [ ] formal Release 1 tag/release created for the final audited release commit.\n",
        encoding="utf-8",
    )

    publication.validate_local_release_contract(tmp_path)

    (docs / "RELEASE_CHECKLIST.md").write_text(
        "- [ ] another unresolved gate\n"
        "- [ ] formal Release 1 tag/release created for the final audited release commit.\n",
        encoding="utf-8",
    )
    with pytest.raises(publication.ReleaseError, match="exactly one unchecked item"):
        publication.validate_local_release_contract(tmp_path)


def test_required_workflow_classifier_requires_every_exact_push_gate() -> None:
    runs = [
        {"id": index, "name": name, "event": "push", "status": "completed", "conclusion": "success"}
        for index, name in enumerate(publication.REQUIRED_WORKFLOWS, start=1)
    ]
    complete, states = publication.classify_required_workflows(runs)
    assert complete
    assert set(states) == set(publication.REQUIRED_WORKFLOWS)
    assert set(states.values()) == {"success"}

    complete, states = publication.classify_required_workflows(runs[:-1])
    assert not complete
    assert states[publication.REQUIRED_WORKFLOWS[-1]] == "missing"


def test_required_workflow_classifier_fails_closed_on_red_gate() -> None:
    runs = [
        {"id": index, "name": name, "event": "push", "status": "completed", "conclusion": "success"}
        for index, name in enumerate(publication.REQUIRED_WORKFLOWS, start=1)
    ]
    runs[0]["conclusion"] = "failure"
    with pytest.raises(publication.ReleaseError, match="required workflow failed"):
        publication.classify_required_workflows(runs)


def test_publication_constants_bind_first_formal_release() -> None:
    assert publication.TAG == "v1.0.0"
    assert publication.RELEASE_NAME == "GenAI at Work — Release 1"
    assert publication.AUTHORIZATION_TITLE == "Authorize Release 1 publication"
    assert publication.REQUIRED_CLOSED_ISSUES == (2, 3)


def test_publication_workflow_is_one_shot_and_write_scoped() -> None:
    workflow = Path(".github/workflows/release1-publish.yml").read_text(encoding="utf-8")
    assert "branches: [main]" in workflow
    assert "contents: write" in workflow
    assert "actions: read" in workflow
    assert "issues: read" in workflow
    assert "startsWith(github.event.head_commit.message, 'Authorize Release 1 publication')" in workflow
    assert "python scripts/publish_release1.py" in workflow
    assert "workflow_dispatch" not in workflow
