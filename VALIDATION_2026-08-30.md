# Reconstruction validation — 2026-08-30

## Identity

This is a new private research reconstruction. It is not represented as the lost historical Phase-4 tree.

## Fresh checks executed

From the canonical private working tree immediately before release freeze:

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src pytest -q`: **58 passed**.
- `python -m compileall -q src scripts`: passed.
- `./scripts/validate_ts_structural.sh`: passed. This is a dependency-light strict structural TypeScript check using temporary declarations; it is not a Next.js production build.
- `git diff --check`: passed.
- longitudinal publication regeneration: `scripts/build_longitudinal.py` reproduces the four committed derived publication artifacts byte-for-byte from the private 630-cell fixture.
- genuine `npm install` / `next build`: **not verified**. The execution runtime cannot resolve `registry.npmjs.org`; no successful dependency installation or production build is claimed.

## Release 1 product-quality code pass

The current source tree includes a code-level product pass, regression-tested in `tests/test_web_release_quality.py`:

- persistent public/private release-mode disclosure;
- first-class Sources/Provenance route;
- skip-to-content and visible keyboard-focus handling;
- reduced-motion CSS;
- responsive Observable Plot redraw via `ResizeObserver`;
- HTML data-table equivalents for chart values;
- table captions and row/column scopes;
- source-registry-backed industry and occupation display names;
- explicit evidence-class and composition-status language;
- corrected public source-provenance documentation.

This is **not** represented as a completed browser, screen-reader, Lighthouse, or visual-regression audit. Those remain external release gates and are listed in `docs/RELEASE1_PRODUCT_QA.md`.

A fresh `npm install --ignore-scripts --no-audit --no-fund` attempt on 2026-08-30 again failed at npm-registry DNS resolution (`EAI_AGAIN`). No successful dependency installation or `next build` is claimed.

## Data/evidence gates

- private subgroup audit rows: **630**;
- private fixture SHA-256: `bdeffa95911a94cb60f904c51efc48f7ce4d1bf1eaaec490f5c4bfacd20d4fba`;
- canonical source metadata rows: **131** = 5 national + 60 industry + 66 occupation series;
- all 131 metadata records have canonical entity identities;
- longitudinal publication validator: **21/21 assertions pass**;
- Q2-2026 industry and occupation diagnostics are regression-tested against the private audited values;
- longitudinal rank-stability and leave-one-out results are generated from code, not copied into the website as a second manual statistics table.

The reproduced longitudinal conclusions are descriptive, aggregate, and non-causal:

- occupation adoption–assisted-hours Pearson and Spearman alignment exceeds industry alignment in all five audited waves;
- across occupations, adoption explains more cross-sectional variation in reported savings than assisted hours in all five waves and all **110/110** leave-one-occupation-out comparisons;
- across industries, `R²(S~H) > R²(S~A)` in **3 of 5** waves, so the Q2-2026 ordering is not treated as a stable law;
- adoption rankings are more persistent than assisted-hours and reported-savings rankings in **10/10** quarter-pair comparisons for both industries and occupations.

## CPS composition implementation

The canonical repository now contains an executable CPS composition and residual pipeline with dedicated tests. The implemented contracts include:

- corrected RPS industry crosswalk and one-to-one 22-group occupation crosswalk;
- four-implied-decimal CPS person weights;
- age 18–64 employed sample;
- employed-absent workers contribute zero actual main-job hours;
- invalid active-worker actual hours are not imputed;
- adoption composition uses worker shares;
- assisted-hours and reported-savings composition use actual main-job hour shares;
- usual hours are an explicitly labeled sensitivity only;
- equal month factors within supported three-month quarters;
- 2% fail-closed coverage gates;
- Q4 2025 explicitly unavailable, with no November–December substitution;
- suppressed composition values propagate as JSON `null`;
- the residual field is named `occupation_adjusted_industry_context_residual` and is not labeled causal or organizational.

**No real CPS composition or occupation-adjusted residual values have been generated in this runtime.** The official April–June 2026 CPS files remain inaccessible from the execution container, and the Census Microdata API requires an API key. Zero empirical CPS residual values are claimed.

## OEWS robustness gate

An external public May-2025 OEWS methodology and derived sensitivity artifact were inspected. The exact underlying staffing matrix is not distributed by that archive, so it was rejected as an empirical input to this project. No OEWS composition values are claimed from that source.

## Rights and publication boundary

- `data/audit/private/` is private research material and must not appear in a public release.
- `DATA_MODE=derived_only` is the rights-safe web mode and exposes derived longitudinal diagnostics without raw RPS observations.
- `DATA_MODE=audit_snapshot` is private research mode.
- `DATA_MODE=fred_live_no_store` remains fail-closed pending a reviewed rights-cleared production source.
- `scripts/export_rights_safe.py` constructs a tracked-file release export, excludes the private audit path, validates the boundary, and records source provenance.

## Remaining external gates

1. Obtain a rights-cleared direct RPS production feed or explicit permission.
2. Execute the CPS pipeline on the official April–June 2026 files in an environment that can access them.
3. Independently obtain May-2025 OEWS staffing data if that robustness analysis remains useful.
4. Run a genuine `npm install` and `next build` in a network-capable environment.
5. Complete browser-level accessibility/screen-reader validation, performance audit, genuine production build, and deployment audit before public launch.
