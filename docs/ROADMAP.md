# Roadmap

Status: **4 September 2026**

Release 1 (`v1.0.0`) established the first public baseline of the U.S. AI Adoption Observatory. The next phase is about extending the measurement system without weakening the distinctions that make the current results interpretable.

## Current baseline

Release 1 provides:

- seven-quarter national and subgroup workplace GenAI evidence through Q2 2026;
- industry and occupation views of adoption, AI-assisted working time, and reported time savings;
- CPS-based occupation-composition benchmarks for industries;
- descriptive occupation-adjusted industry residuals;
- OEWS staffing robustness analysis;
- BTOS–RPS sector comparison;
- a versioned public website and reproducible release structure.

The current release remains descriptive. It does not estimate causal productivity, wage, employment, or firm-performance effects.

## Near-term product work

### Improve the public explorer

Extend the industry and occupation pages so readers can move more easily between levels, trends, composition benchmarks, source definitions, and uncertainty information.

Priorities include:

- clearer comparison views across quarters;
- easier access to source and denominator definitions;
- explicit display of missing periods and source breaks;
- better presentation of composition benchmarks and residuals;
- downloadable derived tables where source-use conditions permit them.

### Release history and revisions

Make source and analytical revisions easier to inspect from the website. A reader should be able to distinguish:

- when an upstream source changed;
- when the observatory published a new version;
- which values changed;
- whether a change reflects new data, a revised source value, or a methodological revision.

### Documentation consolidation

Continue reducing duplication across methodology, provenance, source-specific notes, and maintainer procedures. Durable documentation should describe the current system; dated evidence records should remain clearly identified as historical or source-vintage-specific records.

## Research priorities

### 1. Design-based uncertainty for CPS composition estimates

Release 1 does not provide a full design-based covariance estimate for the custom pooled CPS occupation-composition vectors.

A future method should add design-based intervals only if the required replicate or covariance information can be obtained from an authoritative source and implemented with defensible survey methodology.

Until then, sensitivity and stability diagnostics remain descriptive.

### 2. Richer composition analysis

The current industry analysis uses broad occupation composition to construct descriptive benchmarks. Future work can examine whether finer occupation, task, worker, or firm structure explains additional variation.

Any extension should preserve the distinction between statistical decomposition and causal identification.

### 3. Task exposure versus realized adoption

The project can add a task-level layer comparing theoretical or model-based AI exposure with realized worker-reported use.

This requires:

- a well-defined task/occupation mapping;
- source and publication permissions for the task data;
- explicit separation of capability, exposure, adoption, assisted use, and reported savings.

Exposure should not be used as a substitute for observed adoption.

### 4. Realized economic outcomes

A major future objective is to connect workplace AI use to outcomes such as:

- measured output or productivity;
- wages;
- employment;
- hours;
- firm performance.

These questions require new outcome data and research designs capable of supporting causal or otherwise identified claims. Reported time savings alone are insufficient.

### 5. Mechanism-oriented analysis

Longer-term work should investigate why adoption and use intensity differ across occupations and industries.

Potential mechanisms include task suitability, worker selection, employer tooling, organizational practices, regulation, and market structure. These mechanisms should be studied with data that can distinguish among them instead of assigning causal meaning to aggregate residuals.

## Data and source development

Future releases should continue to:

- update RPS observations as new waves become available;
- refresh CPS composition inputs on a documented schedule;
- update BTOS and OEWS comparisons when new comparable vintages are available;
- preserve source-definition and classification changes explicitly;
- keep third-party redistribution decisions source-specific.

A new source should be added only when its measurement role is clear and it materially improves the observatory.

## Release principles

Future versions should maintain the following properties:

1. every published result is tied to defined source vintages;
2. changed sources regenerate affected analyses;
3. historical releases remain available;
4. public interpretation is reviewed when results or definitions change;
5. the website reads from versioned release artifacts rather than hand-maintained analytical values;
6. unsupported quantities remain unavailable until a defensible method exists.

## What is deliberately outside the current scope

The following are research extensions, not missing pieces of Release 1:

- respondent-level causal mechanism analysis;
- a universal AI-impact or productivity number;
- task-level exposure/adoption analysis without resolved provenance and permissions;
- full design-based CPS composition uncertainty without authoritative covariance information;
- unrestricted redistribution of third-party source data.
