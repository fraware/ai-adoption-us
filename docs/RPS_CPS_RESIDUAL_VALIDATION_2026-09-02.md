# RPS × CPS occupation-adjusted industry-context residual validation

Status date: **2026-09-02**  
Evidence status: **first successful live authorized RPS join; descriptive research evidence, not a public residual leaderboard**

## Executive result

The observatory has completed its first end-to-end live join of the authorized published-aggregate RPS Tracker series to the validated CPS industry × occupation composition system.

The source refresh, topology checks, private-vintage archive rehearsal, RPS longitudinal component, CPS/RPS composition residual build, rights-safe evidence assembly, and artifact upload all passed in GitHub Actions run `33683408001` on canonical commit `3fd0abd9c5573c3c2bca7bb53205bc52fa2cd453`.

The live source contained **137 provider series**, of which **131** are in observatory scope and **6** are intentionally excluded national overall/outside-work constructs. The 131 scoped series contained **962 published aggregate observations**. Their scientific content identity is:

`fe8bffa7cacd029cc23e2ba7e310d925e8c05322f6d53bd89e8234f02e825b73`

The exact retrieved private snapshot file hash is:

`6aebc5a9c317e0ae376b04eb7ae9a7c32342503679f740a3e4085e706177139e`

The successful workflow artifact is `9867278483`, with archive digest:

`15abd9a1ba2a285bfbbe686fc65059286e1261563b17dd325204c72d5905fb3c`

No 962-observation source snapshot is committed to the public repository. The durable package under `data/derived/composition/rps-cps-residuals-2026-09-02/` retains only the approved derived research evidence and source/provenance identities needed to reproduce and review it.

## Source-history topology established by the live source

The live FRED/ALFRED distribution confirms that the subgroup constructs have different legitimate start dates:

- all **42 adoption** subgroup series = 20 industries + 22 occupations and span **Q3 2024 through Q2 2026**;
- all **42 assisted-hours** subgroup series span **Q4 2024 through Q2 2026**;
- all **42 reported-savings** subgroup series span **Q4 2024 through Q2 2026**.

Thus Q3 2024 is an adoption-only subgroup quarter. It is retained in source history but is not inserted into a joint A/H/S analysis. The complete joint A/H/S subgroup window is the seven quarters **Q4 2024 through Q2 2026**.

This is a measurement-availability boundary, not a missing-cell imputation decision. Each construct family must remain internally complete across all 42 subgroup entities; an isolated missing series-period still fails closed.

## Composition periods and estimands

CPS composition evidence is available and validated for **Q2 2025** and **Q2 2026**, so this checkpoint computes industry residuals for those two quarters.

For industry `j`, occupation `o`, period `t`:

- adoption counterfactuals use CPS **worker-share** occupation weights;
- assisted-hours and reported-savings counterfactuals use CPS **actual main-job-hour-share** occupation weights;
- usual main-job hours remain a separately labeled sensitivity only.

The reported quantity is:

`occupation-adjusted industry-context residual = observed industry RPS aggregate - occupation-composition counterfactual`

It is a descriptive standardization gap. It is **not** an identified organizational effect, organizational quality measure, efficiency effect, productivity effect, or causal estimate.

## Validation result

The live residual builder produced:

- **120 primary rows** = 20 industries × 3 metrics × 2 quarters;
- **120/120 supported**, with zero primary suppressed rows;
- **120 leave-one-occupation-out influence rows**;
- **80 usual-hours sensitivity rows** = 20 industries × H/S × 2 quarters;
- **6 cross-period persistence diagnostics**;
- zero residual-identity failures;
- zero unsupported-non-null failures.

The source-side RPS longitudinal component also passed all four release diagnostics: stability, influence, regression contract, and suppression/coverage.

## Composition evidence tiers

The pre-existing CPS composition evidence policy classifies the 20 industries as:

- **16 `primary_stable`**;
- **1 `sensitivity_unstable`** — Management of Companies and Enterprises;
- **1 `limited`** — Other Services, Except Public Administration;
- **2 `excluded` from the primary OEWS-CPS source comparison** — Agriculture and Public Administration because of source-universe comparability, while their CPS/RPS residual calculations remain visible.

The full 20-industry results are retained. The evidence tier is carried on every primary residual row and is not silently used to delete results.

## Cross-quarter persistence

Residual persistence from Q2 2025 to Q2 2026 is **moderate and incomplete**.

### All 20 supported industries

| Metric | Residual-rank Spearman | Same-sign industries | Sign agreement | Median absolute residual change |
|---|---:|---:|---:|---:|
| Adoption | 0.665 | 17/20 | 85% | 4.10 percentage points |
| Assisted hours | 0.451 | 14/20 | 70% | 1.33 pp |
| Reported savings | 0.571 | 14/20 | 70% | 0.40 pp |

