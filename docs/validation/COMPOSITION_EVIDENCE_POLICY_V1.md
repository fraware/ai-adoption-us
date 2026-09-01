# Stability-qualified CPS/OEWS composition evidence

## Policy status

This checkpoint applies `cps-composition-evidence-v1`. The rule was adopted **after** inspecting the
Q2-2025/Q2-2026 empirical reliability diagnostics, so it is not presented as a preregistered
threshold for this checkpoint. Full unfiltered results remain preserved beside this layer.

A definitionally primary-comparable industry is classified as `primary_stable` when dropping any
one constituent month changes the pooled 22-group CPS worker composition by at most **0.10
L1** in every required quarter. Because total variation is half the L1 distance, this corresponds
to at most **0.05 total-variation mass**. This is a project robustness standard, not
a BLS/Census significance threshold.

## Classification

- primary stable industries: **16**
- primary sensitivity-only industries: **1**
- sensitivity-only names: **Management of Companies and Enterprises**
- limited-comparability industries: **1**
- excluded industries: **2**

No observation is deleted. Sensitivity-only industries remain in the unfiltered tables and must be
shown when the full robustness picture is reported.

## Stability-qualified OEWS comparison

Among stable primary industries with complete 22-group OEWS vectors:

- May-2025 OEWS vs Q2-2025 CPS exact median L1: **0.2621780573100409** across **10** industries
- May-2025 OEWS vs Q2-2025 CPS exact median cosine: **0.9745740343570712**
- May-2025 OEWS vs Q2-2025 CPS exact median Spearman: **0.9614571676914954**
- May-2025 OEWS vs Q2-2026 CPS exact median L1: **0.2474364292963317** across **10** industries
- May-2025 OEWS vs Q2-2026 CPS exact median cosine: **0.9740763189185622**
- May-2025 OEWS vs Q2-2026 CPS exact median Spearman: **0.9553924336533033**

Using partial-identification bounds so that unpublished OEWS cells do not force industry deletion:

- Q2-2025 stable-primary median L1 interval: **[0.28787170952905655, 0.28787170952905655]** across **16** industries
- Q2-2026 stable-primary median L1 interval: **[0.3100537486665398, 0.3100537486665398]** across **16** industries

The CPS stable-primary Q2-2025 versus Q2-2026 worker-composition comparison has median L1
**0.07947241769895491**, median cosine **0.9975852921724357**,
and median Spearman **0.9618644067796611** across
**16** industries.

## Methodological caveats

The stability gate is descriptive. Kish weight-dispersion effective n is also descriptive and does
not account for CPS clustering, stratification, or rotation-group dependence. Formal uncertainty
for custom 22-dimensional industry-composition vectors remains an open design-based inference task.

Both comparison quarters occur during the CPS 2020-Census-based sample redesign phase-in, which
BLS says began in April 2025 and will complete in July 2026. BLS expects the redesign to have a
negligible effect on published estimates. We nevertheless retain it as a comparability caveat for
custom thin-domain estimates.

## Scientific boundary

This layer decides how strongly to rely on CPS composition as an input. It does not establish an
RPS industry-context effect, productivity effect, or causal mechanism. Those claims remain gated on
an authorized compatible RPS occupation vintage and the subsequent robustness program.
