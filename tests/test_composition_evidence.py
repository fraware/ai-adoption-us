from __future__ import annotations

from genai_at_work.composition_evidence import classify_composition_evidence


def _row(period: str, industry_id: str, comparability: str, l1: float) -> dict[str, object]:
    return {
        "period": period,
        "industry_index": 1 if industry_id == "stable" else 2,
        "industry_id": industry_id,
        "industry_name": industry_id.title(),
        "comparability": comparability,
        "maximum_leave_one_month_out_l1_to_quarter": l1,
    }


def test_primary_stable_requires_all_periods_to_pass() -> None:
    rows = [
        _row("2025-Q2", "stable", "primary", 0.04),
        _row("2026-Q2", "stable", "primary", 0.10),
        _row("2025-Q2", "unstable", "primary", 0.08),
        _row("2026-Q2", "unstable", "primary", 0.11),
    ]
    classified = classify_composition_evidence(
        rows,
        required_periods=("2025-Q2", "2026-Q2"),
        threshold_l1=0.10,
    )
    by_id = {row.industry_id: row for row in classified}
    assert by_id["stable"].evidence_tier == "primary_stable"
    assert by_id["stable"].passes_stability_rule is True
    assert by_id["unstable"].evidence_tier == "sensitivity_unstable"
    assert by_id["unstable"].passes_stability_rule is False


def test_limited_and_excluded_preserve_source_comparability_tier() -> None:
    rows = [
        _row("2025-Q2", "stable", "limited", 0.5),
        _row("2026-Q2", "stable", "limited", 0.5),
        _row("2025-Q2", "unstable", "excluded", 0.01),
        _row("2026-Q2", "unstable", "excluded", 0.01),
    ]
    classified = classify_composition_evidence(
        rows,
        required_periods=("2025-Q2", "2026-Q2"),
        threshold_l1=0.10,
    )
    by_id = {row.industry_id: row for row in classified}
    assert by_id["stable"].evidence_tier == "limited"
    assert by_id["stable"].passes_stability_rule is None
    assert by_id["unstable"].evidence_tier == "excluded"
    assert by_id["unstable"].passes_stability_rule is None


def test_missing_required_period_fails_closed() -> None:
    rows = [_row("2025-Q2", "stable", "primary", 0.04)]
    try:
        classify_composition_evidence(
            rows,
            required_periods=("2025-Q2", "2026-Q2"),
            threshold_l1=0.10,
        )
    except ValueError as exc:
        assert "missing required reliability periods" in str(exc)
    else:
        raise AssertionError("missing required period did not fail closed")
