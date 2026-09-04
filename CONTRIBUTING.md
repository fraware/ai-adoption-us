# Contributing to GenAI at Work

GenAI at Work is both a research project and a public data product. Contributions are reviewed for software quality, scientific validity, reproducibility, source provenance, data-use permissions, and the accuracy of public interpretation.

## Before you contribute

Open or reference an issue when a change affects any of the following:

- a measurement definition or population;
- an upstream data source or source vintage;
- a weighting, crosswalk, suppression, or uncertainty method;
- a published empirical result or public interpretation;
- the public/private data boundary;
- release behavior or a substantial product feature.

Small documentation corrections and mechanical fixes can usually proceed directly.

Do not add credentials, respondent-level records, private RPS source files, unreviewed third-party datasets, or material whose redistribution status is unclear.

## Scientific changes

Changes that affect empirical outputs should document:

- the quantity being estimated;
- the population and period;
- the source and source vintage;
- the weighting or aggregation rule;
- relevant crosswalks or classification mappings;
- missing-data and suppression rules;
- uncertainty treatment;
- the interpretation that the evidence supports.

Derived descriptive results must remain distinguishable from causal estimates and productivity claims. Missing or unsupported quantities should remain missing unless a documented method justifies estimating them.

A documentation change that alters the interpretation of a result should be reviewed as a scientific change.

## Source and data-use changes

When introducing or changing a data source, include:

1. the authoritative source location;
2. the exact series, table, file, or API scope used;
3. the relevant population, units, and reference period;
4. source-vintage or revision information;
5. the basis for storing and publishing the material included in the repository;
6. any restrictions on redistribution or derived outputs.

Do not assume that public accessibility grants unrestricted permission to copy or redistribute source data.

## Validation

Python changes should pass:

```bash
python -m pip install -e '.[dev]'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src pytest -q
python -m compileall -q src scripts
ruff check src tests scripts
mypy src
```

Web changes should pass from `apps/web`:

```bash
npm ci
npm run lint
DATA_MODE=derived_only npm run build
```

Relevant scientific changes should also regenerate the affected derived artifacts and run the tests that validate their definitions, provenance, and expected output.

Do not weaken tests, type checks, privacy checks, or source-validation rules simply to make a change pass.

## Pull requests

Keep pull requests small enough to review. The description should state:

- what changed and why;
- whether scientific values changed;
- whether public interpretation changed;
- whether source or redistribution permissions are affected;
- whether public/private data boundaries changed;
- what validation was run;
- any remaining limitations;
- whether a new published release is required.

Where practical, separate formatting or refactoring from scientific changes so reviewers can distinguish changes in presentation from changes in evidence.

## Documentation

Documentation should be written for a reader who has no knowledge of the project's development history.

Prefer domain-standard terminology and define project-specific terms on first use. Avoid temporary task labels, development-stage shorthand, pull-request chronology, internal status language, or instructions that are meaningful only to maintainers.

Durable documentation should explain one of four things: the research question, the method, the software/data architecture, or how to reproduce and maintain the public product.

## Publication

Publishing a new version is separate from merging code. A release should correspond to a defined set of source vintages, generated outputs, tests, and public documentation.

Maintainer procedures are documented in [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md). Current published versions are identified by the release registry and the corresponding GitHub release.
