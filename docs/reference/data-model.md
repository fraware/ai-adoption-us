# Canonical data model

## Design requirement

A chart must never infer the meaning of a value from its filename or column position. Construct, population, denominator, unit, source, and transformation status are explicit fields.

## 1. `entities`

One row per entity shown by the site.

| field | type | meaning |
|---|---|---|
| `entity_id` | string | stable internal identifier |
| `entity_type` | enum | `national`, `industry`, `occupation` |
| `name` | string | display label |
| `source_classification` | string/null | source classification label/code |
| `sort_key` | integer | stable display order |

## 2. `metrics`

One row per construct.

Required first-release metrics:

| metric_id | interpretation | denominator |
|---|---|---|
| `adoption_overall` | adults 18–64 using GenAI for any purpose | working-age adults |
| `adoption_work` | employed adults 18–64 who use GenAI for work | employed adults |
| `work_use_last_week` | employed adults who used GenAI for work in prior week | employed adults |
| `work_use_daily` | employed adults who used GenAI every workday in prior week | employed adults |
| `assisted_hours_share` | share of total work hours assisted by GenAI | total work hours |
| `reported_time_savings_share` | self-reported additional hours otherwise needed, as share of total work hours | total work hours |

Fields:

- `metric_id`
- `label`
- `unit`
- `denominator`
- `construct_type`: `direct_response`, `reconstructed`, `self_reported_counterfactual`, `derived`
- `zero_for_nonusers`: boolean/null
- `causal_interpretation_allowed`: always false for Release 1
- `productivity_measure`: boolean
- `definition`
- `caution`

## 3. `series_registry`

One row per source series.

Fields:

- `source` (`fred_rps`)
- `release_id` (`6` for the current RPS tracker release)
- `series_id`
- `title`
- `metric_id`
- `entity_id`
- `frequency`
- `unit`
- `seasonal_adjustment`
- `observation_start`
- `observation_end`
- `last_updated`
- `source_url`
- `citation_text`
- `copyright_status`
- `notes_hash`

`notes_hash` makes source-definition changes detectable even when a series ID remains unchanged.

## 4. `observations`

Canonical long-form table.

Primary key:

`(source, series_id, date, realtime_start, realtime_end)`

Publication key for latest-vintage views:

`(metric_id, entity_id, date)`

Fields:

- `source`
- `series_id`
- `metric_id`
- `entity_id`
- `entity_type`
- `date`
- `period` (for example `2026-Q2`)
- `value`
- `unit`
- `realtime_start`
- `realtime_end`
- `ingested_at_utc`
- `source_last_updated`
- `is_latest_vintage`

Store raw precision; round only in presentation.

## 5. `composition_weights`

This table is not used until Release 1.1.

Fields:

- `source` (`cps`)
- `period`
- `industry_id`
- `occupation_id`
- `weight_basis`: `workers` or `work_hours`
- `share`
- `sample_population`
- `weight_variable`
- `hours_variable` (null for worker weights)
- `crosswalk_version`
- `n_unweighted`

Important:

- Adoption counterfactuals use `weight_basis=workers`.
- Assisted-hours and time-savings counterfactuals use `weight_basis=work_hours`.

## 6. `derived_observations`

All derived values must declare their formula and inputs.

Fields:

- `derived_metric_id`
- `entity_id`
- `date`
- `value`
- `formula_version`
- `input_dataset_version`
- `status`: `production`, `experimental`, `deprecated`
- `interpretation`
- `caution`

Candidate derived metrics:

### `integration_residual`

For a quarter-specific descriptive regression across industries:

`H_jt - E_hat[H_jt | A_jt]`

Allowed UI label: **integration residual** or **assisted-hours residual**.

Disallowed labels: efficiency, productivity, organizational quality.

### `occupation_adjusted_adoption_gap`

`A_jt - sum_o w^workers_jot * A_ot`

Interpretation: composition-standardization residual only.

### `occupation_adjusted_assisted_hours_gap`

`H_jt - sum_o w^hours_jot * H_ot`

### partial-identification bounds

When occupation categories do not align one-to-one, publish a feasible interval rather than inserting arbitrary midpoint allocations.

## 7. Denominator matrix

| source metric | worker weighted | hour weighted | zero for nonusers |
|---|---:|---:|---:|
| work adoption | yes | no | n/a |
| last-week work use | yes | no | n/a |
| daily work use | yes | no | n/a |
| assisted-hours share | no | yes | yes |
| reported-time-savings share | no | yes | yes |

This matrix is a scientific invariant and should have automated tests.
