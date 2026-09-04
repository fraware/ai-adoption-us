# GenAI at Work — Release 1

**Version:** `v1.0.0`  
**Published:** 4 September 2026  
**Public site:** https://fraware.github.io/ai-adoption-us/

Release 1 is the first published baseline of the U.S. AI Adoption Observatory. It measures how generative AI is moving from workplace adoption into routine use, AI-assisted working time, and reported time savings while keeping those quantities distinct from measured productivity or other realized economic outcomes.

## What is included

Release 1 combines four complementary data sources:

- **RPS / Generative AI Adoption Tracker:** national workplace AI-use history and Q2 2026 industry and occupation measures;
- **Current Population Survey:** Q2 2025 and Q2 2026 industry × occupation composition analysis;
- **Occupational Employment and Wage Statistics:** May 2025 staffing-composition robustness analysis;
- **Business Trends and Outlook Survey:** Q2 2026 employer-side industry comparison.

The common RPS industry/occupation analysis window covers seven quarters from Q4 2024 through Q2 2026.

## Main descriptive findings

Release 1 establishes three recurring patterns within that seven-quarter window:

1. Workplace adoption and AI-assisted working time are more tightly aligned across occupations than across industries in every quarter under both Pearson and Spearman measures.
2. Across occupations, adoption explains more cross-sectional variation in reported time savings than AI-assisted hours in all seven quarters and all 154 leave-one-occupation-out checks.
3. Adoption rankings are more persistent than AI-assisted-hours rankings in 20 of 21 quarter-pair comparisons at both the industry and occupation levels.

Across industries, the relationship between reported savings and adoption versus assisted hours changes by quarter; neither is a uniformly stronger descriptor over the full period.

Full results and tables are in [RESULTS.md](RESULTS.md).

## Industry composition analysis

The release uses CPS data to ask how much of an industry's observed AI-use pattern is associated with its broad occupational composition.

- workplace-adoption benchmarks use occupation worker shares;
- AI-assisted-hours and reported-savings benchmarks use occupation work-hour shares.

The difference between the observed industry value and the occupation-composition benchmark is reported as an **occupation-adjusted industry residual**.

This residual is descriptive. It should not be interpreted as an organizational, management, efficiency, productivity, or causal effect.

## Cross-source comparison

BTOS provides an employer-side measure of recent AI use, while RPS measures worker-reported generative-AI use. Their Q2 2026 sector relationship is reported as descriptive cross-source concordance only because the populations, denominators, technology scope, and reference periods differ.

OEWS provides a second view of industry staffing composition and is used as a robustness source rather than combined with CPS into a single weighting system.

## Statistical limitations

Release 1 does not provide full design-based confidence intervals for the custom pooled CPS occupation-composition vectors. The public CPS material used by the project does not supply the multivariate covariance information required for that calculation.

Available stability and sensitivity diagnostics remain descriptive. Marginal variance approximations are not used to construct an unsupported multivariate covariance model.

Q4 2025 CPS composition is also intentionally unavailable because October 2025 CPS data were not collected; November and December are not used as a substitute quarter.

## What Release 1 does not claim

Release 1 does not estimate:

- measured labor-productivity effects;
- output or total-factor-productivity effects;
- wage or employment effects;
- causal effects of workplace AI adoption or use intensity;
- organizational quality or management effects from industry residuals;
- equivalence between RPS worker measures and BTOS employer measures.

Reported time savings remain a self-reported counterfactual measure.

## Public data and source-use boundary

The public product includes the RPS observations and derived analyses covered by the project's documented publication scope. It does not provide the complete historical RPS subgroup source panel as a public database, unrestricted bulk mirror, or generic source query API.

Private source-input material used during release preparation is excluded from the public Git repository and release bundle when redistribution is outside the documented source-use boundary.

See [source-provenance.md](source-provenance.md) and [source-rights/RPS_SOURCE_DECISION.md](source-rights/RPS_SOURCE_DECISION.md).

## Reproducibility

The repository contains the analysis code, versioned derived artifacts, source metadata, crosswalks, tests, and release metadata needed to identify the published analytical version.

Analyses that depend on source files not redistributed here can be reconstructed by reacquiring the registered official source and following [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

## Published version identity

The current published version is identified by:

- GitHub tag `v1.0.0`;
- the corresponding GitHub Release;
- the release entry in `data/registry/observatory_release_registry.json`;
- the versioned artifacts under `data/releases/`.

These machine-readable records identify the exact published build. This document summarizes its scientific and product scope.
