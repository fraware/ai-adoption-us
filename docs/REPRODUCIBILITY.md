# Reproducibility

GenAI at Work separates two kinds of reproducibility:

1. **Public-code reproducibility:** anyone can run the software, tests, website build, and analyses that depend only on files distributed in this repository.
2. **Source-dependent reproducibility:** some analyses require reacquiring official upstream files that are not redistributed here. The repository records the source identity, transformation code, and derived outputs needed to reproduce those analyses when the source is available to the researcher.

This distinction is necessary because not every upstream dataset can be mirrored in a public Git repository.

## 1. Environment

Python requirements:

- Python 3.12+
- dependencies defined in `pyproject.toml`

Install the project and development dependencies:

```bash
python -m pip install -e '.[dev]'
```

The web application uses Node.js dependencies pinned by the lockfile in `apps/web/`.

## 2. Run the Python test suite

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src pytest -q
python -m compileall -q src scripts
ruff check src tests scripts
mypy src
```

These checks cover scientific transformations, schemas, source metadata, public/private data separation, release metadata, and software behavior.

## 3. Build the public website

```bash
cd apps/web
npm ci --no-audit --no-fund
npm run lint
DATA_MODE=derived_only NEXT_TELEMETRY_DISABLED=1 npm run build
```

To run the site locally:

```bash
DATA_MODE=derived_only npm run dev
```

`derived_only` is the public configuration. It does not require private RPS source files.

## 4. Reproducing RPS-derived analysis

Release 1 uses published aggregate Generative AI Adoption Tracker series retrieved through FRED/ALFRED.

The repository records:

- the series included in the project;
- source metadata and definitions;
- source-use restrictions;
- the code used to retrieve and validate observations;
- the generated public observations and derived diagnostics;
- source and artifact checksums used for released versions.

The complete source files used during release preparation are not stored in the public repository. To reproduce the source-dependent analysis, reacquire the registered series from the official interface and run the acquisition and analysis scripts in a private or temporary workspace.

The main acquisition utility is:

```bash
PYTHONPATH=src python scripts/prepare_rps_refresh_candidate.py \
  --output-dir <private-output-directory>
```

The resulting source material should remain outside public Git unless its redistribution status explicitly permits publication.

Release 1's common industry/occupation analysis window is Q4 2024 through Q2 2026, covering seven quarters.

## 5. Reproducing CPS composition analysis

The CPS component uses official Basic Monthly public-use data.

Release 1 includes validated composition packages for:

- Q2 2025;
- Q2 2026.

Derived outputs are stored under `data/derived/composition/`.

The analysis preserves the following definitions:

- worker-share weights for workplace adoption;
- actual-main-job work-hour shares for AI-assisted working time and reported time savings;
- usual-hours weights as a sensitivity analysis;
- explicit coverage and mapping diagnostics.

Q4 2025 is not constructed because October 2025 CPS data were not collected.

The public repository does not claim a full design-based covariance estimate for the custom pooled occupation-composition vectors. See [CPS_COMPOSITION_UNCERTAINTY.md](CPS_COMPOSITION_UNCERTAINTY.md).

## 6. Reproducing OEWS robustness analysis

Release 1 uses official May 2025 OEWS staffing data as an independent establishment-side composition comparison.

The corresponding derived artifacts are under `data/derived/composition/` and retain the source-vintage information needed to distinguish OEWS from CPS-based estimates.

Because OEWS and CPS describe different populations and survey systems, their outputs should be compared as robustness evidence rather than combined into a single weighting scheme.

## 7. Reproducing BTOS–RPS industry comparisons

The BTOS comparison uses a documented sector crosswalk and a preregistered definition of the employer-side AI-use measure.

To reproduce the comparison, use the source and period identified in the BTOS documentation together with the versioned RPS industry observations for the same analysis release.

Relevant files include:

- `BTOS_RPS_INDUSTRY_COMPARISON_PREREGISTRATION_2026-09-02.md`;
- `BTOS_RPS_INDUSTRY_CROSSWALK_2026-09-02.md`;
- `BTOS_RPS_INDUSTRY_TRIANGULATION_2026-09-02.md`.

The resulting correlation is a descriptive comparison across non-equivalent constructs.

## 8. Reconstructing a complete release

A complete release combines one defined set of RPS, CPS, OEWS, and BTOS evidence with a specific repository version.

For Release 1, the main preparation sequence is:

```bash
PYTHONPATH=src python scripts/prepare_rps_refresh_candidate.py \
  --output-dir <private-rps-source>

PYTHONPATH=src python scripts/prepare_rps_observatory_candidate.py \
  --source-snapshot <private-rps-source>/rps_source_snapshot.json \
  --output-dir <private-rps-analysis> \
  --release-id <rps-analysis-id>

PYTHONPATH=src python scripts/prepare_observatory_v1_candidate.py \
  --rps-candidate-root <private-rps-analysis> \
  --output-dir <private-release-build> \
  --release-id <release-id>
```

The generated release manifest records the files and checksums that define the build. Publication tooling verifies that the reviewed source identity and generated outputs have not changed before the version is added to `data/releases/`.

These release utilities are primarily maintainer tools. Researchers reproducing a specific result usually need only the relevant source acquisition and analysis step.

## 9. Version identity

A reproducible analytical version should record, where applicable:

- repository commit;
- source series or file identifiers;
- source vintage or retrieval metadata;
- crosswalk and taxonomy versions;
- generated-artifact checksums;
- public release identifier.

The current published release is recorded in:

- `data/registry/observatory_release_registry.json`;
- the corresponding directory under `data/releases/`;
- the corresponding GitHub release/tag.

For Release 1, the formal tag is `v1.0.0`.

## 10. Revisions

Upstream sources may revise historical values or definitions. A new source vintage should therefore be treated as a new analytical input.

When a source changes:

1. record the new source identity;
2. regenerate affected artifacts;
3. compare the new outputs with the previous version;
4. review any changed public interpretation;
5. publish a new release if the public evidence changes.

Published historical releases remain unchanged.

## 11. Data that are intentionally absent

The public repository does not include:

- private RPS source-input files used during release preparation;
- respondent-level RPS records;
- unrestricted historical subgroup source mirrors;
- credentials or private audit material.

Their absence is intentional and should not be interpreted as a reproducibility omission. The project provides source identity, acquisition code, derived outputs, and provenance while respecting the documented source-use boundary.

See [PRIVATE_RESEARCH_ASSETS.md](PRIVATE_RESEARCH_ASSETS.md) and [source-rights/RPS_SOURCE_DECISION.md](source-rights/RPS_SOURCE_DECISION.md).
