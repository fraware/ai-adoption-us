# Contributing to GenAI at Work

GenAI at Work is a research data product. Contributions are evaluated for software quality, scientific validity, provenance, rights compatibility, and release integrity at the same time.

## Before opening a pull request

Open or reference an issue when a change alters a measurement construct, source relationship, public claim, release contract, or substantial product behavior. Small documentation corrections and narrowly mechanical fixes may proceed directly when their scope is self-evident.

Do not add private RPS source-input bytes, respondent-level records, credentials, unreviewed third-party datasets, or material whose redistribution rights are unclear. Public availability of a source is not sufficient evidence of permission to store, mirror, or redistribute it.

## Scientific changes

A contribution that changes empirical output must identify the measurement object, source vintage, comparison population, period, weighting rule, suppression rule, and interpretation boundary that it affects. Derived descriptive evidence must remain distinguishable from causal or productivity claims.

Changes to registered source series, construct definitions, composition weights, crosswalks, longitudinal windows, uncertainty treatment, or public claim surfaces require corresponding tests and documentation. Unsupported cells and missing evidence must fail closed; they must not be silently imputed, renormalized, or relabeled as complete estimates.

## Code and validation

Python changes should run:

```bash
python -m pip install -e '.[dev]'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src pytest -q
python -m compileall -q src scripts
ruff check src tests scripts
mypy src
```

Web changes should run from `apps/web`:

```bash
npm ci
npm run lint
DATA_MODE=derived_only npm run build
```

The permanent CI workflow remains authoritative for merge evidence. Do not weaken tests, typing, rights/privacy scans, locked dependency installation, or release checks to make a change pass.

## Pull-request scope

Keep pull requests narrow enough to review. State:

- the objective and affected contract;
- whether scientific values or public claims change;
- whether source or redistribution rights are affected;
- whether public/private data boundaries change;
- the validation performed;
- known limitations or intentionally deferred work;
- release impact, including whether a new exact Observatory candidate is required.

A documentation-only statement that changes the interpretation of an empirical result is a scientific change for review purposes.

## Release-sensitive changes

The public release process is governed by the repository release engine and `docs/RELEASE_CHECKLIST.md`. A merged pull request does not by itself authorize publication. Release-sensitive changes may invalidate the current candidate and require a fresh candidate-review package, exact source rehydration, human attestation, promotion, deployment audit, and formal release.

Do not create alternative publication paths around those controls.

## Historical records

Dated validation reports, closed pull requests, immutable release records, and historical reconstruction documents are retained as provenance. Correct their interpretation with explicit historical-status notes instead of rewriting old evidence as though it had been produced under a later repository state.
