# Data sources and provenance

GenAI at Work combines four U.S. data systems that observe different parts of workplace AI use. This document records what each source measures, how it is used, the vintages included in Release 1, and the relevant publication limits.

The sources are intentionally kept distinct. Worker-reported use, employer-reported use, household-survey staffing composition, and establishment staffing data are not interchangeable measurements.

## Real-Time Population Survey / Generative AI Adoption Tracker

**Role in the observatory:** primary source for workplace generative-AI adoption, use frequency, AI-assisted working time, and reported time savings.

**Source:** the Generative AI Adoption Tracker by Alexander Bick, Adam Blandin, and David Deming, distributed as published aggregate series through FRED/ALFRED.

### Series used

The project registers **131 work-focused series**:

- 5 national work-use measures;
- 60 industry series: 20 industries × 3 measures;
- 66 occupation series: 22 occupations × 3 measures.

The three subgroup measures are work adoption, AI-assisted work-hours share, and reported time-savings share.

Release 1 was built from a source history containing **962 observations** across the registered series where observations were available. The common industry/occupation A/H/S analysis window contains **882 observations** over seven quarters, Q4 2024 through Q2 2026.

### Public data included

The public RPS presentation includes:

- seven-quarter national history;
- the latest complete Q2 2026 industry A/H/S cross-section;
- the latest complete Q2 2026 occupation A/H/S cross-section;
- derived longitudinal statistics and diagnostics used in the published analysis.

The project does not publish the complete historical subgroup source panel as a general-purpose database, unrestricted bulk mirror, or generic source API.

### Source-use basis

The repository records published-aggregate project use as permitted on the basis of a project-owner attestation that permission was obtained from the source owner. The underlying correspondence or agreement is not part of the public repository and was not independently inspected as part of the software review.

Accordingly, this repository claims only the use described in [source-rights/RPS_SOURCE_DECISION.md](source-rights/RPS_SOURCE_DECISION.md). It does not infer broader rights for respondent-level data, other RPS products, unrestricted redistribution, or third-party reuse.

RPS source files used during release preparation are acquired outside the public Git history when redistribution is not covered. Published outputs retain source attribution and series provenance.

FRED is a distribution service for the series and should not be described as endorsing this project.

## Current Population Survey (CPS)

**Role in the observatory:** primary source for the occupational composition of industries and for worker- and work-hour-based composition weights.

**Source:** U.S. Census Bureau / U.S. Bureau of Labor Statistics, Current Population Survey Basic Monthly public-use data.

Release 1 includes validated composition analyses for:

- Q2 2025;
- Q2 2026.

For work-adoption benchmarks, the project uses CPS worker shares. For AI-assisted working time and reported-savings benchmarks, it uses actual main-job work-hour shares. Usual-hours weights are retained as a sensitivity analysis.

Q4 2025 is unavailable for CPS composition because October 2025 CPS data were not collected. November and December are not used to construct an artificial three-month quarter.

The CPS analysis produces occupation-composition benchmarks and occupation-adjusted industry residuals. These are descriptive standardization results; they do not identify management quality, organizational effects, efficiency, productivity, or other causal mechanisms.

Release 1 also does not report full design-based confidence intervals for the custom pooled occupation-composition vectors because the necessary multivariate covariance information is not available in the public CPS material used by the project.

## Occupational Employment and Wage Statistics (OEWS)

**Role in the observatory:** independent robustness source for industry × occupation staffing composition.

**Source:** U.S. Bureau of Labor Statistics, Occupational Employment and Wage Statistics.

Release 1 uses **May 2025** OEWS staffing data.

OEWS is establishment-based and primarily covers wage-and-salary employment, whereas CPS is a household survey with a different population and coverage. OEWS is therefore used as a separate robustness comparison, not as a replacement for CPS and not as part of a synthetic combined weighting system.

Agreement or disagreement between CPS and OEWS is reported as source sensitivity. Neither source by itself identifies an organizational or productivity effect.

## Business Trends and Outlook Survey (BTOS)

**Role in the observatory:** employer-side comparison of recent AI use across sectors.

**Source:** U.S. Census Bureau, Business Trends and Outlook Survey.

Release 1 includes the preregistered Q2 2026 BTOS–RPS industry comparison.

The two measures have different units and populations:

- BTOS measures responding employer businesses reporting AI use in any business function during the previous two weeks;
- RPS measures employed adults reporting generative-AI use for their jobs.

Their technology scope, denominator, and reference period also differ. Sector correlations are therefore interpreted only as descriptive cross-source concordance. The analysis does not treat the two percentages as interchangeable and does not reconstruct suppressed BTOS sectors.

## Source revisions

Source data and definitions can change over time. Each published version of the observatory records the source identities and analytical artifacts used for that version.

When an upstream source changes, the project distinguishes among:

- new observations;
- revisions to historical values;
- changes in definitions or wording;
- changes in classifications or crosswalks;
- changes in source-access or publication conditions.

Substantive changes trigger regeneration and review of affected results. Previous public releases remain preserved so that revisions are visible rather than silently replacing earlier evidence.

## Attribution and reuse

Third-party data retain their original terms. The project's publication of selected observations or derived results should not be interpreted as granting rights the project does not hold.

For reproducibility, the repository provides source identifiers, metadata, acquisition and analysis code, public derived artifacts, and source-specific documentation. Where source files are intentionally absent, researchers should reacquire them from the authoritative source subject to the applicable terms.
