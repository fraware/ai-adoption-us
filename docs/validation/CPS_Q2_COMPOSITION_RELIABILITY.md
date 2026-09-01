# CPS occupation-composition empirical reliability checkpoint

## Status

This checkpoint tests whether the pooled Q2 CPS worker-composition vectors are stable to their
three constituent months. It covers Q2 2025 and Q2 2026 and reproduces the already committed
quarterly worker vectors to machine tolerance before computing diagnostics.

It does **not** estimate CPS design-based standard errors for the custom industry-by-occupation
composition vectors. BLS's published generalized-variance machinery does not directly provide a
parameter series for every custom estimate, and borrowing parameters would assume comparable
design effects. The diagnostics below therefore remain descriptive perturbation checks.

## Primary diagnostics

- primary-comparability industries: **17**
- minimum primary person-month count across the two quarter-industry cells: **81**
- minimum primary Kish weight-dispersion effective n: **60.39158432205465**
- primary year-over-year composition changes exceeding their observed within-quarter monthly L1 envelope: **7/17**
- largest primary Q2-2025 to Q2-2026 L1 change: **0.6077589403442754** (Management of Companies and Enterprises)
- that industry's maximum observed within-quarter monthly L1 envelope: **0.4690574043432125**
- largest primary leave-one-month-out perturbation across both years: **0.14218063065667338** (Management of Companies and Enterprises)

## Interpretation

A large quarter-to-quarter change accompanied by large within-quarter or leave-one-month-out
instability is a warning that the pooled composition is sensitive to a thin or volatile CPS domain.
The envelope comparison is not a hypothesis test and must not be described as statistical
significance. Kish effective n is reported only as a weight-concentration diagnostic.

These diagnostics should govern whether individual industry composition estimates are treated as
primary evidence, sensitivity evidence, or flagged for additional uncertainty work before an RPS
occupation-standardization residual is published.
