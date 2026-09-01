# CPS 2025-Q2 composition execution

This checkpoint executes the project's occupation-composition contract on official Basic Monthly CPS public-use files for 2025-Q2. It exists to provide a same-vintage household-side comparison for May 2025 OEWS.

- in-scope person-month rows: **121,331**
- pooled weighted employed population age 18-64: **150,900,974**
- worker-share-supported industries: **20/20**
- minimum worker occupation-mapping coverage: **1.000000**
- fixed-width layout registry: `cps-basic-fixed-width-2025-v1`

Raw CPS files are downloaded into the workflow temporary directory and are not committed. Exact Census source URLs, SHA-256 hashes, file sizes, row counts, and retrieval timestamps are recorded in `input_manifest.json`.

This artifact validates composition inputs only. It does not join RPS observations, estimate a counterfactual, or establish an industry-context effect.
