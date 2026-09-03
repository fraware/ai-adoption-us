# Empirical results — verified Observatory v1 summary

## Status and scope

This document summarizes the longitudinal RPS results reproduced by the authorized live release pipeline and retained as rights-safe publication evidence.

Current analytical scope:

- common A/H/S periods: Q4 2024, Q1 2025, Q2 2025, Q3 2025, Q4 2025, Q1 2026, Q2 2026;
- industries: 20;
- occupations: 22;
- constructs: work adoption (`A`), assisted-hours share (`H`), reported-time-savings share (`S`);
- complete subgroup A/H/S cells: **882** = (20 + 22) × 3 × 7;
- registered RPS source inventory: 131 series;
- latest authorized live source candidate: 962 source observations across the available registered history;
- public observation scope: bounded attributed presentation views only — seven-quarter national history plus the latest Q2 2026 industry and occupation A/H/S cross-sections;
- historical subgroup source panel: not distributed as a public database;
- analysis: unweighted aggregate cross-sectional descriptive diagnostics;
- causal claims: **none**.

The release-candidate longitudinal artifact is generated deterministically from the authorized RPS source snapshot and hash-bound to the candidate source vintage. Public claims must be reviewed against the exact release artifact before promotion.

## Core finding 1 — occupation structure couples adoption and workflow penetration more tightly

For every one of the seven common A/H/S quarters, both Pearson and Spearman alignment between work adoption and assisted-hours share are higher across occupations than across industries.

| Quarter | Industry Pearson r(A,H) | Occupation Pearson r(A,H) | Difference | Industry Spearman | Occupation Spearman |
|---|---:|---:|---:|---:|---:|
| 2024-Q4 | 0.604 | 0.798 | +0.194 | 0.597 | 0.829 |
| 2025-Q1 | 0.473 | 0.762 | +0.289 | 0.346 | 0.700 |
| 2025-Q2 | 0.557 | 0.840 | +0.283 | 0.451 | 0.809 |
| 2025-Q3 | 0.794 | 0.813 | +0.019 | 0.803 | 0.814 |
| 2025-Q4 | 0.641 | 0.898 | +0.257 | 0.629 | 0.906 |
| 2026-Q1 | 0.676 | 0.711 | +0.035 | 0.582 | 0.719 |
| 2026-Q2 | 0.756 | 0.886 | +0.130 | 0.675 | 0.886 |

Defensible interpretation: occupation/task structure organizes the aggregate adoption-to-penetration relationship more tightly than broad industry aggregation does over the observed seven-quarter window.

Not identified: the remaining industry wedge cannot be labeled an organizational effect. It may reflect detailed task mix, worker selection, firm policies, employer tooling, firm characteristics, regulatory context, sampling variation, or other mechanisms.

## Core finding 2 — occupation adoption is a robust descriptor of reported savings

Across occupations, `R²(S~A) > R²(S~H)` in all seven common quarters.

| Quarter | R²(S~A) | R²(S~H) | R²(S~A+H) | Incremental H given A |
|---|---:|---:|---:|---:|
| 2024-Q4 | 0.858 | 0.574 | 0.859 | 0.001 |
| 2025-Q1 | 0.817 | 0.592 | 0.833 | 0.015 |
| 2025-Q2 | 0.857 | 0.624 | 0.857 | 0.001 |
| 2025-Q3 | 0.707 | 0.366 | 0.725 | 0.018 |
| 2025-Q4 | 0.923 | 0.862 | 0.945 | 0.022 |
| 2026-Q1 | 0.766 | 0.682 | 0.850 | 0.084 |
| 2026-Q2 | 0.793 | 0.663 | 0.796 | 0.003 |

The ordering survives all **154/154** leave-one-occupation-out comparisons: 7 quarters × 22 omitted occupations.

This does not establish that adoption causes reported time savings. Both are aggregate subgroup measurements, and reported savings are a self-reported counterfactual construct.

## Core finding 3 — the industry savings relationship changes by quarter

Across industries, the ordering between adoption and assisted hours as descriptors of reported savings is not stable.

