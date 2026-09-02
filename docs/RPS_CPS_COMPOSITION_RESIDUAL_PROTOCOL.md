# Snapshot-native RPS × CPS composition residual protocol

Status: **R1.1 live join implementation — derived evidence only; publication remains gated**

Date: 2026-09-02

## Purpose

This protocol closes the software gap between the rights-cleared RPS published-aggregate refresh pipeline and the already executed CPS occupation-composition evidence.

The source-side input is a validated private `rps_source_snapshot.json`. The join never reconstructs the retired 630-cell private fixture and never exports occupation-level source observations. `prepare_rps_panel` validates the complete 131-series RPS source contract and exposes the 126 industry/occupation A/H/S subgroup series only inside the process. The output is derived residual evidence.

## Estimand

For industry `j`, occupation `o`, period `t`, and metric `m`, the descriptive counterfactual is the occupation-weighted value implied by the corresponding occupation aggregates.

- adoption (`A` / `adoption_work`) uses CPS worker-share occupation weights;
- assisted work hours (`H` / `assisted_hours_share`) uses CPS actual main-job-hour-share occupation weights;
- reported time savings (`S` / `reported_time_savings_share`) uses CPS actual main-job-hour-share occupation weights.

The primary residual is:

`observed industry aggregate - occupation-composition counterfactual`

Its canonical label is **occupation-adjusted industry-context residual**.

This quantity is a descriptive standardization gap. It is not an identified organizational effect, organizational quality measure, efficiency effect, productivity effect, treatment effect, or causal parameter.

## Primary CPS periods

The live join uses the two CPS quarters for which the repository has completed official Basic Monthly composition packages under the current contract:

- `2025-Q2`;
- `2026-Q2`.

Q4 2025 remains unavailable because October 2025 CPS was not collected. November–December are not substituted for the missing month.

The RPS source snapshot must contain every requested CPS period. Missing source periods fail closed.

## Weighting boundary

`src/genai_at_work/composition.py` remains the canonical weighting implementation.

For adoption:

- basis: CPS worker share;
- coverage: mapped worker coverage;
- suppression follows worker coverage/support.

For H and S:

- primary basis: CPS actual main-job-hour share;
- employed-absent workers contribute zero actual main-job hours under the CPS pipeline contract;
- invalid active-worker actual hours are not imputed;
- coverage and suppression follow the actual-hour contract.

Worker weights are never reused for H/S.

## Usual-hours sensitivity

Usual hours are computed only as an explicitly labeled sensitivity for H and S.

A usual-hours cell that fails its coverage/support contract remains suppressed with null predicted/residual values. The pipeline does not silently renormalize an unsupported published cell.

## Composition-basis evidence tiers

The join binds `data/derived/composition/composition-evidence-v1/industry_evidence_tiers.json` to every residual row.

The current tiers summarize evidence about the **occupation-composition basis**, including CPS leave-one-month-out stability and OEWS comparability. They do not automatically establish that a residual is stable or publishable.

This distinction is retained explicitly in output field names such as `composition_basis_evidence_tier`.

## Residual-specific influence diagnostic

For every supported primary residual, the pipeline performs a leave-one-occupation-out sensitivity:

1. remove one positive-weight occupation from the industry composition;
2. renormalize the remaining weights to sum to one;
3. recompute the occupation-composition counterfactual;
4. recompute the residual;
5. record the largest absolute residual shift and the occupation responsible.

This renormalization is an explicit perturbation diagnostic. It is not silent missing-cell renormalization and is not a sampling-inference procedure.

The output labels the perturbation as:

`remove one positive-weight occupation and renormalize remaining weights to one`

## Cross-period persistence

For every A/H/S metric with two supported CPS/RPS periods, the pipeline computes descriptive residual persistence:

- Spearman rank correlation of industry residuals;
- sign agreement count/share;
- median absolute residual change.

Diagnostics are produced for:

- all supported industries;
- the `primary_stable` composition-basis cohort when the evidence-tier registry is supplied.

These are persistence diagnostics, not significance tests.

## Rights-safe outputs

`scripts/build_composition_residuals.py` consumes the private RPS snapshot but writes only derived evidence:

- `composition_residual_evidence.json`;
- `primary_residuals.json`;
- `usual_hours_sensitivity.json`;
- `leave_one_occupation_out_influence.json`;
- `cross_period_persistence.json`;
- `validation_checks.json`;
- `input_manifest.json`.

The input manifest records source scientific identity, exact private snapshot-file hash, canonical registry hashes, CPS composition input hashes, and evidence-tier hash. It explicitly records:

- `source_snapshot_published = false`;
- `public_raw_rps_observations_included = false`.

No occupation-level raw/source observation bundle is written.

## Validation contract

The join fails closed if:

- a requested CPS period is absent from the validated RPS panel;
- CPS composition does not contain exactly the 20 registered industries with indices 1–20;
- the evidence-tier registry and CPS industries disagree;
- a required occupation aggregate is absent;
- the expected primary/sensitivity row counts are not obtained;
- a suppressed primary row contains non-null predicted/residual values;
- `observed - predicted = residual` fails numerical identity;
- a supported leave-one-occupation-out perturbation cannot be constructed.

The current expected row counts for Q2 2025 + Q2 2026 are:

- primary residuals: `2 × 3 × 20 = 120`;
- usual-hours H/S sensitivity: `2 × 2 × 20 = 80`;
- primary leave-one-occupation-out influence summaries: `120`.

The number of persistence rows depends on available cross-period cohorts and is recorded explicitly.

## Live validation integration

`.github/workflows/rps-live-validation.yml` now executes the composition join after live source retrieval, private-vintage archive rehearsal, and RPS longitudinal candidate construction.

The live evidence artifact retains the derived composition outputs under `composition-residuals/`. It still excludes the RPS source snapshot, source detailed diff, and RPS release `inputs/` source objects.

A successful live workflow therefore demonstrates that the current source can feed the CPS composition analysis end-to-end without restoring a public/private raw-fixture dependency.

## Publication rule

Do not publish a one-quarter residual leaderboard.

Any future composition explorer must expose at minimum:

- period;
- metric;
- weighting basis;
- coverage;
- suppression status;
- composition-basis evidence tier;
- residual-specific influence context;
- cross-period persistence context;
- the descriptive/noncausal interpretation boundary.

A residual may be withheld even when its computation is valid if the robustness evidence is not strong enough for responsible display.

## What this protocol does not establish

It does not establish:

- design-based CPS confidence intervals for the custom 22-dimensional composition vectors;
- causal organizational effects;
- productivity effects;
- that every industry residual is stable;
- that the experimental composition explorer is ready for publication;
- rights for respondent microdata or the separate RPS task-index artifact.

Those gates remain independent.
