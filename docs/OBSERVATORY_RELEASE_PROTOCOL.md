# Versioned observatory release protocol

Status: **mandatory publication-governance protocol for future observatory waves and source revisions**.

This protocol governs issue #11. It turns a source-specific research build into a release candidate whose source vintages, rights, definitions, derived artifacts, diagnostics, and public claims can be compared with the currently frozen observatory release before publication.

It does not authorize any data source. A candidate with unresolved rights is blocked.

## Release object

The unit of change is a **release candidate**, not a source file.

A candidate manifest contains four distinct evidence layers:

1. **sources** — provider/dataset, source vintage, retrieval time, reference periods, cryptographic identity, instrument/definition/taxonomy versions, coverage, revision status, and rights contract;
2. **derived artifacts** — deterministic outputs with SHA-256, evidence class, and source dependencies;
3. **diagnostics** — stability, influence, regression-contract, and suppression/coverage checks;
4. **public claims** — stable claim IDs, publication surfaces, artifact dependencies, value/truth digests, evidence class, and interpretation boundary.

Those layers are diffed independently. A source revision can leave an artifact unchanged. An artifact can change while a claim remains substantively unchanged. A claim can also change because its interpretation or evidence class changed even if a file name did not.

## Candidate package layout

The candidate package is prepared by the relevant source-specific pipeline before release staging. The release engine does not fetch data and does not invent a generic data builder.

A package contains:

```text
candidate/
  release.json
  inputs/
    ... locally staged source objects ...
  artifacts/
    ... deterministic rights-safe derived outputs ...
```

Every source object and artifact is identified by file size and SHA-256. The manifest's `build` section must declare:

- a stable builder ID;
- the builder commit/version;
- `deterministic: true`;
- an exact mapping from every source object to its verified hash;
- an exact mapping from every derived artifact to its verified hash.

The release engine verifies those mappings against the actual candidate files. Missing inputs, missing outputs, size mismatches, checksum mismatches, path traversal, or incomplete build coverage stop staging.

The build-provenance record is a contract that the source-specific pipeline has regenerated the candidate. Source-specific builder tests remain responsible for proving the underlying transformation itself; the release engine is the cross-source publication gate.

## Required source contract

Every source entry records:

- `source_id`;
- provider and dataset/product;
- `source_vintage_id`;
- retrieval time;
- reference periods;
- `revision_status` (`unchanged`, `new_wave`, `revision`, or `mixed`);
- instrument version;
- definition ID;
- taxonomy/crosswalk versions;
- local candidate input objects with locator, size, and SHA-256;
- coverage status plus required/observed units;
- rights status and storage/publication/redistribution scopes.

Publication fails closed when:

- source rights are unresolved/denied or publication scope is `none`;
- an existing source's rights contract changes;
- an existing source's instrument, definition, or taxonomy changes;
- a previously frozen source, period, or source object disappears;
- coverage fails;
- source bytes changed while `revision_status` still says `unchanged`.

A definition/taxonomy change is not accepted merely because a reviewer approves the release. It requires a separate measurement-specification decision first.

## Required diagnostics

Every candidate must carry at least one explicit diagnostic in each class:

- `stability`;
- `influence`;
- `regression_contract`;
- `suppression_coverage`.

Each diagnostic has a stable ID, pass/fail status, and value digest. Any failed diagnostic blocks publication.

Source-specific pipelines may add richer diagnostics, but they cannot omit these classes from a release package.

## Claim traceability

Every material changing claim in the candidate has:

- stable `claim_id`;
- publication `surfaces`;
- dependent `artifact_ids`;
- value/truth digest;
- explicit `truth_state`;
- evidence class 1–5;
- interpretation boundary.

A claim is marked affected when:

- the claim itself is added, removed, or modified; or
- any artifact it depends on changed.

This is deliberately conservative. A human reviewer may conclude that wording does not need to change, but the engine may not silently infer that from an unchanged sentence.

## Stage command

Use a fresh staging directory:

```bash
PYTHONPATH=src python scripts/observatory_release.py stage \
  --candidate-manifest /private/release-candidate/release.json \
  --candidate-root /private/release-candidate \
  --staging-dir /private/release-staging/release-2026-q3
```

The public defaults are:

- registry: `data/registry/observatory_release_registry.json`;
- immutable release history: `data/releases/`.

The stage writes:

