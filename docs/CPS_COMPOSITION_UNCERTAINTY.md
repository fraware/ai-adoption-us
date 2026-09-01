# CPS composition uncertainty: design boundary and implementation contract

Status date: **2026-09-02**  
Issue: **#14 — R1.1-G2b**  
Status: **methodology/engineering framework implemented; formal design-based composition uncertainty remains open**

## Decision

The observatory must not turn descriptive CPS reliability diagnostics into inferential uncertainty.

The existing person-month counts, Kish final-weight-dispersion diagnostic, monthly composition movement, leave-one-month-out perturbations, and Q2-2025/Q2-2026 stability checks remain useful quality-control evidence. They are **not** CPS design-based standard errors or confidence intervals.

The current public Basic Monthly CPS inputs used by the observatory are therefore not sufficient, by themselves, to support a covariance-aware design-based confidence interval for each custom 20-industry × 22-major-occupation composition vector.

The repository now has an explicit uncertainty interface that can consume defensible covariance inputs when they become available and can reproduce BLS generalized-variance-function arithmetic for **marginal approximation/benchmarking**. The latter is not promoted to a full composition covariance.

## Official-method review

### 1. Direct CPS variance estimation is replication-based

Census Bureau *Current Population Survey: Design and Methodology, Technical Paper 77* describes the CPS direct variance system as successive-difference replication (SDR). The current system uses 160 replicates and is constructed to reflect CPS sample-design features. The 2010 redesign also incorporates rotation group in the replicate construction to support variances and covariances under the rotating-panel design.

Primary source:

- U.S. Census Bureau and U.S. Bureau of Labor Statistics, *Current Population Survey: Design and Methodology, Technical Paper 77*: https://www2.census.gov/programs-surveys/cps/methodology/CPS-Tech-Paper-77.pdf

### 2. The public Basic Monthly distribution reviewed here does not expose that full replicate system

The Census CPS datasets page publishes Basic Monthly public-use files and separately identifies replicate-weight products for supplements where available. In the public Basic Monthly distribution and documentation reviewed for this project on 2026-09-02, no documented general-purpose Basic Monthly replicate-weight file was identified that would allow the observatory to reconstruct the internal 160-replicate SDR covariance for arbitrary industry × occupation domains.

This is an evidence statement about the public materials reviewed, not a claim that no such access path can exist. Issue #14 remains open partly to resolve whether BLS/Census can provide a suitable public or research-access variance path.

Primary source:

- U.S. Census Bureau, CPS datasets: https://www.census.gov/programs-surveys/cps/data/datasets.html

### 3. BLS provides an official approximate GVF path for many Basic CPS estimates

The July 2026 BLS guide *Calculating Approximate Standard Errors and Confidence Intervals for Current Population Survey Estimates* documents generalized variance functions (GVFs) and parameter/factor tables PF-1 through PF-16. For a percentage `p` with denominator level `y`, the guide gives

```text
se(p; y; f) = f * sqrt(((alpha + beta*y) / y) * p * (100 - p))
```

where `p` and its standard error are expressed in percentage points. The guide explicitly permits borrowing alpha/beta parameters from a conceptually similar series when the target series is not tabulated, while stating the implicit assumption: the lending and borrowing series have approximately equal design effects. It advises same-type borrowing when possible and, among plausible lending series, generally favors the parameters producing the larger standard error.

The same guide provides factors for quarterly averages and changes over time. These factors are tied to a lending series; they are not a generic license to assume independent CPS months.

Primary source:

- U.S. Bureau of Labor Statistics, *Calculating Approximate Standard Errors and Confidence Intervals for Current Population Survey Estimates*, July 2026: https://www.bls.gov/cps/methods/calculating-standard-errors-and-confidence-intervals.pdf

### 4. Marginal GVF standard errors do not identify a 22-dimensional composition covariance

Each industry composition satisfies

```text
sum_o w[j,o,t] = 1.
```

Consequently its covariance matrix is singular and obeys

```text
Cov(w, 1' w) = 0,
```

so rows/columns sum to zero (up to numerical tolerance). Treating independently calculated marginal standard errors as a diagonal covariance matrix violates this constraint and discards the negative/positive covariance among occupation shares.

A marginal GVF approximation can therefore be used only as a sensitivity or calibration check unless a defensible covariance construction is supplied separately.

### 5. Quarter pooling also requires cross-month covariance

CPS is a rotating-panel survey. BLS warns that estimates close in time can share sample and that covariance matters for changes/averages. The observatory pools April–June records with equal month factors; a formal covariance for the pooled occupation levels must therefore include the off-diagonal month-to-month covariance blocks. Setting these blocks to zero merely because they are unavailable would be an unsupported independence assumption.

