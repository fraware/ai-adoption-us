# Data model

The data model makes the meaning and provenance of every published value explicit. A chart should never have to infer a measure, population, denominator, source, or transformation from a filename or column position.

This document describes the conceptual model. Machine-readable schemas and registries under `data/contracts/` and `data/registry/` are authoritative for field-level validation.

## 1. Entities

An entity is the population grouping to which an observation refers.

| Field | Type | Meaning |
| --- | --- | --- |
| `entity_id` | string | Stable identifier |
| `entity_type` | enum | `national`, `industry`, or `occupation` |
| `name` | string | Human-readable label |
| `source_classification` | string / null | Source classification code or label |
| `sort_key` | integer | Stable display order |

## 2. Metrics

A metric describes the measurement construct independently of any particular entity or period.

Core metrics include:

| Metric | Interpretation | Denominator |
| --- | --- | --- |
| `adoption_work` | Employed adults aged 18–64 reporting generative-AI use for work | Employed adults |
| `work_use_last_week` | Employed adults reporting work use in the previous week | Employed adults |
| `work_use_daily` | Employed adults reporting use every workday in the previous week | Employed adults |
| `assisted_hours_share` | Share of total working time assisted by generative AI | Total work hours |
| `reported_time_savings_share` | Self-reported additional time otherwise required, expressed relative to total work hours | Total work hours |

Some source registries also contain broader adoption measures that are outside the observatory's main workplace comparison.

Metric metadata should record:

- stable metric identifier;
- display label;
- unit;
- denominator;
- construct type;
- whether nonusers are assigned zero where relevant;
- definition;
- interpretation warning.

Construct types distinguish direct responses, reconstructed measures, self-reported counterfactuals, and derived quantities.

None of the Release 1 workplace measures is itself a causal productivity measure.

## 3. Source-series registry

The source-series registry maps an upstream series to the project's metric and entity definitions.

Typical fields include:

- source;
- source release or vintage;
- series identifier;
- source title;
- metric identifier;
- entity identifier;
- frequency;
- unit;
- seasonal-adjustment status;
- observation start and end;
- source update metadata;
- source URL;
- citation text;
- publication or copyright metadata;
- a hash of source notes or definitions.

Definition hashes allow the software to detect a substantive metadata change even when the upstream series identifier remains unchanged.

## 4. Observations

Observations use a long-form representation: one row represents one source value for one entity, metric, and period.

Typical fields include:

- source;
- series identifier;
- metric identifier;
- entity identifier and type;
- date and normalized period, such as `2026-Q2`;
- value and unit;
- source-vintage metadata;
- ingestion timestamp;
- source update timestamp.

Source precision is preserved in stored analytical values. Rounding is a presentation decision.

Where the upstream system supplies revision or real-time metadata, the model retains enough information to distinguish a current observation from an earlier vintage.

## 5. Composition weights

CPS and OEWS composition analyses represent the share of an industry's workers or work hours attributable to each occupation.

Typical fields include:

- source;
- period;
- industry identifier;
- occupation identifier;
- weighting basis: `workers` or `work_hours`;
- share;
- sample population;
- survey weight variable;
- hours variable where applicable;
- crosswalk version;
- unweighted sample count or coverage information.

The weighting basis is part of the scientific definition:

- workplace adoption uses worker shares;
- AI-assisted working time and reported time savings use work-hour shares.

Release 1 includes CPS composition analyses for Q2 2025 and Q2 2026, with OEWS May 2025 used as an independent robustness source.

## 6. Derived observations

A derived observation is calculated from one or more source observations or composition weights. It should record enough metadata to reconstruct both the value and its interpretation.

Typical fields include:

- derived metric identifier;
- entity and period;
- value;
- formula or method version;
- input dataset or source-vintage identity;
- status;
- interpretation;
- caution or limitation.

### Occupation-composition benchmark

For industry `j`, occupation `o`, period `t`, and metric `m`, an industry benchmark is constructed from occupation-level RPS values and industry occupation weights.

For adoption:

```text
A_hat(j,t) = Σ_o w_worker(j,o,t) × A(o,t)
```

For AI-assisted working time and reported time savings:

```text
H_hat(j,t) = Σ_o w_hours(j,o,t) × H(o,t)
S_hat(j,t) = Σ_o w_hours(j,o,t) × S(o,t)
```

### Occupation-adjusted industry residual

```text
residual(j,t,m) = observed(j,t,m) - benchmark(j,t,m)
```

This is a descriptive standardization residual. It does not identify organizational quality, efficiency, productivity, or a causal effect.

### Partial-identification intervals

When a source classification is materially coarser than the target classification, the method may report a feasible interval instead of imposing an arbitrary allocation within the broad category.

## 7. Evidence status

Derived and published objects should be distinguishable by evidentiary status. A useful conceptual classification is:

- **observed:** a published source value or deterministic aggregation of source values;
- **derived descriptive:** a deterministic transformation, correlation, regression, composition benchmark, residual, or stability statistic;
- **approximate uncertainty:** an explicitly labeled approximation with documented assumptions;
- **design-based uncertainty:** an interval or covariance result supported by the relevant survey design information;
- **causal outcome:** a separately identified effect using appropriate outcome data and research design.

Release 1 contains observed and derived descriptive evidence. It does not promote reported time savings or industry residuals into causal outcome measures.

## 8. Missing and suppressed values

Missingness is represented explicitly. The software should distinguish among at least:

- source value unavailable;
- source value suppressed;
- classification or coverage insufficient;
- method unsupported for that period or cell.

An unavailable component is not silently renormalized into an apparently complete estimate.

## 9. Denominator and weighting matrix

| Measure | Worker-based population | Work-hour-based population | Nonusers assigned zero in source construction |
| --- | ---: | ---: | ---: |
| Work adoption | yes | no | n/a |
| Use last week | yes | no | n/a |
| Daily work use | yes | no | n/a |
| AI-assisted work-hours share | no | yes | yes |
| Reported time-savings share | no | yes | yes |

These distinctions are part of the measurement definition and are tested in the analysis code.

## 10. Versioning

Public results are versioned with the source and analytical state used to create them. Depending on the artifact, this includes source identifiers, source vintage, crosswalk version, method version, checksums, and release identifier.

A revised source or method creates a new analytical version; published historical releases are not silently rewritten.
