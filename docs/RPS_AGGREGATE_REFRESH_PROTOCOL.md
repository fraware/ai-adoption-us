# RPS published-aggregate refresh protocol

Status: **D-G1 tranche 2 — release-candidate integration implemented; D-G1 remains open**

Date: 2026-09-02

## Purpose

The RPS live published-aggregate rights gate is cleared for the project use recorded in `docs/source-rights/RPS_SOURCE_DECISION.md`. D-G1 requires a repeatable source-refresh path that preserves provenance, detects upstream change, regenerates dependent evidence, and feeds the existing observatory release engine without restoring the retired raw-FRED-to-public-tree architecture.

The RPS production-feed path now has two deliberately separate stages:

1. **source refresh candidate** — retrieve and validate the authorized published aggregate source into a private/transient source snapshot;
2. **observatory candidate component** — consume an already validated private snapshot, partition its source bytes into immutable period objects, regenerate derived longitudinal evidence, and emit a release-engine-compatible candidate manifest.

Neither stage promotes a release. Promotion remains owned by the generic observatory release protocol and requires explicit scientific, editorial, rights, and CI review.

## Source and rights boundary

The current transport layer is the official FRED/ALFRED distribution of the Real-Time Population Survey Generative AI Adoption Tracker. FRED is treated as distribution infrastructure; the underlying project permission is the source-owner permission recorded through the project-owner attestation in `RPS_SOURCE_DECISION.md`.

The cleared scope covers published aggregate observations required by this project, versioned aggregate source checkpoints, selected attributed display, and derived aggregate analysis. It does not establish permission for:

- respondent-level microdata;
- the historical replication package;
- the separate occupation/task-adoption-index artifact;
- unrestricted public mirroring of the complete source database;
- a public API that republishes the complete underlying Tracker database.

Accordingly, source observation bytes remain private/transient candidate inputs. The public release path is `derived_only`. The RPS candidate builder does not create a public raw-observation bundle.

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

A refresh fails closed if the provider release gains, loses, duplicates, or changes the identity of a series relative to the registered contract. Provider drift requires explicit registry/source-scope review before a candidate can advance.

The six excluded national constructs are checked as part of provider inventory validation, but their observation histories are not retrieved by the observatory refresh builder.

## Stage 1: source refresh candidate

`src/genai_at_work/rps_refresh.py` implements the source-specific refresh layer. For every one of the 131 registered series it:

1. validates the exact provider series ID against the canonical manifest;
2. obtains current series metadata and copyright/source tags through the official API client;
3. normalizes series identity through the existing RPS registry logic;
4. requires exact agreement on metric, entity ID, entity type, and entity name;
5. records stable definition metadata, including a hash of provider notes;
6. retrieves the published aggregate observations;
7. normalizes dates, periods, values, realtime fields, units, and source-update metadata;
8. requires observation dates to remain unique and ordered.

The source snapshot receives a deterministic `content_sha256` calculated from scientific source content and stable metadata. Retrieval time and FRED's retrieval-date realtime envelope are excluded from this content identity so an unchanged upstream source remains content-identical across retrieval runs.

`scripts/prepare_rps_refresh_candidate.py` writes the source snapshot and refresh diff only to an external transient directory or, for repository-local work, beneath the ignored private root:

`data/audit/private/`

The source candidate remains non-public and non-promoting.

## Stage 2: observatory candidate component

`src/genai_at_work/rps_release.py` and `scripts/prepare_rps_observatory_candidate.py` connect an accepted private source snapshot to the generic observatory release contract.

This stage performs **no network access**. It first recomputes the source snapshot's scientific `content_sha256`, then revalidates the registered 137/131/6 inventory, canonical entity/metric identity, rights boundary, complete period coverage, percentage domain, and one-observation-per-series-per-quarter contract.

The builder then derives the analytical panel used by the current longitudinal publication surfaces:

- 20 industries × 3 subgroup constructs;
- 22 occupations × 3 subgroup constructs;
- 126 subgroup series total;
- every complete quarterly period present in the validated 131-series source snapshot.

The five work-focused national series remain part of source coverage and provenance but are not inserted into the industry/occupation A/H/S regression panel.

## Period-partitioned private inputs

A cumulative source snapshot is unsuitable as the single immutable release source object because adding a new quarter would change the cumulative file hash and could be misclassified as a historical revision.

The observatory candidate therefore materializes one private source object per complete quarter:

