# CPS design-variance path decision — 2026-09-03

Issue: **#14 — R1.1-G2b**  
Decision: **public full design covariance remains unsupported**

## Executive decision

The observatory does not currently have a defensible public-data path to a CPS design-based covariance matrix for its three-month, 22-occupation industry composition vectors.

This is narrower than saying that CPS design-based variance estimation is impossible. The official CPS system does estimate variances and covariances. The problem is that the design inputs needed to reproduce that system for arbitrary Basic Monthly public-use domains were not identified in the public Basic Monthly distribution reviewed on 2026-09-03.

BLS generalized variance functions (GVFs) remain useful for scalar and marginal approximation, including quarterly averages and changes over time when an applicable or defensibly borrowed parameter/factor row exists. They do **not** identify the multivariate covariance required by the observatory.

Accordingly:

- no current public CPS composition receives a design-based confidence interval;
- no independent-month quarter covariance is fabricated;
- no diagonal matrix of marginal GVF variances is promoted to a composition covariance;
- no occupation-adjusted RPS residual receives an inferential interval from CPS-only marginal uncertainty;
- descriptive reliability diagnostics remain published and separate from inference.

The machine-readable decision is `data/registry/cps_design_variance_decision.json`.

## 1. What the official CPS design method actually uses

*CPS Design and Methodology, Technical Paper 77* describes the direct CPS variance method as successive-difference replication (SDR). Replicate factors are constructed from a 160-by-160 Hadamard matrix, replicate weights pass through the weighting steps applied to the full sample, and variance is estimated from replicate estimates relative to the full-sample estimate.

The 2010 design change is particularly relevant here: rotation group was added to the SDR sort criteria, allowing variances and covariances to be estimated at the rotation-group level. The same technical paper documents the 4-8-4 rotation pattern, with about three-fourths of sample units shared across consecutive months and one-half shared for the same month in consecutive years.

Primary source:

- U.S. Census Bureau and U.S. Bureau of Labor Statistics, *Current Population Survey: Design and Methodology, Technical Paper 77*: https://www2.census.gov/programs-surveys/cps/methodology/CPS-Tech-Paper-77.pdf

These facts make the core constraint explicit: repeated-sample dependence is part of the CPS variance design. It cannot be discarded merely because the public point-estimation file does not expose the complete replication system.

## 2. What was identified in the public Basic Monthly distribution

The Census CPS dataset index separates **Basic Monthly CPS Data** from **CPS Supplement and Replicate Weights Data**. The latter is described as supplement data plus replicate weights *if available*. The Basic Monthly public files themselves expose the monthly microdata and statistical weights used for point estimation.

Primary sources:

- Census CPS datasets: https://www.census.gov/programs-surveys/cps/data/datasets.html
- BLS CPS public-use microdata: https://www.bls.gov/cps/data/public-use-file.htm

No general-purpose Basic Monthly public replicate-weight product sufficient to reconstruct the internal 160-replicate SDR covariance for arbitrary industry × occupation domains was identified in the official public materials reviewed on 2026-09-03.

That sentence is intentionally scoped to the reviewed public materials. It is not an assertion that a restricted, agency-provided, or future access path cannot exist.

Census maintains restricted-use demographic microdata access through the Federal Statistical Research Data Center system and the Standard Application Process, but the existence and operational availability of the specific Basic Monthly replicate/covariance inputs required here has **not** been verified. Restricted access is therefore a research-access candidate, not a solved production path.

Reference:

- Census restricted-use data: https://www.census.gov/topics/research/guidance/restricted-use-microdata.html

## 3. What the BLS GVF path does provide

The July 2026 BLS guide *Calculating Approximate Standard Errors and Confidence Intervals for Current Population Survey Estimates* provides α/β generalized-variance parameters and factors for:

- monthly estimates;
- consecutive month changes;
- monthly changes one year apart;
- quarterly averages;
- consecutive quarterly-average changes;
- annual averages;
- consecutive annual-average changes.

