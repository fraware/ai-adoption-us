# RPS private-vintage storage and backend conformance contract

Status: **D-G1 package/integrity, recovery conformance, and exact configuration-binding software implemented on this branch; production durable backend still pending**

Date: 2026-09-03

## Purpose

A production longitudinal observatory must be able to prove which exact source bytes were retrieved, preserve a changed source vintage without silently re-fetching mutable upstream data, recover the same immutable package later, and demonstrate that the recovery evidence refers to the same reviewed storage configuration that governed the write.

The repository therefore separates four questions:

1. **What is an immutable private RPS vintage?** The package codec and store define its bytes, namespace, rights metadata, comparison binding, and create-only semantics.
2. **What backend configuration was reviewed?** A strict private configuration attestation records the storage-control claims needed for D-G1 and has its exact file SHA-256 computed.
3. **Can that configured backend return the same package later?** The two-phase conformance protocol writes a challenge and independently reads back, recovers, and verifies the exact event while binding both phases to the exact configuration-attestation SHA-256.
4. **Are the infrastructure claims in the attestation true?** This remains an external operational fact. Repository software can validate and bind the attestation; it cannot prove ownership, access control, physical durability, or retention merely because filesystem I/O succeeds.

The fourth question remains unresolved in the current production environment.

## Current D-G1 state

`RPS live validation` run `33687737639` succeeded on merged `main`, establishing successful live retrieval and the configured FRED credential path for that execution. Its retained review artifact records 137 provider series, 131 observatory series, six intentional exclusions, 962 observations, scientific content SHA-256 `fe8bffa7cacd029cc23e2ba7e310d925e8c05322f6d53bd89e8234f02e825b73`, and exact source-snapshot SHA-256 `66b3ffbaebf43c3c8434556eec9329a232d8f17483ba3a613e6b00d214af3f74`.

That run records `archive_contract_rehearsed=true` and `archive_persisted_durably=false`. It therefore establishes source/package behavior without establishing durable storage.

Global Observatory v1 composition software is merged through PR #57. Activation evidence is merged through PR #58, with two of four activation gates recorded as passed. The vendor-neutral backend recovery harness is merged through PR #59 at `57e8483987fc59190abc05f2f2878e85c4e7be83`.

This branch adds exact configuration-attestation binding. It does not configure storage, mutate the two pending gates, activate the weekly schedule, stage a global release, or promote a release.

## Trust and rights boundary

A private vintage contains exact `rps_source_snapshot.json` bytes, including authorized published aggregate source observations. When a predecessor is supplied it may also contain `rps_refresh_diff.json` with old/new aggregate values.

Accordingly:

- storage scope is `private`;
- `public_archive = false`;
- exact snapshots and detailed diffs must never be committed to the public repository;
- they must never be uploaded as ordinary public-repository Actions artifacts;
- repository-local private material is permitted only beneath ignored `data/audit/private/`;
- external archive roots must be operator-controlled private storage;
- archival does not widen source-owner permission or authorize public bulk redistribution.

The backend attestation and conformance evidence contain no source observation bytes, but they can contain operational identifiers. They therefore carry `public_evidence_approved=false` and are review material, not automatically publishable artifacts.

## Immutable private-vintage package

The package namespace is:

```text
<backend-root>/
  <source-id>/
    <exact-source-snapshot-sha256>/
      private_vintage_manifest.json
      rps_source_snapshot.json
      rps_refresh_diff.json        # when a previous snapshot was supplied
```

`archive_event_id` and `source_snapshot_sha256` identify the exact acquisition-file bytes. `source_content_sha256` separately identifies scientific content while excluding query-time transport-envelope variation. The event directory name, manifest event ID, and exact source-file SHA-256 must agree.

The store uses create-only event semantics. A stale or competing lock fails closed; corrupt existing packages are rejected; a package cannot be rebound to another predecessor; and event files are never updated in place. Local POSIX storage is hardened to owner-only permissions and fails if those permissions cannot be applied.

## Private backend configuration attestation

`src/genai_at_work/private_backend_config.py` defines a strict v1 attestation consumed by the conformance protocol. The attestation is a private JSON document, not a credential file and not a self-proving infrastructure certificate.

Its exact schema records:

- a logical `backend_id`;
- a non-secret path-like `configuration_ref`;
- `environment_scope = production_rps_refresh`;
- the supported storage interface (`mounted_filesystem` or `object_store_mount`);
- explicit assertions that the backend is operator-controlled, private-access-only, non-ephemeral, persistent beyond one execution, and approved for the recorded RPS source-storage rights;
- the canonical RPS source-rights decision reference;
- separate non-secret review references for access control, durability, and retention;
- an explicit timezone-bearing review timestamp;
- `credentials_embedded=false`;
- `public_evidence_approved=false`.

Unknown fields fail validation. Review/reference fields accept only path-like identifiers; URL/query/credential-style syntax is rejected. The loader rejects symbolic links, validates the JSON, and returns SHA-256 of the exact attestation file bytes.

These checks establish a disciplined evidence format. They do not establish that an operator's assertions are true. Gate 3 still requires review of the real infrastructure represented by the attestation.

## Two-phase backend conformance protocol

`src/genai_at_work/private_vintage_backend.py` and `scripts/rehearse_rps_private_backend.py` implement the recovery protocol.

### Phase 1: write challenge

