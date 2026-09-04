# Methodology

This document describes the measurement framework used by GenAI at Work and the methods behind Release 1 of the U.S. AI Adoption Observatory.

The central methodological choice is to treat workplace generative-AI adoption, use intensity, reported time savings, and realized economic outcomes as distinct quantities. A high adoption rate does not imply intensive workflow use, and reported time savings are not equivalent to measured productivity.

## 1. Measurement framework

The observatory distinguishes the following stages:

### Work adoption

The share of employed adults who report using generative AI for their job.

This is an extensive-margin measure: it indicates whether use occurs, not how frequently or intensively it occurs.

### Recent and routine use

Frequency measures indicate how recently and how regularly respondents used generative AI for work. Denominators matter: a measure among all employed adults differs from a measure conditional on being an adopter.

### AI-assisted working time

The RPS estimates the share of total working time involving generative-AI assistance from reported days of use, active-use duration, and hours worked. Published values use the midpoint of implied lower and upper bounds, with nonusers assigned zero.

This is a time-allocation measure. It is not the share of workers who use AI.

### Reported time savings

Respondents who used generative AI for work in the previous week report how much additional time they believe the same work would have required without AI. Nonusers are assigned zero.

This is a self-reported counterfactual. It is not an observed measure of labor productivity, output, total-factor productivity, wages, or GDP.

### Realized outcomes

Output, productivity, wages, employment, and firm performance require separate outcome data and an identification strategy. Release 1 does not estimate these effects.

## 2. Primary worker-side source: RPS

Release 1 uses published aggregate series from the Generative AI Adoption Tracker's Real-Time Population Survey (RPS), retrieved through the official FRED/ALFRED interface within the project's documented source-use boundary.

The GenAI Adoption Tracker describes the RPS as a nationally representative online labor-market survey of U.S. adults aged 18–64 designed to complement government surveys such as the Current Population Survey.

The observatory uses national, industry, and occupation series for workplace adoption, AI-assisted working time, and reported time savings, together with national use-frequency measures.

The exact series inventory, source metadata, and retrieval information are documented in [source-provenance.md](source-provenance.md) and the machine-readable registries under `data/registry/`.

## 3. Descriptive longitudinal analysis

Release 1's common industry/occupation analysis window contains seven quarters from Q4 2024 through Q2 2026.

For each quarter, the project calculates descriptive relationships among:

- work adoption (`A`);
- AI-assisted work-hours share (`H`);
- reported time-savings share (`S`).

The analysis includes:

- Pearson and Spearman association between adoption and assisted hours;
- univariate and bivariate regressions describing cross-sectional variation in reported savings;
- leave-one-group-out sensitivity checks;
- rank persistence across quarter pairs;
- comparisons between industry and occupation aggregation.

These statistics describe aggregate cross-sectional structure. They are not causal estimates.

See [RESULTS.md](RESULTS.md) for the reproduced values.

## 4. Industry composition analysis with CPS

Industry-level AI use may partly reflect the occupations employed within each industry. The project therefore constructs occupation-composition benchmarks using the Current Population Survey (CPS).

### Population alignment

CPS samples are restricted to the closest defensible population match to the RPS workplace measures, including the 18–64 age range and an aligned employed-worker universe.

The relevant CPS variables include person weights, main-job industry, main-job occupation, class of worker, usual hours, and actual hours in the survey reference week. Exact variable definitions and codes are taken from the documentation for the relevant CPS vintage.

### Quarter construction

CPS months are selected to match the RPS quarter as closely as possible. The exact month set is recorded in each derived composition package.

Q4 2025 is intentionally unavailable for CPS composition because October 2025 CPS data were not collected. November and December are not treated as a substitute three-month quarter.

### Worker-share weights

For work adoption, industry occupation weights are based on the weighted number of workers:

```text
w_worker(j,o,t) = workers(j,o,t) / workers(j,t)
```

The occupation-composition benchmark for industry adoption is:

```text
A_hat(j,t) = Σ_o w_worker(j,o,t) × A(o,t)
```

### Work-hour weights

For AI-assisted working time and reported time savings, occupation weights are based on weighted main-job work hours:

```text
w_hours(j,o,t) = work_hours(j,o,t) / work_hours(j,t)
```

The corresponding benchmarks are:

```text
H_hat(j,t) = Σ_o w_hours(j,o,t) × H(o,t)
S_hat(j,t) = Σ_o w_hours(j,o,t) × S(o,t)
```

Actual main-job hours are preferred because they align most closely with the RPS reference-week measures. Usual hours are retained as a labeled sensitivity analysis.

### Occupation-adjusted industry residual

For any metric `m`, the project reports:

