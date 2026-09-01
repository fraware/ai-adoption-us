# CPS 2026-Q2 composition execution - official-data checkpoint

## Status

This record documents execution of the occupation-composition **weighting layer** on official Basic Monthly CPS fixed-width public-use files for 2026-Q2.

It does **not** claim completed RPS occupation-composition counterfactuals or occupation-adjusted industry-context residuals. Those require a compatible authorized RPS occupation observation vintage, which is intentionally absent from the public repository.

## Execution identity

- source build commit: `604b8d32e516de4b958a859a61c7ab7c25c45f30`
- generated at: `2026-09-01T07:02:34.413942+00:00`
- in-scope CPS person-month rows: **117,687**
- pooled weighted civilian employed population age 18-64: **149,605,939**
- industry groups produced: **20**
- coverage gate: **98.0%**

## Source inputs

Official compressed fixed-width Basic CPS files were used for April, May, and June 2026. Exact source URLs, Census record-layout URL, SHA-256 checksums, file sizes, row counts, and the execution retrieval/validation timestamp are frozen in `data/derived/composition/cps-q2-2026/input_manifest.json`.

The live ingestion path is pinned to the official 2026 fixed-width record layout. The earlier assumption that the Census `.csv` distribution was a headered variable-name file was falsified by real-data execution and is not used as the authoritative production path.

## Population alignment

The RPS/CPS comparison target is the civilian employed population ages 18-64.

An independent fixed-width population audit was run before the composition transformation and committed as `data/derived/composition/cps-q2-2026/population_audit.json`.

For the pooled April-June files it verifies:

- raw person records read: **366,172**;
- employed age-18-64 person-month records with positive final weight: **117,687**;
- final civilian analysis person-month records: **117,687**;
- pooled civilian analysis weight: **149,605,939.1384**;
- Armed Forces industry exclusions in the in-scope employed sample: **0**;
- Armed Forces occupation records in the civilian-industry sample: **0**;
- unmapped civilian industry records: **0**;
- unmapped civilian occupation records: **0**;
- independently accumulated civilian weight matches the composition-pipeline weight within a `1e-4` absolute numerical tolerance; the observed difference is approximately `2.2e-6` workers.

This confirms that the composition output is not obtaining full coverage by silently dropping a material unmapped population.

## Weighting contract executed

- adoption composition basis: worker shares;
- assisted-hours/reported-savings composition basis: actual-main-job-hour shares;
- usual-main-job-hours: sensitivity only;
- equal one-third month factors across April, May, and June;
- employed-absent workers: zero actual hours under the existing implementation contract;
- invalid active-worker actual hours: not imputed;
- unsupported mapping/validity coverage: fail closed at the configured 98% gate.

## Primary validation summary

- worker-share-supported industries: **20/20**;
- actual-hour-supported industries: **20/20**;
- minimum worker occupation-mapping coverage: **1.000000**;
- minimum valid-worker coverage for actual hours: **1.000000**;
- minimum actual-hour occupation-mapping coverage: **1.000000**;
- all supported weight vectors sum to one;
- all weights are nonnegative;
- worker-share and actual-hour-share occupation compositions differ by more than `1e-6` L1 distance in **20/20** industries;
- median worker-share versus actual-hour-share L1 distance: **0.049687**.

The last result empirically validates the methodological rule that worker weights cannot simply be reused for assisted-hours or reported-savings composition.

## Usual-hours sensitivity result

The usual-hours specification is intentionally secondary. Under the precommitted 98% valid-worker gate, only **1/20** industries supports a usual-hours composition vector.

This is not an occupation-mapping failure: conditional on a valid usual-hours value, occupation mapping coverage is **100%**. The limiting object is the share of workers with a point-valued `PEHRUSL1`; official CPS coding permits `-4 = HOURS VARY`, so a nontrivial fraction of otherwise eligible workers does not have a point-valued usual-hours response.

Across industries, valid-worker coverage for usual hours ranges from approximately **88.2% to 98.1%**. The project therefore keeps the 98% gate and suppresses unsupported usual-hours point estimates. It does not lower the threshold or impute `HOURS VARY` responses merely to manufacture a complete sensitivity table.

A future robustness extension may use an explicitly justified partial-identification or bounded sensitivity design. That would be a new specification, not a relabeling of the current complete-case usual-hours analysis.

## Machine-readable evidence

The versioned execution package contains:

- `cps_composition.json` - worker, actual-hour, and supported usual-hour occupation shares by industry;
- `coverage.csv` - per-industry coverage and suppression state;
- `sensitivity.csv` - worker-versus-hour and actual-versus-usual composition diagnostics where supported;
- `validation_checks.json` - global execution and sanity checks;
- `population_audit.json` - independent civilian-population boundary audit;
- `input_manifest.json` - source identity, checksums, crosswalk versions, and execution provenance.

Raw CPS public-use input files are not committed to the repository.

## Scientific boundary and next gate

This checkpoint establishes that official CPS Q2-2026 occupation-composition weights are operational and scientifically supported under the primary worker-share and actual-main-job-hour-share specifications.

It does **not** establish an industry-context effect, an organizational effect, or a productivity effect. It does not yet generate empirical occupation-composition counterfactuals because the public repository has no authorized compatible RPS occupation-observation vintage.

The next empirical gate is to join these validated composition weights only to an authorized RPS occupation vintage and then run the prespecified residual robustness program: influence diagnostics, coverage sensitivity, temporal replication, and independent OEWS composition comparison where appropriate. Only after those tests can an occupation-adjusted industry-context residual be considered for publication.