## Implemented contract

`src/genai_at_work/cps_uncertainty.py` now separates three support states:

1. `design_covariance` — a full covariance matrix has been supplied through a defensible design method;
2. `gvf_marginal_approximation` — BLS-style marginal approximate standard errors only;
3. `unsupported` — insufficient evidence for inferential uncertainty.

### GVF arithmetic

`approximate_percentage_standard_error` implements the published BLS percentage formula and requires the lending series and borrowing rationale to be recorded. Invalid parameter/estimate combinations fail closed rather than returning an imaginary/negative variance.

`approximate_composition_marginal_standard_errors` returns marginal share standard errors in 0–1 share units and marks covariance as unavailable.

### Covariance validation

`build_composition_covariance` requires:

- unique occupation labels;
- shares in `[0,1]` summing to one;
- finite, square, symmetric covariance;
- nonnegative marginal variances;
- positive-semidefinite covariance (within tolerance);
- the composition sum-to-one covariance constraint.

A diagonal matrix assembled from marginal GVF variances is intentionally rejected as a valid composition covariance.

### Delta-method propagation

If a full design covariance `C_x` for weighted occupation levels `x` becomes available, the composition `w_i = x_i / sum(x)` is propagated with

```text
J[i,k] = (1{i=k} - w_i) / sum(x)
C_w = J C_x J'
```

via `composition_covariance_from_level_covariance`.

### Quarter pooling

`pooled_composition_covariance_from_month_block` accepts a complete month-major covariance block for monthly occupation levels. It includes every cross-month block when deriving the covariance of equal-month pooled levels, then transforms those pooled levels into shares. An incomplete block fails closed.

### Future RPS counterfactual propagation

For a fixed vector of RPS occupation values `a`, `composition_counterfactual_standard_error` computes the CPS-composition contribution

```text
Var(a' w) = a' C_w a.
```

This is **not** a total standard error for the future RPS composition counterfactual or residual. It excludes RPS occupation-estimate uncertainty, covariance among RPS occupation estimates, observed-industry RPS uncertainty, and any cross-source dependence.

## What this checkpoint does not establish

This checkpoint does not produce design-based confidence intervals for the current Q2 2025 or Q2 2026 CPS composition artifacts.

It does not:

- infer a replicate design from Basic Monthly person records;
- treat final CPS weights as sufficient design information;
- label Kish weight-dispersion effective n as a survey-design effective sample size;
- turn month-to-month or leave-one-month-out movement into a sampling variance;
- assume CPS months are independent;
- infer a 22 × 22 covariance matrix from 22 marginal GVF standard errors;
- select a lending PF series solely because it produces convenient uncertainty;
- propagate CPS-only uncertainty and call it uncertainty for an RPS residual.

## Remaining work before issue #14 can close

### A. Resolve the variance-input path

Obtain an authoritative answer from BLS/Census on whether one of the following is available for Basic Monthly custom domains:

1. public or research-access replicate weights / SDR replicate estimates;
2. a supported method for obtaining direct variances and covariances for arbitrary weighted Basic CPS domains;
3. official covariance/design-effect guidance sufficiently specific to industry × major occupation shares and pooled-quarter estimates.

The response and exact applicable vintages must be recorded.

### B. If GVF borrowing is retained as a benchmark, predefine the lending-series rule

Before looking at desired confidence intervals, define a conceptually justified lending-series map for the target numerator/base, document the design-effect argument, and test plausible alternative lenders. Report the range. Do not select lenders post hoc to obtain a preferred conclusion.

This exercise remains a marginal approximation unless a covariance method is separately justified.

### C. Validate against official estimates

For at least one CPS estimate that can be reconstructed from the same public-use inputs and has a published BLS standard error, compare:

- the observatory point estimate;
- the applicable approximate or direct standard error;
- any lending-series approximation under consideration.

Differences must be explained before applying a method to thin custom domains.

### D. Validate the pooled-quarter covariance

Any eventual quarter method must account for the CPS rotating-panel overlap across April, May, and June. A covariance construction that assumes independent months is not accepted without external methodological evidence.

### E. Propagate source-specific uncertainty separately

When authorized RPS occupation and industry observations become available, preserve separate uncertainty components for:

- CPS composition;
- RPS occupation values;
- RPS observed industry values;
- any covariance induced by common RPS sampling.

Only after those components and their dependence structure are justified should the observatory report an inferential interval for an occupation-adjusted industry-context residual.

## Publication state

Until the remaining work is completed, current CPS composition reliability evidence remains **descriptive**. No current public composition result should display a design-based confidence interval generated by this module.
