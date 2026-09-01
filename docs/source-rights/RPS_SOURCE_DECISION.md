# RPS source-rights and production-feed decision

Status: **OPEN — direct permission/feed decision not yet obtained**

This record governs whether and how GenAI at Work may ingest, store, transform, and publish direct Real-Time Population Survey (RPS) Generative AI Adoption Tracker observations in the public observatory.

No public-source availability is treated as permission for independent redistribution. Until this record is resolved, the public product remains `DATA_MODE=derived_only` and `fred_live_no_store` remains fail-closed.

## Why this decision is required

The canonical RPS registry currently maps 131 source series: 5 national constructs, 60 industry series, and 66 occupation series. Many are surfaced through FRED, but FRED is a distribution layer rather than the underlying data owner.

Current FRED API terms state that third-party series may be copyrighted and subject to owner restrictions; use of the FRED API does not override those rights, and users must contact the data owner before using third-party data for purposes beyond personal use. Therefore, the existence of RPS series in FRED is not sufficient authority for a persistent public observation store or independent interactive redistribution.

Primary terms reviewed:

- FRED API Terms of Use: https://fred.stlouisfed.org/docs/api/terms_of_use.html
- FRED API overview: https://fred.stlouisfed.org/docs/api/fred/overview.html

## Underlying measurement/product identified

Primary source family:

- Real-Time Population Survey Generative AI Adoption Tracker;
- public tracker: https://www.genaiadoptiontracker.com/;
- Harvard Project on Workforce description: https://pw.hks.harvard.edu/post/the-generative-ai-adoption-tracker.

The tracker states that its data come from the RPS, a nationally representative online labor-market survey of working-age adults ages 18–64, and that the public tracker combines multiple survey waves. The tracker cites the underlying research by Alexander Bick, Adam Blandin, and David Deming.

This repository does not infer from the tracker’s public presentation that the underlying subgroup observations may be persisted or redistributed independently.

## Current contact route

Harvard Project on Workforce public contact page:

https://pw.hks.harvard.edu/contact

Current public contacts reviewed on 2026-09-01:

- general inquiries: `projectonworkforce@hks.harvard.edu`;
- research and press: `kerry_mckittrick@gse.harvard.edu`;
- research and press: `ngazzaneo@hks.harvard.edu`.

Initial outreach should be directed to the research contact and/or general Project on Workforce address, with a request to route the inquiry to the data owner or person authorized to grant publication/feed rights if necessary.

## Exact permission/feed request

The observatory seeks a documented decision covering all of the following.

### Data delivery

- machine-readable national series;
- machine-readable industry series;
- machine-readable occupation series;
- complete available historical observations;
- historical revisions/vintages where available;
- stable identifiers and metadata;
- expected future release cadence and update mechanism.

### Publication and redistribution

- permission for independent non-commercial/public-interest interactive publication of direct observations;
- whether observation values may be included in downloadable CSV/Parquet/JSON artifacts;
- whether derived subgroup statistics may be redistributed;
- whether transformed/standardized composition results may be published;
- whether charts/tables may display historical values persistently after future source revisions;
- attribution, citation, disclaimer, and branding requirements.

### Storage and caching

- whether raw/normalized observations may be persisted in the project’s build/data store;
- permitted caching duration if persistence is restricted;
- whether server-side no-store retrieval is required;
- whether archival source vintages may be retained for reproducibility;
- any restrictions on public mirrors, APIs, bulk download, or derived release archives.

### Methods, revisions, and uncertainty

- questionnaire/instrument wording and change log;
- subgroup-estimation methodology;
- standard errors, confidence intervals, replicate weights, or equivalent inference information;
- revision policy and historical-vintage availability;
- weighting/methodology changes over time;
- treatment of missing/suppressed subgroup estimates.

### Research access

- latest microdata availability;
- application/research-use process, if any;
- permitted linkage or enrichment with CPS/O*NET/firm-side data;
- restrictions on publication of microdata-derived aggregate results.

## Decision outcomes and engineering consequences

### Outcome A — direct machine-readable feed + explicit publication/storage rights

Implement a versioned direct RPS ingestion adapter. Record every source vintage and revision, retain immutable analytical history if permitted, generate public observation artifacts within the granted terms, and retire FRED as the production observation backbone except where useful for source-link provenance.

### Outcome B — publication permitted but persistence/cache constrained

Implement only the explicitly permitted server-side/no-store or bounded-cache architecture. Public downloadable data and historical-vintage retention remain disabled unless separately authorized. Reproducibility must rely on permitted derived artifacts and source-vintage metadata.

### Outcome C — direct observation redistribution not permitted

Keep the public product rights-safe and derived-only for RPS. Do not reconstruct a persistent FRED cache as a workaround. Reassess the product design around derived diagnostics, metadata/source links, and other public data sources while preserving private research reproducibility under an authorized research-use arrangement if available.

## Required fields when resolved

- provider/data owner:
- authorized contact:
- contact date(s):
- response date(s):
- permission status: `granted | denied | conditional | unclear`
- delivery format:
- complete-history availability:
- historical-vintage availability:
- update cadence:
- storage/cache terms:
- direct observation publication terms:
- downloadable redistribution terms:
- derived-result redistribution terms:
- attribution/disclaimer requirements:
- uncertainty/inference assets:
- microdata/research-access status:
- engineering decision:
- effective date:
- evidence/reference retained at:

## Current decision

**Unresolved.** No direct permission response has yet been recorded in this repository. The public architecture therefore remains fail-closed with respect to direct RPS observations.
