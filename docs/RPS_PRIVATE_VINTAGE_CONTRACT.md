# RPS private-vintage storage and backend conformance contract

Status: **D-G1 package/integrity and backend-conformance software implemented; production durable backend still pending**

Date: 2026-09-03

## Purpose

A production longitudinal observatory must be able to prove which exact source bytes were retrieved, preserve a changed source vintage without silently re-fetching mutable upstream data, and later recover the same immutable package before release construction.

The repository therefore separates three questions that must not be conflated:

1. **What is an immutable private RPS vintage?** The package codec and store define its exact bytes, namespace, rights metadata, comparison binding, and create-only semantics.
2. **Can a configured backend return the same package later?** The two-phase backend conformance protocol writes a challenge and independently reads back, recovers, and verifies the exact event.
3. **Is that backend genuinely durable, private, operator-controlled, and correctly retained?** This is an infrastructure fact. It requires separately reviewed configuration/access-control evidence and cannot be inferred from successful filesystem I/O alone.

The third question remains unresolved in the current production environment.

## Current D-G1 state

The live provider path is already evidenced. `RPS live validation` run `33687737639` succeeded on merged `main`, establishing both successful live retrieval and the configured FRED credential path for that execution. Its rights-safe artifact records 137 provider series, 131 observatory series, six intentional exclusions, 962 observations, and an exact source-snapshot SHA-256 of `66b3ffbaebf43c3c8434556eec9329a232d8f17483ba3a613e6b00d214af3f74`.

That run also records `archive_contract_rehearsed=true` and `archive_persisted_durably=false`. It therefore validates package semantics while explicitly failing to establish durable storage.

The complete Observatory v1 global-baseline composition software is also merged on `main` through PR #57 at commit `28e2141869c35f92faf20d796f3b2b2f003e4c3a`. Activation evidence is merged through PR #58 at commit `6aa39dfa3ef9630d87a610e01d6b8376a3098b65`: two of four source-check activation gates are recorded as passed, while durable backend configuration and backend write/read/verify remain pending.

No first global release has been staged or promoted by those changes.

## Trust and rights boundary

A private vintage contains the exact `rps_source_snapshot.json`, including authorized published aggregate source observations. When a predecessor is supplied it may also contain a detailed `rps_refresh_diff.json` with old/new aggregate values.

Accordingly:

- storage scope is `private`;
- `public_archive = false`;
- exact source snapshots and detailed diffs must never be committed to the public repository;
- they must never be uploaded as ordinary public-repository Actions artifacts;
- repository-local development archives are permitted only beneath ignored `data/audit/private/`;
- external archive roots must be operator-controlled private storage;
- archival does not widen source-owner permission or authorize public bulk redistribution.

The operator commands enforce the repository-local path boundary. A production backend must enforce equivalent privacy outside the repository through its own access controls.

## Two identities: retrieval event and scientific content

RPS/FRED retrievals include transport/realtime-envelope fields that may change between acquisitions even when stable scientific observations are unchanged. The archive retains two different identities:

1. `archive_event_id` / `source_snapshot_sha256`: SHA-256 of the exact snapshot-file bytes.
2. `source_content_sha256`: the scientific content digest that excludes query-time transport-envelope variation.

Two retrieval events may therefore have different exact file identities while sharing one scientific content identity. A stable-definition or observation change advances the scientific identity.

This distinction is mandatory for revision classification and release reproducibility.

## Immutable package namespace

The package layout is:

```text
<backend-root>/
  <source-id>/
    <exact-source-snapshot-sha256>/
      private_vintage_manifest.json
      rps_source_snapshot.json
      rps_refresh_diff.json        # when a previous snapshot was supplied
```

The event directory name, manifest `archive_event_id`, and `source_snapshot_sha256` must agree. There is no mutable `latest` pointer in the package contract. Any later pointer/index mechanism requires separate review because predecessor selection is part of provenance.

## Manifest and exact-byte contract

`private_vintage_manifest.json` records the source/event identities, exact source size and SHA-256, scientific content SHA-256, retrieval timestamp, provider release ID, inventory counts, rights decision reference, private storage scope, builder commit, predecessor binding, revision classification, exact hashes/sizes of archived files, `immutable=true`, and `public_archive=false`.

The source snapshot is copied byte-for-byte rather than parsed and reserialized. Installation verifies source size and SHA-256. Later package verification recomputes both exact-byte and scientific-content identities.

When a previous snapshot is supplied, the private comparison diff is bound to the exact predecessor snapshot SHA-256, prior scientific identity, current scientific identity, revision classification, change counts, and detailed changes. An existing event cannot later be rebound to a different predecessor.

## Create-only and concurrency semantics

The operator-facing store acquires a per-event lock using exclusive creation before installation. A competing or stale lock fails closed and requires operator inspection; it is never silently deleted.

Once an event exists:

- byte-identical replay with the same predecessor binding is idempotent;
- corrupt packages are rejected and never overwritten;
- alternate predecessor bindings are rejected;
- event files are never updated in place.

On ordinary POSIX filesystems the store also applies owner-only permissions (`0700` directories and `0600` files) and fails if privacy hardening cannot be applied. Remote backends require equivalent authorization through their native controls.

## Two-phase backend conformance protocol

`src/genai_at_work/private_vintage_backend.py` and `scripts/rehearse_rps_private_backend.py` add a vendor-neutral recovery protocol on top of the immutable package store.

It is deliberately two-phase so a later process or execution can prove read-back independently from the write transaction.

### Phase 1: write challenge

The `write` command stores the exact source package and emits source-byte-free review evidence. The challenge contains only identities and control metadata:

