# Product specification

## 1. Objective

Build a technical data publication that answers a narrow but consequential question:

> How is generative AI moving from availability and adoption into actual work?

The product is not intended to estimate a single aggregate "AI impact" number. It should make it easier to inspect where adoption, routine use, workflow penetration, and reported benefit move together—and where they do not.

## 2. Audience

Primary:

- AI researchers and lab strategists
- economists and labor-market researchers
- firm leaders designing AI deployment
- policy researchers
- technically sophisticated journalists and investors

Secondary:

- informed general readers who need a faithful picture of workplace AI diffusion

## 3. Editorial position

The site should make fewer claims than a typical dashboard and expose more of the measurement machinery.

Every chart should answer four questions without requiring a methodology appendix:

1. What exactly is measured?
2. What is the denominator?
3. Is this directly observed, reconstructed, or self-reported counterfactual?
4. What cannot be inferred from it?

## 4. Information architecture

### `/` — AI at Work

Narrative landing page, not a grid of KPI cards.

Sequence:

1. Current national snapshot.
2. Time-series chart showing work adoption, last-week work use, daily work use, assisted-hours share, and reported-time-savings share.
3. Explanation of why those lines are not interchangeable.
4. Industry conversion scatterplot (`adoption -> assisted hours`).
5. Occupation conversion scatterplot.
6. Two short case studies selected from data, not hard-coded rankings.
7. Link into methodology and downloadable data.

### `/explore/industries`

Primary exploratory workspace.

Controls:

- quarter
- metric
- compare industries
- absolute level / change since previous year
- optional residual overlay

Views:

- ranked dot plot
- time-series small multiples or comparison lines
- adoption vs assisted-hours scatter
- assisted-hours vs reported-savings scatter
- data table with source-series links

Never label a residual "efficiency," "productivity," or "organizational quality."

### `/explore/occupations`

Same basic grammar as industries, enabling direct comparison between occupation and industry structures.

### `/explore/composition`

Experimental view. It should be visually and linguistically separated from directly reported RPS estimates.

Displays:

- observed industry adoption
- occupation-composition counterfactual
- residual / feasible interval where partial identification is used
- decomposition metadata: CPS period, sample definition, weighting basis, crosswalk version

For work-hours-assisted and reported-savings counterfactuals, use work-hour shares rather than worker shares.

### `/methodology`

A first-class product page, not legal fine print.

Sections:

- survey populations
- exact metric definitions
- denominator matrix
- assisted-hours construction
- reported-time-savings interpretation
- survey-question changes / revisions
- RPS-CPS population alignment
- industry/occupation crosswalks
- uncertainty limitations
- source copyright and attribution
- reproducibility/versioning

### `/blog/after-adoption`

Technical essay using the website as evidence. All numeric callouts should be loaded from generated data rather than manually duplicated in prose where practical.

### `/data`

Download page containing:

- canonical observations (CSV / Parquet where permitted)
- series registry
- derived metrics
- data dictionary
- build timestamp / source vintages
- citations and copyright notices

## 5. Visual design

Use an editorial research aesthetic rather than a SaaS dashboard aesthetic.

- readable serif or neutral editorial display type for headings
- compact sans-serif for controls/tables
- generous whitespace
- one strong chart per section
- direct labels where possible
- no decorative gradients, gauges, speedometers, or "AI score" dials
- color only when it encodes a variable or highlights a selected entity
- chart annotations should state measurement caveats in plain language

Accessibility:

- WCAG AA contrast
- keyboard-operable controls
- text alternatives for every chart
- tabular fallback for core figures
- no meaning encoded only by color

## 6. Product invariants

The following statements should remain true across all versions of the site:

- Adoption is not workflow penetration.
- Assisted hours are not the same as hours saved.
- Reported hours saved are not measured labor productivity.
- Industry residuals are not automatically organizational effects.
- Cross-sectional correlations are descriptive unless a separate identification strategy is supplied.
- Small/noisy subgroup cells should never be turned into leaderboards without stability diagnostics.

## 7. First release scope

Ship the RPS data publication first.

Release 1:

- national overview
- full industry explorer
- full occupation explorer
- conversion views
- methodology
- technical blog
- reproducible RPS pipeline

Release 1.1:

- CPS composition counterfactuals
- explicit worker-weight and hour-weight methodologies
- sensitivity / partial-identification bounds

Release 1.2:

- BTOS triangulation when exact construct alignment is defensible

This sequencing keeps the first public release useful while preventing unfinished cross-survey inference from contaminating directly reported data.
