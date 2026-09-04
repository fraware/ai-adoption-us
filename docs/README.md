# Documentation

This directory documents the U.S. AI Adoption Observatory: what it measures, how the estimates are constructed, where the data come from, how to reproduce the analysis, and how the public site is maintained.

The documentation is organized by reader need. You should not need knowledge of the project's development history to understand the current system.

## Start here

- [Empirical results](RESULTS.md) — the main findings in Release 1, with interpretation limits.
- [Methodology](methodology.md) — definitions, populations, weighting, composition analysis, uncertainty, and cross-source comparisons.
- [Source provenance](source-provenance.md) — source-by-source provenance, vintages, and use constraints.
- [Data model](data-model.md) — the structure and semantics of observations and derived outputs.
- [Architecture](ARCHITECTURE.md) — how source acquisition, analysis, publication data, and the website fit together.
- [Reproducibility](REPRODUCIBILITY.md) — how to run the public code and reconstruct source-dependent analyses.

## Specialized methods

These documents explain analyses that require more detail than the general methodology page.

- [CPS composition uncertainty](CPS_COMPOSITION_UNCERTAINTY.md)
- [RPS–CPS composition and residual methodology](RPS_CPS_COMPOSITION_RESIDUAL_PROTOCOL.md)
- [BTOS–RPS industry comparison preregistration](BTOS_RPS_INDUSTRY_COMPARISON_PREREGISTRATION_2026-09-02.md)
- [BTOS–RPS industry crosswalk](BTOS_RPS_INDUSTRY_CROSSWALK_2026-09-02.md)
- [BTOS–RPS industry results](BTOS_RPS_INDUSTRY_TRIANGULATION_2026-09-02.md)
- [OEWS provenance audit](OEWS_PROVENANCE_AUDIT.md)

Dated files in this section record the data vintage or analysis decision they describe. They are evidence records, not project-status documents.

## Data access and source permissions

- [Private research assets](PRIVATE_RESEARCH_ASSETS.md) — what is intentionally excluded from the public repository and why.
- [RPS source decision](source-rights/RPS_SOURCE_DECISION.md) — the project's recorded basis and limits for using published RPS aggregates.

The repository does not treat public accessibility as blanket permission to mirror or redistribute third-party source data. Public outputs are limited to source material and derived results within the documented use boundary.

## Software and publication

- [Product specification](product-spec.md) — intended behavior of the public data product.
- [Release checklist](RELEASE_CHECKLIST.md) — maintainer checklist for publishing a new version.
- [Release protocol](OBSERVATORY_RELEASE_PROTOCOL.md) — implementation details for versioning and publication.
- [Release 1 notes](RELEASE1_NOTES.md) — scope and limitations of `v1.0.0`.
- [Roadmap](ROADMAP.md) — research and product work after Release 1.

These files are maintainer references. The current public release is identified by the release registry in `data/registry/observatory_release_registry.json` and the corresponding GitHub release.

## Historical records

Some dated validation, reproduction, and methodological-decision files remain because they document how a particular result or source decision was established. They should be read as evidence for that specific vintage, not as instructions for current development.

Development handoffs, temporary execution plans, and reconstruction notes are not part of the public documentation model and should not be used as references for the current project.
