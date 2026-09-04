# Product specification

Status: **Release 1 published 4 September 2026**

## 1. Purpose

GenAI at Work is a public data publication built around one question:

> How is generative AI moving from availability and adoption into actual work?

The product presents workplace AI as a measurement sequence rather than a single adoption or impact number. It distinguishes adoption, frequency of use, AI-assisted working time, reported time savings, and—where future evidence supports it—realized economic outcomes.

## 2. Audience

The primary audience includes researchers, economists, policy analysts, technology and business leaders, journalists, and other readers who need a defensible view of workplace AI adoption in the United States.

The interface should remain accessible to informed general readers while preserving the definitions and qualifications required for technical interpretation.

## 3. Product principles

### Measurement before ranking

The product should make clear what a number measures before emphasizing which industry or occupation is highest. Rankings should not dominate when differences are noisy, unstable, or unsupported.

### Distinct constructs remain distinct

The interface must preserve the following distinctions:

- workplace adoption is not use intensity;
- AI-assisted work hours are not hours saved;
- reported time savings are not measured labor productivity;
- occupation-adjusted industry residuals are descriptive standardization results, not causal organizational effects;
- employer-reported BTOS use and worker-reported RPS use are different measures.

### Provenance near interpretation

A reader should be able to determine the population, denominator, period, source, and relevant limitation without leaving the analytical context.

### Missingness is visible

Unavailable, suppressed, or unsupported values should appear as such. The product should not interpolate or silently reconstruct evidence that the underlying method does not support.

### Versioned evidence

Published pages should load their analytical values from versioned release artifacts. Manual copies of analytical values should be avoided where the released data can be loaded directly.

## 4. Public pages

### `/` — overview

The home page introduces the measurement sequence and the main Release 1 findings. It should answer three questions quickly:

1. how workplace generative-AI use has changed over time;
2. how adoption differs from workflow penetration and reported time savings;
3. where industry and occupation patterns diverge.

The page should provide direct paths to the underlying industry, occupation, methodology, source, and research views.

### `/explore/industries`

The industry page presents supported industry observations for workplace adoption, AI-assisted working time, and reported time savings.

Where available, it also shows:

- occupation-composition benchmarks;
- occupation-adjusted industry residuals;
- composition coverage and weighting information;
- BTOS employer-side comparison;
- longitudinal stability context.

Residuals must remain labeled as descriptive results.

### `/explore/occupations`

The occupation page presents corresponding workplace adoption, AI-assisted working time, and reported time-savings evidence across occupations, together with longitudinal relationships and rank persistence.

It should make it easy to compare occupation structure with industry structure without implying that the two aggregation levels measure the same mechanisms.

### `/methodology`

The methodology page explains:

- construct definitions and denominators;
- RPS population and measurement;
- CPS composition weighting;
- crosswalk and coverage rules;
- OEWS robustness analysis;
- BTOS comparison;
- uncertainty limitations;
- missing-data treatment;
- source revisions and versioning.

### `/sources`

The sources page identifies each upstream source, its role, relevant vintage, population, and publication boundary. It also explains which source material is intentionally absent from the public repository.

### `/blog/after-adoption`

The technical essay provides a narrative interpretation of the released evidence. Its quantitative claims should remain consistent with the same versioned data used by the interactive pages.

## 5. Release 1 evidence

Release 1 includes:

- seven-quarter workplace GenAI evidence from Q4 2024 through Q2 2026;
- national history plus Q2 2026 industry and occupation views for adoption, AI-assisted work hours, and reported time savings;
- CPS Q2 2025 and Q2 2026 industry × occupation composition analysis;
- descriptive occupation-adjusted industry residuals;
- May 2025 OEWS composition robustness analysis;
- Q2 2026 BTOS–RPS industry comparison;
- methodology, provenance, and technical-research pages linked to the same published evidence.

The complete historical RPS subgroup source panel is not offered as a public database or unrestricted bulk download.

## 6. Visual and interaction design

The visual language should resemble an analytical publication more than a business-intelligence dashboard.

Design requirements:

- charts should have a clear analytical purpose;
- titles and annotations should state the measured quantity directly;
- units and denominators should be visible where ambiguity is possible;
- tables should provide accessible equivalents for important charted values;
- color should encode data or selection, not decorative status;
- keyboard navigation, semantic structure, contrast, and reduced-motion behavior should be supported;
- mobile layouts should preserve the substantive finding and its qualification;
- unstable or unsupported cells should not be turned into leaderboards.

## 7. Data configuration

The application uses an explicit `DATA_MODE` setting.

- `derived_only` — public mode using published observations and derived artifacts.
- `audit_snapshot` — private research mode for explicitly supplied audit data.
- `fred_live_no_store` — reserved server-side mode for direct source access without persistent public storage.

The public application should not switch automatically into a private data source when public data are unavailable.

## 8. Publication model

A published version consists of a defined repository version, source vintages, generated artifacts, validation results, and release metadata.

A new version should be published when source data, methods, or public analytical results change materially. The publication process should:

1. reacquire and validate required source data;
2. regenerate affected analysis artifacts;
3. run scientific and software validation;
4. review changed values, definitions, provenance, and interpretation;
5. create a new immutable release directory and registry entry;
6. deploy the website from that version;
7. retain the previous version for comparison.

Implementation details are documented for maintainers in [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md).

## 9. Product development after Release 1

Near-term development should focus on making the existing evidence easier to interrogate rather than adding unsupported analytical depth.

Priorities include:

- richer quarter-to-quarter comparison;
- clearer revision and vintage history;
- improved composition-explorer interactions;
- downloadable derived tables where source-use conditions permit;
- stronger uncertainty presentation when methodologically supported;
- eventual task-level and economic-outcome layers under separate source and identification requirements.

See [ROADMAP.md](ROADMAP.md) for the research and product roadmap.
