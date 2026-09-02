# BTOS firm-side AI evidence — construct and source alignment

Status date: **2026-09-02**  
Issue: **#9 — R1.2**  
Status: **construct gate established; no BTOS observations ingested**

## Decision

The Business Trends and Outlook Survey (BTOS) can add a valuable firm-side evidence layer to the observatory, but it cannot be treated as a worker-level analogue of RPS adoption.

The canonical relationship is:

```text
BTOS: business reports about business AI use, business functions, and task changes
RPS:  worker reports about GenAI work adoption, assisted work time, and reported time savings
```

These measurement objects may be compared as triangulation after exact source vintages and a sector crosswalk are validated. They must not be merged into a composite adoption score or interpreted as identifying an organizational effect.

This checkpoint does **not** add a BTOS statistic, download an official BTOS workbook into the repository, or perform a BTOS-to-RPS sector join. The machine-readable contract is `data/registry/btos_construct_scope_v1.json`.

## 1. Survey population and unit

The Census Bureau describes BTOS as a continuous, high-frequency survey of U.S. employer businesses. The sample is approximately 1.2 million businesses divided into six panels of roughly 200,000 businesses, with each panel asked to report once every 12 weeks for about one year and data collection every two weeks.

For data from September 11, 2023 onward, the published BTOS universe includes single- and multi-location employer businesses in the U.S. economy, excluding farms. Published sector products use 2022 NAICS.

Sources:

- https://www.census.gov/hfp/btos/about
- https://www.census.gov/data/experimental-data-products/business-trends-and-outlook-survey.html

This is a **business** survey. Its published percentages are not worker-weighted RPS adoption rates. The current methodology states that a percentage for a response category is the sum of nonresponse-adjusted business weights for that response divided by the sum of nonresponse-adjusted weights for businesses responding to the question.

Source:

- https://www.census.gov/hfp/btos/downloads/methodology/Business_Trends_and_Outlook_Survey_Methodology_V6.pdf

## 2. Core AI series: a structural wording break in November 2025

The original BTOS core AI question asked about use of AI **in producing goods or services**. Beginning with the collection that started November 17, 2025, Census replaced that formulation with the broader **in any of its business functions** wording.

The updated current-use object is therefore business-reported AI use in any business function over the previous two weeks. The corresponding expected-use question asks about the next six months.

Census reports that a level shift was observed in conjunction with the wording change and created a new AI time series beginning with the December 4, 2025 release. The older series remains separately available under the historical `AI Core Questions (Original)` table.

Source:

- https://www.census.gov/hfp/btos/downloads/AI%20Question%20Wording%20Updates.pdf

### Governance consequence

The observatory must never splice the pre-change and post-change AI core series into one continuous adoption series. A chart or statistic spanning the break must either:

1. display the two series as different measurement regimes; or
2. restrict analysis to one regime.

A visual level discontinuity is not evidence of an economic adoption shock when the measurement question itself changed.

## 3. 2025–26 AI supplement: a pooled snapshot, not a biweekly core series

The third AI supplement was fielded from November 17, 2025 through February 8, 2026. Census pooled responses from all six biweekly panels. Nonresponse adjustment was performed panel by panel, and weights were adjusted to reflect pooled estimation. The published percentage for a response category uses adjusted business weights among businesses responding to that question.

The supplement is therefore a pooled six-panel business snapshot. It is not a single biweekly core observation and should not inherit the core series' time label mechanically.

Sources:

- https://www.census.gov/hfp/btos/about
- https://www.census.gov/hfp/btos/downloads/methodology/Business_Trends_and_Outlook_Survey_Methodology_V6.pdf

### Selected constructs

The official 2025–26 questionnaire defines several objects relevant to the observatory.

**Question 24 — business-function use.** Over the last six months, the business reports whether it used AI in each of 15 listed business functions, including production, service provision, strategy, finance/accounting, sales/marketing, customer service, R&D, IT, HR, communications, management/administration, sourcing/supply chain/purchasing, quality, distribution, and legal/compliance.

**Question 25 — task-change modes.** Over the last six months, the business may report that AI was used to perform a task previously done by an employee, supplement or enhance an employee task, introduce a new task, or none of these. The item is multi-select.

**Question 26 — replacement intensity.** Businesses that report replacement in Question 25 classify the number of employee tasks instead performed by AI as small, moderate, or large. This is an ordinal category, not a count of tasks or a productivity measure.

Source:

- https://www2.census.gov/data/experimental-data-products/business-trends-and-outlook-survey/questionnaire-ai-supplement.pdf

These questions are especially useful because they separate business-level AI use from function breadth and reported task change. They still do not measure the same object as worker-reported RPS task adoption.

