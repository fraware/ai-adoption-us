# Architecture and trust boundaries

## 1. System objective

The system is both a research pipeline and a public data publication. The architecture must preserve a hard distinction between:

1. source metadata;
2. private research observations;
3. generated derived diagnostics;
4. public website artifacts;
5. future cross-survey composition outputs.

## 2. High-level architecture

```text
                        ┌──────────────────────┐
                        │ RPS / FRED metadata  │
                        └──────────┬───────────┘
                                   │ registry only in public repo
                                   ▼
                       data/registry/*.json|yaml
                                   │
                ┌──────────────────┴─────────────────┐
                │                                    │
                ▼                                    ▼
     PRIVATE RESEARCH ONLY                    PUBLIC RIGHTS-SAFE
 data/audit/private/...                     data/derived/longitudinal/
                │                                    │
                ▼                                    │
 scripts/build_longitudinal.py                       │
                │                                    │
                └──────────────► deterministic derived diagnostics
                                                     │
                                                     ▼
                                              apps/web/lib/
                                                     │
                                                     ▼
                                               Next.js routes
```

Future Release 1.1 adds:

```text
Official CPS monthly public-use files
             │
             ▼
  src/genai_at_work/cps.py
             │
             ▼
 industry × occupation worker/hour shares
             │
             ▼
 src/genai_at_work/composition.py
             │
             ▼
 occupation-composition counterfactuals
             │
             ▼
 occupation-adjusted industry-context residuals
```

## 3. Trust boundary: private RPS observations

`data/audit/private/` is the private research boundary.

Rules:

- never commit it to this public repository;
- never copy it under `apps/web/public/`;
- never include it in a static deployment artifact;
- `audit_snapshot` mode is for controlled research environments only;
- public releases are constructed by `scripts/export_rights_safe.py`;
- derived public statistics must be regenerated from private inputs and then reviewed for publication suitability.

## 4. Public release modes

### `derived_only`

The intended public Release 1 mode.

Loads only generated, rights-safe diagnostics. It cannot render raw subgroup observation tables because those inputs are absent.

### `audit_snapshot`

Private research mode.

Requires the private fixture. A public build without the fixture cannot silently fall back into this mode.

### `fred_live_no_store`

Reserved mode. It is intentionally fail-closed until source rights and production behavior are reviewed.

No code should turn this mode into a persistent cache without explicit rights approval.

## 5. Scientific module boundaries

### `rps_registry.py`

Canonical source-series identity and metadata. The registry cardinality contract is 131 work-focused series:

- 5 national;
- 60 industry;
- 66 occupation.

### `longitudinal.py`

Pure descriptive analysis over audited subgroup panels. It owns:

- cross-sectional regressions;
- Pearson/Spearman coupling;
- leave-one-out diagnostics;
- rank stability;
- cross-level comparisons.

### `cps.py`

CPS public-use parsing, crosswalk application, weighting, coverage, and quarter pooling.

Critical denominator contract:

- adoption counterfactual → worker shares;
- assisted-hours / reported-savings counterfactuals → actual-main-job-hour shares.

### `composition.py`

Consumes RPS occupation outcomes plus CPS industry×occupation composition weights and emits counterfactuals/residuals.

The residual is a mechanical standardization residual, never a causal organizational estimate.

## 6. Web architecture

The Next.js app consumes either:

- rights-safe derived longitudinal artifacts; or
- private audited observations in controlled research mode.

Routes:

- `/` — narrative overview;
- `/explore/industries`;
- `/explore/occupations`;
- `/methodology`;
- `/sources`;
- `/blog/after-adoption`.

Future route:

- `/explore/composition` after Release 1.1 empirical gates pass.

## 7. Generated-artifact contract

The following files are generated publication artifacts and must reproduce byte-for-byte from the private fixture:

- `data/derived/longitudinal/longitudinal_diagnostics.json`;
- `data/derived/longitudinal/quarter_diagnostics.csv`;
- `data/derived/longitudinal/rank_stability.csv`;
- `data/derived/longitudinal/validation_checks.json`.

Source-series manifests are metadata registries, not observation stores.

## 8. Fail-closed principles

The system must prefer an explicit missing state over a convenient fabricated value.

Examples:

- unsupported CPS quarter → unavailable;
- composition coverage breach → `null`;
- missing private fixture → audit tests skip/fail as designed, never fabricate;
- unavailable production source → `fred_live_no_store` remains disabled;
- raw-data rights uncertainty → no public raw-data export.