```text
candidate/
  release.json
  inputs/
    rps/
      2025-Q2.json
      2025-Q3.json
      ...
  artifacts/
    longitudinal/
      longitudinal_diagnostics.json
      quarter_diagnostics.csv
      rank_stability.csv
      validation_checks.json
```

Every quarterly input contains all 131 registered source observations for that period and is SHA-256 bound in the candidate manifest. These files stay under `inputs/` and are never copied by the release engine into the public immutable archive.

This partitioning gives the release diff meaningful source semantics:

- a new quarter adds a new period and source object while prior quarter hashes remain unchanged;
- a historical value change modifies the corresponding frozen quarter object;
- a simultaneous new quarter and historical change is classified as `mixed`;
- removal of a previously frozen period/object remains fail-closed in the generic release engine.

## Deterministic derived artifacts

For every complete candidate period, the builder regenerates the existing longitudinal analytical family from the exact source snapshot:

- quarter-level A/H/S correlations and descriptive regressions;
- leave-one-entity-out influence diagnostics;
- pairwise and consecutive rank stability;
- cross-level industry/occupation comparisons;
- machine-readable validation checks.

The derived release artifacts are:

- `rps-longitudinal-diagnostics`;
- `rps-quarter-diagnostics`;
- `rps-rank-stability`;
- `rps-longitudinal-validation`.

All are declared with `evidence_class = 2` and depend explicitly on the RPS source ID. The release manifest's `build.input_sha256` and `build.output_sha256` mappings exactly cover every private quarterly input and every derived artifact.

The builder commit is resolved from a clean Git working tree. Candidate construction fails if the working tree is dirty, preventing a manifest from claiming a source revision that does not correspond to committed builder code.

## Required diagnostics

The RPS component emits all four diagnostic classes required by the generic observatory release engine:

- `stability` — validates complete finite rank-stability structures and expected quarter-pair counts;
- `influence` — validates leave-one-out counts and influence ranges for each entity type and period;
- `regression_contract` — checks correlations, R² values, and incremental R² quantities remain finite and inside their mathematical domains;
- `suppression_coverage` — binds the complete-series/entity/period/value validation result.

Any failed diagnostic is carried as `status = fail`, which causes the generic release engine to block publication.

These diagnostics establish computational and coverage contracts. They do not convert descriptive aggregate relationships into causal evidence or conventional inferential claims.

## Claim traceability

`data/registry/longitudinal_claim_inventory.json` remains the conservative publication dependency registry. Each registered longitudinal public claim is bound to the complete RPS derived artifact set in the candidate manifest.

This intentionally over-approximates dependency scope. Until a finer machine-verified dependency graph exists, a changed longitudinal artifact causes every registered dependent public claim to enter review. The release engine may not silently infer that unchanged wording remains valid after upstream evidence changes.

Current tracked surfaces include the homepage longitudinal summary, industry explorer, occupation explorer, technical essay, and repository-level longitudinal status.

## Candidate revision semantics

The RPS component follows the generic release engine's source transition language:

- first RPS component build: source `revision_status = new_wave`, release `release_type = baseline`;
- added period with frozen prior period hashes: `new_wave`;
- changed historical period object with no added period: `revision`;
- added period plus historical change: `mixed`;
- unchanged source objects: `unchanged` at source level; any changed derived artifact still constitutes a release revision.

`source_vintage_id` is the deterministic scientific content hash of the accepted source snapshot. An actual source change must advance that identity.

Definition and taxonomy identity are separately hashed. A future change to the registered construct/entity/definition contract is blocked by the generic release engine and requires an explicit specification decision instead of ordinary wave promotion.

## Generic release-engine compatibility

The generated `release.json` is validated by the existing `validate_release_manifest` contract and is suitable as an input component to the generic stage/review machinery.

The RPS source entry declares:

- `storage_scope = private`;
- `publication_scope = derived_only`;
- `redistribution_scope = derived_only`.

The candidate records `source_input_bytes_publication = false`.

A scientifically valid changed candidate reaches the generic `BLOCKED_REVIEW_REQUIRED` state only after it has been composed into the appropriate observatory release and staged. That state is a review requirement, not publication authorization.

## Global baseline boundary

The repository's observatory release registry currently has **no promoted global baseline**. The RPS component alone is not the whole public observatory release.

Accordingly, `prepare_rps_observatory_candidate.py` emits an explicit global-baseline warning and performs no promotion. The candidate manifest also identifies itself as the RPS longitudinal component only.

