"""Occupation-composition counterfactuals for RPS industry outcomes.

These are descriptive counterfactuals. A residual is named an occupation-adjusted
industry-context residual and is not interpreted as an organizational or causal effect.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from genai_at_work.cps import IndustryComposition
from genai_at_work.metrics.conversion import composition_counterfactual

WORKER_METRICS = {"adoption_work"}
HOUR_METRICS = {"assisted_hours_share", "reported_time_savings_share"}


def _coerce_float(value: object, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError(f"{field} must be numeric, got {type(value).__name__}")
    try:
        return float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{field} must be numeric, got {value!r}") from exc


@dataclass(frozen=True)
class CompositionResidual:
    industry_id: str
    industry_index: int
    period: str
    metric_id: str
    weight_basis: str
    observed: float | None
    predicted_from_occupation_mix: float | None
    occupation_adjusted_industry_context_residual: float | None
    suppressed: bool
    coverage: float | None


def _rps_values(
    records: Iterable[Mapping[str, object]],
    *,
    entity_type: str,
    period: str,
    metric_id: str,
) -> dict[str, float]:
    out: dict[str, float] = {}
    for row in records:
        if (
            str(row.get("entity_type")) == entity_type
            and str(row.get("period")) == period
            and str(row.get("metric_id")) == metric_id
        ):
            entity_id = str(row["entity_id"])
            if entity_id in out:
                raise ValueError(f"duplicate RPS value for {entity_type}/{entity_id}/{metric_id}/{period}")
            out[entity_id] = _coerce_float(row["value"], field="RPS value")
    return out


def composition_residuals(
    compositions: Iterable[IndustryComposition],
    rps_records: Iterable[Mapping[str, object]],
    *,
    period: str,
    metric_id: str,
    hours_basis: str = "actual",
) -> list[CompositionResidual]:
    if metric_id not in WORKER_METRICS | HOUR_METRICS:
        raise ValueError(f"unsupported composition metric: {metric_id}")
    if hours_basis not in {"actual", "usual"}:
        raise ValueError("hours_basis must be 'actual' or 'usual'")

    records = list(rps_records)
    occupation = _rps_values(records, entity_type="occupation", period=period, metric_id=metric_id)
    industry = _rps_values(records, entity_type="industry", period=period, metric_id=metric_id)
    if not occupation:
        raise ValueError(f"no occupation RPS values for {metric_id}/{period}")
    if not industry:
        raise ValueError(f"no industry RPS values for {metric_id}/{period}")

    out: list[CompositionResidual] = []
    for comp in compositions:
        observed = industry.get(comp.industry_id)
        if observed is None:
            raise ValueError(f"missing observed industry RPS value for {comp.industry_id}/{metric_id}/{period}")

        if metric_id in WORKER_METRICS:
            weights = comp.worker_weights
            suppressed = comp.worker_suppressed
            coverage = comp.worker_coverage
            weight_basis = "CPS worker share"
        elif hours_basis == "actual":
            weights = comp.actual_hour_weights
            suppressed = comp.actual_hours_suppressed
            coverage = min(
                comp.actual_hours_valid_worker_coverage,
                comp.actual_hours_mapping_coverage if comp.actual_hours_mapping_coverage is not None else 0.0,
            )
            weight_basis = "CPS actual main-job hour share"
        else:
            weights = comp.usual_hour_weights
            suppressed = comp.usual_hours_suppressed
            coverage = min(
                comp.usual_hours_valid_worker_coverage,
                comp.usual_hours_mapping_coverage if comp.usual_hours_mapping_coverage is not None else 0.0,
            )
            weight_basis = "CPS usual main-job hour share (sensitivity)"

        if suppressed or weights is None:
            predicted = residual = None
        else:
            missing = sorted(set(weights) - set(occupation))
            if missing:
                raise ValueError(f"missing occupation RPS values required by composition: {missing}")
            keys = sorted(weights)
            predicted = composition_counterfactual(
                [weights[k] for k in keys],
                [occupation[k] for k in keys],
            )
            residual = observed - predicted

        out.append(
            CompositionResidual(
                industry_id=comp.industry_id,
                industry_index=comp.industry_index,
                period=period,
                metric_id=metric_id,
                weight_basis=weight_basis,
                observed=observed,
                predicted_from_occupation_mix=predicted,
                occupation_adjusted_industry_context_residual=residual,
                suppressed=suppressed or weights is None,
                coverage=coverage,
            )
        )
    return sorted(out, key=lambda row: row.industry_index)
