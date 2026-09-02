"""Deterministic BTOS-RPS industry triangulation under the canonical v1 protocol."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any


def average_ranks(values: Sequence[float]) -> list[float]:
    """Return one-based average ranks, preserving ties exactly."""

    order = sorted(range(len(values)), key=values.__getitem__)
    ranks = [0.0] * len(values)
    cursor = 0
    while cursor < len(order):
        end = cursor
        while end + 1 < len(order) and values[order[end + 1]] == values[order[cursor]]:
            end += 1
        rank = ((cursor + 1) + (end + 1)) / 2.0
        for position in range(cursor, end + 1):
            ranks[order[position]] = rank
        cursor = end + 1
    return ranks


def pearson_correlation(x: Sequence[float], y: Sequence[float]) -> float:
    """Return the ordinary unweighted Pearson correlation."""

    if len(x) != len(y):
        raise ValueError("correlation inputs must have equal length")
    if len(x) < 2:
        raise ValueError("correlation requires at least two observations")

    x_mean = sum(x) / len(x)
    y_mean = sum(y) / len(y)
    numerator = sum((a - x_mean) * (b - y_mean) for a, b in zip(x, y, strict=True))
    x_ss = sum((a - x_mean) ** 2 for a in x)
    y_ss = sum((b - y_mean) ** 2 for b in y)
    denominator = math.sqrt(x_ss * y_ss)
    if denominator == 0:
        raise ValueError("correlation is undefined for a constant input")
    return numerator / denominator


def spearman_correlation(x: Sequence[float], y: Sequence[float]) -> float:
    """Return Spearman rank correlation using average ranks for ties."""

    return pearson_correlation(average_ranks(x), average_ranks(y))


def _object_rows(value: object, *, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValueError(f"{label}[{index}] must be an object")
        rows.append({str(key): cell for key, cell in item.items()})
    return rows


def assemble_eligible_pairs(
    btos_checkpoint: dict[str, Any],
    rps_checkpoint: dict[str, Any],
    crosswalk: dict[str, Any],
    *,
    include_limited: bool,
) -> list[dict[str, Any]]:
    """Assemble eligible sector pairs without imputation or fuzzy joins."""

    if rps_checkpoint.get("metric_id") != "adoption_work":
        raise ValueError("v1 triangulation requires RPS adoption_work")
    if rps_checkpoint.get("period") != "Q2 2026":
        raise ValueError("v1 triangulation requires the preregistered RPS Q2 2026 period")
    if btos_checkpoint.get("cycle") != "202611":
        raise ValueError("v1 triangulation requires preregistered BTOS cycle 202611")

    btos_rows = _object_rows(btos_checkpoint.get("sectors"), label="BTOS sectors")
    rps_rows = _object_rows(rps_checkpoint.get("rows"), label="RPS rows")
    crosswalk_rows = _object_rows(crosswalk.get("entries"), label="crosswalk entries")

    btos_by_index = {
        int(row["entity_index"]): row
        for row in btos_rows
        if isinstance(row.get("entity_index"), int)
    }
    rps_by_index = {int(row["entity_index"]): row for row in rps_rows}

    allowed_tiers = {"primary", "limited"} if include_limited else {"primary"}
    pairs: list[dict[str, Any]] = []
    for mapping in sorted(crosswalk_rows, key=lambda row: int(row["entity_index"])):
        if mapping.get("mapping_status") != "mapped":
            continue
        if mapping.get("comparability") not in allowed_tiers:
            continue

        entity_index = int(mapping["entity_index"])
        btos = btos_by_index.get(entity_index)
        rps = rps_by_index.get(entity_index)
        if btos is None or rps is None:
            raise ValueError(f"missing source row for mapped entity {entity_index}")

        if btos.get("entity_id") != mapping.get("entity_id"):
            raise ValueError(f"BTOS entity mismatch for {entity_index}")
        if btos.get("entity_name") != mapping.get("entity_name"):
            raise ValueError(f"BTOS entity name mismatch for {entity_index}")
        if rps.get("entity_name") != mapping.get("entity_name"):
            raise ValueError(f"RPS entity name mismatch for {entity_index}")

        btos_value = btos.get("estimate_pct")
        if btos.get("suppression_code") is not None or btos_value is None:
            continue
        rps_value = rps.get("value_pct")
        if not isinstance(rps_value, int | float):
            continue

        pairs.append(
            {
                "entity_index": entity_index,
                "entity_name": str(mapping["entity_name"]),
                "comparability": str(mapping["comparability"]),
                "btos_estimate_pct": float(btos_value),
                "rps_adoption_work_pct": float(rps_value),
            }
        )

    return pairs


def correlation_summary(pairs: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Compute the two descriptive statistics permitted by protocol v1."""

    if len(pairs) < 10:
        raise ValueError("protocol v1 requires at least 10 eligible sectors")
    btos = [float(row["btos_estimate_pct"]) for row in pairs]
    rps = [float(row["rps_adoption_work_pct"]) for row in pairs]
    return {
        "n": len(pairs),
        "weighting": "unweighted across eligible sectors",
        "spearman_rho": round(spearman_correlation(btos, rps), 12),
        "pearson_r": round(pearson_correlation(btos, rps), 12),
        "inference": "descriptive only; no p-value or confidence interval",
    }


def execute_v1(
    btos_checkpoint: dict[str, Any],
    rps_checkpoint: dict[str, Any],
    crosswalk: dict[str, Any],
) -> dict[str, Any]:
    """Execute the fixed primary analysis and expanded comparability sensitivity."""

    primary_pairs = assemble_eligible_pairs(
        btos_checkpoint, rps_checkpoint, crosswalk, include_limited=False
    )
    expanded_pairs = assemble_eligible_pairs(
        btos_checkpoint, rps_checkpoint, crosswalk, include_limited=True
    )
    primary_indices = {int(row["entity_index"]) for row in primary_pairs}

    pairs = []
    for row in expanded_pairs:
        pairs.append(
            {
                **row,
                "included_primary": int(row["entity_index"]) in primary_indices,
                "included_expanded_sensitivity": True,
            }
        )

    primary = correlation_summary(primary_pairs)
    primary.update(
        {
            "tier": "primary-comparability only",
            "entity_indices": [int(row["entity_index"]) for row in primary_pairs],
        }
    )
    expanded = correlation_summary(expanded_pairs)
    expanded.update(
        {
            "tier": "primary plus eligible limited-comparability sectors",
            "added_entity_indices": [
                int(row["entity_index"])
                for row in expanded_pairs
                if int(row["entity_index"]) not in primary_indices
            ],
        }
    )
    return {"primary": primary, "expanded_sensitivity": expanded, "pairs": pairs}
