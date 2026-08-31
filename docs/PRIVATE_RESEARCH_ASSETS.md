# Private research assets and public-repository boundary

This repository is public. The private RPS audit observation fixture must therefore **not** be committed here.

## Required private asset

Path expected by the private research mode:

`data/audit/private/rps_subgroup_5q_audit.json`

Last frozen fixture properties:

- rows: **630**;
- industries: 20;
- occupations: 22;
- metrics: 3 (`A`, `H`, `S`);
- quarters: 5 (Q2 2025 through Q2 2026);
- SHA-256: `bdeffa95911a94cb60f904c51efc48f7ce4d1bf1eaaec490f5c4bfacd20d4fba`.

## Why it is absent

The fixture was assembled for private research/audit use from FRED-hosted third-party RPS series. The public release architecture deliberately does not redistribute the raw subgroup observations.

The omission is intentional and must not be “fixed” by copying the private fixture into the public Git repository.

## Recovery procedure

An authorized researcher with access to the private research package should:

1. restore the fixture at the exact path above;
2. verify the SHA-256;
3. run the full private test suite;
4. regenerate the four longitudinal derived artifacts;
5. require byte-for-byte agreement before accepting a result freeze.

If the fixture changes because the underlying source is revised, do not overwrite the old research freeze silently. Create a new dated/versioned fixture, regenerate all diagnostics, and record the changed source vintage.

## Public substitutes

The public repository contains:

- the full source-series metadata manifest;
- the complete longitudinal analysis implementation;
- rights-safe aggregate derived diagnostics;
- validation checks;
- source provenance and methodology.

These permit inspection of the method and published conclusions without redistributing the underlying private audit observations.