- `stage_manifest.json` — binds current registry identity, candidate manifest hash, canonical candidate digest, release-diff digest, and gate state;
- `release_diff.json` — source/artifact/diagnostic/claim changes and contract failures;
- `review_package.json` — changed sources/diagnostics and affected public claims/surfaces;
- `publication_gate.json` — fail-closed status.

Gate states include:

- `BLOCKED_RIGHTS`;
- `BLOCKED_DEFINITION_CHANGE`;
- `BLOCKED_MISSING_SERIES`;
- `BLOCKED_COVERAGE`;
- `BLOCKED_DIAGNOSTICS`;
- `BLOCKED_REVISION_STATUS`;
- `BLOCKED_CONTRACT`;
- `BLOCKED_REVIEW_REQUIRED`;
- `REPRODUCED_CURRENT_RELEASE`.

A new, valid wave normally reaches `BLOCKED_REVIEW_REQUIRED`. That is intentional: data changing without a contract violation still require human scientific/editorial review before publication.

## Review attestation

Promotion requires an attestation bound to the exact staged release. It records:

```json
{
  "stage_id": "<stage fingerprint>",
  "release_id": "release-2026-q3",
  "candidate_manifest_sha256": "<exact manifest hash>",
  "reviewer": "<identity>",
  "reviewed_at": "2026-09-01T15:00:00Z",
  "scientific_reviewed": true,
  "editorial_reviewed": true,
  "source_rights_reviewed": true,
  "ci_passed": true,
  "candidate_commit": "<validated commit>",
  "ci_run_ids": [123456],
  "artifact_sha256": {
    "artifact-id": "<exact candidate artifact hash>"
  },
  "reviewed_source_ids": ["<every changed source>"],
  "reviewed_diagnostic_ids": ["<every changed diagnostic>"],
  "reviewed_claim_ids": ["<every affected claim>"]
}
```

The attestation must exactly cover the changed source IDs, changed diagnostic IDs, affected claim IDs, and all candidate artifact hashes. Scientific review, editorial review, source-rights review, and candidate CI evidence are separate required assertions.

CI evidence in the attestation is an audit record; the normal repository PR/main workflows remain the authoritative executable CI system.

## Promote command

```bash
PYTHONPATH=src python scripts/observatory_release.py promote \
  --candidate-manifest /private/release-candidate/release.json \
  --candidate-root /private/release-candidate \
  --staging-dir /private/release-staging/release-2026-q3 \
  --attestation /private/release-staging/release-2026-q3/review-attestation.json
```

Promotion re-verifies:

- current release registry identity;
- candidate manifest checksum and canonical digest;
- every candidate input/output checksum;
- release diff;
- gate status;
- stage fingerprint;
- attestation scope and artifact hashes.

It then creates a new immutable directory under `data/releases/<release_id>/` and advances the registry only after the reviewed release has been written successfully.

An existing release ID/directory is never overwritten.

## Source-byte boundary

The observatory release archive **never copies source input bytes**.

Local `inputs/` exist only so staging can verify the exact source bytes consumed by the source-specific pipeline. Public release manifests remove local input paths and retain only provenance metadata such as locator, size, and cryptographic checksum.

Only declared derived artifacts are copied into the immutable release directory.

This protects the release engine from becoming an accidental redistribution path. A future decision to redistribute source data must be implemented as a separate rights-reviewed export surface, not inferred from this pipeline.

## New waves versus revisions

A **new wave** extends reference periods/source objects under unchanged measurement and rights contracts.

A **revision** changes previously frozen source bytes under the same measurement and rights contracts and must say so explicitly in `revision_status`.

A **definition change** changes the measurement object and is blocked from this normal release path until separately specified and approved.

A **rights change** is likewise blocked until the source-rights decision is updated.

Previously frozen periods or source objects cannot disappear silently.

## First release

`data/registry/observatory_release_registry.json` intentionally starts with no promoted release. This does not retroactively label the current engineering/research repository snapshot as a public observatory release.

The first actual observatory release must be staged as a `baseline`, explicitly reviewed, pass CI, and then be promoted through this same mechanism.

## Synthetic validation

Public tests create a fully synthetic baseline package, stage it, generate an exact review attestation, promote it into a temporary immutable release history, and then stage a synthetic new wave against that frozen baseline.

The tests also prove fail-closed behavior for unresolved rights, failed coverage, definition drift, missing historical periods/source objects, incomplete build hashes, and incomplete review coverage.

No synthetic release is promoted into the repository's real `data/releases/` tree.
