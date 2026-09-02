# RPS published-aggregate refresh protocol

Status: **D-G1 tranche 1 — source candidate foundation; D-G1 remains open**

Date: 2026-09-02

## Purpose

The RPS live published-aggregate rights gate is now cleared for the project use recorded in `docs/source-rights/RPS_SOURCE_DECISION.md`. The next engineering requirement is a repeatable source-refresh path that preserves provenance, detects upstream change, and feeds the existing observatory release engine without restoring the retired raw-FRED-to-public-tree architecture.

This protocol defines that source-candidate layer.

## Source and rights boundary

The current transport layer is the official FRED/ALFRED distribution of the Real-Time Population Survey Generative AI Adoption Tracker. FRED is treated as distribution infrastructure; the underlying project permission is the source-owner permission recorded through the project-owner attestation in `RPS_SOURCE_DECISION.md`.

The cleared scope covers published aggregate observations required by this project, versioned aggregate source checkpoints, selected attributed display, and derived aggregate analysis. This protocol does not infer permission for:

- respondent-level microdata;
- the historical replication package;
- the separate occupation/task-adoption-index artifact;
- unrestricted public mirroring of the complete source database;
- a public API that republishes the complete underlying Tracker database.

The refresh pipeline therefore produces a private/transient source candidate. It does not create a public raw-observation bundle.

## Canonical provider inventory

The registered provider contract is:

- FRED release ID: `6`;
- current provider release inventory: `137` series;
- current observatory registry: `131` series;
- included national work-focused series: `5`;
- industry series: `60` = 20 industries × 3 subgroup constructs;
- occupation series: `66` = 22 occupations × 3 subgroup constructs;
- intentionally excluded national overall/outside-work series: `6`.

The provider inventory must reconcile exactly as:

`137 = 131 included + 6 intentionally excluded`.

A refresh fails closed if the provider release gains, loses, duplicates, or changes the identity of a series relative to the registered contract. Provider drift requires an explicit registry/source-scope review before observation retrieval proceeds.

The six excluded national constructs are checked as part of the provider inventory, but their observation histories are not retrieved by the observatory refresh builder.

## Source-candidate construction

`src/genai_at_work/rps_refresh.py` implements the source-specific candidate builder. For every one of the 131 registered series it:

1. validates the exact provider series ID against the canonical manifest;
2. obtains current series metadata and copyright/source tags through the official API client;
3. normalizes the series identity through the existing RPS registry logic;
4. requires exact agreement on metric, entity ID, entity type, and entity name;
5. records stable definition metadata, including a hash of the provider notes;
6. retrieves the published aggregate observations;
7. normalizes dates, periods, values, realtime fields, units, and source-update metadata;
8. requires observation dates to remain unique and ordered.

The snapshot receives a deterministic `content_sha256` calculated from source content and stable metadata. Retrieval time is deliberately excluded from this content digest, so an unchanged upstream source remains content-identical across retrieval runs.

The source snapshot retains metadata needed to diagnose definition changes without copying full provider notes text into every candidate.

## Private storage boundary

`scripts/prepare_rps_refresh_candidate.py` accepts an explicit `--output-dir`.

If the destination is inside the repository, it must resolve beneath:

`data/audit/private/`

That path is Git-ignored and excluded from the public product. An external transient directory is also permitted.

The command writes:

- `rps_source_snapshot.json` — the private source observation snapshot;
- `rps_refresh_diff.json` — the private detailed revision/new-wave diff;
- `rps_refresh_candidate.json` — a review-safe summary containing provenance hashes, inventory counts, change counts, and the next release gate.

The summary explicitly records `public_raw_observations_included = false` and `promotion_state = source-candidate-only`.

## Revision semantics

When a previous private source snapshot is supplied, the refresh is classified as:

- `unchanged` — no added, revised, removed, or definition-changed source content;
- `new_wave` — one or more new observation dates, with no historical or definition changes;
- `revision` — historical values were revised or removed, or registered series definition metadata changed, with no new wave;
- `mixed` — both new-wave content and revisions/definition changes are present.

Definition drift currently monitors title, metric identity, entity identity, frequency, unit, seasonal-adjustment status, and source-notes hash.

Any status other than `unchanged` requires release review. A new wave is not silently promoted merely because its series inventory is complete.

## Release boundary

This tranche does **not** promote a source snapshot into the public observatory and does **not** close D-G1.

After a candidate is retrieved and reviewed, downstream work must still:

1. determine whether the source change is scientifically compatible with existing constructs and taxonomies;
2. regenerate every dependent derived artifact from the exact candidate source vintage;
3. run the required stability, influence, regression-contract, suppression/coverage, and claim-dependency diagnostics;
4. stage a candidate through the existing observatory release engine;
5. bind scientific/editorial/source-rights review to the exact staged hashes and build revision;
6. promote only after the release gate passes.

The release engine remains authoritative for promotion. Source input bytes are not copied into its public release archive.

## CLI

Example private research execution:

```bash
PYTHONPATH=src python scripts/prepare_rps_refresh_candidate.py \
  --output-dir data/audit/private/rps-refresh-2026-09-02
```

With a previous private snapshot:

```bash
PYTHONPATH=src python scripts/prepare_rps_refresh_candidate.py \
  --output-dir data/audit/private/rps-refresh-next \
  --previous-snapshot data/audit/private/rps-refresh-current/rps_source_snapshot.json
```

The command requires `FRED_API_KEY`. HTML scraping and manual copying are not accepted substitutes for the registered distribution path.

## Current limitations and remaining D-G1 work

This tranche establishes deterministic source acquisition and source-change classification, but the production-feed issue remains open. Remaining work includes:

- execute the pipeline against the complete live 137-series provider release and inspect the resulting candidate evidence;
- decide and pin the operational cadence/trigger for future source checks;
- integrate a reviewed source candidate into the generic observatory release-candidate builder and dependent-regeneration graph;
- preserve upstream historical vintages/revisions where the official distribution exposes them adequately;
- determine the exact long-run direct machine-readable Tracker delivery path if a source-owner feed becomes preferable to FRED/ALFRED transport;
- carry available uncertainty/sample-size assets with future observations without fabricating unavailable subgroup inference information;
- add networked workflow execution only once the required credential/secret path and evidence-retention policy are explicitly configured;
- complete the first end-to-end new-wave rehearsal before calling D-G1 complete.

No public-launch, causal, productivity, or source-equivalence claim follows from successful source retrieval alone.
