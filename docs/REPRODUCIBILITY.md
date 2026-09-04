# Reproducibility contract

## Scope

The public repository is a rights-safe reproduction and release-control package. It contains source code, registries, versioned public/derived evidence, CPS/OEWS/BTOS inputs or source identities where redistribution permits them, validation logic, the web publication, and the release machinery. It deliberately excludes private RPS candidate input bytes and does not expose the complete historical RPS subgroup source panel as a public database.

Reproducibility has four distinct layers:

1. public code/build reproducibility;
2. official-source reproduction after reacquiring source bytes and validating their registered identity;
3. exact Observatory candidate reproduction on a pinned Git commit;
4. post-review exact rehydration before promotion.

These are separate claims and must remain separate.

## Tier A — public code and web-build reproducibility

A clean public checkout must execute:

```bash
python -m pip install -e '.[dev]'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src pytest -q
python -m compileall -q src scripts
ruff check src tests scripts
mypy src
```

The rights-safe web surface is lockfile-reproducible:

```bash
cd apps/web
npm ci --no-audit --no-fund
npm run lint
DATA_MODE=derived_only NEXT_TELEMETRY_DISABLED=1 npm run build
```

Permanent CI additionally starts the non-Pages production server and smoke-tests all public routes. Rendered browser/accessibility QA and native macOS Safari QA are separate executable gates. Browser evidence, exact workflow identities, and dated QA records remain distinct from scientific-source reproduction.

## Tier B — official-source evidence reproduction

### RPS published aggregate source

The current RPS path uses the authorized published aggregate Generative AI Adoption Tracker distribution through FRED/ALFRED. `scripts/prepare_rps_refresh_candidate.py` retrieves the registered source inventory into a private or external candidate workspace. The refresh layer validates:

- the 137-series provider release inventory;
- the 131-series Observatory registry scope;
- the six intentionally excluded national constructs;
- canonical series identities and definitions;
- quarterly observations and percentage-domain validity;
- the no-unrestricted-bulk-redistribution boundary;
- a stable scientific `content_sha256` that excludes query-time retrieval-envelope fields.

The current reviewed scientific state contains 962 observations in the registered 131-series history. The common A/H/S subgroup analytical window is Q4 2024–Q2 2026: seven quarters and 882 subgroup cells.

The source snapshot and complete historical subgroup input objects remain private release-candidate material. They are hash-bound to the candidate and are never copied into the promoted public release.

### CPS composition

Official CPS Basic Monthly public-use files are reacquired from the Census source path and verified against their committed manifests. The validated Q2 2025 and Q2 2026 composition packages are under:

- `data/derived/composition/cps-q2-2025/`;
- `data/derived/composition/cps-q2-2026/`.

The current contract preserves:

- worker-share weights for adoption composition;
- actual-main-job-hour shares for assisted-hours and reported-savings composition;
- usual hours as a labeled sensitivity;
- explicit support/coverage gates;
- no design-based interval claim for custom pooled composition vectors without an approved covariance method.

Q4 2025 remains explicitly unavailable because October 2025 CPS was not collected; no two-month substitute is used.

### OEWS robustness

Official May 2025 OEWS staffing data provide an independent establishment-side occupation-composition robustness source. The public evidence is under:

- `data/derived/composition/oews-may-2025/`;
- `data/derived/composition/oews-may-2025-cross-vintage/`;
- the current OEWS/RPS adoption robustness package referenced by the Observatory baseline contract.

OEWS and CPS population differences remain explicit. They are not averaged into a synthetic composition measure.

### BTOS triangulation

The current Observatory baseline includes the preregistered Q2 2026 BTOS–RPS industry triangulation. Reproduction preserves the cross-construct boundary: BTOS employer-business AI use and RPS worker GenAI adoption have different units, denominators, technology scope, and reference periods. The result is descriptive sector concordance, not an identity-line gap or causal estimate.

## Tier C — exact Observatory candidate reproduction

The complete Release 1 candidate is composed from one RPS source vintage plus repository-bound CPS/OEWS/BTOS evidence.

The canonical sequence is:

```bash
PYTHONPATH=src python scripts/prepare_rps_refresh_candidate.py \
  --output-dir <private-rps-refresh>

PYTHONPATH=src python scripts/prepare_rps_observatory_candidate.py \
  --source-snapshot <private-rps-refresh>/rps_source_snapshot.json \
  --output-dir <private-rps-component> \
  --release-id <rps-component-id>

PYTHONPATH=src python scripts/prepare_observatory_v1_candidate.py \
  --rps-candidate-root <private-rps-component> \
  --output-dir <private-global-candidate> \
  --release-id <global-release-id>

PYTHONPATH=src python scripts/observatory_release.py stage \
  --candidate-manifest <private-global-candidate>/release.json \
  --candidate-root <private-global-candidate> \
  --staging-dir <immutable-stage>
```