The operator supplies the source snapshot, backend root, and the exact private configuration-attestation file. Backend ID and configuration reference are derived from that attestation; the CLI no longer accepts them as free-form command-line assertions.

The write challenge contains:

- backend ID;
- configuration reference;
- exact `configuration_evidence_sha256`;
- backend namespace;
- source/event identity;
- scientific content and exact snapshot SHA-256 identities;
- predecessor identity when applicable;
- canonical package digest;
- exact writer Git commit;
- private/nonpublic package flags;
- `source_bytes_in_evidence=false`;
- `public_evidence_approved=false`;
- `activation_gates_updated=false`;
- `durability_established_by_software_alone=false`.

The challenge has an exact v1 field inventory. Unknown fields, malformed identities, widened publication claims, source-byte claims, activation claims, and durability claims fail closed.

Example:

```bash
PYTHONPATH=src python scripts/rehearse_rps_private_backend.py write \
  --source-snapshot /private/rps-refresh/rps_source_snapshot.json \
  --backend-root /mounted/private-rps-vault \
  --configuration-evidence /private/review/rps-backend-configuration.json \
  --challenge-out /private/review/backend-write-challenge.json
```

For a later source state, `--previous-snapshot` binds the new event to an exact predecessor.

### Phase 2: independent read-back verification

The verifier must supply the same exact configuration-attestation file. Before reading the archived package, verification recomputes the attestation SHA-256 and requires all three configuration identities to agree with the write challenge:

- backend ID;
- configuration reference;
- configuration file SHA-256.

The verifier then validates the backend package, archived writer commit, scientific identity, exact source identity, predecessor binding, and package digest. It copies the package into a fresh recovery namespace and verifies the recovered package again. Verification evidence is bound to the verifier's clean Git commit.

Example:

```bash
PYTHONPATH=src python scripts/rehearse_rps_private_backend.py verify \
  --challenge /private/review/backend-write-challenge.json \
  --backend-root /mounted/private-rps-vault \
  --configuration-evidence /private/review/rps-backend-configuration.json \
  --evidence-out /private/review/backend-readback-evidence.json
```

The strongest operational rehearsal runs `verify` in a separate execution after the write, reacquiring the backend through the normal production path. Local same-process success is useful software testing but is insufficient evidence of production durability.

## Repository-local privacy boundary

The rehearsal CLI rejects repository-local backend roots, source snapshots, predecessor snapshots, configuration attestations, challenges, and verification outputs outside `data/audit/private/`. External paths remain permitted so an operator-controlled private mount can be used.

This prevents source-byte-free review evidence from being mistaken for automatically public repository content merely because it contains no source observations.

## Activation evidence contract

The source-check policy contains four activation gates:

1. successful live validation — **passed**;
2. FRED credential verified in the execution environment — **passed**;
3. operator-controlled durable private-vintage backend configured — **pending**;
4. independent private-backend write/read/verify rehearsal passed — **pending**.

Activation status is derived only from validated evidence recorded in `data/registry/rps_refresh_policy.json`. Every activation row has an exact allowed field inventory; unsupported extra claims fail closed.

When Gate 3 is eventually recorded as passed, it must include:

- backend ID;
- configuration-evidence reference;
- exact configuration-evidence SHA-256;
- verification date.

When Gate 4 is eventually recorded as passed, it must include:

- rehearsal ID;
- verification-evidence reference;
- exact verification-evidence SHA-256;
- backend ID;
- configuration-evidence reference;
- exact configuration-evidence SHA-256;
- verification date.

Gate 4 validation requires its backend ID, configuration reference, and configuration SHA-256 to match Gate 3 exactly. This prevents a recovery rehearsal from being rebound after the fact to a different backend attestation.

Neither the conformance library nor its CLI edits the policy or marks gates passed. A separate reviewed repository change is required after the infrastructure and recovery evidence have actually been inspected.

## Release reconstruction

Once an exact RPS vintage is durably retained and independently verified, downstream candidate construction consumes the archived snapshot directly:

```bash
PYTHONPATH=src python scripts/prepare_rps_observatory_candidate.py \
  --source-snapshot <private-package>/rps_source_snapshot.json \
  --output-dir <private-rps-candidate-dir> \
  --release-id <rps-candidate-id>
```

The complete Observatory v1 composer can then combine that validated private RPS component with pinned repository evidence. Candidate construction remains non-promoting until exact-candidate scientific, editorial, rights, and CI review are complete.

## What remains unresolved

Repository software can define, validate, and cryptographically bind the evidence chain. It cannot create durable private infrastructure by assertion. D-G1 still requires:

1. configure a real operator-controlled durable private storage location reachable from the production refresh environment;
2. create and independently review the private v1 configuration attestation against that real backend, including its access-control, durability, retention, and source-rights assertions;
3. execute the two-phase write/read/verify protocol against that backend, preferably across separate executions;
4. review the exact configuration SHA-256 and recovery-evidence SHA-256, then record Gates 3 and 4 through a separate reviewed policy change;
5. activate the pinned Wednesday 18:00 UTC weekly source check through a separate reviewed repository change;
6. create the first complete global candidate from the exact durably archived RPS vintage and bind all candidate reviews to exact hashes;
7. rehearse a subsequent new-wave or source-revision transition against a frozen predecessor.

Until items 1–4 are complete, periodic checking must remain disabled. Until exact-candidate review and explicit release-engine promotion are complete, no global release should be claimed as staged or public.
