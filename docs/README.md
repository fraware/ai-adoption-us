# Documentation

This directory documents the U.S. AI Adoption Observatory: what it measures, what Release 1 finds, where the data come from, how the analysis works, how to reproduce it, and how the public site is maintained.

The documentation is organized for readers who have no knowledge of the project's development history.

## Start here

- [Empirical results](RESULTS.md) — the main Release 1 findings and their interpretation limits.
- [Methodology](methodology.md) — measurement definitions, populations, weighting, cross-source analysis, missingness, and statistical interpretation.
- [Data sources and provenance](source-provenance.md) — source-by-source scope, vintages, populations, and publication boundaries.
- [Release 1 notes](RELEASE1_NOTES.md) — what shipped in `v1.0.0` and what the release does not claim.

## Research methods

- [CPS composition analysis and uncertainty](CPS_COMPOSITION_UNCERTAINTY.md) — industry occupation-composition benchmarks, residuals, robustness diagnostics, and the current design-based uncertainty boundary.
- [OEWS robustness analysis](OEWS_ROBUSTNESS.md) — independent establishment-side staffing comparison and OEWS-weighted adoption robustness.
- [BTOS–RPS industry comparison](BTOS_RPS_COMPARISON.md) — employer-versus-worker construct alignment, period selection, crosswalk, source reproduction, and Release 1 results.

The machine-readable crosswalks, source definitions, and released analytical artifacts underlying these documents are versioned under `data/registry/`, `data/derived/`, and `data/releases/`.

## Data and software

- [Data model](data-model.md) — the semantics of observations, metrics, composition weights, derived results, missingness, and versioning.
- [Architecture](ARCHITECTURE.md) — how source acquisition, scientific processing, versioned publication data, and the web application fit together.
- [Reproducibility](REPRODUCIBILITY.md) — how to run the public code and reconstruct analyses that require reacquiring upstream source data.

## Data access and source use

- [Private research assets](PRIVATE_RESEARCH_ASSETS.md) — which source material is intentionally absent from the public repository and why.
- [RPS source-use decision](source-rights/RPS_SOURCE_DECISION.md) — the recorded basis and limits for using published RPS aggregates in this project.

Public accessibility is not treated as blanket permission to mirror or redistribute third-party source data. Each source retains its own terms and publication boundary.

## Product and operations

- [Product specification](product-spec.md) — intended behavior and information architecture of the public observatory.
- [RPS data updates](RPS_DATA_UPDATES.md) — how new or revised Tracker data are detected and incorporated; also records the current automation limitation.
- [Deployment](DEPLOYMENT.md) — GitHub Pages build, public data mode, privacy, security, and deployment verification.
- [Release checklist](RELEASE_CHECKLIST.md) — maintainer checklist for publishing a new observatory version.
- [Roadmap](ROADMAP.md) — research and product priorities after Release 1.

The current published version is identified by `data/registry/observatory_release_registry.json`, the corresponding directory under `data/releases/`, and the matching GitHub release/tag.

## Documentation policy

Durable documentation describes the current research product, its evidence, and its operation. Temporary execution plans, handoffs, issue-stage terminology, pre-release QA checkpoints, and duplicated reference copies are not part of the current documentation tree.

When historical development detail is needed, use Git history, pull requests, workflow records, and immutable release artifacts. Those are better archival sources than keeping obsolete status documents beside the current methodology.