## 4. API and source-vintage contract

The official BTOS API reference states that core BTOS data can be accessed by period/strata and that time series require sequentially retrieving periods and joining them. It also states that supplemental content is currently **not available through the API**; the official Excel files must be used for supplement data.

Source:

- https://www.census.gov/hfp/btos/downloads/BTOS%20API%20Reference%20Documentation.pdf

This creates two reproducibility paths:

### Core AI

For a core analysis, freeze each exact period/dataset used and record:

- period ID and collection/reference dates;
- exact question and answer identifiers;
- strata fields;
- estimate and uncertainty fields;
- retrieval date;
- source endpoint/query;
- suppression/null behavior.

Do not reconstruct a time series without recording every constituent period.

### AI supplement

For the supplement, acquire the official downloadable file and record:

- canonical URL;
- retrieval date;
- file size;
- SHA-256;
- questionnaire/methodology vintage;
- table/sheet identity;
- suppression and uncertainty fields.

Do not substitute core API data for unavailable supplement data.

## 5. Sector taxonomy and unclassified businesses

Current BTOS products use 2022 NAICS sector and subsector classifications. A BTOS-to-RPS comparison therefore requires a versioned mapping from Census sector categories into the observatory's 20 RPS industry groups.

Multi-location businesses operating in more than one sector can be assigned to an unclassified sector and excluded from detailed sector totals to avoid double counting. That exclusion affects the denominator of detailed sector comparisons and must be surfaced as a coverage/universe caveat rather than silently redistributed.

Sources:

- https://www.census.gov/hfp/btos/about
- https://www.census.gov/data/experimental-data-products/business-trends-and-outlook-survey.html

## 6. Cross-source construct contract

The observatory will keep the following objects distinct.

| Symbol | Object | Unit / denominator |
| --- | --- | --- |
| `B_core_current` | Current BTOS business AI use under post-Nov-2025 wording | Businesses responding to BTOS question, survey-weighted |
| `B_core_expected` | Expected BTOS business AI use over next six months | Businesses responding to BTOS question, survey-weighted |
| `B_function` | BTOS business-reported AI use by named business function | Businesses responding to supplement item, pooled weighted estimate |
| `B_task_change` | BTOS business report of task replacement/enhancement/new task | Businesses responding to supplement item, pooled weighted estimate |
| `A_worker` | RPS worker-reported GenAI adoption for work | Workers under RPS measurement contract |
| `H_worker` | RPS share of work hours actively using GenAI | Worker/work-hour construct |
| `S_worker` | RPS reported counterfactual hours-saved share | Worker self-report construct |

Forbidden collapses:

- business AI use ≠ worker adoption;
- business-function use ≠ worker task adoption;
- business-reported task replacement/enhancement ≠ productivity;
- legacy BTOS AI series ≠ post-change BTOS AI series;
- a sector-level BTOS/RPS association ≠ an organizational effect;
- BTOS and RPS measures must not be averaged into a composite adoption score.

## 7. Public-source use and attribution

The Census Data API terms allow services to search, display, analyze, retrieve, and view released Census data, subject to confidentiality, representation, attribution, and access conditions. The terms prohibit reidentification and specify the notice:

> This product uses the Census Bureau Data API but is not endorsed or certified by the Census Bureau.

Source:

- https://www.census.gov/data/developers/about/terms-of-service.html

The 2025–26 supplement is an official aggregate public statistical product distributed through the Census downloads page, not respondent microdata. Its eventual ingestion should still pin the exact public artifact and applicable Census website/source terms and citation. This memo does not make a broad legal conclusion beyond the reviewed public-use paths.

## 8. Required reproduction before any new result

Before introducing a BTOS chart or cross-source statistic, the project must:

1. pin exact official source periods/files and provenance;
2. identify exact question/answer/estimate/uncertainty fields;
3. build and test the 2022-NAICS-to-RPS-20-industry crosswalk;
4. preserve unclassified/ambiguous sector treatment and mapping coverage;
5. reproduce official national and sector estimates from the pinned source;
6. preserve published suppression and uncertainty information;
7. label every comparison as business-versus-worker triangulation;
8. keep the November 2025 core-series break explicit;
9. keep supplement pooling and six-month reference windows explicit;
10. avoid causal, productivity, or organizational-effect language.

## Current status

The construct/source gate is ready for a versioned ingestion implementation. No BTOS observation value is canonical in the observatory as a result of this checkpoint.

The next empirical step for #9 is to acquire a specific post-change core release and/or the 2025–26 AI supplement through its official distribution path, freeze its provenance, reproduce published estimates, and then validate the sector crosswalk before any RPS comparison is generated.
