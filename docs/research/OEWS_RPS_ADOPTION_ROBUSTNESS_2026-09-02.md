# OEWS-weighted RPS adoption robustness — 2026-09-02

## Status

This checkpoint records the first successful live application of May-2025 OEWS occupation composition to the RPS work-adoption measure. It is an independent robustness analysis for the CPS worker-share occupation counterfactual, not a replacement estimator and not a pooled CPS/OEWS estimate.

The live computation executed in GitHub Actions run `33687737639` on canonical commit `3fb2cff4a9b1cbc2f340c8db00328efaa2c30130`. The run completed authorized RPS retrieval, source-contract validation, the CPS residual build, the OEWS-weighted adoption calculation, rights-safe evidence assembly, and artifact upload. The RPS scientific-content identity is `fe8bffa7cacd029cc23e2ba7e310d925e8c05322f6d53bd89e8234f02e825b73`.

## Estimand and source distinction

For each RPS industry, the OEWS counterfactual applies May-2025 establishment-side occupational employment shares to RPS occupation-level work-adoption rates. The residual is observed RPS industry adoption minus that OEWS-weighted occupation counterfactual.

This is deliberately separate from the primary CPS worker-share counterfactual. CPS/RPS describe employed people from a household-side frame; OEWS describes wage-and-salary employment from establishments and excludes important parts of the self-employed universe. The two residuals must not be averaged, and residual magnitude differences are not treated as measurement error by construction.

Q2 2025 is the primary temporal comparison because it is closest to the May-2025 OEWS vintage. Q2 2026 is retained as a cross-vintage sensitivity.

## Missing OEWS cells

Unpublished OEWS industry-by-occupation cells are not set to zero. For an incomplete industry vector, published occupation counts are divided by the published all-occupations employment total. The remaining published-total mass is allowed to occupy the missing canonical occupation groups. Because the adoption counterfactual is linear, the lower and upper bounds place that residual mass on the minimum and maximum RPS adoption values among the missing occupations.

If published observed occupation employment exceeds the published all-occupations total, the procedure fails closed instead of introducing an implicit rounding model.

The live build produced 40 industry-period counterfactual rows. Thirty-two are point identified and eight are partially identified; no row is unsupported. Among the 17 primary-comparability industries in each quarter, 14 are point identified and three are partially identified. The three partially identified primary industries are Mining, Utilities, and Real Estate in both quarters. Their intervals are narrow: the maximum primary residual interval width is 0.0622 percentage points in Q2 2025 and 0.0270 percentage points in Q2 2026.

## Cross-source result

Across the 17 primary-comparability industries, CPS and OEWS residual signs agree for 16 of 17 industries in Q2 2025 and 16 of 17 in Q2 2026. No primary result has an indeterminate OEWS sign.

Among the 14 point-identified primary industries, residual-rank Spearman correlation is 0.833 in Q2 2025 and 0.969 in Q2 2026. Median absolute CPS-versus-OEWS residual differences are 1.95 percentage points and 2.86 percentage points respectively. These magnitude differences are retained as evidence of source-universe/composition sensitivity; they are not averaged away.

The single directional disagreement changes across quarters:

- **Q2 2025 — Arts, Entertainment, and Recreation:** CPS residual `-0.232 pp`; OEWS residual `+6.998 pp`.
- **Q2 2026 — Educational Services:** CPS residual `-0.842 pp`; OEWS residual `+1.012 pp`.

The disagreement cases are important. The Q2-2025 CPS residual for Arts/Entertainment/Recreation is near zero while the OEWS result is materially positive. In Q2 2026, Educational Services remains a smaller but genuine sign disagreement. Neither is suppressed from the evidence package.

## Interpretation

The independent establishment-side weighting exercise supports a strong robustness statement for the **direction and cross-industry ordering of adoption residuals**, particularly in Q2 2026. It does not establish equality of CPS and OEWS counterfactual magnitudes, and it does not identify an organizational effect.

This analysis also does not provide an independent OEWS robustness test for assisted-hours penetration or reported time savings. Those measures require work-hour composition weights; substituting OEWS employment shares for the primary CPS actual-hour weights would change the estimand and is not done.

The result therefore strengthens the evidence that occupation mix alone does not reproduce all observed cross-industry adoption differences, while preserving the project's central limitation: the remaining residual is a descriptive occupation-adjusted industry-context gap. It is not a causal organizational, efficiency, productivity, or technology-effect estimate.

## Publication disposition

The OEWS comparison is suitable as contextual robustness evidence. It does **not** justify an industry residual leaderboard. The primary CPS leave-one-occupation analysis remains materially influential, temporal persistence is incomplete, and formal CPS design-based uncertainty remains a separate unresolved gate under issue #14.

## Durable evidence

Canonical derived files under `data/derived/composition/oews-rps-adoption-2026-09-02/` contain:

- primary OEWS counterfactuals for the 17 primary-comparability industries in Q2 2025 and Q2 2026;
- the corresponding independent CPS-versus-OEWS residual comparison;
- the live summary and validation checks;
- exact input/source identities and workflow provenance.

The 962-observation private RPS source snapshot is not committed. The full 40-row transient live outputs remain cryptographically identified in `provenance.json`; the durable public tables retain the primary-comparability analytical subset required for the robustness conclusion.
