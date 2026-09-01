# Private research assets and public-repository boundary

This repository is public. The private RPS audit observation fixture must therefore **not** be committed here.

## Required private asset

Path expected by the private research mode:

`data/audit/private/rps_subgroup_5q_audit.json`

Current frozen fixture properties are machine-registered in `data/registry/private_fixture_freeze.json`. The baseline freeze has:

- rows: **630**;
- industries: 20;
- occupations: 22;
- metrics: 3 (`A`, `H`, `S`);
- quarters: 5 (Q2 2025 through Q2 2026);
- SHA-256: `bdeffa95911a94cb60f904c51efc48f7ce4d1bf1eaaec490f5c4bfacd20d4fba`.

## Why it is absent

The fixture was assembled for private research/audit use from third-party RPS series. The public release architecture deliberately does not redistribute the raw subgroup observations.

The omission is intentional and must not be “fixed” by copying the private fixture into the public Git repository.

## Recovery of the current freeze

An authorized researcher recovering the existing frozen package should:

1. restore the fixture at the exact path above;
2. verify its SHA-256 against `data/registry/private_fixture_freeze.json`;
3. run the full private test suite;
4. regenerate the four longitudinal derived artifacts with `scripts/build_longitudinal.py`;
5. require byte-for-byte agreement with `data/derived/longitudinal/` before accepting the recovered freeze.

This recovery path is only for reproducing the **same** frozen fixture.

## Revision of the private fixture

A candidate source revision must never overwrite the current fixture first.

Any revised candidate must go through `scripts/private_fixture_revision_gate.py` and the mandatory procedure in `docs/PRIVATE_FIXTURE_REVISION_PROTOCOL.md`. The gate:

- verifies the current fixture against the registered checksum before any mutation;
- preserves the current fixture and current derived freeze in a private archive;
- validates the candidate under the existing scope/rights/definition contract;
- regenerates all four longitudinal artifacts into a separate staging directory;
- produces a private cell-level diff and public-artifact hash diff;
- marks all registered dependent claims for review when derived evidence changes;
- blocks promotion until an attestation is bound to the exact candidate checksum, stage fingerprint, staged artifact hashes, and every affected claim;
- fails closed when rights or construct definitions change or when publication diagnostics fail;
- emits a public validation record without raw private observations only after explicit reviewed promotion.

A new wave is not a fixture revision. New-wave ingestion belongs to the versioned update/release pipeline and must not use the revision gate to bypass the broader measurement and publication review.

## Public substitutes

The public repository contains:

- the full source-series metadata manifest;
- the machine-readable private-freeze identity and contract, without the fixture itself;
- the complete longitudinal analysis implementation;
- the private-fixture revision gate implementation and public tests;
- the longitudinal public-claim inventory;
- rights-safe aggregate derived diagnostics;
- validation checks;
- source provenance and methodology.

These permit inspection of the method, governance process, and published conclusions without redistributing the underlying private audit observations.
