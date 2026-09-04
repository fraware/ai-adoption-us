from __future__ import annotations

from pathlib import Path

FRED_CONCURRENCY_GROUP = "group: authorized-rps-fred-source"
FRED_WORKFLOWS = (
    Path(".github/workflows/rps-live-validation.yml"),
    Path(".github/workflows/observatory-candidate-review.yml"),
    Path(".github/workflows/observatory-promotion.yml"),
)


def test_all_release_workflows_using_live_fred_share_one_serial_queue() -> None:
    """Prevent concurrent release-critical retrievals from exceeding provider limits."""

    for workflow in FRED_WORKFLOWS:
        text = workflow.read_text(encoding="utf-8")
        assert "FRED_API_KEY" in text, workflow
        assert FRED_CONCURRENCY_GROUP in text, workflow
        assert "cancel-in-progress: false" in text, workflow


def test_candidate_review_rebuilds_when_live_source_client_changes() -> None:
    """Source-client changes must automatically invalidate the current candidate."""

    text = Path(".github/workflows/observatory-candidate-review.yml").read_text(
        encoding="utf-8"
    )
    assert "'src/genai_at_work/rps_refresh.py'" in text
    assert "'src/genai_at_work/sources/fred.py'" in text
