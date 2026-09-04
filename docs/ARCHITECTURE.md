# Architecture

GenAI at Work is composed of four layers: source acquisition, scientific analysis, versioned publication data, and a public web application. The architecture is designed so that a published chart or number can be traced back to a defined source vintage and reproducible transformation.

## 1. System overview

```text
Official upstream sources
        │
        ▼
Source acquisition and validation
        │
        ├── source identity and metadata
        └── private source files where redistribution is restricted
        │
        ▼
Scientific processing
        │
        ├── RPS longitudinal analysis
        ├── CPS industry × occupation composition
        ├── OEWS robustness analysis
        └── BTOS industry comparison
        │
        ▼
Versioned public artifacts
        │
        ├── observations permitted for publication
        ├── derived tables and diagnostics
        └── provenance and release metadata
        │
        ▼
Next.js public website
```

The repository separates source material from derived public output because different upstream datasets have different storage and redistribution conditions.

## 2. Repository layers

### `src/genai_at_work/`

Python modules for data validation, analysis, composition methods, provenance, and release preparation.

### `data/contracts/`

Schemas and structural definitions for observations and generated artifacts.

### `data/registry/`

Machine-readable metadata for sources, taxonomies, crosswalks, source-use decisions, and published releases.

### `data/derived/`

Versioned derived outputs that can be included in the public repository. These include longitudinal RPS diagnostics, CPS/OEWS composition results, and BTOS–RPS comparison results.

### `data/releases/`

Immutable directories representing published versions of the observatory.

### `apps/web/`

The Next.js website. Public pages load versioned publication data and present national, industry, occupation, methodology, source, and research views.

### `scripts/`

Command-line utilities for acquiring sources, regenerating analysis, validating outputs, and publishing releases.

### `tests/`

Scientific and software tests covering source definitions, transformations, privacy boundaries, derived results, and the web build.

## 3. Source acquisition

The project uses official upstream interfaces whenever available.

### RPS

Published aggregate RPS series are retrieved through FRED/ALFRED. The acquisition code validates the registered series inventory, metadata, observation domain, and source identity before analysis.

Some RPS source files used during reproduction are not committed to the public repository. Only observations and derived outputs covered by the documented public-use boundary are published.

### CPS

CPS Basic Monthly public-use files are used to estimate industry × occupation composition and working-time weights. Each analysis package records the months and classification definitions used.

### OEWS

May 2025 OEWS staffing data provide an establishment-side composition robustness source.

### BTOS

BTOS data provide an employer-side measure of recent AI use for sector-level comparison with worker-reported RPS adoption.

Source details are documented in [source-provenance.md](source-provenance.md).

## 4. Scientific processing

### RPS longitudinal analysis

The RPS analysis computes descriptive relationships among workplace adoption, AI-assisted working time, and reported time savings across industries and occupations.

The main procedures include:

- Pearson and Spearman association;
- cross-sectional regression summaries;
- leave-one-group-out sensitivity checks;
- rank persistence across quarters.

### CPS composition analysis

CPS provides the occupation mix within each industry. Worker shares are used for adoption benchmarks, while actual main-job work-hour shares are used for assisted-hours and reported-savings benchmarks.

Observed industry values are compared with these occupation-composition benchmarks. The resulting residual is descriptive and does not identify an organizational or causal effect.

### OEWS robustness analysis

OEWS provides a second view of industry staffing composition. It is kept analytically separate from CPS because the populations and survey designs differ.

### BTOS comparison

BTOS and RPS are linked through a documented industry crosswalk. Their sector-level association is reported as a cross-source descriptive comparison, not as a comparison of equivalent measures.

The complete statistical methodology is described in [methodology.md](methodology.md).

## 5. Public and private data boundaries

The repository has two distinct data domains.

### Public domain

The public Git repository contains:

- source metadata and provenance;
- schemas and crosswalks;
- public observations covered by the project's source-use decisions;
- derived tables, diagnostics, and robustness results;
- published release artifacts;
- code and documentation.

### Private or transient domain

Source files that cannot be redistributed are acquired into a private or transient workspace during reproduction or publication. They are used to generate verified public outputs and are not copied into the public release.

`data/audit/private/` represents the repository-local private workspace boundary and is excluded from Git.

See [PRIVATE_RESEARCH_ASSETS.md](PRIVATE_RESEARCH_ASSETS.md) for details.

## 6. Web data modes

The application exposes an explicit `DATA_MODE` configuration.

### `derived_only`

The public mode used by the released website. It loads published observations and derived analysis artifacts only.

### `audit_snapshot`

A private research mode for explicitly supplied audit data. It is not used by the public website.

### `fred_live_no_store`

A reserved server-side mode for direct source access without persistent storage. Release 1 does not require this mode for the public site.

The application does not automatically switch from a public mode into a private data source.

## 7. Versioning and provenance

Generated results are associated with the source and repository state from which they were produced. Depending on the analysis, the recorded identity includes:

- source series or files;
- source vintage or retrieval metadata;
- crosswalk and taxonomy versions;
- generated-artifact checksums;
- repository commit;
- published release identifier.

Historical releases are preserved instead of modifying published data in place. The current public version is recorded in `data/registry/observatory_release_registry.json` and the corresponding GitHub release.

## 8. Publication process

A new public version follows a conventional reproducible-release sequence:

1. acquire the required source vintages;
2. validate source identities and definitions;
3. regenerate all affected analysis artifacts;
4. run scientific and software tests;
5. review changed values, methodology, provenance, and public interpretation;
6. create a versioned release directory;
7. update the release registry;
8. deploy the website from that release;
9. preserve the previous release unchanged.

The implementation includes checksum and source-identity checks so that a source revision or changed analysis input cannot be published under an earlier reviewed version.

Maintainer details are documented in [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md).

## 9. Public website

The website is intentionally a thin presentation layer over versioned data. It should not contain manually copied analytical values when those values can be loaded from published artifacts.

This keeps the website, downloadable evidence, and documented methodology aligned across releases.

## 10. Design principles

The architecture follows five principles:

1. **Traceability:** a published result should be traceable to its source and transformation.
2. **Separation of concerns:** source acquisition, analysis, release data, and presentation remain distinct.
3. **Explicit data permissions:** public storage and redistribution are decided source by source.
4. **Versioned revisions:** changed source data produce a new analytical version instead of silently overwriting history.
5. **Evidence-bounded publication:** unsupported estimates remain unavailable and descriptive analyses are not relabeled as causal findings.
