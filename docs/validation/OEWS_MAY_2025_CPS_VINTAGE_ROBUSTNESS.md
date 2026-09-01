# May 2025 OEWS cross-source and CPS-vintage robustness

## Status

This checkpoint separates two sources of disagreement in occupation composition: source-system differences between OEWS and CPS, and temporal movement between Q2 2025 and Q2 2026 CPS.

The OEWS source is held fixed at May 2025. No additional BLS request is made by this comparison step; it consumes the previously frozen OEWS aggregate artifact.

## Exact-vector comparison

For primary-comparability industries with all 22 OEWS major occupation groups published:

- OEWS vs Q2 2025 CPS median L1: **0.2772387012212034**
- OEWS vs Q2 2025 CPS median cosine: **0.9724645398102251**
- OEWS vs Q2 2025 CPS median Spearman: **0.9604743083003953**
- OEWS vs Q2 2026 CPS median L1: **0.25325221201813486**
- OEWS vs Q2 2026 CPS median cosine: **0.973706182811574**
- OEWS vs Q2 2026 CPS median Spearman: **0.9491812535290797**

The exact same-industry L1 difference is defined as Q2-2026 L1 minus Q2-2025 L1. Its median is **0.004652307064510364** across **11** primary industries with exact OEWS vectors.

## Partial identification for unpublished OEWS cells

All primary industries with a coherent published-total residual receive an L1 interval. Complete OEWS vectors have zero-width intervals. Incomplete vectors allow the residual unpublished employment mass to be allocated arbitrarily across the missing canonical occupations.

- Q2 2025 CPS median primary L1 lower bound: **0.2980375879144468**
- Q2 2025 CPS median primary L1 upper bound: **0.2980375879144468**
- Q2 2026 CPS median primary L1 lower bound: **0.3209737915610507**
- Q2 2026 CPS median primary L1 upper bound: **0.3209737915610507**
- maximum unresolved OEWS mass share among partially identified primary industries: **0.001976976461624004**

These intervals address unpublished-cell allocation only. They do not represent confidence intervals and do not absorb OEWS model uncertainty, CPS sampling uncertainty, or published-value rounding uncertainty.

## CPS temporal stability

Across primary-comparability industries, Q2 2025 versus Q2 2026 CPS worker-share composition has:

- median L1 distance: **0.08960026006702666**
- median cosine similarity: **0.9972584734339354**
- median Spearman rank correlation: **0.9607344632768362**

## Scientific boundary

This analysis strengthens or weakens the claim that the CPS occupation-composition layer is structurally reasonable across an independent employer-side source and nearby vintages. It does not identify an RPS industry-context effect. That gate remains closed until an authorized compatible RPS occupation vintage is available.
