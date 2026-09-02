from __future__ import annotations

from typing import Any

import pytest

from genai_at_work.composition_snapshot import (
    CompositionSnapshotError,
    build_composition_residual_evidence,
    compositions_from_document,
)
from genai_at_work.longitudinal import AuditRecord
from genai_at_work.rps_release import PreparedRpsPanel

OCCUPATIONS = tuple(f"occupation-{index}" for index in range(1, 23))
INDUSTRIES = tuple(f"industry-{index}" for index in range(1, 21))
METRICS = ("adoption_work", "assisted_hours_share", "reported_time_savings_share")
PERIODS = ("2025-Q2", "2026-Q2")


def _composition_document(*, suppress_usual: bool = False) -> dict[str, Any]:
    industries: list[dict[str, Any]] = []
    for index, industry_id in enumerate(INDUSTRIES, start=1):
        worker = {occupation_id: 1.0 / len(OCCUPATIONS) for occupation_id in OCCUPATIONS}
        actual_raw = {occupation_id: float(position) for position, occupation_id in enumerate(OCCUPATIONS, start=1)}
        actual_total = sum(actual_raw.values())
        actual = {key: value / actual_total for key, value in actual_raw.items()}
        industries.append(
            {
                "industry_id": industry_id,
                "industry_index": index,
                "industry_name": f"Industry {index}",
                "worker_coverage": 1.0,
                "actual_hours_valid_worker_coverage": 1.0,
                "actual_hours_mapping_coverage": 1.0,
                "usual_hours_valid_worker_coverage": 0.95 if suppress_usual else 1.0,
                "usual_hours_mapping_coverage": 1.0,
                "worker_weights": worker,
                "actual_hour_weights": actual,
                "usual_hour_weights": None if suppress_usual else worker,
                "worker_suppressed": False,
                "actual_hours_suppressed": False,
                "usual_hours_suppressed": suppress_usual,
            }
        )
    return {"coverage_gate": 0.98, "industries": industries}


def _panel() -> PreparedRpsPanel:
    records: list[AuditRecord] = []
    for period_index, period in enumerate(PERIODS):
        for metric_index, metric_id in enumerate(METRICS):
            occupation_values: dict[str, float] = {}
            for occupation_index, occupation_id in enumerate(OCCUPATIONS, start=1):
                value = 5.0 + occupation_index + metric_index * 2.0 + period_index
                occupation_values[occupation_id] = value
                records.append(
                    AuditRecord(
                        entity_type="occupation",
                        entity_id=occupation_id,
                        entity_index=occupation_index,
                        metric_id=metric_id,
                        period=period,
                        value=value,
                        series_id=f"occ-{occupation_index}-{metric_id}",
                        audit_scope="private_release_candidate_input",
                        rights_status="copyrighted",
                    )
                )
            mean = sum(occupation_values.values()) / len(occupation_values)
            for industry_index, industry_id in enumerate(INDUSTRIES, start=1):
                # Preserve both positive and negative residuals and change them mildly across periods.
                offset = (industry_index - 10.5) * 0.3 + period_index * ((industry_index % 3) - 1) * 0.1
                records.append(
                    AuditRecord(
                        entity_type="industry",
                        entity_id=industry_id,
                        entity_index=industry_index,
                        metric_id=metric_id,
                        period=period,
                        value=mean + offset,
                        series_id=f"ind-{industry_index}-{metric_id}",
                        audit_scope="private_release_candidate_input",
                        rights_status="copyrighted",
                    )
                )
    return PreparedRpsPanel(
        periods=PERIODS,
        period_rows={},
        subgroup_records=tuple(records),
        definition_id="sha256:" + "a" * 64,
        taxonomy_version="sha256:" + "b" * 64,
        series_count=131,
        observation_count=131 * len(PERIODS),
    )


def _tiers() -> list[dict[str, Any]]:
    return [
        {
            "industry_id": industry_id,
            "industry_index": index,
            "evidence_tier": "primary_stable",
            "reason": "synthetic stable fixture",
            "stability_threshold_l1": 0.1,
            "maximum_leave_one_month_out_l1_across_required_periods": 0.05,
        }
        for index, industry_id in enumerate(INDUSTRIES, start=1)
    ]


def test_composition_document_parser_rejects_extra_shape_risk_but_accepts_names() -> None:
    rows = compositions_from_document(_composition_document())
    assert len(rows) == 20
    assert rows[0].industry_id == "industry-1"
    assert rows[-1].industry_index == 20
    assert rows[0].worker_weights is not None
    assert rows[0].actual_hour_weights is not None
    assert rows[0].worker_weights != rows[0].actual_hour_weights


def test_snapshot_panel_builds_residual_influence_and_persistence_evidence() -> None:
    evidence = build_composition_residual_evidence(
        _panel(),
        {period: _composition_document() for period in PERIODS},
        evidence_tiers=_tiers(),
    )
    assert evidence["periods"] == list(PERIODS)
    assert len(evidence["primary_residuals"]) == 2 * 3 * 20
    assert len(evidence["usual_hours_sensitivity"]) == 2 * 2 * 20
    assert len(evidence["leave_one_occupation_out_influence"]) == 2 * 3 * 20
    assert len(evidence["cross_period_persistence"]) == 6
    assert evidence["validation"]["status"] == "pass"
    assert evidence["validation"]["primary_supported_row_count"] == 120
    assert all(
        row["composition_basis_evidence_tier"] == "primary_stable"
        for row in evidence["primary_residuals"]
    )
    assert all(
        row["supported"] is True
        for row in evidence["leave_one_occupation_out_influence"]
    )
    assert all(
        0.0 <= row["sign_agreement_share"] <= 1.0
        for row in evidence["cross_period_persistence"]
    )


def test_actual_hour_metrics_use_hour_weights_and_adoption_uses_worker_weights() -> None:
    evidence = build_composition_residual_evidence(
        _panel(),
        {period: _composition_document() for period in PERIODS},
        evidence_tiers=_tiers(),
    )
    period_rows = [row for row in evidence["primary_residuals"] if row["period"] == "2026-Q2"]
    adoption = next(row for row in period_rows if row["metric_id"] == "adoption_work")
    assisted = next(row for row in period_rows if row["metric_id"] == "assisted_hours_share")
    assert adoption["weight_basis"] == "CPS worker share"
    assert adoption["hours_basis"] == "worker"
    assert assisted["weight_basis"] == "CPS actual main-job hour share"
    assert assisted["hours_basis"] == "actual"


def test_usual_hour_suppression_propagates_nulls_without_affecting_primary() -> None:
    evidence = build_composition_residual_evidence(
        _panel(),
        {period: _composition_document(suppress_usual=True) for period in PERIODS},
        evidence_tiers=_tiers(),
    )
    assert evidence["validation"]["primary_supported_row_count"] == 120
    assert all(row["suppressed"] is True for row in evidence["usual_hours_sensitivity"])
    assert all(
        row["occupation_adjusted_industry_context_residual"] is None
        for row in evidence["usual_hours_sensitivity"]
    )


def test_missing_rps_period_and_incomplete_tier_registry_fail_closed() -> None:
    with pytest.raises(CompositionSnapshotError, match="does not contain required"):
        build_composition_residual_evidence(
            _panel(),
            {"2024-Q4": _composition_document()},
            evidence_tiers=_tiers(),
        )
    with pytest.raises(CompositionSnapshotError, match="must contain 20 industries"):
        build_composition_residual_evidence(
            _panel(),
            {"2026-Q2": _composition_document()},
            evidence_tiers=_tiers()[:-1],
        )
