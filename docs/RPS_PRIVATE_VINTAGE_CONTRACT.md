# RPS private-vintage storage contract

Status: **D-G1 storage-format tranche — vendor-neutral private archive contract; D-G1 remains open**

Date: 2026-09-02

## Purpose

A production longitudinal observatory must be able to prove exactly which source bytes were retrieved, compare a later source state with a previously frozen retrieval, and rebuild a reviewed candidate from the same source vintage without silently re-fetching mutable upstream data.

The manual RPS source probe intentionally keeps source bytes transient because this repository is public. That is safe for a compatibility probe, but it is insufficient for a production release history.

This contract defines the missing durable private-vintage **package format and integrity semantics**. It deliberately does not select a storage vendor. The same package may live on an operator-controlled private filesystem, a private mounted object store, or a future backend adapter that preserves the contract below.

## Trust and rights boundary

The archive contains the exact private `rps_source_snapshot.json`, including published aggregate source observations. It may also contain a detailed source comparison diff with old/new aggregate cell values.

Accordingly:

- storage scope is `private`;
- `public_archive = false`;
- the package must never be committed to the public repository;
- the package must never be uploaded as an ordinary public-repository Actions artifact;
- repository-local development archives are permitted only beneath the ignored `data/audit/private/` boundary;
- external archive roots must be operator-controlled private storage;
- archiving does not widen the source-owner permission or authorize public bulk redistribution.

The CLI enforces the repository-local boundary. A future remote backend must enforce equivalent access control outside this repository.

## Two identities: retrieval event versus scientific content

RPS/FRED retrievals contain transport/realtime envelope fields whose values may change across retrieval dates even when the scientific observations and stable definitions are identical.

The archive therefore retains two different SHA-256 identities:

1. `archive_event_id` / `source_snapshot_sha256` — SHA-256 of the **exact snapshot file bytes**. This identifies the acquisition event exactly.
2. `source_content_sha256` — the existing RPS scientific content digest that excludes query-time transport-envelope changes.

This distinction is mandatory.

Two retrievals may legitimately have different `archive_event_id` values while sharing the same `source_content_sha256`. Such a pair is an auditable repeated retrieval of scientifically unchanged content, not a source revision.

A real observation or stable-definition change advances `source_content_sha256`.

## Package namespace

The private archive layout is:

```text
<archive-root>/
  <source-id>/
    <exact-source-snapshot-sha256>/
      private_vintage_manifest.json
      rps_source_snapshot.json
      rps_refresh_diff.json        # present when a previous snapshot was supplied
```

The event directory name is the exact snapshot-file SHA-256. The manifest's `archive_event_id` and `source_snapshot_sha256` must equal that directory name.

The source ID is restricted to a filesystem-safe identifier. Path traversal or alternate namespace construction is rejected.

No mutable `latest` pointer is part of this package contract. Production orchestration must choose the previous vintage explicitly or implement a separately reviewed private index/pointer mechanism. This prevents a mutable pointer from becoming an unexamined part of source identity.

## Manifest contract

`private_vintage_manifest.json` records:

- schema and archive type;
- exact retrieval-event ID;
- source ID;
- scientific content SHA-256;
- exact source-snapshot SHA-256 and byte size;
- retrieval timestamp;
- provider release ID;
- observation count;
- provider/observatory/excluded inventory counts and inventory status;
- rights decision reference and explicit private/nonpublic scope;
- exact builder Git commit;
- comparison binding to a previous exact snapshot when supplied;
- new-wave/revision/mixed/unchanged status and change counts;
- exact hashes and sizes for every archived file;
- `immutable = true` and `public_archive = false`.

The manifest does not claim that a source was published or promoted. It is private source provenance only.

## Exact source-byte preservation

The archive copies `rps_source_snapshot.json` byte-for-byte. It does not parse and reserialize the source snapshot as the archived source object.

After the copy, the writer verifies both file size and SHA-256 against the original before installation. Later verification recomputes the exact file SHA-256 and the scientific content digest from the archived snapshot.

This permits downstream candidate construction to consume the exact archived file:

```bash
PYTHONPATH=src python scripts/prepare_rps_observatory_candidate.py \
  --source-snapshot <private-package>/rps_source_snapshot.json \
  --output-dir <private-candidate-dir> \
  --release-id <candidate-id>
```