### 16-industry `primary_stable` CPS-composition cohort

| Metric | Residual-rank Spearman | Same-sign industries | Sign agreement | Median absolute residual change |
|---|---:|---:|---:|---:|
| Adoption | 0.526 | 13/16 | 81.25% | 4.41 pp |
| Assisted hours | 0.421 | 12/16 | 75% | 1.21 pp |
| Reported savings | 0.553 | 11/16 | 68.75% | 0.51 pp |

These results do not support presenting residuals as stable industry scores or a league table. Stability is meaningfully below perfect even after restricting to the pre-existing `primary_stable` composition cohort.

## Leave-one-occupation influence

The influence diagnostic removes each positive-weight occupation in turn, renormalizes the remaining weights to one, and records the largest resulting residual shift for every industry/metric/quarter row. This is an explicit composition sensitivity, not sampling inference.

Across all 120 rows:

- **21/120** maximum-influence perturbations reverse the residual sign;
- median maximum absolute shift is approximately **5.01 pp for adoption**, **1.22 pp for assisted hours**, and **0.31 pp for reported savings**.

Within the 96 rows belonging to the 16-industry `primary_stable` cohort:

- **19/96** maximum-influence perturbations reverse the residual sign;
- median maximum absolute shift is approximately **4.63 pp for adoption**, **1.22 pp for assisted hours**, and **0.29 pp for reported savings**.

Examples illustrate why influence context is mandatory:

- Construction adoption, Q2 2026: baseline residual about **+1.07 pp**; removing Construction and Extraction occupations and renormalizing shifts it by about **11.62 pp**, to roughly **−10.55 pp**.
- Administrative/Support/Waste adoption, Q2 2026: baseline about **+7.79 pp**; removing Building and Grounds Cleaning/Maintenance shifts it by about **9.48 pp**, to roughly **−1.69 pp**.
- Accommodation/Food adoption, Q2 2026: the largest shift is about **13.74 pp**, driven by Food Preparation and Serving occupations; the residual remains negative but changes materially in magnitude.

These are composition leverage diagnostics. They do not establish that the influential occupation causes the industry residual.

## Usual-hours sensitivity

The existing 98% coverage gate is retained; it was not relaxed to manufacture a sensitivity result.

For Q2 2025, **0/20** industries have supported usual-hours H/S composition under that gate. For Q2 2026, **1/20** does: Public Administration at about **98.09%** valid-worker coverage. Consequently 78 of 80 usual-hours H/S sensitivity rows are suppressed.

For the one supported Q2 2026 industry:

- Public Administration assisted-hours residual: actual-hours basis about **−4.20 pp** versus usual-hours sensitivity about **−4.26 pp**;
- Public Administration savings residual: actual-hours basis about **−0.83 pp** versus usual-hours sensitivity about **−0.85 pp**.

This isolated agreement is not evidence that actual and usual hours are interchangeable across industries. The broad usual-hours sensitivity remains unsupported because non-point-valued usual-hours responses prevent the 98% gate from being met.

## What this closes and what it does not

### R1.1-G1 / issue #5

The empirical RPS blocker for R1.1-G1 is now resolved. The validated CPS composition foundation already existed; this live execution supplies the previously missing authorized RPS A/H/S join and produces the required occupation-composition counterfactuals/residuals for every supported cell. Once this evidence package is merged with green CI, issue #5 can close.

### R1.1-G2 / issue #6 remains open

This checkpoint advances, but does not complete, the residual robustness gate. It supplies:

- two CPS-supported quarters;
- sign/rank persistence;
- leave-one-occupation-out influence;
- actual-hours primary estimates;
- usual-hours sensitivity under the unchanged coverage gate.

Still required before #6 can close include the remaining predeclared robustness dimensions where defensible: explicit coverage-threshold sensitivity, finer-occupation/crosswalk sensitivity, class-of-worker sensitivity where supported, and inferential/partial-identification treatment where evidence permits. Formal design-based CPS composition uncertainty remains separately open under issue #14.

### R1.1-G3 / issue #7 remains open

The OEWS composition foundation is already canonical, but #7 still requires applying the authorized RPS adoption observations to the independent May 2025 OEWS employment composition. Unpublished OEWS occupation cells must remain partially identified rather than zero-imputed or silently renormalized. CPS and OEWS counterfactuals must be reported independently; they must not be averaged.

## Publication decision

This validation does **not** authorize an industry-residual ranking surface.

A future UI may expose residual evidence only after the remaining robustness gate decides which rows/findings are stable enough to display and carries weighting basis, evidence tier, coverage, suppression, influence, period persistence, and interpretation limits with the result.

No public-launch, causal, organizational-effect, efficiency, or productivity claim follows from this checkpoint.
