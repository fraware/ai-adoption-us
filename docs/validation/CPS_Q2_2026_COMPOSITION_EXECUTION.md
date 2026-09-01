# CPS 2026-Q2 composition execution - official-data checkpoint

## Status

This record documents execution of the occupation-composition **weighting layer** on official
Basic Monthly CPS fixed-width public-use files for 2026-Q2.

It does **not** claim completed RPS occupation-composition counterfactuals or
occupation-adjusted industry-context residuals. Those require a compatible authorized RPS
occupation observation vintage, which is intentionally absent from the public repository.

## Execution identity

- source build commit: `604b8d32e516de4b958a859a61c7ab7c25c45f30`
- generated at: `2026-09-01T07:02:34.413942+00:00`
- in-scope CPS person-month rows: **117,687**
- pooled weighted employed population age 18-64: **149,605,939**
- industry groups produced: **20**
- coverage gate: **98.0%**

## Source inputs

Official compressed fixed-width Basic CPS files were used. Exact source URLs, record-layout URL,
SHA-256 checksums, file sizes, row counts, and the execution retrieval/validation timestamp are
frozen in the adjacent `input_manifest.json`.

## Weighting contract executed

- adoption composition basis: worker shares;
- assisted-hours/reported-savings composition basis: actual-main-job-hour shares;
- usual-main-job-hours: sensitivity only;
- equal month factors within the quarter;
- employed-absent workers: zero actual hours under the existing implementation contract;
- invalid active-worker actual hours: not imputed;
- unsupported mapping/validity coverage: fail closed at the configured gate.

## Validation summary

- worker-share-supported industries: **20/20**
- actual-hour-supported industries: **20/20**
- usual-hour-supported industries: **1/20**
- minimum worker mapping coverage: **1.000000**
- minimum valid-worker coverage for actual hours: **1.000000**
- minimum actual-hour occupation mapping coverage: **1.000000**
- supported weight vectors sum to one: **True**
- all weights nonnegative: **True**
- industries with worker-share versus actual-hour-share L1 difference > 1e-6: **20**

The machine-readable per-industry coverage and actual-versus-usual-hours sensitivity diagnostics
are committed beside the composition artifact.

## Scientific boundary and next gate

This checkpoint establishes whether official CPS composition inputs and the weighting
implementation are operational on real data. It does not establish an industry-context effect
and it does not produce a productivity or causal claim.

The next step is to inspect suppression and coverage diagnostics and then join validated
composition weights only to an authorized compatible RPS occupation vintage. Only after that
join and the prespecified robustness suite can an occupation-adjusted industry-context residual
be considered for publication.
