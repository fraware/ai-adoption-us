# CPS LN same-period uncertainty benchmark

## Result

The official Basic Monthly CPS public-use file reconstructs BLS series
`LNU02032201` for 2026 M07 under the
published **employed people age 16+** universe and the broad Management,
Professional, and Related occupation definition.

- BLS published estimate: **69,913 thousand persons**
- public-use reconstruction: **69,877.392835 thousand persons**
- reconstruction minus published estimate: **-35.607165 thousand persons**
- absolute reconstruction discrepancy: **0.063584 official standard errors**
- published BLS standard error: **560.000000 thousand persons**
- BLS-style 90% same-period confidence interval: **[68,991.800, 70,834.200] thousand persons**
- exact published-rounding reproduction: **False**
- project public-use validation threshold: **≤ 1.0 official standard error**
- threshold satisfied: **True**

## Why exact equality is not the validation rule

Census documents that disclosure-avoidance protections in Basic Monthly CPS public-use
files can cause estimates below the top-line labor-force totals—including estimates
using occupation—to differ slightly from BLS estimates based on internal files. Census
states that these differences should remain well within the sampling variability of the
CPS estimate. Accordingly, this project does not require an occupation estimate from the
public-use file to round exactly to the internal-file BLS publication.

The project uses **one published BLS standard error** as a conservative, explicit
validation threshold for this reconstruction. This is a project quality-control rule,
not a BLS significance test and not a Census-prescribed threshold. The exact difference
and its standardized value remain published regardless of pass/fail status.

## What this validates

This benchmark establishes a reproducible connection among three official outputs:
the Basic Monthly CPS public-use record, the BLS LN published point estimate, and the
BLS LN published standard-error aspect. The public-use reconstruction checks the
universe, occupation coding, and composited-final-weight arithmetic. The standard error
itself remains an official BLS design-based output; it is not reconstructed from the
public-use file.

## What this does not validate

BLS states that LN standard errors are intended for comparisons within the same
reference period. They do not provide the cross-month covariance needed for month-,
quarter-, or shorter year-over-year inference under the CPS rotating-panel design.
This benchmark therefore does not supply a covariance matrix for the observatory's
22-dimensional industry occupation shares and does not support a confidence interval
for a pooled-quarter residual.
