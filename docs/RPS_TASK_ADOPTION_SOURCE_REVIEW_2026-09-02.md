# RPS occupation/task adoption indices — source and construct review

Status date: **2026-09-02**  
Issue: **#17 — R1.3-G1**  
Status: **canonical assets identified; ingestion/publication remains source-gated**

## Decision

The released RPS occupation- and task-adoption indices are scientifically relevant to the observatory's upstream measurement sequence:

```text
capability/exposure -> realized task adoption -> occupation adoption -> assisted-hours penetration -> reported savings
```

They are not yet approved for ingestion or public redistribution.

The official RPS Data page identifies the occupation and task index workbooks, and the Federal Reserve Bank of St. Louis states that the data are publicly available for download through the RPS. Public downloadability establishes discoverability and access. It does not, by itself, establish permission for the observatory to mirror the workbook bytes, retain future vintages, redistribute the values, or publish transformed derivatives.

The current task workbook also fails the observatory's reproducibility gate because its metadata does not identify the exact O*NET database release used to build the occupation-to-work-activity mapping. The field still contains a literal pre-release placeholder.

Accordingly:

- no workbook observations are added to this repository;
- no exposure/adoption correlation is computed from these assets yet;
- no task taxonomy is silently inferred from the current O*NET release;
- no stable Google Sheet identifier is treated as an immutable data vintage;
- no public-download statement is promoted into a redistribution license.

The machine-readable gate is `data/registry/rps_task_adoption_source_scope_v1.json`.

## Canonical source chain

### RPS discovery layer

The official RPS Data page lists, under Generative AI:

- an `Occupation` adoption-index workbook;
- a `Task` adoption-index workbook;
- the associated paper, *What Work Does Generative AI Do?*.

Source: https://sites.google.com/view/covid-rps/data

The official RPS Generative AI page also advertises `Occupation and Task Adoption Indices` alongside the paper.

Source: https://sites.google.com/view/covid-rps/generative-ai

### Current publication

The current publisher record is:

> Alexander Bick, Adam Blandin, David J. Deming, and Tyler Schumacher, *What Work Does Generative AI Do?*, Federal Reserve Bank of St. Louis Working Paper 2026-017, August 25, 2026, DOI 10.20955/wp.2026.017.

Publisher record: https://www.fedinprint.org/item/fedlwp/103693/original  
DOI: https://doi.org/10.20955/wp.2026.017

The September 1, 2026 St. Louis Fed summary states that the indices are based on nearly 14,000 workers across four quarterly waves between August 2025 and May 2026 and that the data are publicly available for download through the RPS. It also states that the indices will be updated with future survey waves.

Source: https://www.stlouisfed.org/on-the-economy/2026/sep/what-work-does-generative-ai-do

The update statement is consequential for provenance: the delivery URL is a mutable surface, not an immutable vintage identifier.

## Occupation workbook

Canonical public asset:

```text
adoption_rates_by_occupation.xlsx
Google Sheet ID: 1_JfNtZVoBi5W_jHEJ1UOs2rhHYRtLXGM
```

Metadata observed on 2026-09-02:

- four pooled RPS waves: August 2025, November 2025, February 2026, May 2026;
- employed respondents with valid occupation, overall at-work GenAI-use, last-week GenAI-use, and survey-weight information;
- survey weighting after pooling the four survey dates;
- directly recorded detailed **2018 SOC** occupation;
- official SOC Major Group, Minor Group, and Broad Occupation aggregations;
- supplied mapping to **2018 Census occupation codes**;
- `adoption_rate`: survey-weighted share in the occupation answering yes to whether they use GenAI for their job, stored on a 0-1 scale;
- `number_observations`: unweighted respondent count across the pooled waves;
- suppression: adoption rate blank below 20 unweighted respondent observations;
- generation statement: `00 - master.do` on **6 Aug 2026**.

The workbook's citation field still reads:

```text
[INSERT FULL CITATION TO THE MEASUREMENT PAPER BEFORE PUBLIC RELEASE]
```

This placeholder is stale because a current publisher citation now exists. It is a release-metadata defect; the observatory records the correct current publication separately and does not rewrite the upstream file.

No standard-error, confidence-interval, license, or copyright field was identified in the workbook metadata visible during this review. This statement is intentionally scoped to the metadata reviewed; it is not a claim that no uncertainty information exists elsewhere in the full research package or paper.

## Task/work-activity workbook

Canonical public asset:

```text
adoption_rates_by_work_activity.xlsx
Google Sheet ID: 17OI5xRALkN4lDZ1fHw2R9xPJUdDgWyFU
```

Metadata observed on 2026-09-02:

- the same four pooled RPS waves;
- the same stated employed-worker population and pooling weights;
- O*NET work-activity aggregation;
- respondents linked to up to 10 O*NET Detailed Work Activities associated with their occupation, then reporting which activities they perform;
- `adoption_rate`: survey-weighted share of performed work-activity observations for which the respondent reports using GenAI; respondents who do not use GenAI for their job are coded zero for task-level use;
- `number_observations`: unweighted work-activity observations;
- at IWA and BWA levels, one respondent can contribute multiple observations;
- suppression below 20 unweighted work-activity observations for DWA, IWA, and BWA;
- released levels: Detailed Work Activity, Intermediate Work Activity, Broad Work Activity;
- generation statement: `00 - master.do` on **6 Aug 2026**.