- backend ID and separately reviewable configuration-evidence reference;
- exact backend namespace;
- source ID and archive event ID;
- scientific and exact snapshot SHA-256 identities;
- predecessor snapshot identity when present;
- canonical package digest over the manifest and archived files;
- exact writer Git commit;
- private/nonpublic package flags;
- explicit `source_bytes_in_evidence=false`;
- explicit `public_evidence_approved=false`;
- explicit `activation_gates_updated=false`;
- explicit `durability_established_by_software_alone=false`.

The challenge has an exact v1 field inventory. Unknown fields, malformed identities, unsafe IDs, widened publication scope, source-byte claims, false activation claims, or false durability claims fail closed.

`public_evidence_approved=false` is deliberate. The challenge excludes source observations, but a backend ID, namespace, or configuration-evidence reference can still be operationally sensitive. Source-byte safety is therefore not treated as public-publication approval.

Example:

```bash
PYTHONPATH=src python scripts/rehearse_rps_private_backend.py write \
  --source-snapshot /private/rps-refresh/rps_source_snapshot.json \
  --backend-root /mounted/private-rps-vault \
  --backend-id private-rps-vault-v1 \
  --configuration-evidence-ref ops/private-rps-vault/configuration-v1 \
  --challenge-out /private/review/backend-write-challenge.json
```

The configuration reference must be a non-secret review identifier. Credentials, signed URLs, access tokens, secret-bearing connection strings, or other credential material must never be encoded in it.

For a later source state, `--previous-snapshot` may bind the event to an exact predecessor.

### Phase 2: independent read-back verification

The `verify` command loads the previously emitted challenge and locates the exact event by source/event identity. It then:

1. verifies the backend package and every archived byte against its manifest;
2. requires the archived writer commit to match the challenge;
3. verifies scientific identity, exact snapshot identity, and predecessor binding;
4. recomputes the canonical package digest;
5. copies the retrieved package into a fresh recovery namespace;
6. verifies the recovered package again;
7. binds the verification evidence to the verifier's clean Git commit.

Example:

```bash
PYTHONPATH=src python scripts/rehearse_rps_private_backend.py verify \
  --challenge /private/review/backend-write-challenge.json \
  --backend-root /mounted/private-rps-vault \
  --evidence-out /private/review/backend-readback-evidence.json
```

The strongest operational rehearsal runs `verify` in a separate process/execution after the write, with the backend remounted or reacquired through the normal production credential path. That separation is operational evidence, not something a local library can manufacture.

## Source-byte-free review evidence

Neither challenge nor verification evidence contains source observations or detailed private diffs. Verification output records cryptographic identities, backend/configuration references, writer/verifier commits, recovery result, private/nonpublic package flags, and explicit control boundaries:

- `source_bytes_in_evidence=false`;
- `public_evidence_approved=false`;
- `activation_gates_updated=false`;
- `durability_established_by_software_alone=false`;
- `requires_independent_backend_configuration_review=true`.

These JSON files are suitable for controlled review because they omit source observation bytes. They are not automatically approved for public distribution: infrastructure identifiers and configuration references must be reviewed separately before any publication decision.

A successful conformance rehearsal proves that the exact challenged package was later recoverable and internally valid at that backend path. It does not prove that the path is durable across infrastructure loss, that its ACLs are correct, that retention is adequate, or that the operator actually controls the underlying service.

## Relationship to the activation gates

The pinned source-check policy contains four activation gates:

1. successful live validation — **passed**;
2. FRED credential verified in the execution environment — **passed**;
3. operator-controlled durable private-vintage backend configured — **pending**;
4. independent private-backend write/read/verify rehearsal passed — **pending**.

This conformance software supplies the mechanism needed to evidence Gate 4 once Gate 3 is genuinely configured. It does not mutate `data/registry/rps_refresh_policy.json` and cannot mark either gate passed automatically.

Gate 3 requires separately reviewable infrastructure evidence describing the actual backend, production reachability, private authorization model, and retention/control boundary. Gate 4 requires a successful challenge/read-back verification against that same reviewed backend identity. Only after both pieces are inspected should a separate reviewed change update activation evidence.

## Release reconstruction

Once an exact vintage is durably retained and verified, downstream candidate construction consumes the archived snapshot directly:

```bash
PYTHONPATH=src python scripts/prepare_rps_observatory_candidate.py \
  --source-snapshot <private-package>/rps_source_snapshot.json \
  --output-dir <private-rps-candidate-dir> \
  --release-id <rps-candidate-id>
```

The complete Observatory v1 composer can then consume that validated private RPS component together with the pinned repository evidence. Candidate construction remains non-promoting until exact-candidate scientific, editorial, rights, and CI review are complete.

## What remains unresolved

Repository software can define and verify the storage contract, but it cannot create an operator's private infrastructure by assertion. D-G1 still requires:

1. configure a real operator-controlled durable private storage location reachable from the production refresh environment;
2. retain separately reviewable configuration/access-control evidence for that backend;
3. execute the two-phase write/read/verify protocol against that backend, preferably across separate executions;
4. review the backend configuration and cryptographic recovery evidence and only then record Gates 3 and 4 as passed;
5. activate the pinned weekly Wednesday 18:00 UTC source check through a separate reviewed repository change;
6. create the first complete global candidate from the exact durably archived RPS vintage and bind all release reviews to its hashes;
7. rehearse a subsequent new-wave or source-revision transition against a frozen predecessor.

Until the first four items are complete, periodic checking must remain disabled. Until exact-candidate review and explicit release-engine promotion are complete, no global release should be claimed as staged or public.
