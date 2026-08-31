# Reproducibility contract

## Public repository reproducibility

The public repository is intentionally a **rights-safe reproduction package**. It contains source code, registries, generated public diagnostics, validation logic, product source, and the committed Node lockfile, but excludes the private copyrighted RPS observation fixture.

Accordingly there are two reproducibility tiers.

## Tier A — public/source reproducibility

A clean public checkout must be able to execute the public Python surface:

```bash
python -m pip install -e '.[dev]'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src pytest -q
python -m compileall -q src scripts
ruff check src tests scripts
mypy src
```

Private-fixture-dependent tests are expected to skip when the fixture is absent. Governance, registry, CPS, composition, and public web-release tests must execute. The expected public/private distinction is documented in `VALIDATION_2026-08-31.md`; do not reinterpret expected private-fixture skips as failed public coverage.

The rights-safe web surface is lockfile-reproducible:

```bash
cd apps/web
npm ci --no-audit --no-fund
npm run lint
DATA_MODE=derived_only NEXT_TELEMETRY_DISABLED=1 npm run build
```

Permanent GitHub Actions CI additionally starts the production server and smoke-tests:

- `/`;
- `/blog/after-adoption`;
- `/explore/industries`;
- `/explore/occupations`;
- `/methodology`;
- `/sources`.

The first successful networked optimized build was GitHub Actions run `33411128343` on 2026-08-31. That bootstrap-era run used `npm install`; permanent CI intentionally upgrades the reproducibility contract to `npm ci` against the committed `package-lock.json`.

## Tier B — private empirical reproduction

Restore the private fixture exactly at:

`data/audit/private/rps_subgroup_5q_audit.json`

Verify its SHA-256 before use. The last frozen research fixture hash is:

`bdeffa95911a94cb60f904c51efc48f7ce4d1bf1eaaec490f5c4bfacd20d4fba`

Then run:

```bash
PYTHONPATH=src python scripts/build_longitudinal.py \
  --fixture data/audit/private/rps_subgroup_5q_audit.json \
  --output-dir data/derived/longitudinal
```

The committed longitudinal publication artifacts must reproduce byte-for-byte according to the private validation contract.

The private fixture must never be copied into the public repository or public build context merely to make Tier B reproducibility convenient.

## CPS composition reproduction

Required Q2 2026 official Basic Monthly CPS inputs:

- April 2026 public-use file;
- May 2026 public-use file;
- June 2026 public-use file.

Do not substitute a two-month quarter.

Execution sequence:

```bash
PYTHONPATH=src python scripts/build_cps_composition.py ...
PYTHONPATH=src python scripts/build_composition_residuals.py ...
```

Before publication, verify:

- CPS input vintages and checksums;
- quarter/month registry;
- worker-weight sums and hour-weight sums;
- coverage diagnostics;
- suppression propagation;
- actual-hours primary specification;
- usual-hours sensitivity kept separate;
- no Q4-2025 November/December substitution;
- output provenance identifies the exact Git commit, crosswalk versions, and source files.

No empirical CPS composition or residual result is part of the current public reproducibility claim.

## Source identity

Never identify a research result solely by a filename. A complete research freeze records:

- Git commit SHA;
- source-file checksums;
- private-fixture checksum where applicable;
- registry checksum/cardinality;
- generated-artifact checksums;
- Python/test environment;
- Node and npm versions;
- package-lock state;
- source vintages and retrieval dates;
- build/CI run identity;
- public/private data mode.

`RELEASE_PROVENANCE.json` records the current public-handoff provenance checkpoint. Dated validation files preserve execution evidence instead of silently rewriting history.

## Determinism

The longitudinal builder must use deterministic ordering and LF line endings. Publication artifacts must not change because of platform-specific CSV serialization.

Dependency resolution for the web application is locked through `apps/web/package-lock.json`; CI uses `npm ci`, not a fresh unconstrained install.

GitHub Actions used by permanent CI are pinned to immutable commit SHAs, with the human-readable release tag retained as a comment in the workflow.

## Rights boundary

A clean public checkout must contain no tracked path under:

`data/audit/private/`

Permanent CI also rejects tracked bootstrap transfer material and generated TypeScript build metadata.

## What is intentionally not reproducible from the public repository alone

The public repository cannot reconstruct the 630 private RPS source observations because those bytes are deliberately excluded. This is a rights boundary, not a missing-code boundary.

The public repository can inspect the complete analysis code and the rights-safe derived result artifacts generated from those observations.

Likewise, the current public repository does not reproduce a real CPS composition result because the required official monthly input execution has not yet been completed and validated.
