# RPS public observation delivery contract v1

Status date: **2026-09-03**

## Decision

The observatory may publish a bounded, presentation-oriented projection of the authorized RPS aggregate source. It must not publish the complete RPS source history as a static data bundle, expose a generic series-query API, or create an unrestricted bulk mirror.

The machine-readable contract is `data/registry/rps_public_observation_delivery_v1.json`. The executable validator and materializer are in `src/genai_at_work/rps_public_view.py`.

## Public views

The v1 public observation layer contains exactly three observation views:

1. **National history** — the complete available history of the five registered national work measures: work adoption, work use in the prior week, daily work use, assisted-hours share, and reported time-savings share.
2. **Latest industry cross-section** — the latest complete common quarter for the 20 registered industries and the three A/H/S measures used by the longitudinal analysis.
3. **Latest occupation cross-section** — the same latest complete common quarter for the 22 registered occupation groups and the three A/H/S measures.

The latest industry and occupation views are cross-sections only. Historical subgroup observations remain private release-candidate inputs. Historical subgroup structure is published through derived diagnostics, rank-stability results, composition counterfactuals, robustness artifacts, and other reviewed release outputs.

## Rights boundary

This design implements the current source-rights decision without broadening it. The retained decision permits selected attributed aggregate values in the observatory and derived aggregate analysis. It does not establish unrestricted bulk mirroring, a complete-source public API, respondent-level access, or rights to the separate task-index product.

The public observation materializer therefore fails closed if its contract attempts to enable bulk redistribution, a generic query API, historical subgroup publication, or raw source-object publication.

## Release architecture

The public view must be generated from the same validated private RPS source state used to build an observatory release candidate. It is a release artifact, not a second source-ingestion path. Source observations remain private inputs; only the bounded public projection may be copied into a promoted public release.

The intended flow is:

`private RPS source vintage -> validated RPS component -> bounded public observation view -> complete observatory candidate -> explicit review -> promoted release -> website`

No web route should read the private source snapshot or infer a current source state independently of the promoted release.

## Product consequence

This contract is sufficient for a materially richer static observatory without shipping the complete source database. The homepage can show national diffusion and conversion history. The industry and occupation explorers can show the latest observed A/H/S cross-sections. Multi-wave subgroup claims continue to come from the existing derived longitudinal artifacts.

If a future product requires arbitrary historical subgroup observation queries, the public delivery architecture and rights scope must be reviewed explicitly before implementation.
