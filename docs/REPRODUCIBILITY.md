# Reproducibility contract

## Public repository reproducibility

The public repository is intentionally a **rights-safe** reproduction package. It contains all source code, registries, generated public diagnostics, validation logic, and product source, but excludes the private copyrighted RPS observation fixture.

Accordingly there are two reproducibility tiers.

## Tier A — public/source reproducibility

A clean public checkout must be able to:

```bash
python -m pip install -e '.[dev]'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src pytest -q
python -m compileall -q src scripts
./scripts/validate_ts_structural.sh
```

Private-fixture-dependent tests are expected to skip when the fixture is absent. All governance, registry, CPS, composition, and public web-release tests must execute.

The web build must be validated separately:

```bash
cd apps/web
npm install
DATA_MODE=derived_only npm run build
```

GitHub Actions is the canonical network-capable validation path until a lockfile is established.

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

The four publication artifacts must reproduce byte-for-byte.

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
- no Q4-2025 November/December substitution.

## Source identity

Never identify a research result solely by a filename. A complete research freeze should record:

- Git commit SHA;
- source-file checksums;
- private-fixture checksum;
- registry checksum/cardinality;
- generated-artifact checksums;
- Python/test environment;
- Node/package-lock state;
- source vintages and retrieval dates.

## Determinism

The longitudinal builder must use deterministic ordering and LF line endings. Publication artifacts should not change because of platform-specific CSV serialization.

## What is intentionally not reproducible from the public repository alone

The public repository cannot reconstruct the 630 private RPS source observations because those bytes are deliberately excluded. This is a rights boundary, not a missing-code boundary.

The public repository can inspect the complete analysis code and the derived result artifacts generated from those observations.
