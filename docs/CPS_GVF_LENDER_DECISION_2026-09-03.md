# CPS GVF lender decision for Observatory v1

Status date: **2026-09-03**  
Issue: **#14 — R1.1-G2b**  
Decision: **No canonical GVF lender is supported for Observatory v1. GVF borrowing remains sensitivity/benchmarking research only.**

## Decision

The current evidence does not support selecting one BLS generalized-variance-function (GVF) lending series as the canonical marginal uncertainty model for the observatory's custom CPS industry-by-occupation composition domains.

Observatory v1 will therefore keep current CPS composition uncertainty in the existing **descriptive / inferentially unsupported** publication state. It will not attach a GVF-derived confidence interval to custom composition vectors or occupation-adjusted RPS residuals.

This decision is deliberately narrower than saying that GVFs are invalid. BLS documents GVF borrowing as an approximate method when the target and lending series have sufficiently similar design effects. The unresolved project-specific problem is the absence of a pre-specified, validated concept/design-effect mapping from the observatory's custom domains to an official lending series. The project will not choose a lender post hoc because it gives convenient uncertainty.

## Evidence considered

### 1. Official same-period direct-SE validation is now reproducible

A single batched request to the BLS Public Data API v2 successfully retrieved the complete published direct-standard-error family `LNU02032201` through `LNU02032214` for July 2026. The successful rights-safe run is GitHub Actions run `33724372289` on branch head `6ffa252424d1c653aec7cbd09e6943fd732559f6`.

The durable selected evidence is recorded at:

`data/derived/composition/cps-ln-se-benchmark-2026-07/direct_se_family.json`

This extends the existing same-period `LNU02032201` benchmark without changing its interpretation: direct BLS standard errors are authoritative validation outputs for those published same-period series, not a covariance product for the observatory's pooled custom composition vectors.

### 2. The validation-family boundary was corrected from live source evidence

The earlier one-series-at-a-time probe reached the BLS keyless daily request threshold after suffix `10`, so it could not establish the state of suffixes `11` through `20`. That quota result was not evidence of missing series.

After the probe was converted to one batched request, BLS returned values and standard errors for suffixes `01` through `14` and explicitly reported `LNU02032215` through `LNU02032220` as nonexistent. The permanent validation family is therefore `01` through `14`; the six nonexistent IDs are not treated as missing observations.

This correction follows the project's source-first rule: when live source behavior contradicts an assumption, correct the assumption instead of weakening validation or preserving a convenient inventory.

### 3. The official PF workbook is not a reliable hosted-runner dependency

The experimental workflow probing BLS's official `parameters-and-factors-for-calculating-standard-errors.xlsx` URL failed on GitHub's hosted Ubuntu runner with HTTP 403 in run `33694358717`.

No unofficial mirror was substituted. The experimental workflow is removed rather than merged as a permanently red ordinary CI surface. This access limitation does not itself determine the scientific GVF decision; BLS's published methodological guide remains authoritative for the formula and borrowing conditions.

### 4. A defensible lending-series mapping has not been established

BLS's published CPS standard-error guidance permits borrowing parameters from a conceptually similar series under an approximate equal-design-effect assumption. The repository implements the arithmetic and requires both the lending series and borrowing rationale to be recorded.

What has not been established is a pre-specified rule demonstrating that any one available official PF series is a sufficiently close design-effect match for each custom industry-by-major-occupation domain used by the observatory. Direct-SE validation of published occupation aggregates does not supply that mapping automatically.

Without such a rule, selecting a lender from observed fit would be post hoc calibration and would not justify a canonical public uncertainty model.

### 5. Even a good marginal lender would not solve the composition-inference problem

A 22-category composition sums to one. Marginal standard errors do not identify the off-diagonal covariance terms required for joint inference or for propagation through an occupation-weighted counterfactual.

The repository's public design-variance decision has already established that the available public Basic Monthly CPS path does not identify the custom 22-dimensional SDR covariance. Quarter pooling additionally requires cross-month covariance under the CPS rotating-panel design.

Therefore a marginal GVF decision cannot, by itself, justify:

- a design-based confidence interval for an industry occupation-composition vector;
- a pooled-quarter composition covariance;
- a total uncertainty interval for an occupation-predicted RPS metric; or
- a confidence interval for an occupation-adjusted industry-context residual.

## V1 publication contract

For Observatory v1:

1. CPS composition estimates and composition-adjusted residuals remain **derived descriptive** evidence.
2. Existing stability, month-movement, leave-one-month-out, cross-vintage, and OEWS robustness diagnostics remain visible as reliability evidence; none is relabeled as a sampling variance.
3. No canonical GVF-derived marginal interval is published for custom composition cells.
4. No 22-dimensional covariance matrix is inferred from marginal standard errors.
5. No independence assumption is inserted for April-May-June CPS pooling.
6. No residual is given an inferential confidence interval until CPS and RPS uncertainty components and their relevant dependence structures are defensibly identified.
7. The lack of a canonical GVF lender is **not a blocker for Observatory v1**. Unsupported inference fails closed while honest descriptive evidence remains publishable.

## Research status after this tranche

Issue #14 remains open. Future work may revisit GVF borrowing as sensitivity analysis if official parameter provenance and a pre-specified concept/design-effect mapping can be established. A future canonical lender would require out-of-sample validation against appropriate official direct-SE targets and explicit sensitivity to plausible alternatives.

A stronger design-based composition result still requires an authoritative covariance path, such as suitable CPS replicate/direct covariance access or comparably strong BLS/Census guidance for the custom domains and pooled-quarter estimator.

## Reopen criteria for the v1 lender decision

Reconsider the public v1 boundary only if new authoritative evidence materially changes publishability, for example:

- BLS/Census provides an official parameter family or lending rule specifically defensible for the target custom domains;
- a pre-specified concept-matching rule can be validated out of sample against an adequate direct-SE benchmark set; or
- authoritative design-based covariance access makes marginal borrowing unnecessary for the public inferential claim.

Until then, the scientifically correct action is to fail closed on inferential CPS composition uncertainty and return the main execution effort to the operational RPS feed, complete global baseline, release promotion, and public observatory product.
