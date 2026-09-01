# RPS/FRED series-scope audit — 2026-09-01

Status: **verified catalog-scope reconciliation; source-rights decision remains open**

This note reconciles the current FRED release catalog for the Real-Time Population Survey (RPS) Generative AI Adoption Tracker with this repository's narrower source-series registry. It is a metadata/provenance audit only. No RPS observation values are added to the public repository by this audit.

## Result

FRED announced **137 RPS Generative AI series** on 2026-07-24 and currently exposes them under the release `Real-Time Population Survey: Generative Artificial Intelligence Adoption Tracker`.

This repository intentionally registers **131 series**, not 137:

- 5 national work/economic constructs;
- 20 industries × 3 metrics = 60 industry series;
- 22 occupations × 3 metrics = 66 occupation series.

Therefore:

`5 + 60 + 66 = 131`

The full FRED release contains the same 126 industry/occupation A/H/S subgroup series plus **11 national series**:

`11 + 60 + 66 = 137`

The six-series difference is exactly the national overall/outside-of-work use block that is outside the current observatory work-measurement scope. The 131-series registry is therefore a deliberate analytical subset of the 137-series provider catalog, not a stale or incomplete subgroup inventory.

## Five national series in the observatory registry

| Construct | FRED series ID | Repository role |
|---|---|---|
| Adoption rate for work | `RPSGENAIUSAGESHAREWORK` | `adoption_work` |
| Use last week for work | `RPSGENAIUSAGESHARELWWORK` | `work_use_last_week` |
| Daily use for work | `RPSGENAIUSAGESHAREEDLWWOR` | `work_use_daily` |
| Work hours assisted | `RPSGENAIASSISTWRKHRSALL` | `assisted_hours_share` |
| Reported time savings | `RPSGENAITSALL` | `reported_time_savings_share` |

These constructs correspond to the observatory's measurement ladder from work adoption through recent/routine use, work-hour penetration, and reported counterfactual benefit.

## Six national FRED series intentionally outside the current registry

| Construct | FRED series ID | Scope reason |
|---|---|---|
| Adoption rate overall | `RPSGENAIUSAGESHAREALL` | any-purpose adoption, not specifically work adoption |
| Adoption rate outside of work | `RPSGENAIUSAGESHARENONWORK` | personal/non-work use |
| Daily use overall | `RPSGENAIUSAGESHAREEDLWALL` | any-purpose daily use |
| Daily use outside of work | `RPSGENAIUSAGESHAREEDLWNON` | personal/non-work daily use |
| Use last week overall | `RPSGENAIUSAGESHARELWALL` | any-purpose recent use |
| Use last week outside of work | `RPSGENAIUSAGESHARELWNONWO` | personal/non-work recent use |

The omission of these six series is intentional. They may be useful for a future diffusion-context analysis, but adding them to the canonical observatory registry would be a measurement-scope decision, not a source-maintenance correction.

## Source references reviewed

Provider/release evidence:

- St. Louis Fed announcement, 2026-07-24: https://news.research.stlouisfed.org/2026/07/fred-adds-data-about-the-adoption-of-generative-artificial-intelligence/
- Current FRED release: https://fred.stlouisfed.org/release?rid=6

Six omitted national series:

- https://fred.stlouisfed.org/series/RPSGENAIUSAGESHAREALL
- https://fred.stlouisfed.org/series/RPSGENAIUSAGESHARENONWORK
- https://fred.stlouisfed.org/series/RPSGENAIUSAGESHAREEDLWALL
- https://fred.stlouisfed.org/series/RPSGENAIUSAGESHAREEDLWNON
- https://fred.stlouisfed.org/series/RPSGENAIUSAGESHARELWALL
- https://fred.stlouisfed.org/series/RPSGENAIUSAGESHARELWNONWO

Repository registry:

- `data/registry/rps_source_series_manifest.json`

## Rights reading reviewed on 2026-09-01

Current RPS FRED series pages are marked **Copyrighted: Citation Required**. FRED's summarized legal terms say series with that label may be displayed or published with proper attribution provided prohibited uses are avoided.

At the same time, FRED's FAQ, full services terms, and API terms state that copyright-noticed/third-party series remain subject to the data owner's rights; FRED cannot grant owner permission; and third-party data should not be used for purposes beyond personal use without contacting the data owner.

References:

- FRED legal terms: https://fred.stlouisfed.org/legal/
- FRED API terms: https://fred.stlouisfed.org/docs/api/terms_of_use.html

Because those statements do not provide a sufficiently unambiguous source-owner grant for this project's persistent independent public observatory, the repository must continue to treat direct RPS publication/storage/redistribution as unresolved pending an explicit owner/data-provider decision.

### Correction to earlier working interpretation

The current FRED API Terms of Use reviewed on 2026-09-01 were searched for `cache`, `archive`, and `store`; no cache/archive-specific prohibition was found in the current API terms text. The project must therefore **not** cite a FRED API cache/archive prohibition as a reason for the present architecture unless a specific current term is subsequently identified and retained.

The current fail-closed architecture remains justified by the unresolved third-party/source-owner permission scope itself, including persistent display, storage, downloadable redistribution, public API redistribution, historical-vintage retention, and transformed-result publication.

## Engineering consequence

1. Keep the canonical registry at 131 series unless a separate measurement-scope decision adds non-work national constructs.
2. Do not infer that the 131 count is stale merely because the provider catalog contains 137 series.
3. Keep `DATA_MODE=derived_only` for direct RPS observations until the source-owner decision is resolved.
4. Keep FRED as metadata/provenance/discovery evidence; do not promote it to the long-run production-rights authority.
5. Preserve the three independent gates in `RPS_PERMISSION_REQUEST.md`: live aggregate observatory rights/feed, historical replication-package reuse, and detailed task/occupation research access.
