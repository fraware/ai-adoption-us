# CPS composition analysis and uncertainty

This document describes how GenAI at Work uses the Current Population Survey (CPS) to construct occupation-composition benchmarks for industries, how those benchmarks are validated, and why Release 1 does not report full design-based confidence intervals for them.

## 1. Purpose

Industry-level workplace AI use partly reflects the occupations employed within each industry. To separate this compositional component from the observed industry aggregate, the project uses CPS Basic Monthly public-use data to estimate the occupation mix of each industry.

The resulting benchmark answers a descriptive question:

> What industry value would be implied by the observed occupation-level RPS values if they were combined using that industry's CPS occupation composition?

The difference between the observed industry value and this benchmark is a descriptive standardization residual. It is not a causal estimate of an employer, organization, or industry effect.

## 2. Periods included in Release 1

Release 1 contains validated CPS composition packages for:

- Q2 2025;
- Q2 2026.

Q4 2025 is intentionally unavailable because October 2025 CPS data were not collected. November and December are not used to construct a two-month substitute for a three-month quarter.

## 3. Population and classification

The CPS sample is aligned as closely as possible to the worker-side RPS population, including the 18–64 age range and an appropriate employed-worker universe.

The analysis uses CPS main-job industry and major-occupation classifications together with versioned crosswalks under `data/registry/`. Each generated composition package records its source months, classification versions, coverage, and mapping information.

## 4. Weighting

For industry `j`, occupation `o`, and quarter `t`, define the occupation worker share as:

```text
w_worker(j,o,t) = weighted workers(j,o,t) / weighted workers(j,t)
```

and the occupation work-hour share as:

```text
w_hours(j,o,t) = weighted actual main-job hours(j,o,t)
                 / weighted actual main-job hours(j,t)
```

The benchmark depends on the RPS measure being standardized.

For workplace adoption:

```text
A_hat(j,t) = Σ_o w_worker(j,o,t) × A(o,t)
```

For AI-assisted working time and reported time savings:

```text
H_hat(j,t) = Σ_o w_hours(j,o,t) × H(o,t)
S_hat(j,t) = Σ_o w_hours(j,o,t) × S(o,t)
```

Worker shares are not reused for the work-hour-based measures.

Actual main-job hours are the primary hour measure because they align most closely with the RPS reference-week constructs. Usual main-job hours are retained only as a labeled sensitivity where coverage is sufficient.

## 5. Occupation-adjusted industry residual

For metric `m`:

```text
residual(j,t,m) = observed(j,t,m) - benchmark(j,t,m)
```

A positive residual means the observed industry value is above the value implied by its broad occupation composition under the specified weighting scheme; a negative residual means it is below.

The residual can reflect many mechanisms, including finer task composition, worker selection, employer tools, firm characteristics, regulation, measurement error, and sampling variation. Without a separate identification strategy, it should not be called an organizational effect, efficiency measure, productivity effect, or causal firm effect.

## 6. Coverage and suppression

Each industry composition is checked for classification coverage and support. A material unmapped or unsupported share is not silently removed and renormalized into an apparently complete estimate.

For sensitivity analyses, an explicit leave-one-occupation-out perturbation may intentionally remove one positive-weight occupation and renormalize the remaining weights. That operation is a robustness diagnostic, not missing-data treatment and not sampling inference.

## 7. Release 1 robustness evidence

The Q2 2025 and Q2 2026 composition analysis produced 120 primary industry residuals: 20 industries × 3 RPS measures × 2 quarters. All 120 primary rows were computationally supported under the primary weighting definitions.

### Cross-quarter persistence

Across all 20 industries, residual rank correlations between Q2 2025 and Q2 2026 were:

| Measure | Spearman correlation | Same-sign industries | Median absolute change |
| --- | ---: | ---: | ---: |
| Work adoption | 0.665 | 17/20 | 4.10 percentage points |
| AI-assisted work hours | 0.451 | 14/20 | 1.33 pp |
| Reported time savings | 0.571 | 14/20 | 0.40 pp |

These values indicate moderate, incomplete persistence. They do not support treating residuals as stable industry scores or a league table.

### Leave-one-occupation-out sensitivity

For each supported industry/measure/quarter row, the analysis removes each positive-weight occupation in turn, renormalizes the remaining composition, and records the largest residual shift.

Across the 120 primary rows:

- 21 maximum-influence perturbations reverse the residual sign;
- the median maximum absolute shift is approximately 5.01 percentage points for adoption;
- 1.22 percentage points for AI-assisted hours;
- 0.31 percentage points for reported savings.

This sensitivity reinforces the decision to present composition residuals with context rather than as precise industry performance measures.

### Usual-hours sensitivity

The usual-hours sensitivity uses the existing 98% valid-worker coverage requirement. It is poorly supported for most industries because some CPS usual-hours responses are not point-valued.

Under that rule, none of the 20 Q2 2025 industries and only Public Administration in Q2 2026 meet the support threshold for the H/S usual-hours sensitivity. The broad absence of support is retained rather than weakening the coverage rule.

## 8. Why the current reliability diagnostics are not confidence intervals

The project reports several useful descriptive quality checks, including:

- person counts;
- weight-dispersion diagnostics;
- month-to-month composition movement;
- leave-one-month-out perturbations;
- cross-period persistence;
- leave-one-occupation-out influence;
- cross-source comparison with OEWS.

These diagnostics measure stability or sensitivity. They are not design-based CPS standard errors and should not be presented as substitutes for sampling uncertainty.

## 9. CPS design-based variance

The official CPS direct variance system uses successive-difference replication (SDR). *Current Population Survey: Design and Methodology, Technical Paper 77* describes a 160-replicate system designed to reflect CPS sample structure, including its rotating-panel design.

Primary reference:

- U.S. Census Bureau and U.S. Bureau of Labor Statistics, *Current Population Survey: Design and Methodology, Technical Paper 77*: https://www2.census.gov/programs-surveys/cps/methodology/CPS-Tech-Paper-77.pdf

The public Basic Monthly files used by this project provide the data and final weights needed for point estimation. In the official public Basic Monthly materials reviewed for Release 1, the project did not identify a general-purpose replicate-weight product sufficient to reconstruct the 160-replicate SDR covariance for arbitrary industry × occupation domains.

This is a statement about the public materials reviewed. It does not imply that no restricted or future agency access path can exist.

## 10. Generalized variance functions

BLS publishes generalized-variance-function (GVF) methods for approximate standard errors for many CPS estimates.

For a percentage `p` with base level `y`, the published form is:

```text
se(p; y; f) = f × sqrt(((alpha + beta × y) / y) × p × (100 - p))
```

where the applicable `alpha`, `beta`, and factor `f` depend on the series and comparison.

Primary reference:

- U.S. Bureau of Labor Statistics, *Calculating Approximate Standard Errors and Confidence Intervals for Current Population Survey Estimates*, July 2026: https://www.bls.gov/cps/methods/calculating-standard-errors-and-confidence-intervals.pdf

BLS permits borrowing parameters from a conceptually similar series under an approximate equal-design-effect assumption. Release 1 does not select a single borrowing series for the custom industry × occupation domains because no prespecified, validated mapping from those domains to an official lending series was established.

GVFs therefore remain useful for scalar validation and sensitivity work, not as the public uncertainty model for the composition vectors.

## 11. Why marginal standard errors are insufficient

An industry composition has 22 occupation shares that sum to one. Its covariance matrix must therefore contain the cross-occupation dependence implied by that compositional constraint.

A symmetric 22 × 22 covariance matrix has 253 unique entries. The sum-to-one constraint imposes 22 independent linear restrictions, leaving 231 free parameters. Even if 22 marginal variances were known, **209 covariance degrees of freedom would remain unidentified**.

Consequently, a diagonal matrix of marginal GVF variances is not a valid substitute for the required composition covariance.

The project explicitly does not:

- infer the missing off-diagonal covariance terms from marginal standard errors;
- choose an arbitrary positive-semidefinite matrix and call it design-based;
- assume a simple multinomial covariance multiplied by one design effect;
- treat final person weights alone as sufficient survey-design information.

## 12. Quarter pooling and repeated-sample dependence

CPS uses a rotating-panel design, so adjacent months share sample. A design-based covariance for a pooled April–June composition must account for both:

- covariance among occupations within a month;
- covariance across occupations and months.

The project does not assume April, May, and June are independent simply because the required cross-month covariance is unavailable.

A scalar quarterly GVF factor for one published series does not identify the multivariate covariance of a pooled 22-category composition.

## 13. Software support

`src/genai_at_work/cps_uncertainty.py` distinguishes three computational states:

- `covariance_aware` — a full covariance matrix is supplied and passes mathematical checks;
- `gvf_marginal_approximation` — only BLS-style marginal approximate standard errors are available;
- `unsupported` — the available evidence is insufficient for inferential uncertainty.

A mathematically valid covariance is not automatically a CPS design-based covariance. Survey-design interpretation requires independent methodological provenance.

When a full level covariance `C_x` is available, the software can propagate it to normalized composition shares with the delta method:

```text
J[i,k] = (1{i=k} - w_i) / sum(x)
C_w = J C_x J'
```

For fixed occupation-level RPS values `a`, the composition-only contribution to the variance of a benchmark is then:

```text
Var(a' w) = a' C_w a
```

That quantity would still exclude RPS sampling uncertainty and any dependence between RPS components.

## 14. Release 1 uncertainty status

For the published Release 1 composition analysis:

```text
official scalar CPS benchmark: validated
GVF scalar/marginal approximation: available for validation or sensitivity
full design-based covariance for pooled 22-category compositions: unsupported
design-based confidence interval for occupation-composition benchmark: unsupported
inferential confidence interval for occupation-adjusted industry residual: unsupported
```

Accordingly, Release 1 reports the composition analysis as derived descriptive evidence and keeps stability, influence, and OEWS comparisons separate from formal sampling inference.

## 15. What would support stronger inference

A future design-based uncertainty analysis would require authoritative evidence such as:

1. Basic Monthly replicate weights or replicate estimates suitable for the relevant domains;
2. an agency-supported method for direct variance and covariance estimation for arbitrary Basic Monthly industry × occupation domains; or
3. official covariance/design-effect guidance covering both cross-occupation and cross-month dependence for the pooled estimator.

Any new method should be validated against official CPS estimates before it is used for public intervals.