```text
residual(j,t,m) = observed(j,t,m) - composition_benchmark(j,t,m)
```

The residual indicates how far the observed industry value lies from the value predicted by its broad occupational composition under the specified weighting scheme.

It should not be interpreted as an organizational effect, management-quality effect, efficiency estimate, productivity effect, or causal firm effect. Many unmeasured mechanisms can contribute to the difference.

The detailed composition, robustness, and uncertainty treatment is documented in [CPS_COMPOSITION_UNCERTAINTY.md](CPS_COMPOSITION_UNCERTAINTY.md).

## 5. Classification alignment and coverage

Industry and occupation classifications can differ across sources and vintages. Crosswalks are therefore treated as versioned inputs.

Each composition analysis records, as applicable:

- CPS months and vintage;
- industry and occupation classification systems;
- RPS labels;
- crosswalk version and checksum;
- aggregation rules;
- class-of-worker restrictions;
- unmatched weighted share;
- coverage and suppression diagnostics.

Results with inadequate mapping or support are reported as unavailable. The analysis does not silently renormalize away material unmatched employment.

## 6. OEWS robustness analysis

The Occupational Employment and Wage Statistics (OEWS) May 2025 data provide an independent establishment-side view of occupation × industry staffing.

OEWS differs from CPS in population, data collection, and weighting. The project therefore uses OEWS as a robustness comparison rather than combining it with CPS into a synthetic composition estimate.

Agreement across CPS and OEWS can increase confidence that a composition pattern is not an artifact of one staffing data system. Disagreement is treated as information about source sensitivity.

See [OEWS_ROBUSTNESS.md](OEWS_ROBUSTNESS.md) for the source-universe differences, partial-identification treatment for unpublished cells, and released robustness results.

## 7. BTOS industry comparison

The Business Trends and Outlook Survey (BTOS) provides a separate employer-side measure of recent AI use.

Release 1 compares BTOS sector-level current AI use with RPS worker-reported generative-AI work adoption under a prespecified industry crosswalk and suppression rule.

The two measures are not equivalent:

- BTOS measures responding employer businesses;
- RPS measures employed adults;
- the technology definitions differ;
- the denominators differ;
- the reference periods differ.

Correlations between them are interpreted only as descriptive cross-source concordance.

See [BTOS_RPS_COMPARISON.md](BTOS_RPS_COMPARISON.md) for the period-selection rule, source reproduction, crosswalk, eligible sector sets, and Release 1 results.

## 8. Uncertainty and statistical interpretation

### RPS descriptive statistics

Release 1 reports aggregate descriptive correlations, regressions, rankings, and leave-one-group-out checks. These should not be interpreted as conventional hypothesis tests unless an appropriate sampling-uncertainty model is available for the exact statistic.

### CPS composition uncertainty

The public CPS Basic Monthly material used in Release 1 does not provide the full covariance information required for a design-based confidence interval for the custom pooled 22-category occupation-composition vectors.

For that reason, Release 1 does not attach full design-based confidence intervals to these custom composition benchmarks or residuals. Available stability, sensitivity, and reliability diagnostics remain descriptive.

Marginal generalized-variance-function approximations are not used to infer an otherwise unidentified multivariate covariance matrix.

See [CPS_COMPOSITION_UNCERTAINTY.md](CPS_COMPOSITION_UNCERTAINTY.md) for the detailed treatment.

## 9. Missing data and suppression

Missing or unsupported values remain missing unless a documented method justifies estimation.

In particular:

- unavailable CPS quarters are shown as gaps;
- suppressed BTOS sectors are not reconstructed from neighboring values;
- unsupported composition cells are not silently renormalized into complete estimates;
- source revisions are versioned rather than overwritten without record.

This policy is intended to keep the public output faithful to the evidence actually available.

## 10. Source revisions and vintages

Several upstream sources can revise historical observations or definitions. Reproducible analyses therefore record source identity and vintage alongside generated artifacts.

A source update is reviewed for changes in:

- series identity;
- units and frequency;
- population or question wording;
- classification systems;
- historical values;
- redistribution or publication constraints.

A substantive definition change is treated as a measurement break and documented in the public output instead of being presented as continuous data.

## 11. Interpretation rules

The following distinctions apply throughout the project:

- adoption is distinct from use intensity;
- AI-assisted hours are distinct from hours saved;
- reported time savings are distinct from measured productivity;
- theoretical AI exposure or capability is distinct from realized adoption;
- cross-sectional associations are descriptive without a separate identification strategy;
- occupation-adjusted industry residuals are descriptive standardization residuals;
- BTOS employer use and RPS worker use are different constructs.

These distinctions are part of the measurement design, not editorial caveats added after analysis.
