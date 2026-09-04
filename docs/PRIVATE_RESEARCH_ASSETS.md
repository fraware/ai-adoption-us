# Data intentionally excluded from the public repository

Some source material used for research validation and release preparation is intentionally absent from this public repository. This is a source-use and redistribution decision, not a missing-data accident.

## RPS source material

The project has used two kinds of non-public RPS material during its development and validation:

1. source files acquired during preparation of the current published-aggregate release; and
2. an earlier five-quarter subgroup audit fixture used for private validation.

Neither is distributed as a public source-data package.

The public repository instead contains the source-series metadata, acquisition and analysis code, versioned derived results, and the bounded RPS observations covered by the project's documented publication scope.

## Historical five-quarter audit fixture

The earlier private audit fixture is expected, when used, at:

```text
data/audit/private/rps_subgroup_5q_audit.json
```

Its recorded identity is stored in `data/registry/private_fixture_freeze.json`:

- 630 observations;
- 20 industries;
- 22 occupations;
- 3 measures (`A`, `H`, `S`);
- 5 quarters, Q2 2025 through Q2 2026;
- SHA-256 `bdeffa95911a94cb60f904c51efc48f7ce4d1bf1eaaec490f5c4bfacd20d4fba`.

This fixture is historical validation material. It is not the controlling empirical source for Release 1, which uses the authorized published-aggregate source history and a seven-quarter common analysis window.

## Reproducing the historical fixture analysis

A researcher who is independently authorized to possess the exact historical fixture can verify it by:

1. placing it at the path above;
2. checking its SHA-256 against `data/registry/private_fixture_freeze.json`;
3. running the tests that require the private fixture;
4. regenerating the historical longitudinal artifacts with `scripts/build_longitudinal.py`;
5. comparing the resulting artifacts with the corresponding recorded historical outputs.

This procedure verifies the previously recorded fixture. It does not authorize obtaining or redistributing the underlying source data.

## Current source-dependent reproduction

Release 1 reproduction does not depend on distributing the historical private fixture. Current RPS analyses are reconstructed by acquiring the registered published aggregate series through the official source interface in a private or temporary workspace.

The acquisition and release-preparation code records source identity and generates the public observations and derived outputs that are eligible for publication. Source-input files remain outside the public release when the documented use boundary does not permit redistribution.

See [REPRODUCIBILITY.md](REPRODUCIBILITY.md) for the current workflow.

## Public material available for inspection

The public repository includes:

- the RPS series registry and source metadata;
- source-use documentation;
- acquisition and validation code;
- longitudinal analysis code;
- CPS, OEWS, and BTOS methodology and derived evidence;
- public RPS observations included in the released product;
- versioned derived diagnostics;
- checksums and release metadata needed to identify the published analytical version.

This provides transparency about the method and published results without turning the repository into an unauthorized mirror of third-party source data.

## General rule

Do not commit credentials, respondent-level records, private audit files, or third-party source files whose redistribution is outside the documented publication scope.

If a new source is added, its storage and publication conditions should be documented explicitly before source material is placed in the public repository.
