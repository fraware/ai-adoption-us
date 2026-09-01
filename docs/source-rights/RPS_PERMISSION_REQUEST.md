# RPS production-data permission and feed request

Status: **READY FOR OUTREACH — not yet sent**

This document is the canonical request for resolving the Real-Time Population Survey (RPS) / GenAI Adoption Tracker production-data gate for GenAI at Work.

The objective is to obtain answers that map directly to the engineering outcomes in `RPS_SOURCE_DECISION.md`. A public website, public download control, FRED distribution, or an academic replication package is not treated as a substitute for explicit terms governing persistent third-party publication.

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

I am building **GenAI at Work**, a public-interest research observatory on how generative AI is entering U.S. work. The project distinguishes adoption from frequency of use, share of work hours assisted by GenAI, reported time savings, and later economic outcomes; it also studies how these measures differ across occupations and industries. The public repository is designed around reproducible, versioned source provenance and conservative claim boundaries.

The Real-Time Population Survey / GenAI Adoption Tracker is an important primary source for this work. I would like to use the Tracker data in a way that is useful to researchers and policymakers while respecting the data owners' publication, storage, attribution, and redistribution requirements. At present, I am deliberately keeping direct RPS observations out of the public data store until those terms are clear.

Could you please confirm the permitted use and, if possible, the preferred machine-readable delivery mechanism for the Tracker data? In particular, I would appreciate guidance on the following:

1. **Direct display:** May a non-commercial/public-interest third-party website persistently display the published national, industry, and occupation Tracker observations in interactive charts and tables with full attribution?
2. **Storage:** May those published observations be stored in a versioned project data store for reproducible builds and historical analysis? If storage is constrained, what caching/no-store policy should be used?
3. **Downloadable redistribution:** May published observation values be included in downloadable CSV, JSON, or Parquet files, or exposed through a public API?
4. **Derived results:** May statistics derived from the published observations—such as longitudinal correlations, stability measures, occupation-standardized industry counterfactuals, and other transformed aggregate analyses—be redistributed publicly?
5. **Historical vintages and revisions:** Is there a machine-readable source containing the complete Tracker history, including revised historical values where applicable? Are prior vintages retained or available?
6. **Future updates:** Is there a stable feed, endpoint, file, or other preferred mechanism for obtaining future quarterly releases and metadata?
7. **Uncertainty and methods:** Are standard errors, confidence intervals, replicate weights, subgroup sample sizes, suppression rules, survey instruments, or a methodology/change log available for the published subgroup estimates?
8. **Microdata:** Is there a research-access process for the current/later RPS GenAI microdata? If so, what restrictions apply to linkage with public occupational/task or labor-market data and publication of aggregate derived results?
9. **Historical replication package:** The published *Management Science* article identifies supplemental data files / a replication package. Are those files intended for independent research reuse, and is there a specific license or set of terms we should follow?
10. **Attribution:** What citation, disclaimer, branding, or source-link language would you like third-party research products to use?

If useful, a simple response such as the table below is enough; I am happy to implement whichever restrictions you prefer. If another person or institution is the appropriate data-rights contact, I would be grateful if you could route this request to them.

The goal is to make the source relationship explicit rather than infer permissions from public availability. I would also be glad to share the observatory architecture or repository if that would help evaluate the request.

Best,
Mateo Petel

## Requested decision matrix

| Question | Requested answer | Engineering consequence |
|---|---|---|
| Persistent interactive display of published values | yes / no / conditional | direct observation charts enabled or disabled |
| Persistent server/build storage | yes / no / bounded cache | source adapter and cache architecture |
| Downloadable CSV/JSON/Parquet redistribution | yes / no / conditional | `/data` direct-observation downloads |
| Public API redistribution | yes / no / conditional | future observation API |
| Redistribution of derived aggregate statistics | yes / no / conditional | longitudinal/composition research publication |
| Historical values available | yes / no | common-panel rebuild |
| Historical vintages/revisions available | yes / no | revision-aware observatory archive |
| Stable future machine-readable feed | endpoint / file / none | update pipeline |
| Standard errors / CIs / replicate information | available / unavailable | uncertainty layer |
| Questionnaire + methodology change log | available / unavailable | construct-version registry |
| Current/later microdata research access | process / unavailable | mechanism research program |
| Historical paper replication reuse terms | license / terms / clarification | historical microdata path |
| Required attribution/disclaimer | exact language | public UI and data metadata |

## Decision discipline

A response must be interpreted narrowly. Permission to display charts does not imply bulk redistribution. Permission to use derived statistics does not imply permission to persist raw observations. Permission attached to the published-paper replication files does not imply permission for later Tracker waves.

When a response is received, record the sender, date, exact language, attachments/links, and resulting engineering decision in `RPS_SOURCE_DECISION.md`. If any material term is ambiguous, keep the corresponding feature fail-closed and request clarification.
