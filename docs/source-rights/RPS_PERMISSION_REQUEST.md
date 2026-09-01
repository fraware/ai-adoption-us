# RPS production-data permission and feed request

Status: **READY FOR OUTREACH — no sent message is recorded in the repository**

This document is the canonical request for resolving the Real-Time Population Survey (RPS) / GenAI Adoption Tracker data gate for GenAI at Work.

The objective is to obtain answers that map directly to the engineering outcomes in `RPS_SOURCE_DECISION.md`. Public presentation, a public download control, FRED distribution, a paper replication package, and access to research microdata are treated as distinct evidence/rights paths. None is assumed to confer rights attached to another.

## Decision structure

The request deliberately separates three gates:

1. **Live aggregate observatory gate** — rights and delivery mechanism for current/future published Tracker national, industry, and occupation observations.
2. **Historical replication gate** — reuse terms and contents of the replication package associated with Bick, Blandin, and Deming, *The Rapid Adoption of Generative AI*.
3. **Detailed task/occupation research gate** — research access to the respondent/task/occupation data underlying later RPS work, including the 2026 task-level research program.

A positive answer on one gate must not be interpreted as permission on another.

## Proposed contact route

Primary:

- Kerry McKittrick — Project on Workforce research inquiry — `kerry_mckittrick@gse.harvard.edu`

Routing / fallback:

- Project on Workforce general inquiries — `projectonworkforce@hks.harvard.edu`

The public Project on Workforce contact page identifies these addresses. If neither recipient is authorized to decide data-use terms, the request asks them to route it to the Tracker/RPS data owner or authorized decision-maker.

## Proposed subject

**GenAI Adoption Tracker data permission and research-feed request**

## Proposed message

Dear Kerry and Project on Workforce team,

I am building **GenAI at Work**, a public-interest research observatory on how generative AI is entering U.S. work. The project distinguishes adoption from frequency of use, share of work hours assisted by GenAI, reported time savings, and later economic outcomes; it also studies how these measures differ across occupations and industries. The public repository is designed around reproducible source provenance, versioned estimates, and explicit limits on what each measure can support.

The Real-Time Population Survey / GenAI Adoption Tracker is an important primary source for this work. I would like to use the Tracker data in a way that is useful to researchers and policymakers while fully respecting the data owners' publication, storage, attribution, and redistribution requirements. At present, direct RPS observations are deliberately excluded from the public observation store until those terms are explicit.

To avoid conflating different forms of access, I would be grateful for guidance on three separate questions.

### A. Current and future Tracker aggregate data

1. May a non-commercial/public-interest third-party website persistently display published national, industry, and occupation Tracker observations in interactive charts and tables with full attribution?
2. May those published observations be stored in a versioned project data store for reproducible builds, revision tracking, and historical analysis? If storage is constrained, what cache/no-store policy should be used?
3. May published observation values be included in downloadable CSV, JSON, or Parquet files, or exposed through a public API?
4. May transformed aggregate results derived from the published observations—such as longitudinal stability measures, cross-sectional relationships, and occupation-standardized industry counterfactuals—be redistributed publicly?
5. Is there a machine-readable source containing the complete available Tracker history, including revised historical values where applicable? Are prior vintages retained or available?
6. Is there a stable endpoint, file, or other preferred mechanism for obtaining future quarterly releases and accompanying metadata?
7. What citation, disclaimer, branding, or source-link language should an independent research product use?

### B. Historical paper replication package

8. The published version of *The Rapid Adoption of Generative AI* is described by the authors as including microdata and a replication package. What license or reuse terms govern those files?
9. Do those terms permit independent non-commercial research, reproduction of published estimates, linkage to public occupational/task datasets, and publication of new aggregate analyses derived from the replication data?
10. Which survey waves and variables are actually covered by the package, and should any portions be treated as restricted or non-redistributable?

### C. Detailed task/occupation research access

11. The later RPS research program now includes detailed occupation- and task-level GenAI adoption measurement. Is there a research-access process for the respondent-level or task-level data underlying that work and/or later Tracker waves?
12. If research access is possible, what restrictions apply to linkage with CPS, O*NET, OEWS, or other public labor-market data and to publication of aggregate derived results?
13. Are survey instruments, codebooks, weighting documentation, subgroup sample sizes, standard errors/confidence intervals, replicate information, suppression rules, and a methodology/change log available for these detailed estimates?

If useful, the decision matrix below is sufficient; I am happy to implement whichever restrictions you prefer. If another person or institution is the appropriate rights or data-access contact, I would be grateful if you could route this request to them.

The goal is to make the source relationship explicit rather than infer permissions from public availability. I would also be glad to share the observatory architecture or repository if that would help evaluate the request.

Best,
Mateo Petel

## Requested decision matrix

| Gate | Question | Requested answer | Engineering / research consequence |
|---|---|---|---|
| Live aggregate | Persistent interactive display of published values | yes / no / conditional | direct observation charts enabled or disabled |
| Live aggregate | Persistent server/build storage | yes / no / bounded cache | source adapter and cache architecture |
| Live aggregate | Downloadable CSV/JSON/Parquet redistribution | yes / no / conditional | `/data` direct-observation downloads |
| Live aggregate | Public API redistribution | yes / no / conditional | future observation API |
| Live aggregate | Redistribution of derived aggregate statistics | yes / no / conditional | longitudinal/composition research publication |
| Live aggregate | Complete historical values available | yes / no | common-panel rebuild |
| Live aggregate | Historical vintages/revisions available | yes / no | revision-aware archive |
| Live aggregate | Stable future machine-readable feed | endpoint / file / none | update pipeline |
| Live aggregate | Required attribution/disclaimer | exact language | public UI and data metadata |
| Historical replication | Replication-package reuse terms | license / terms / clarification | historical microdata research path |
| Historical replication | Permitted linkage and new aggregate research | yes / no / conditional | historical mechanism research |
| Detailed research | Current/later respondent or task microdata access | process / unavailable | task/occupation mechanism research |
| Detailed research | Permitted external-data linkage | yes / no / conditional | CPS/O*NET/OEWS enrichment |
| Methods | Standard errors / CIs / replicate information | available / unavailable | uncertainty layer |
| Methods | Questionnaire + methodology change log | available / unavailable | construct-version registry |

## Interpretation discipline

A response must be interpreted narrowly.

- Permission to display charts does not imply downloadable or API redistribution.
- Permission to publish derived statistics does not imply permission to persist or redistribute source observations.
- Permission attached to the published-paper replication package does not imply rights for later Tracker waves.
- Research access to respondent-level or task-level data does not imply permission to redistribute those data.
- A preferred citation is not a substitute for a data-use license or explicit permission where one is required.

When a response is received, record the sender, date, exact language, attachments/links, and resulting engineering decision in `RPS_SOURCE_DECISION.md`. Preserve the three gates separately. If any material term is ambiguous, keep the corresponding feature fail-closed and request clarification.

## Outreach record rule

Do not change this document to `SENT` based on intent, a draft, or an unverified mail-history assumption. Mark it sent only when an actual sent-message record is available. Until then, the repository statement is limited to: **no sent message is recorded in the repository**.