A later refresh comparison may likewise use the exact archived snapshot as `--previous-snapshot`.

## Private revision evidence

When `--previous-snapshot` is supplied, the archive calculates the existing RPS source diff and stores `rps_refresh_diff.json` privately.

That diff is bound to:

- the exact prior snapshot SHA-256;
- the prior scientific content SHA-256;
- the current scientific content SHA-256;
- the classified revision state;
- change counts and detailed changed cells/definitions.

The detailed diff is intentionally private because it may reproduce old/new source values. The public/review-safe Actions evidence remains the summarized change counts and cryptographic identities.

An existing archived retrieval event may not later be rebound to a different previous snapshot. Comparison provenance is immutable. A conflicting re-archive request fails closed.

## Create-only and concurrency semantics

The operator-facing store acquires a per-event lock using exclusive file creation (`O_EXCL`) before installing a new package.

This prevents two cooperating writers from concurrently installing the same retrieval event. The lock records the event SHA and process ID for operator diagnosis.

A stale lock is **not** silently deleted. It is treated as evidence of another or interrupted writer and requires explicit inspection before removal.

Once a package exists:

- byte-identical re-archival with the same previous-vintage binding is idempotent;
- a corrupt existing package is rejected and never overwritten;
- a different previous-vintage binding is rejected;
- no file in the event package is updated in place.

The low-level package codec verifies package immutability; the operator-facing `private_vintage_store` adds exclusive locking and comparison-binding enforcement.

## Local filesystem privacy hardening

On ordinary POSIX filesystems, the store attempts to apply owner-only permissions:

- event/source directories: `0700`;
- files: `0600`.

Failure to apply these permissions fails the store operation rather than silently weakening local confidentiality.

This filesystem mode is not a substitute for a remote backend's access-control policy. A cloud/object-store implementation must provide equivalent private authorization and exact-byte retrieval guarantees through its own controls.

## Operator command

Archive a first private retrieval event:

```bash
PYTHONPATH=src python scripts/archive_rps_private_vintage.py \
  --source-snapshot /private/rps-refresh/rps_source_snapshot.json \
  --archive-root /private/rps-vintages
```

Archive a later retrieval and retain exact private comparison evidence:

```bash
PYTHONPATH=src python scripts/archive_rps_private_vintage.py \
  --source-snapshot /private/rps-refresh-next/rps_source_snapshot.json \
  --previous-snapshot /private/rps-vintages/<source>/<prior-event>/rps_source_snapshot.json \
  --archive-root /private/rps-vintages
```

The command requires a clean Git worktree. Its output reports the event ID, scientific content hash, exact snapshot hash, retrieval time, comparison status, previous exact snapshot hash, builder commit, and private storage status.

## What this tranche establishes

The implementation establishes a testable source-vintage storage format with:

- exact-byte preservation;
- separate scientific and retrieval-event identities;
- immutable source/comparison provenance;
- detailed private revision evidence;
- tamper detection;
- create-only event locking;
- idempotent replay under the same provenance binding;
- explicit rights/private-storage metadata;
- storage-vendor-neutral retrieval by ordinary file path.

This is sufficient to define what a future durable backend must preserve.

## What remains unresolved

This tranche does **not** configure a durable remote/private storage service for GitHub-hosted execution. The current repository tooling does not expose such a backend, and selecting one without an explicit access-control/retention decision would move the problem instead of solving it.

Before D-G1 can close, production execution still needs:

1. a real operator-controlled private storage location reachable from the source-refresh execution environment;
2. credentials and access control for that private backend;
3. an explicit retention rule for retrieval events, including treatment of non-promoted probes versus release-referenced vintages;
4. a reviewed mechanism for selecting the prior event without introducing a silent mutable-source fallback;
5. successful live source retrieval and archival;
6. reconstruction of a candidate from the archived exact bytes;
7. complete global observatory baseline composition and reviewed promotion;
8. a subsequent-wave/revision rehearsal against a frozen archived predecessor.

The package contract intentionally precedes the backend choice so those later decisions cannot alter source identity, revision semantics, or public/private boundaries implicitly.
