# Release checklist

This checklist is for maintainers publishing a new version of GenAI at Work after Release 1. It describes the scientific and operational checks that should be completed before the public site is updated.

The current published version is identified by `data/registry/observatory_release_registry.json` and the corresponding GitHub release. Historical release records should not be edited in place.

## 1. Define the release scope

Before rebuilding the observatory, record:

- which upstream sources changed;
- the source vintages or retrieval dates;
- whether any source definition, wording, classification, or access condition changed;
- which analysis artifacts and public pages are affected;
- whether the release changes only software/documentation or also changes empirical evidence.

If a source definition changed materially, treat it as a measurement revision, not as an ordinary data refresh.

## 2. Verify source provenance and publication conditions

For every source included in the release:

- use the documented authoritative acquisition path;
- verify the registered series or file identity;
- record the relevant period and vintage;
- confirm that the intended public output remains within the documented source-use boundary;
- preserve required attribution;
- keep source files outside the public repository when redistribution is not covered.

Do not broaden public source-data access simply because an upstream dataset is publicly accessible.

## 3. Regenerate affected analyses

Rebuild all outputs that depend on changed sources or methods.

For the current measurement system, this can include:

- RPS public observations and longitudinal diagnostics;
- CPS industry × occupation composition weights and benchmarks;
- occupation-adjusted industry residuals;
- OEWS robustness analysis;
- BTOS–RPS sector comparison;
- source and release metadata;
- charts or tables generated from those artifacts.

Do not patch published analytical values manually when they can be regenerated from source-defined inputs.

## 4. Review scientific definitions

Confirm that the release preserves the project's core measurement distinctions:

- work adoption is different from use intensity;
- AI-assisted work hours are different from hours saved;
- reported time savings are different from measured productivity;
- theoretical capability or exposure is different from realized adoption;
- occupation-adjusted industry residuals remain descriptive unless a separate identification strategy supports a stronger interpretation;
- BTOS employer use and RPS worker use remain distinct constructs.

Check populations, denominators, weighting rules, crosswalks, missing-data treatment, and suppression logic for every changed analysis.

## 5. Review uncertainty and missingness

For any new or revised statistical interval or uncertainty estimate, verify that the method is supported by the relevant source design and inputs.

Do not infer missing covariance information from marginal standard errors or assume independence across repeated survey observations without methodological support.

Unavailable or suppressed values should remain explicit. In particular, historical source gaps should not be interpolated simply to create a visually continuous series.

## 6. Run software and scientific validation

From the repository root:

```bash
python -m pip install -e '.[dev]'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src pytest -q
python -m compileall -q src scripts
ruff check src tests scripts
mypy src
```

From `apps/web`:

```bash
npm ci --no-audit --no-fund
npm run lint
DATA_MODE=derived_only NEXT_TELEMETRY_DISABLED=1 npm run build
```

Run any additional source-specific reproduction or validation scripts required by the changed evidence.

If application behavior changed, also run the relevant browser, accessibility, and production-route checks used by continuous integration.

## 7. Review public interpretation

Read every public page affected by the release as a publication, not only as a software build.

Check that:

- headline claims are reproduced by the released artifacts;
- periods and denominators are stated correctly;
- descriptive statistics are not presented as causal effects;
- reported savings are not described as measured productivity;
- source differences and measurement breaks are visible where they affect interpretation;
- missing or suppressed evidence is represented accurately;
- methodology and provenance documentation match the released data.

Documentation changes that alter the interpretation of a result should receive the same scientific review as analytical changes.

## 8. Verify the public/private data boundary

Before publication, inspect the candidate public artifacts and web build for accidental inclusion of:

- credentials;
- private RPS source files;
- respondent-level data;
- private audit fixtures;
- source paths or metadata that expose private storage locations;
- third-party source material outside the documented redistribution scope.

The public website should run in `derived_only` mode.

## 9. Create the versioned release

The repository's release tooling should create a new immutable directory under `data/releases/` and advance the release registry to the new version.

The published release should record enough identity information to reproduce the analytical state, including the relevant source identities, generated artifacts, repository version, and checksums.

Previous release directories and registry history should remain unchanged.

## 10. Deploy and inspect the site

Deploy the website from the versioned release and verify the production origin.

At minimum, inspect:

- home page;
- industry explorer;
- occupation explorer;
- methodology;
- sources;
- technical essay;
- responsive layouts;
- chart/table consistency;
- release/version information.

A successful build is necessary but is not a substitute for checking the published analytical content.

## 11. Publish release notes

Create release notes that state:

- release date and version;
- new or revised source vintages;
- material changes in empirical results;
- methodology changes;
- measurement breaks or newly unavailable periods;
- source-use or provenance changes;
- important product changes;
- known limitations.

Avoid internal issue labels, pull-request chronology, temporary project terminology, or implementation details unless they are necessary for technical reproducibility.

## 12. After publication

Preserve the previous release and record any upstream revision detected after publication as a new source event.

If a post-release error affects public evidence or interpretation, correct it through a new version with explicit release notes rather than silently changing the historical release.

For source-update operations, see [RPS_DATA_UPDATES.md](RPS_DATA_UPDATES.md). For source-dependent reconstruction, see [REPRODUCIBILITY.md](REPRODUCIBILITY.md). For the public hosting configuration and post-deployment checks, see [DEPLOYMENT.md](DEPLOYMENT.md).
