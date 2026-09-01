# Reproducibility contract

## Scope

The public repository is a **rights-safe reproduction package**. It contains source code, registries, versioned derived diagnostics, CPS/OEWS composition evidence, validation logic, product source, and locked web dependencies. It deliberately excludes the private copyrighted RPS subgroup fixture and does not mirror source datasets whose redistribution is outside the project boundary.

Reproducibility therefore has three distinct layers:

1. public code/build reproducibility;
2. official-source composition reproduction after reacquiring source bytes and verifying them against committed manifests;
3. private RPS empirical reproduction with the authorized private fixture restored separately.

Do not collapse these into a single claim.

## Tier A — public code and artifact reproducibility

A clean public checkout must execute the public Python surface:

```bash
python -m pip install -e '.[dev]'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src pytest -q
python -m compileall -q src scripts
ruff check src tests scripts
mypy src
```

Private-fixture-dependent tests are expected to skip when the RPS fixture is absent. Governance, registry, CPS/OEWS, composition, rights, and public web-release tests must execute.

The rights-safe web surface is lockfile-reproducible:

```bash
cd apps/web
npm ci --no-audit --no-fund
npm run lint
DATA_MODE=derived_only NEXT_TELEMETRY_DISABLED=1 npm run build
```

Permanent release CI also starts the optimized production server and smoke-tests:

- `/`;
- `/blog/after-adoption`;
- `/explore/industries`;
- `/explore/occupations`;
- `/methodology`;
- `/sources`.

Rendered browser/accessibility QA is a separate executable layer using the pinned browser toolchain in `apps/web/package-lock.json`. In the workflow environment it runs the production server and executes:

```bash
npm run qa:browser
```

The workflow records exact browser versions, screenshots/traces, axe results, runtime/console failures, Lighthouse output, and build-size evidence. WebKit evidence is an engine-level proxy and is not a substitute for real Safari/iOS or screen-reader validation.

## Tier B — official CPS composition reproduction

Raw CPS public-use files are not committed. They must be reacquired from the official Census source path and verified against the committed `input_manifest.json` for the target evidence vintage.

### Q2 2026 primary composition execution

The validated package is under:

`data/derived/composition/cps-q2-2026/`

It contains at minimum:

- `cps_composition.json`;
- `input_manifest.json`;
- `coverage.csv`;
- `sensitivity.csv`;
- `population_audit.json`;
- `validation_checks.json`.

The audited executor is `scripts/execute_cps_composition.py`. A representative invocation is:

```bash
PYTHONPATH=src python scripts/execute_cps_composition.py \
  --year 2026 \
  --quarter 2 \
  --input-dir <official-cps-input-dir> \
  --output-dir data/derived/composition/cps-q2-2026 \
  --validation-report docs/validation/CPS_Q2_2026_COMPOSITION_EXECUTION.md \
  --source-build-commit <git-sha>
```

`--download-missing` may be used only when the official source URLs remain valid and the resulting bytes are verified through the generated provenance/checksum record.

The primary 2026 contract requires:

- employed adults age 18–64 under the implemented CPS employment filter;
- equal month factors within the quarter;
- adoption composition from worker shares;
- assisted-hours/reported-savings composition from actual-main-job-hour shares;
- usual hours as sensitivity only;
- employed-absent workers contribute zero actual main-job hours;
- invalid active-worker actual hours are not imputed;
- unsupported mapping/validity coverage fails closed at the configured gate.

### Q2 2025 historical-layout composition execution

The same-vintage household-side comparison for May 2025 OEWS is under:

`data/derived/composition/cps-q2-2025/`

It is intentionally produced through the audited historical-layout path, not by pretending the 2026 fixed-width layout is valid for 2025:

```bash
PYTHONPATH=src python scripts/execute_cps_2025_composition.py \
  --quarter 2 \
  --input-dir <official-cps-2025-input-dir> \
  --output-dir data/derived/composition/cps-q2-2025 \
  --validation-report docs/validation/CPS_2025_Q2_COMPOSITION_EXECUTION.md \
  --source-build-commit <git-sha>
```

The executor uses the versioned 2025 fixed-width layout registry and records exact official source URLs, SHA-256 hashes, file sizes, row counts, retrieval timestamps, and crosswalk versions.