Candidate construction is bound to a clean Git HEAD. The RPS component cryptographically binds the exact governed source files that present longitudinal/source claims. Global composition revalidates those claim-surface hashes and requires every repository artifact that depends on RPS to match the candidate RPS vintage through `data/registry/observatory_v1_rps_repository_bindings.json`.

The release manifest binds every source object and public artifact by SHA-256. Staging additionally binds the candidate manifest bytes and canonical digest, release diff, review package, release-registry predecessor state, and publication gate into one portable `stage_id`.

A rights-safe review package contains the sanitized candidate manifest, candidate artifacts, stage records, and an uncompleted attestation template. It contains no private `inputs/`, source snapshot, or source `local_path` fields.

## Tier D — trusted post-review exact rehydration

Human review is performed against the exact candidate-review package. Promotion cannot rely solely on that earlier build. Before canonical promotion, `scripts/rehydrate_observatory_v1_candidate.py`:

1. requires a clean checkout of the exact reviewed candidate commit;
2. requires the release registry to remain at the predecessor state recorded by the reviewed stage;
3. re-fetches the authorized RPS source;
4. requires the fresh scientific source content hash to equal the reviewed RPS source vintage;
5. rebuilds the RPS component, claim-surface bindings, global candidate, and stage;
6. requires byte-identical private candidate-manifest identity and identical sanitized manifest;
7. requires the rehydrated stage manifest, release diff, review package, and publication gate to equal the reviewed records exactly;
8. emits only a rights-safe `rehydration_identity.json` for review/promotion binding.

Any scientific source revision, repository evidence change, claim-surface change, registry advance, artifact drift, or stage drift fails closed and requires a new candidate review.

The promotion workflow is deliberately two-phase. A first `rehydrate` run produces the deterministic rehydration identity. A later `promote` run requires the human attestation to contain that identity file's SHA-256, repeats exact rehydration, verifies exact-commit CI evidence through the release engine, promotes the immutable release, and writes the rehydration trace into the release record.

The low-level release engine cannot update the canonical release registry/release tree without the internal exact-rehydration capability supplied by `scripts/promote_rehydrated_observatory_v1.py`.

## Public deployment identity

Promotion produces one release-only authorization commit. `scripts/validate_observatory_publication_commit.py` requires:

- commit subject `Authorize Observatory release <release-id>`;
- the commit parent to be the exact human-reviewed candidate commit;
- changed paths to be limited to `data/registry/observatory_release_registry.json` and `data/releases/<release-id>/...`;
- valid release-manifest, review-record, rehydration-identity, and artifact checksums;
- explicit exact-rehydration traceability.

GitHub Pages builds may run on ordinary changes for QA, but deployment and the live deployment audit run only for this validated authorization commit. Thus engineering changes on `main` do not silently replace the public Observatory release.

## Source identity and revision discipline

A research/release freeze is identified by more than a filename. It records, as applicable:

- Git commit SHA;
- scientific source-vintage identities;
- source-object checksums;
- registry/crosswalk versions;
- generated-artifact checksums;
- governed claim-surface checksums;
- candidate manifest SHA-256 and canonical digest;
- stage ID and release diff;
- exact CI run identities;
- deterministic rehydration identity;
- reviewer and reviewed timestamp;
- promoted release-manifest identity;
- authorization/deployment commit.

A source revision, registry/crosswalk revision, methodology change, governed public-file change, or repository evidence change triggers regeneration and explicit review. Analytical history is retained instead of silently overwritten.

## Rights boundary

A clean public checkout contains no tracked path under `data/audit/private/`. Private RPS source-input bytes remain outside the promoted release. The bounded public RPS artifact contains only the contracted national history and latest industry/occupation A/H/S presentation views. It does not create an unrestricted historical subgroup database, public source mirror, bulk download product, or generic source query API.

The current permission record is `docs/source-rights/RPS_SOURCE_DECISION.md`. Its evidence basis is a project-owner attestation that source-owner permission was obtained for the published aggregate project use described there. The underlying correspondence/agreement is not retained in the public repository and was not independently inspected as part of the code change; the project does not infer broader legal terms from that attestation.

## Historical private fixture

The earlier five-quarter, 630-row private RPS fixture and its frozen hash remain part of repository history and historical validation records. They are no longer the controlling Release 1 empirical source path. Current Release 1 evidence is built from the authorized live published-aggregate source and the seven-quarter common A/H/S window described above.
