# RPS source-rights and production-feed decision

Status: **OPEN — direct permission/feed decision not yet obtained**

This record governs whether and how GenAI at Work may ingest, store, transform, and publish direct Real-Time Population Survey (RPS) Generative AI Adoption Tracker observations in the public observatory.

Until an authorized source-owner/data-provider decision is recorded here, the public product remains `DATA_MODE=derived_only` and `fred_live_no_store` remains fail-closed. Public availability, FRED distribution, a public tracker, and a preferred citation are not treated as substitutes for an explicit decision covering the product's intended persistent use.

## Current source/catalog audit

The current FRED release for the RPS Generative AI Adoption Tracker contains **137 series**. FRED announced that release on 2026-07-24.

The repository's canonical RPS source registry intentionally contains **131 series**:

- 5 national work/economic constructs;
- 60 industry series = 20 industries × adoption / assisted-hours / reported-savings;
- 66 occupation series = 22 occupations × adoption / assisted-hours / reported-savings.

The six-series difference has been provenance-resolved. FRED's full release contains 11 national series; the repository excludes exactly six national overall/outside-of-work constructs:

- `RPSGENAIUSAGESHAREALL` — adoption overall;
- `RPSGENAIUSAGESHARENONWORK` — adoption outside work;
- `RPSGENAIUSAGESHAREEDLWALL` — daily use overall;
- `RPSGENAIUSAGESHAREEDLWNON` — daily use outside work;
- `RPSGENAIUSAGESHARELWALL` — use last week overall;
- `RPSGENAIUSAGESHARELWNONWO` — use last week outside work.

Therefore 131 is a deliberate work-focused analytical subset of the 137-series provider catalog, not a stale subgroup inventory. The detailed audit is recorded in `docs/reference/RPS_FRED_SERIES_SCOPE_2026-09-01.md`.

Adding any of those six non-work national constructs later would be a measurement-scope decision, not a routine source-registry repair.

## Why a direct rights decision is still required

Current RPS series on FRED are labeled **Copyrighted: Citation Required**.

FRED's summarized services terms say that series with this label may be displayed or published with proper attribution, provided prohibited uses are avoided. However, FRED's FAQ and full services terms also state that copyright-noticed/third-party data remain subject to the data owner's rights and that the data owner must be contacted for uses beyond personal use. The FRED API terms likewise state that API access does not override third-party rights and that FRED cannot grant source-owner permission.

This combination is not sufficiently unambiguous to treat FRED as the rights authority for a persistent independent observatory that may store source values, preserve historical vintages, expose interactive observations, offer downloads/APIs, and publish transformed statistics.

Primary terms reviewed on 2026-09-01:

- FRED legal notices and services terms: https://fred.stlouisfed.org/legal/
- FRED API Terms of Use: https://fred.stlouisfed.org/docs/api/terms_of_use.html
- current RPS FRED release: https://fred.stlouisfed.org/release?rid=6

### Correction to an earlier working interpretation

The current FRED API Terms of Use were re-read and searched on 2026-09-01 for `cache`, `archive`, and `store`. The current API terms text reviewed in this audit does **not** contain a cache/archive-specific prohibition.

Accordingly, this repository must not justify `fred_live_no_store` by claiming that the current FRED API terms explicitly prohibit caching or archiving unless a specific current provision is subsequently identified and retained.

The present fail-closed architecture is instead grounded in the unresolved source-owner permission scope: FRED distribution does not itself establish the project's rights to persistent independent storage, display, redistribution, historical-vintage retention, or transformed-result publication.

## Underlying measurement/product identified

Primary source family:

- Real-Time Population Survey Generative AI Adoption Tracker;
- public tracker: https://www.genaiadoptiontracker.com/;
- Harvard Project on Workforce description: https://pw.hks.harvard.edu/post/the-generative-ai-adoption-tracker.

The tracker states that its data come from the RPS, a nationally representative online labor-market survey of working-age adults ages 18–64, and cites the underlying research by Alexander Bick, Adam Blandin, and David Deming.

This repository does not infer from the tracker’s public presentation that the underlying subgroup observations may be persisted or redistributed independently.

## Separate historical replication-data path

A distinct research-data path exists for **Bick, Blandin, and Deming (2026), “The Rapid Adoption of Generative AI,” Management Science, DOI 10.1287/mnsc.2025.02523**.

The peer-reviewed article advertises supplemental data files. Adam Blandin's research page describes the published version as including microdata and a replication package. The earlier NBER working-paper page also exposes a data-appendix location for Working Paper 32966.

Relevant public references reviewed on 2026-09-01:

- Management Science article: https://doi.org/10.1287/mnsc.2025.02523
- Adam Blandin research page: https://sites.google.com/view/blandin/research
- NBER Working Paper 32966: https://www.nber.org/papers/w32966
- NBER data-appendix location advertised by the paper: https://www.nber.org/data-appendix/w32966