The first real observatory release must be composed deliberately from the complete set of publication components that are intended to be frozen under one global release identity, then reviewed and promoted through `scripts/observatory_release.py`.

Promoting an RPS-only component as the first global baseline would incorrectly imply that the rest of the current observatory had been frozen under that release. This tranche does not do that.

## Operator commands

### 1. Retrieve a private source candidate

```bash
PYTHONPATH=src python scripts/prepare_rps_refresh_candidate.py \
  --output-dir data/audit/private/rps-refresh-2026-09-02
```

For comparison with a previous private snapshot:

```bash
PYTHONPATH=src python scripts/prepare_rps_refresh_candidate.py \
  --output-dir data/audit/private/rps-refresh-next \
  --previous-snapshot data/audit/private/rps-refresh-current/rps_source_snapshot.json
```

This networked step requires `FRED_API_KEY`. HTML scraping and manual copying are not accepted substitutes for the registered distribution path.

### 2. Build the RPS observatory component

```bash
PYTHONPATH=src python scripts/prepare_rps_observatory_candidate.py \
  --source-snapshot data/audit/private/rps-refresh-2026-09-02/rps_source_snapshot.json \
  --output-dir data/audit/private/rps-observatory-candidate-2026-09-02 \
  --release-id rps-candidate-2026-09-02
```

For a subsequent wave or revision, provide the previously frozen release manifest used for comparison:

```bash
PYTHONPATH=src python scripts/prepare_rps_observatory_candidate.py \
  --source-snapshot data/audit/private/rps-refresh-next/rps_source_snapshot.json \
  --output-dir data/audit/private/rps-observatory-candidate-next \
  --release-id rps-candidate-next \
  --previous-release-manifest /path/to/previous/release_manifest.json
```

Repository-local candidate directories are restricted to `data/audit/private/`; external transient paths are also allowed. The command refuses non-empty candidate directories and dirty Git working trees.

It prints a review-oriented summary including source vintage, revision status, periods, number of source objects, derived artifacts, diagnostic statuses, claim count, builder commit, and an explicit statement that promotion was not performed.

## Validation coverage

The public test suite uses synthetic 131-series snapshots and verifies:

- exact release-engine manifest compatibility;
- `derived_only` source rights and publication boundary;
- all registered longitudinal claims are traceable;
- every required diagnostic passes on a valid complete panel;
- a new wave adds one period object without changing frozen historical input hashes;
- a historical source value revision changes only its period object;
- simultaneous new-wave and historical change becomes `mixed`;
- source snapshot tampering fails content-hash validation;
- incomplete series-period coverage fails closed;
- retrieval-time/realtime-envelope changes do not alter scientific candidate input or artifact hashes;
- the operator command remains private, does not contain live-source fetching, and contains no promotion path.

The repository-wide release-candidate workflow additionally runs the full Python test suite, source compilation, Ruff, strict mypy, Git whitespace checks, TypeScript validation, optimized Next.js production build, private-data build-tree checks, and route smoke tests.

## Current limitations and remaining D-G1 work

D-G1 remains open. Tranche 2 closes the missing software connection between an authorized RPS source snapshot and a release-engine-compatible derived candidate component, but it does not establish that a live source execution or a global observatory release has occurred.

Remaining work is:

1. execute the refresh pipeline against the complete live 137-series provider release using an authorized credential path and retain the resulting private evidence;
2. inspect actual live coverage, source metadata, definition hashes, period coverage, and any revision/new-wave diff instead of assuming the synthetic contract matches the current upstream state;
3. decide and pin the operational source-check cadence/trigger and release-date handling;
4. determine how upstream historical vintages/revisions should be retained when the official distribution exposes them adequately;
5. carry available uncertainty/sample-size assets with future observations without fabricating unavailable subgroup standard errors or covariance information;
6. compose the first complete global observatory baseline rather than promoting the RPS component in isolation;
7. stage that complete baseline through the generic release engine, run CI, perform explicit scientific/editorial/rights review, and promote only if the exact staged hashes are approved;
8. execute at least one end-to-end synthetic or real subsequent-wave rehearsal against a frozen promoted baseline and verify immutable-history behavior;
9. decide whether a source-owner direct machine-readable feed should eventually replace FRED/ALFRED transport, without changing source semantics silently.

Networked automation should be added only when the credential/secret path, cadence, failure notification, and evidence-retention policy are explicit.

No public-launch, causal, productivity, organizational-effect, source-equivalence, or successful-live-refresh claim follows from this tranche alone.