| Quarter | R²(S~A) | R²(S~H) | H minus A | R²(S~A+H) | Incremental H given A |
|---|---:|---:|---:|---:|---:|
| 2024-Q4 | 0.497 | 0.356 | -0.140 | 0.543 | 0.046 |
| 2025-Q1 | 0.426 | 0.542 | +0.116 | 0.662 | 0.236 |
| 2025-Q2 | 0.353 | 0.612 | +0.259 | 0.649 | 0.296 |
| 2025-Q3 | 0.767 | 0.506 | -0.261 | 0.767 | 0.001 |
| 2025-Q4 | 0.636 | 0.793 | +0.158 | 0.880 | 0.245 |
| 2026-Q1 | 0.796 | 0.663 | -0.133 | 0.878 | 0.082 |
| 2026-Q2 | 0.674 | 0.729 | +0.055 | 0.801 | 0.127 |

`H` has the higher univariate R² in **4 of 7** quarters; `A` has the higher value in **3 of 7**.

The Q2 2026 result — assisted hours explaining more industry-level variation in reported savings than adoption — is therefore a reproduced cross-section within a quarter-dependent relationship, not a general law.

## Core finding 4 — adoption rankings are more persistent, with one pairwise exception relative to assisted hours

Median Spearman rank correlations across all 21 quarter pairs:

| Aggregation | Adoption | Assisted hours | Reported savings |
|---|---:|---:|---:|
| Industries | **0.847** | 0.598 | 0.678 |
| Occupations | **0.788** | 0.561 | 0.639 |

Adoption rank persistence exceeds assisted-hours rank persistence in **20/21** quarter-pair comparisons for industries and **20/21** for occupations.

Adoption rank persistence exceeds reported-savings rank persistence in **19/21** quarter-pair comparisons at both aggregation levels.

This supports a comparative persistence claim, not an absolute invariance claim. The hierarchy of who adopts GenAI is more persistent across most quarter pairs, while the depth of active workflow penetration and reported benefit varies more.

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
- `R²(S~A) = 0.793012`
- `R²(S~H) = 0.662970`
- `R²(S~A+H) = 0.796002`
- `r(A,H) = 0.885850`
- leave-one-occupation comparison: A beats H in 22/22 omissions.

## Composition and cross-source evidence

The global Observatory v1 candidate also includes separately governed descriptive evidence:

- CPS Q2 2025 and Q2 2026 occupation-composition counterfactuals and reliability diagnostics;
- occupation-adjusted industry-context residual artifacts with explicit descriptive-only interpretation;
- May 2025 OEWS establishment-side composition robustness evidence;
- preregistered Q2 2026 BTOS–RPS industry triangulation.

The BTOS and RPS percentages are not interchangeable. BTOS measures responding employer businesses reporting AI use in any business function during the last two weeks, while RPS measures employed adults reporting GenAI use for their jobs. Their sector correlations are descriptive cross-source concordance only.

The CPS residuals are likewise not organizational effects, efficiency estimates, or productivity effects. Custom pooled CPS composition vectors do not receive design-based confidence intervals in Release 1 because an approved survey-covariance implementation is not available.

## What these results do not establish

They do not establish:

- measured labor productivity;
- output or TFP effects;
- wage effects;
- employment effects;
- organizational quality;
- firm-level complementarity;
- causal effects of adoption or assisted use;
- causal interpretation of occupation-adjusted industry residuals;
- construct equivalence between BTOS employer AI use and RPS worker GenAI adoption;
- conventional design-based statistical significance for the custom pooled CPS composition vectors.

Quarterly movement can represent a combination of true change, composition change, and sampling variation. Descriptive correlations and regressions are reported as such.

## Current scientific interpretation

The strongest current descriptive model is:

```text
persistent diffusion/adoption hierarchy
        ↓
workflow conversion / penetration
        ↓
reported benefit
```

Occupation structure tightly organizes the first conversion relationship across the observed window. Industry introduces additional variation. The validated composition evidence narrows some plausible explanations, but the remaining wedge is still mechanistically unidentified and must not be renamed as a causal effect.