For averages and changes over time, Technical Paper 77 states that adjustment factors are calculated from historical correlations under an equal-monthly-variance approximation. The BLS guide applies the factor to a monthly-style GVF evaluated at the appropriate averaged level/base.

Primary source:

- BLS, *Calculating Approximate Standard Errors and Confidence Intervals for Current Population Survey Estimates*, July 2026: https://www.bls.gov/cps/methods/calculating-standard-errors-and-confidence-intervals.pdf

The guide also permits borrowing parameters and factors for an unlisted target when a conceptually related lending series has approximately similar design effects. Same-type borrowing is preferred, and among plausible lenders BLS generally advises the one producing the larger standard error.

This is useful for **marginal sensitivity and calibration**. It does not transform the public microdata into the internal SDR replicate system.

## 4. Why 22 marginal standard errors cannot identify the composition covariance

Let the 22 occupation shares for industry `j` be `w`, with

```text
1' w = 1.
```

A symmetric 22 × 22 covariance matrix has

```text
22 × 23 / 2 = 253
```

unique entries. The composition constraint implies

```text
C 1 = 0,
```

which imposes 22 independent linear restrictions on a symmetric matrix. The admissible symmetric simplex covariance space therefore has

```text
253 - 22 = 231
```

free parameters.

Suppose, generously, that a defensible GVF exercise supplied all 22 marginal variances. Fixing those 22 diagonal entries still leaves

```text
231 - 22 = 209
```

unidentified covariance degrees of freedom.

The sum-to-one constraint therefore does not rescue a diagonal GVF construction. It constrains the missing covariances; it does not determine them.

This is why `src/genai_at_work/cps_uncertainty.py` rejects independent marginal variances as a valid composition covariance and why `src/genai_at_work/cps_design_variance.py` now pins the 209-degree underidentification result.

## 5. Why a quarterly factor is still insufficient

For one scalar CPS series, a BLS quarterly-average factor summarizes enough historical dependence to approximate the variance of that specific three-month average under the guide's assumptions.

Our required object is different. Before normalization, a three-month × 22-occupation quarter contains a 66-dimensional vector of occupation levels. A design-based pooled composition requires the covariance among occupations **within each month** and across occupations **across months**. The scalar quarterly factor for occupation `o` supplies, at most, information about one quadratic form involving that scalar series across the three months. It does not supply cross-occupation covariance blocks.

Consequently, even a complete set of scalar quarterly factors for all 22 target occupations would not identify the 22 × 22 covariance of the final composition vector.

The following shortcuts remain prohibited:

- assume April, May, and June are independent;
- infer one common correlation coefficient from a quarterly factor and apply it across occupations;
- assume a survey-design covariance has the simple-random-sample multinomial form times one scalar design effect;
- choose an arbitrary nearest positive-semidefinite matrix consistent with marginal GVFs and call it design-based;
- use household or month identifiers as substitutes for the SDR design variables.

Any of these may define a sensitivity model if explicitly labeled and preregistered. None is the official CPS design covariance.

## 6. What would change the decision

The public full-design covariance gate can be reconsidered only if at least one of these paths is established with applicable vintage and provenance:

1. authoritative Basic Monthly replicate weights or replicate estimates sufficient to reproduce the relevant SDR covariance;
2. an agency-supported direct method for variances and covariances of arbitrary Basic Monthly industry × occupation domains;
3. official domain-specific covariance/design-effect guidance covering both cross-occupation and cross-month dependence.

Any such path must then be validated against official CPS estimates before it is used for public composition intervals.

## 7. Publication state

The same-period `LNU02032201` benchmark remains valid and useful: it connects an official CPS point estimate, its official BLS standard error, and the public-use reconstruction. It validates one scalar same-reference-period benchmark.

It does **not** provide the missing covariance structure for the observatory's pooled composition vectors.

Until the variance-input gate changes, the public uncertainty state is therefore:

```text
same-period official scalar benchmark: validated
GVF scalar / marginal approximation: available with lender provenance
full CPS design covariance for 22-part pooled composition: unsupported
pooled-quarter design-based composition CI: unsupported
occupation-adjusted RPS residual inferential CI: unsupported
```
