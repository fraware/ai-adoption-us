# Empirical results — verified public summary

## Status and scope

This document summarizes the results reproduced from the private audited five-wave RPS subgroup fixture and published only as rights-safe derived diagnostics.

Scope:

- periods: Q2 2025, Q3 2025, Q4 2025, Q1 2026, Q2 2026;
- industries: 20;
- occupations: 22;
- constructs: work adoption (`A`), assisted-hours share (`H`), reported-time-savings share (`S`);
- private audited cells: 630;
- public raw RPS observations: **not distributed here**;
- analysis: unweighted aggregate cross-sectional descriptive diagnostics;
- causal claims: **none**.

The canonical generated source for the numbers below is `data/derived/longitudinal/longitudinal_diagnostics.json`.

## Core finding 1 — occupation structure couples adoption and workflow penetration more tightly

For every audited wave, both Pearson and Spearman alignment between work adoption and assisted-hours share are higher across occupations than across industries.

| Quarter | Industry Pearson r(A,H) | Occupation Pearson r(A,H) | Difference | Industry Spearman | Occupation Spearman |
|---|---:|---:|---:|---:|---:|
| 2025-Q2 | 0.557 | 0.840 | +0.283 | 0.451 | 0.809 |
| 2025-Q3 | 0.794 | 0.813 | +0.019 | 0.803 | 0.814 |
| 2025-Q4 | 0.641 | 0.898 | +0.257 | 0.629 | 0.906 |
| 2026-Q1 | 0.676 | 0.711 | +0.035 | 0.582 | 0.719 |
| 2026-Q2 | 0.756 | 0.886 | +0.130 | 0.675 | 0.886 |

Defensible interpretation: occupation/task structure organizes the aggregate adoption-to-penetration relationship more tightly than industry aggregation does.

Not identified: the remaining industry wedge cannot be labeled an organizational effect. It may reflect detailed task mix, worker selection, firm policies, employer tooling, firm characteristics, regulatory context, sampling variation, or other mechanisms.

## Core finding 2 — occupation adoption is an unusually robust descriptor of reported savings

Across occupations, `R²(S~A) > R²(S~H)` in all five waves.

| Quarter | R²(S~A) | R²(S~H) | R²(S~A+H) | Incremental H given A |
|---|---:|---:|---:|---:|
| 2025-Q2 | 0.857 | 0.624 | 0.857 | 0.001 |
| 2025-Q3 | 0.707 | 0.366 | 0.725 | 0.018 |
| 2025-Q4 | 0.923 | 0.862 | 0.945 | 0.022 |
| 2026-Q1 | 0.766 | 0.682 | 0.850 | 0.084 |
| 2026-Q2 | 0.793 | 0.663 | 0.796 | 0.003 |

The ordering survives all **110/110** leave-one-occupation-out comparisons (5 waves × 22 omitted occupations).

This does not establish that adoption causes time savings. Both are aggregate subgroup measurements and reported savings are a self-reported counterfactual construct.

## Core finding 3 — the industry savings relationship changes by wave

Across industries, the ordering between adoption and assisted hours as descriptors of reported savings is not stable.

| Quarter | R²(S~A) | R²(S~H) | H minus A | R²(S~A+H) | Incremental H given A |
|---|---:|---:|---:|---:|---:|
| 2025-Q2 | 0.353 | 0.612 | +0.259 | 0.649 | 0.296 |
| 2025-Q3 | 0.767 | 0.506 | -0.261 | 0.767 | 0.001 |
| 2025-Q4 | 0.636 | 0.793 | +0.158 | 0.880 | 0.245 |
| 2026-Q1 | 0.796 | 0.663 | -0.133 | 0.878 | 0.082 |
| 2026-Q2 | 0.674 | 0.729 | +0.055 | 0.801 | 0.127 |

`H` outperforms `A` in 3 of 5 waves; `A` outperforms `H` in 2 of 5 waves.

Therefore the Q2 2026 result — assisted hours explaining more industry-level variation in reported savings than adoption — is real but **wave-dependent**, not a general law.

## Core finding 4 — adoption rankings are substantially more persistent

Median Spearman rank correlations across all 10 quarter pairs:

| Aggregation | Adoption | Assisted hours | Reported savings |
|---|---:|---:|---:|
| Industries | **0.850** | 0.614 | 0.711 |
| Occupations | **0.873** | 0.608 | 0.727 |

Adoption rank persistence exceeds assisted-hours rank persistence in **10/10** quarter-pair comparisons for industries and **10/10** for occupations.

Adoption rank persistence also exceeds reported-savings rank persistence in **10/10** quarter-pair comparisons at both aggregation levels.

Interpretation: the hierarchy of who adopts GenAI is relatively persistent, while the depth of active workflow penetration and reported benefit is materially more variable.

## Q2 2026 reproduced reference diagnostics

Industries:

- `R²(H~A) = 0.572065`
- `R²(S~A) = 0.674362`
- `R²(S~H) = 0.729351`
- `R²(S~A+H) = 0.801126`
- `r(A,H) = 0.756350`
- leave-one-industry comparison: H beats A in 18/20 omissions.

Occupations:

- `R²(H~A) = 0.784730`
- `R²(S~A) = 0.793013`
- `R²(S~H) = 0.662970`
- `R²(S~A+H) = 0.796002`
- `r(A,H) = 0.885850`
- leave-one-occupation comparison: A beats H in 22/22 omissions.

## What these results do not establish

They do not establish:

- measured labor productivity;
- output or TFP effects;
- wage effects;
- employment effects;
- organizational quality;
- firm-level complementarity;
- causal effects of adoption or assisted use;
- conventional statistical significance of subgroup differences.

Subgroup standard errors are not available in the audited series pages used for this reconstruction. Quarterly movement can represent a combination of true change and sampling variation.

## Current scientific interpretation

The most defensible current conceptual model is:

```text
persistent diffusion/adoption hierarchy
        ↓
workflow conversion / penetration
        ↓
reported benefit
```

Occupation structure tightly organizes the first conversion relationship. Industry introduces additional variation that remains mechanistically unidentified.

That unidentified wedge is the target of Release 1.1 composition analysis and the longer-run mechanism research program.
