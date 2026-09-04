# Empirical results

This document summarizes the main descriptive findings in Release 1 (`v1.0.0`) of the U.S. AI Adoption Observatory.

## Scope

The industry and occupation analysis uses seven common quarterly observations from Q4 2024 through Q2 2026.

- industries: 20;
- occupations: 22;
- measures: work adoption (`A`), AI-assisted work-hours share (`H`), and reported time-savings share (`S`);
- complete industry/occupation A/H/S observations used in the seven-quarter analysis: **882** = (20 + 22) × 3 × 7;
- registered RPS series in project scope: 131;
- latest source history used for Release 1: 962 observations across those registered series, where observations are available;
- public RPS presentation: seven-quarter national history plus the latest Q2 2026 industry and occupation A/H/S cross-sections;
- statistical interpretation: aggregate, cross-sectional, and descriptive;
- causal claims: none.

The historical subgroup source panel is not distributed as a general public database. Published findings are reproduced from versioned release artifacts.

## 1. Adoption and AI-assisted working time are more tightly aligned across occupations

In every quarter, both Pearson and Spearman associations between work adoption and AI-assisted working time are higher across occupations than across industries.

| Quarter | Industry Pearson r(A,H) | Occupation Pearson r(A,H) | Difference | Industry Spearman | Occupation Spearman |
|---|---:|---:|---:|---:|---:|
| 2024-Q4 | 0.604 | 0.798 | +0.194 | 0.597 | 0.829 |
| 2025-Q1 | 0.473 | 0.762 | +0.289 | 0.346 | 0.700 |
| 2025-Q2 | 0.557 | 0.840 | +0.283 | 0.451 | 0.809 |
| 2025-Q3 | 0.794 | 0.813 | +0.019 | 0.803 | 0.814 |
| 2025-Q4 | 0.641 | 0.898 | +0.257 | 0.629 | 0.906 |
| 2026-Q1 | 0.676 | 0.711 | +0.035 | 0.582 | 0.719 |
| 2026-Q2 | 0.756 | 0.886 | +0.130 | 0.675 | 0.886 |

The defensible interpretation is that occupational structure organizes the aggregate relationship between adoption and workflow penetration more tightly than broad industry grouping over this seven-quarter window.

The remaining industry variation is not identified as an organizational effect. It may reflect finer task composition, worker selection, employer tools, firm characteristics, regulation, sampling variation, or other mechanisms.

## 2. Across occupations, adoption is a robust descriptor of reported savings

Across occupations, `R²(S~A)` is greater than `R²(S~H)` in all seven quarters.

| Quarter | R²(S~A) | R²(S~H) | R²(S~A+H) | Incremental H given A |
|---|---:|---:|---:|---:|
| 2024-Q4 | 0.858 | 0.574 | 0.859 | 0.001 |
| 2025-Q1 | 0.817 | 0.592 | 0.833 | 0.015 |
| 2025-Q2 | 0.857 | 0.624 | 0.857 | 0.001 |
| 2025-Q3 | 0.707 | 0.366 | 0.725 | 0.018 |
| 2025-Q4 | 0.923 | 0.862 | 0.945 | 0.022 |
| 2026-Q1 | 0.766 | 0.682 | 0.850 | 0.084 |
| 2026-Q2 | 0.793 | 0.663 | 0.796 | 0.003 |

The ordering also holds in all **154 of 154** leave-one-occupation-out comparisons: seven quarters × 22 omitted occupations.

This does not establish that adoption causes reported time savings. Both quantities are aggregate subgroup measures, and reported savings are self-reported counterfactual estimates.

## 3. Across industries, the savings relationship changes by quarter

The relative explanatory power of adoption and AI-assisted hours is not stable across industries.

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

The Q2 2026 result, in which assisted hours explain more industry-level variation in reported savings than adoption, is therefore one reproduced cross-section within a quarter-dependent relationship, not a general law.

## 4. Adoption rankings are more persistent than assisted-hours rankings

Median Spearman rank correlations across all 21 quarter pairs are:

| Aggregation | Adoption | Assisted hours | Reported savings |
|---|---:|---:|---:|
| Industries | **0.847** | 0.598 | 0.678 |
| Occupations | **0.788** | 0.561 | 0.639 |

Adoption rank persistence exceeds assisted-hours rank persistence in **20 of 21** quarter-pair comparisons for industries and **20 of 21** for occupations.

Adoption rank persistence exceeds reported-savings rank persistence in **19 of 21** quarter-pair comparisons at both aggregation levels.

This supports a comparative persistence claim, not absolute invariance. The relative ordering of adoption is more stable across most quarter pairs, while the depth of workflow use and reported benefit varies more.

## Q2 2026 reference diagnostics

### Industries

- `R²(H~A) = 0.572065`
- `R²(S~A) = 0.674362`
- `R²(S~H) = 0.729351`
- `R²(S~A+H) = 0.801126`
- `r(A,H) = 0.756350`
- leave-one-industry comparison: H exceeds A in 18 of 20 omissions.

### Occupations

- `R²(H~A) = 0.784730`
- `R²(S~A) = 0.793012`
- `R²(S~H) = 0.662970`
- `R²(S~A+H) = 0.796002`
- `r(A,H) = 0.885850`
- leave-one-occupation comparison: A exceeds H in 22 of 22 omissions.

## Composition and cross-source evidence

Release 1 also includes three complementary descriptive analyses.

### CPS occupation composition

CPS Q2 2025 and Q2 2026 data are used to construct occupation-composition benchmarks for industry adoption, AI-assisted working time, and reported savings. The difference between the observed industry value and its benchmark is reported as an occupation-adjusted industry residual.

These residuals are descriptive standardization results. They are not organizational, efficiency, productivity, or causal effects.

### OEWS robustness

May 2025 OEWS staffing data provide an independent establishment-side comparison for the occupation-composition analysis.

### BTOS comparison

The Q2 2026 BTOS–RPS sector comparison provides a second source on recent AI use. BTOS measures responding employer businesses reporting AI use in any business function during the previous two weeks, while RPS measures employed adults reporting generative-AI use for their jobs.

The measures are not interchangeable. Their sector association is interpreted as descriptive cross-source concordance only.

## Statistical limitations

Release 1 does not provide full design-based confidence intervals for the custom pooled CPS occupation-composition vectors because the required multivariate covariance information is not available in the public CPS materials used by the project.

Sensitivity, stability, and reliability diagnostics therefore remain descriptive. Marginal variance approximations are not used to create an unsupported multivariate covariance structure.

## What these results do not establish

The results do not establish:

- measured labor productivity;
- output or total-factor-productivity effects;
- wage effects;
- employment effects;
- organizational quality;
- firm-level complementarity;
- causal effects of adoption or AI-assisted use;
- causal interpretation of occupation-adjusted industry residuals;
- equivalence between BTOS employer AI use and RPS worker GenAI adoption;
- conventional design-based statistical significance for the custom pooled CPS composition vectors.

Quarterly movement can combine real change, compositional change, and sampling variation. Correlations and regressions are reported as descriptive statistics.

## Summary interpretation

The Release 1 evidence is consistent with a three-stage descriptive picture:

```text
adoption and diffusion
        ↓
workflow penetration
        ↓
reported time savings
```

The relationship between adoption and workflow penetration is more tightly organized across occupations than across industries in the observed period. Industry-level variation remains only partly explained by broad occupational composition, and the remaining difference is not mechanistically identified.
