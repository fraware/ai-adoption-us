"""Build rights-safe occupation-composition residual evidence from a validated RPS panel.

The source-side input is a :class:`PreparedRpsPanel` produced by the RPS release
adapter. No raw RPS source snapshot is emitted. The outputs are descriptive
standardization diagnostics only: an occupation-adjusted industry-context
residual is observed industry aggregate minus the occupation-mix counterfactual.
It is not an organizational, productivity, efficiency, or causal effect.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict
from itertools import combinations
from math import isfinite
from statistics import median
from typing import Any

from genai_at_work.composition import (
    HOUR_METRICS,
    WORKER_METRICS,
    CompositionResidual,
    composition_residuals,
)
from genai_at_work.cps import IndustryComposition
from genai_at_work.longitudinal import AuditRecord, ranks, spearman
from genai_at_work.rps_release import PreparedRpsPanel

PRIMARY_METRICS = (
    "adoption_work",
    "assisted_hours_share",
    "reported_time_savings_share",
)
EXPECTED_INDUSTRY_COUNT = 20


class CompositionSnapshotError(ValueError):
    """Raised when snapshot-native composition evidence violates its contract."""


def _float(mapping: Mapping[str, Any], key: str, *, context: str) -> float:
    value = mapping.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CompositionSnapshotError(f"{context}.{key} must be numeric")
    numeric = float(value)
    if not isfinite(numeric):
        raise CompositionSnapshotError(f"{context}.{key} must be finite")
    return numeric


def _optional_float(mapping: Mapping[str, Any], key: str, *, context: str) -> float | None:
    value = mapping.get(key)
    if value is None:
        return None
    return _float(mapping, key, context=context)


def _int(mapping: Mapping[str, Any], key: str, *, context: str) -> int:
    value = mapping.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise CompositionSnapshotError(f"{context}.{key} must be an integer")
    return value


def _bool(mapping: Mapping[str, Any], key: str, *, context: str) -> bool:
    value = mapping.get(key)
    if not isinstance(value, bool):
        raise CompositionSnapshotError(f"{context}.{key} must be boolean")
    return value


def _string(mapping: Mapping[str, Any], key: str, *, context: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise CompositionSnapshotError(f"{context}.{key} must be a non-empty string")
    return value


def _weights(mapping: Mapping[str, Any], key: str, *, context: str) -> dict[str, float] | None:
    raw = mapping.get(key)
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        raise CompositionSnapshotError(f"{context}.{key} must be an object or null")
    out: dict[str, float] = {}
    for occupation_id, value in raw.items():
        if not isinstance(occupation_id, str) or not occupation_id:
            raise CompositionSnapshotError(f"{context}.{key} contains an invalid occupation id")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise CompositionSnapshotError(f"{context}.{key}.{occupation_id} must be numeric")
        numeric = float(value)
        if not isfinite(numeric) or numeric < 0.0:
            raise CompositionSnapshotError(
                f"{context}.{key}.{occupation_id} must be finite and non-negative"
            )
        out[occupation_id] = numeric
    return out


def compositions_from_document(document: Mapping[str, Any]) -> list[IndustryComposition]:
    """Parse a checked-in CPS composition document without accepting extra fields blindly."""

    raw_industries = document.get("industries")
    if not isinstance(raw_industries, list):
        raise CompositionSnapshotError("composition.industries must be a list")
    out: list[IndustryComposition] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_industries):
        if not isinstance(raw, Mapping):
            raise CompositionSnapshotError(f"composition.industries[{index}] must be an object")
        context = f"composition.industries[{index}]"
        industry_id = _string(raw, "industry_id", context=context)
        if industry_id in seen:
            raise CompositionSnapshotError(f"duplicate CPS composition industry_id: {industry_id}")
        seen.add(industry_id)
        out.append(
            IndustryComposition(
                industry_id=industry_id,
                industry_index=_int(raw, "industry_index", context=context),
                worker_coverage=_float(raw, "worker_coverage", context=context),
                actual_hours_valid_worker_coverage=_float(
                    raw, "actual_hours_valid_worker_coverage", context=context
                ),
                actual_hours_mapping_coverage=_optional_float(
                    raw, "actual_hours_mapping_coverage", context=context
                ),
                usual_hours_valid_worker_coverage=_float(
                    raw, "usual_hours_valid_worker_coverage", context=context
                ),
                usual_hours_mapping_coverage=_optional_float(
                    raw, "usual_hours_mapping_coverage", context=context
                ),
                worker_weights=_weights(raw, "worker_weights", context=context),
                actual_hour_weights=_weights(raw, "actual_hour_weights", context=context),
                usual_hour_weights=_weights(raw, "usual_hour_weights", context=context),
                worker_suppressed=_bool(raw, "worker_suppressed", context=context),
                actual_hours_suppressed=_bool(raw, "actual_hours_suppressed", context=context),
                usual_hours_suppressed=_bool(raw, "usual_hours_suppressed", context=context),
            )
        )
    out.sort(key=lambda row: row.industry_index)
    if len(out) != EXPECTED_INDUSTRY_COUNT:
        raise CompositionSnapshotError(
            f"CPS composition must contain {EXPECTED_INDUSTRY_COUNT} industries, observed {len(out)}"
        )
    if [row.industry_index for row in out] != list(range(1, EXPECTED_INDUSTRY_COUNT + 1)):
        raise CompositionSnapshotError("CPS composition industry indices must be exactly 1..20")
    return out


def audit_records_as_mappings(records: Sequence[AuditRecord]) -> list[dict[str, object]]:
    """Expose only the subgroup fields required by the composition calculation."""

    return [
        {
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "metric_id": row.metric_id,
            "period": row.period,
            "value": row.value,
        }
        for row in records
    ]


def _tier_index(raw_tiers: Sequence[Mapping[str, Any]] | None) -> dict[str, dict[str, Any]]:
    if raw_tiers is None:
        return {}
    out: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(raw_tiers):
        industry_id = _string(raw, "industry_id", context=f"evidence_tiers[{index}]")
        if industry_id in out:
            raise CompositionSnapshotError(f"duplicate evidence tier for {industry_id}")
        tier = _string(raw, "evidence_tier", context=f"evidence_tiers[{index}]")
        out[industry_id] = {
            "composition_basis_evidence_tier": tier,
            "composition_basis_reason": raw.get("reason"),
            "composition_basis_stability_threshold_l1": raw.get("stability_threshold_l1"),
            "composition_basis_max_leave_one_month_out_l1": raw.get(
                "maximum_leave_one_month_out_l1_across_required_periods"
            ),
        }
    if len(out) != EXPECTED_INDUSTRY_COUNT:
        raise CompositionSnapshotError(
            f"Evidence-tier registry must contain {EXPECTED_INDUSTRY_COUNT} industries"
        )
    return out


def _weight_vector(
    composition: IndustryComposition,
    *,
    metric_id: str,
    hours_basis: str,
) -> dict[str, float] | None:
    if metric_id in WORKER_METRICS:
        return composition.worker_weights
    if metric_id not in HOUR_METRICS:
        raise CompositionSnapshotError(f"unsupported metric for influence analysis: {metric_id}")
    if hours_basis == "actual":
        return composition.actual_hour_weights
    if hours_basis == "usual":
        return composition.usual_hour_weights
    raise CompositionSnapshotError(f"unsupported hours basis: {hours_basis}")


def _occupation_values(
    records: Sequence[Mapping[str, object]], *, period: str, metric_id: str
) -> dict[str, float]:
    out: dict[str, float] = {}
    for row in records:
        if (
            row.get("entity_type") == "occupation"
            and row.get("period") == period
            and row.get("metric_id") == metric_id
        ):
            entity_id = row.get("entity_id")
            value = row.get("value")
            if not isinstance(entity_id, str):
                raise CompositionSnapshotError("occupation record has invalid entity_id")
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise CompositionSnapshotError("occupation record has invalid value")
            out[entity_id] = float(value)
    return out


def _influence_for_row(
    residual: CompositionResidual,
    composition: IndustryComposition,
    records: Sequence[Mapping[str, object]],
    *,
    hours_basis: str,
) -> dict[str, Any]:
    base = residual.occupation_adjusted_industry_context_residual
    observed = residual.observed
    weights = _weight_vector(composition, metric_id=residual.metric_id, hours_basis=hours_basis)
    if residual.suppressed or base is None or observed is None or weights is None:
        return {
            "industry_id": residual.industry_id,
            "industry_index": residual.industry_index,
            "period": residual.period,
            "metric_id": residual.metric_id,
            "hours_basis": hours_basis,
            "supported": False,
            "max_absolute_residual_shift": None,
            "most_influential_occupation_id": None,
            "most_influential_occupation_weight": None,
            "baseline_residual": base,
            "perturbed_residual": None,
        }

    occupation = _occupation_values(records, period=residual.period, metric_id=residual.metric_id)
    perturbations: list[tuple[float, str, float, float]] = []
    for occupation_id, removed_weight in sorted(weights.items()):
        if removed_weight <= 0.0 or removed_weight >= 1.0:
            continue
        if occupation_id not in occupation:
            raise CompositionSnapshotError(
                f"missing RPS occupation value for leave-one-out sensitivity: {occupation_id}"
            )
        denominator = 1.0 - removed_weight
        predicted = sum(
            weight * occupation[other_id]
            for other_id, weight in weights.items()
            if other_id != occupation_id
        ) / denominator
        perturbed_residual = observed - predicted
        shift = perturbed_residual - base
        perturbations.append((abs(shift), occupation_id, removed_weight, perturbed_residual))

    if not perturbations:
        raise CompositionSnapshotError(
            f"no valid leave-one-occupation-out perturbation for {residual.industry_id}/{residual.metric_id}"
        )
    max_abs, occupation_id, removed_weight, perturbed_residual = max(
        perturbations, key=lambda item: (item[0], item[1])
    )
    return {
        "industry_id": residual.industry_id,
        "industry_index": residual.industry_index,
        "period": residual.period,
        "metric_id": residual.metric_id,
        "hours_basis": hours_basis,
        "supported": True,
        "sensitivity_definition": "remove one positive-weight occupation and renormalize remaining weights to one",
        "max_absolute_residual_shift": max_abs,
        "most_influential_occupation_id": occupation_id,
        "most_influential_occupation_weight": removed_weight,
        "baseline_residual": base,
        "perturbed_residual": perturbed_residual,
    }


def _sign(value: float) -> int:
    if value > 0.0:
        return 1
    if value < 0.0:
        return -1
    return 0


def _persistence(
    primary_rows: Sequence[Mapping[str, Any]],
    periods: Sequence[str],
    *,
    tier: str | None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for earlier, later in combinations(periods, 2):
        for metric_id in PRIMARY_METRICS:
            by_period: dict[str, dict[str, Mapping[str, Any]]] = {}
            for period in (earlier, later):
                indexed: dict[str, Mapping[str, Any]] = {}
                for row in primary_rows:
                    if row.get("period") != period or row.get("metric_id") != metric_id:
                        continue
                    if tier is not None and row.get("composition_basis_evidence_tier") != tier:
                        continue
                    residual = row.get("occupation_adjusted_industry_context_residual")
                    if isinstance(residual, bool) or not isinstance(residual, (int, float)):
                        continue
                    industry_id = row.get("industry_id")
                    if not isinstance(industry_id, str):
                        raise CompositionSnapshotError("primary residual row has invalid industry_id")
                    indexed[industry_id] = row
                by_period[period] = indexed
            common = sorted(set(by_period[earlier]) & set(by_period[later]))
            if len(common) < 2:
                continue
            earlier_values = [
                float(by_period[earlier][industry_id]["occupation_adjusted_industry_context_residual"])
                for industry_id in common
            ]
            later_values = [
                float(by_period[later][industry_id]["occupation_adjusted_industry_context_residual"])
                for industry_id in common
            ]
            sign_agreement = sum(
                _sign(first) == _sign(second)
                for first, second in zip(earlier_values, later_values, strict=True)
            )
            out.append(
                {
                    "earlier_period": earlier,
                    "later_period": later,
                    "metric_id": metric_id,
                    "cohort": tier or "all_supported",
                    "industry_count": len(common),
                    "residual_rank_spearman": spearman(ranks(earlier_values), ranks(later_values)),
                    "sign_agreement_count": sign_agreement,
                    "sign_agreement_share": sign_agreement / len(common),
                    "median_absolute_residual_change": median(
                        abs(second - first)
                        for first, second in zip(earlier_values, later_values, strict=True)
                    ),
                }
            )
    return out


def build_composition_residual_evidence(
    panel: PreparedRpsPanel,
    composition_documents: Mapping[str, Mapping[str, Any]],
    *,
    evidence_tiers: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build derived residual, influence, and cross-period persistence evidence."""

    if not composition_documents:
        raise CompositionSnapshotError("at least one CPS composition document is required")
    requested_periods = tuple(sorted(composition_documents))
    unavailable = sorted(set(requested_periods) - set(panel.periods))
    if unavailable:
        raise CompositionSnapshotError(
            f"RPS panel does not contain required CPS composition periods: {unavailable}"
        )

    tier_by_industry = _tier_index(evidence_tiers)
    records = audit_records_as_mappings(panel.subgroup_records)
    primary_rows: list[dict[str, Any]] = []
    sensitivity_rows: list[dict[str, Any]] = []
    influence_rows: list[dict[str, Any]] = []

    for period in requested_periods:
        compositions = compositions_from_document(composition_documents[period])
        composition_by_id = {row.industry_id: row for row in compositions}
        if tier_by_industry and set(composition_by_id) != set(tier_by_industry):
            raise CompositionSnapshotError(
                f"CPS composition/evidence-tier industry mismatch for {period}"
            )

        for metric_id in PRIMARY_METRICS:
            residuals = composition_residuals(
                compositions,
                records,
                period=period,
                metric_id=metric_id,
                hours_basis="actual",
            )
            for residual in residuals:
                row = asdict(residual)
                row["hours_basis"] = "worker" if metric_id in WORKER_METRICS else "actual"
                row["interpretation"] = "occupation-adjusted descriptive industry-context residual; not a causal or organizational effect"
                if tier_by_industry:
                    row.update(tier_by_industry[residual.industry_id])
                primary_rows.append(row)
                influence_rows.append(
                    _influence_for_row(
                        residual,
                        composition_by_id[residual.industry_id],
                        records,
                        hours_basis="actual",
                    )
                )

        for metric_id in sorted(HOUR_METRICS):
            residuals = composition_residuals(
                compositions,
                records,
                period=period,
                metric_id=metric_id,
                hours_basis="usual",
            )
            for residual in residuals:
                row = asdict(residual)
                row["hours_basis"] = "usual_sensitivity"
                row["interpretation"] = "usual-hours sensitivity only; occupation-adjusted descriptive industry-context residual"
                if tier_by_industry:
                    row.update(tier_by_industry[residual.industry_id])
                sensitivity_rows.append(row)

    expected_primary = len(requested_periods) * len(PRIMARY_METRICS) * EXPECTED_INDUSTRY_COUNT
    if len(primary_rows) != expected_primary:
        raise CompositionSnapshotError(
            f"primary residual row count mismatch: expected {expected_primary}, observed {len(primary_rows)}"
        )
    expected_sensitivity = len(requested_periods) * len(HOUR_METRICS) * EXPECTED_INDUSTRY_COUNT
    if len(sensitivity_rows) != expected_sensitivity:
        raise CompositionSnapshotError(
            f"usual-hours sensitivity row count mismatch: expected {expected_sensitivity}, observed {len(sensitivity_rows)}"
        )

    invalid_identity = 0
    unsupported_nonnull = 0
    supported_primary = 0
    for row in primary_rows:
        observed = row["observed"]
        predicted = row["predicted_from_occupation_mix"]
        residual = row["occupation_adjusted_industry_context_residual"]
        suppressed = bool(row["suppressed"])
        if suppressed:
            if predicted is not None or residual is not None:
                unsupported_nonnull += 1
            continue
        supported_primary += 1
        if not all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in (observed, predicted, residual)):
            invalid_identity += 1
            continue
        if abs(float(observed) - float(predicted) - float(residual)) > 1e-9:
            invalid_identity += 1

    persistence = _persistence(primary_rows, requested_periods, tier=None)
    if tier_by_industry:
        persistence.extend(
            _persistence(primary_rows, requested_periods, tier="primary_stable")
        )

    validation = {
        "status": "pass" if invalid_identity == 0 and unsupported_nonnull == 0 else "fail",
        "periods": list(requested_periods),
        "rps_panel_periods": list(panel.periods),
        "source_series_count": panel.series_count,
        "source_observation_count": panel.observation_count,
        "primary_row_count": len(primary_rows),
        "primary_supported_row_count": supported_primary,
        "primary_suppressed_row_count": len(primary_rows) - supported_primary,
        "usual_hours_sensitivity_row_count": len(sensitivity_rows),
        "leave_one_occupation_out_row_count": len(influence_rows),
        "residual_identity_failure_count": invalid_identity,
        "unsupported_nonnull_failure_count": unsupported_nonnull,
        "composition_evidence_tiers_bound": bool(tier_by_industry),
        "interpretation_boundary": (
            "Residuals are descriptive standardization gaps. Leave-one-occupation-out diagnostics are explicit renormalized sensitivities, not sampling inference. Rank/sign persistence is descriptive and does not identify organizational or productivity effects."
        ),
    }
    if validation["status"] != "pass":
        raise CompositionSnapshotError(f"composition residual validation failed: {validation}")

    return {
        "schema_version": 1,
        "artifact_type": "rps_cps_occupation_adjusted_industry_context_residual_evidence",
        "source_definition_id": panel.definition_id,
        "source_taxonomy_version": panel.taxonomy_version,
        "periods": list(requested_periods),
        "primary_residuals": primary_rows,
        "usual_hours_sensitivity": sensitivity_rows,
        "leave_one_occupation_out_influence": influence_rows,
        "cross_period_persistence": persistence,
        "validation": validation,
        "publication_guardrail": (
            "Do not publish a one-quarter residual leaderboard. Any display must expose weighting basis, coverage, suppression, composition-basis evidence tier, influence context, and cross-period persistence."
        ),
    }