### Reliability layer

Cross-quarter CPS reliability evidence is retained under:

`data/derived/composition/cps-q2-reliability/`

and documented in:

`docs/validation/CPS_Q2_COMPOSITION_RELIABILITY.md`.

This evidence evaluates composition stability/reliability. It does not turn CPS composition weights into an RPS residual.

## Tier C — OEWS robustness reproduction

Official May 2025 OEWS staffing data are the independent establishment-side robustness basis. The public derived evidence is retained under:

- `data/derived/composition/oews-may-2025/`;
- `data/derived/composition/oews-may-2025-cross-vintage/`.

The execution/robustness paths are implemented in:

- `scripts/execute_oews_composition.py`;
- `scripts/compare_oews_cps_vintages.py`.

Validation records are:

- `docs/validation/OEWS_MAY_2025_CPS_ROBUSTNESS.md`;
- `docs/validation/OEWS_MAY_2025_CPS_VINTAGE_ROBUSTNESS.md`.

OEWS and CPS have different populations and coverage. Reproduction must preserve those differences and report disagreements; the two sources must not be averaged into a synthetic composition measure.

## Composition residual boundary

The repository now reproduces **composition inputs and robustness evidence**. It does not yet reproduce a public occupation-adjusted RPS industry-context residual.

The canonical residual requires a compatible rights-cleared RPS occupation vintage:

`observed industry value - occupation-composition counterfactual`

The join must remain fail-closed until the source-rights decision permits the required RPS observations and the residual robustness suite is rerun. No CPS/OEWS artifact alone identifies an organizational or productivity effect.

## Tier D — private RPS empirical reproduction

Restore the authorized private fixture exactly at:

`data/audit/private/rps_subgroup_5q_audit.json`

Verify its SHA-256 before use. The last frozen research fixture hash recorded by the project is:

`bdeffa95911a94cb60f904c51efc48f7ce4d1bf1eaaec490f5c4bfacd20d4fba`

Then run:

```bash
PYTHONPATH=src python scripts/build_longitudinal.py \
  --fixture data/audit/private/rps_subgroup_5q_audit.json \
  --output-dir data/derived/longitudinal
```

The applicable frozen longitudinal publication artifacts must reproduce byte-for-byte under the private validation contract.

The private fixture must never be copied into the public repository or public build context merely to make private reproduction convenient.

## Source identity

Never identify a research result solely by a filename. A complete research freeze records:

- Git commit SHA;
- source-file checksums;
- private-fixture checksum where applicable;
- registry/crosswalk versions and checksums;
- generated-artifact checksums;
- Python/test environment;
- Node/npm and browser-tool versions where applicable;
- package-lock state;
- source vintages and retrieval dates;
- build/workflow identity;
- public/private data mode.

`RELEASE_PROVENANCE.json` records a public-handoff provenance checkpoint. Dated validation files preserve execution evidence instead of silently rewriting history.

## Determinism and revision discipline

Longitudinal and composition builders must use deterministic ordering and stable serialization where the artifact contract requires it. Publication artifacts must not drift because of platform-specific formatting.

A source revision, registry/crosswalk revision, private-fixture revision, or methodology change must trigger regeneration and a structured comparison against the previous frozen evidence before publication. The observatory must retain analytical history rather than silently overwriting it.

Web dependency resolution is locked through `apps/web/package-lock.json`; release CI uses `npm ci`, not a fresh unconstrained install. Workflow dependencies are pinned to immutable commit SHAs.

## Rights boundary

A clean public checkout must contain no tracked path under:

`data/audit/private/`

Permanent CI also rejects tracked bootstrap transfer material and generated TypeScript build metadata.

Public availability of a source is not treated as permission to mirror, persist, expose through an API, or redistribute it independently.

## What the public repository cannot reproduce by itself

The public repository cannot reconstruct the 630 private RPS source observations because those bytes are deliberately excluded. This is a rights boundary, not a missing-code boundary.

The public repository can inspect and validate the rights-safe longitudinal artifacts derived from the frozen private panel, and it contains the public CPS/OEWS composition artifacts and all code required to regenerate them after reacquiring and verifying the official source bytes.

The public repository still cannot reproduce the RPS-dependent industry residual until a rights-cleared RPS observation path exists.