### Historical package access status

A clean networked runner tested the official INFORMS replication-files endpoint advertised by the published article. The HTTPS request failed certificate validation because the endpoint presented an expired TLS certificate. Certificate verification was **not** disabled and the transport-security failure was not bypassed. No replication package or microdata were retrieved.

Therefore package contents, license/reuse terms, microdata schema, and covered waves remain **unverified**. The existence/advertisement of replication materials is source-supported; the project does not claim possession of or rights to their contents.

### Interpretation

This historical path may support, subject to actual package terms:

- reconstruction of published survey analysis;
- validation of weighting and subgroup construction;
- respondent-level occupation/industry analysis;
- task-level analysis from covered early waves;
- comparison of later Tracker definitions against the published-paper instrument;
- reproducible historical mechanism research.

It must not be assumed to authorize:

- redistribution of current 2025–2026 Tracker observations;
- persistent mirroring of current Tracker values;
- publication of later-wave microdata absent from the package;
- use outside the actual package terms.

## Three independent gates

The canonical permission request preserves three separate decisions:

1. **Live aggregate observatory gate** — current/future published national, industry, and occupation Tracker observations, including persistent display, storage, redistribution, revisions, attribution, and delivery mechanism.
2. **Historical replication gate** — package contents and reuse terms for the published paper's replication materials.
3. **Detailed task/occupation research gate** — access and publication terms for respondent/task/occupation data underlying later RPS research.

A positive decision on one gate must not be propagated to another.

Canonical request: `docs/source-rights/RPS_PERMISSION_REQUEST.md`.

## Current contact route

Harvard Project on Workforce public contact page:

https://pw.hks.harvard.edu/contact

Public contacts recorded for routing:

- general inquiries: `projectonworkforce@hks.harvard.edu`;
- research and press: `kerry_mckittrick@gse.harvard.edu`;
- research and press: `ngazzaneo@hks.harvard.edu`.

The request should be routed to the Tracker/RPS data owner or an authorized decision-maker if those contacts do not hold the relevant rights authority.

No outreach is recorded as sent in this repository unless an actual sent-message record or direct response is available.

## Exact live aggregate decision required

### Data delivery

- machine-readable national, industry, and occupation values;
- complete available historical observations;
- historical revisions/vintages where available;
- stable identifiers and metadata;
- future release cadence and update mechanism.

### Publication and redistribution

- permission for independent non-commercial/public-interest persistent interactive display;
- downloadable CSV/JSON/Parquet redistribution;
- public API redistribution;
- publication of transformed aggregate statistics, including longitudinal and composition-standardized results;
- persistence of superseded historical values for reproducibility;
- attribution, citation, disclaimer, and branding requirements.

### Storage

- whether published observations may be persisted in a versioned build/data store;
- whether any bounded-cache or no-store constraint applies;
- whether historical source vintages may be retained;
- any restriction on mirrors, bulk downloads, APIs, or release archives.

### Methods, revisions, and uncertainty

- questionnaire/instrument wording and change log;
- subgroup-estimation methodology;
- standard errors, confidence intervals, replicate information, or equivalent uncertainty assets;
- revision policy and historical-vintage availability;
- weighting/methodology changes over time;
- treatment of missing/suppressed subgroup estimates.

### Research access

- latest microdata availability;
- application/research-use process;
- permitted linkage with CPS/O*NET/OEWS or other public labor-market sources;
- publication restrictions on microdata-derived aggregate results.

## Decision outcomes and engineering consequences

### Outcome A — direct feed plus explicit publication/storage rights

Implement a versioned direct RPS ingestion adapter. Record source vintages and revisions, retain immutable analytical history if permitted, generate public observation artifacts within the granted terms, and retire FRED as the production observation backbone except for metadata/provenance links where useful.

### Outcome B — display/publication permitted with storage or redistribution constraints

Implement only the explicitly authorized architecture. Separate persistent display, server/build storage, historical-vintage retention, downloadable redistribution, API redistribution, and derived-result publication; do not infer one permission from another.

### Outcome C — direct observation use not authorized for the intended observatory

Keep public RPS observations fail-closed and derived-only. Do not reconstruct a FRED-backed persistent store as a substitute for source-owner permission. Reassess the public product around authorized derived evidence, provenance/source links, and complementary public sources.

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
- storage terms:
- direct observation display/publication terms:
- downloadable redistribution terms:
- public API terms:
- derived-result publication terms:
- attribution/disclaimer requirements:
- uncertainty/inference assets:
- microdata/research-access status:
- engineering decision:
- effective date:
- evidence/reference retained at:

## Current decision

**Unresolved.** No direct source-owner permission response has yet been recorded in this repository. The public architecture therefore remains fail-closed with respect to direct RPS observations.