Two upstream metadata defects remain visible.

First, the activity-source row states:

```text
database release: [INSERT EXACT O*NET DATABASE RELEASE BEFORE PUBLIC RELEASE]
```

This blocks exact task-taxonomy reproduction. O*NET changes over time; the observatory will not infer the missing release from the publication date, the current O*NET release, an exposure paper's O*NET vintage, or apparent task counts.

Second, the citation field retains the same pre-release placeholder as the occupation workbook.

No standard-error, confidence-interval, license, or copyright field was identified in the workbook metadata visible during this review. Again, this is a scoped observation, not a claim about every file or appendix associated with the research.

## Construct contract

Issue #17 exists to prevent a common measurement error: treating theoretical exposure and realized adoption as interchangeable.

The observatory will preserve the following objects:

| Symbol | Construct | Interpretation boundary |
| --- | --- | --- |
| `E_task` | task exposure/capability | model- or rubric-based estimate of where AI could be relevant; not realized use |
| `E_occ` | occupation exposure/capability | occupation aggregate of an exposure/capability construct; not realized use |
| `A_task` | realized task adoption | worker-reported GenAI use for a performed work activity |
| `A_occ` | realized occupation adoption | worker-reported at-work GenAI use aggregated by occupation |
| `H` | assisted-hours penetration | share of work hours actively using GenAI |
| `S` | reported savings | self-reported counterfactual hours-saved share |

These constructs answer different questions. Correlation between them does not collapse them into a single latent `AI impact` variable.

## What the current release supports scientifically

The current source documentation is sufficient to establish that the authors intentionally measure realized adoption separately from exposure. The St. Louis Fed summary reports broad but shallow adoption and explicitly notes that exposure measures explain only part of the cross-occupation/task variation.

That supports the **research question** in #17. It does not yet authorize the observatory to ingest the released values or establish a specific exposure benchmark for comparison.

The eventual analysis, after the source gate clears, should therefore:

1. reproduce upstream headline distributions before adding new statistics;
2. keep each exposure measure separate;
3. report Pearson and rank relationships with coverage and suppression denominators;
4. use descriptive `exposure-adoption gap` language for residual/rank disagreements;
5. test sensitivity to taxonomy crosswalk choices and generic-task classifications;
6. preserve the distinction between respondent counts and work-activity observation counts;
7. avoid worker-level causal interpretation from aggregate occupation/task indices.

## Rights boundary

### What is established

- The official RPS Data page links the two workbooks.
- The St. Louis Fed says the indices are publicly downloadable through the RPS.
- The assets are currently viewable through Google-hosted workbook surfaces.

### What is not established

This review found no asset-specific license or explicit source-owner permission covering:

- repository storage of workbook bytes;
- public mirroring/redistribution of the values;
- publication of transformed derived tables;
- systematic historical-vintage retention as the workbook is updated;
- attribution requirements beyond the workbook's intended paper citation.

FRED terms are not imported onto these separate Google-hosted RPS assets. Conversely, the fact that FRED distributes other RPS Tracker series does not resolve the rights status of these workbooks.

The rights state is therefore **unresolved** and fail-closed.

## Reproducibility boundary

The current Google Sheet IDs identify delivery surfaces, not immutable releases. Before ingestion, an authorized retrieval path must produce canonical bytes and the observatory must record at minimum:

- retrieval timestamp;
- SHA-256 of each workbook;
- workbook generation/vintage metadata;
- exact survey waves;
- exact O*NET database release and crosswalk artifact;
- current citation;
- source-owner terms/permission applicable to storage and redistribution;
- uncertainty/variance information, or an explicit documented absence from the release.

A future update at the same Google Sheet ID must be treated as a potential new source vintage and diffed before any canonical output changes.

## Exposure-measure gate

No exposure series has been selected in this checkpoint.

Selection must precede looking for the most favorable correlation. Candidate exposure measures can differ in model, task taxonomy, scoring rubric, aggregation, and vintage. The observatory should define a small set of scientifically defensible exposure measures *a priori* and compare each independently. It should not tune or average them into a composite to maximize agreement with realized adoption.

For every exposure measure, record:

- underlying AI/model/rubric;
- task and occupation taxonomy/vintage;
- score semantics and scale;
- crosswalk loss/coverage;
- aggregation weights;
- publication/reuse terms;
- whether the measure encodes substitution, assistance, feasibility, time savings, or another construct.

## Blocking conditions for issue #17

Issue #17 must remain open until all of the following are resolved:

1. **Asset rights:** explicit terms or source-owner permission adequate for the intended storage, derived analysis, and publication mode.
2. **Immutable provenance:** canonical workbook bytes acquired through an authorized path and hashed.
3. **Task taxonomy:** exact O*NET database release and supplied occupation-to-work-activity crosswalk identified.
4. **Uncertainty:** determine what uncertainty/variance information accompanies the indices and what can validly be inferred for comparisons.
5. **Exposure preregistration:** exposure measure(s), vintages, taxonomy alignment, and comparison metrics fixed before examining gap rankings.
6. **Source reproduction:** upstream headline quantities reproduced within documented tolerance before novel results are accepted.

Until then, the source is **identified and scientifically relevant, but not ingestion-ready**.
