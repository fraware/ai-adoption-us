# CPS composition execution status — 2026-08-30

## Scientific contract

The Q2 2026 composition target uses the April, May, and June 2026 Basic Monthly CPS public-use files with equal month factors.

- Adoption counterfactuals use worker-share weights.
- Assisted-hours and reported-savings counterfactuals use actual main-job-hour weights.
- Usual main-job hours are retained only as an explicitly labeled sensitivity.
- The 18–64 employed population is selected with `PRTAGE` and `PREMPNOT`.
- `PWSSWGT` is decoded using four implied decimal places.
- Employed-absent respondents (`PEMLR=2`) receive zero actual main-job hours.
- Invalid active-worker `PEHRACT1` values are not imputed.
- `PEHRUSL1=-4` (hours vary) is not silently imputed.
- Coverage below 98% suppresses the relevant composition weights.
- Q4 2025 is unavailable because October 2025 CPS interviewing was not conducted; no two-month substitution is permitted.

These rules are implemented in `src/genai_at_work/cps.py` and tested with synthetic fixtures.

## Corrected crosswalk

The production industry crosswalk is `data/registry/cps_industry_crosswalk_v2.json`.

The corrected RPS ordering is:

- IND3 Construction
- IND4 Manufacturing
- IND5 Wholesale Trade
- IND6 Retail Trade
- IND7 Transportation and Warehousing
- IND8 Utilities

Civilian `PRDTIND1` codes 1–51 are assigned exactly once. `PRDTOCC1` codes 1–22 map one-to-one to the RPS occupation groups; Armed Forces is excluded.

## Official Q2 2026 inputs

The Census 2026 Basic Monthly CPS page lists the required public-use files. The direct CSV endpoints are:

- `https://www2.census.gov/programs-surveys/cps/datasets/2026/basic/apr26pub.csv`
- `https://www2.census.gov/programs-surveys/cps/datasets/2026/basic/may26pub.csv`
- `https://www2.census.gov/programs-surveys/cps/datasets/2026/basic/jun26pub.csv`

The same page also provides compressed `.dat.gz` variants.

## Current infrastructure block

In the current execution container, DNS resolution for `www2.census.gov` fails. Direct container download therefore cannot obtain the three official files. The Census Microdata API is not used as a substitute because, as of August 2026, data queries require an API key and no key is available in this runtime.

As a result:

- no Q2 2026 CPS composition estimates have been generated;
- no occupation-adjusted industry residuals from real CPS data have been generated;
- no synthetic or proxy composition matrix is substituted.

## Execution once the files are available

```bash
PYTHONPATH=src python scripts/build_cps_composition.py \
  --year 2026 \
  --quarter 2 \
  --input-dir /path/to/cps \
  --output data/audit/derived/cps_composition_2026_Q2.json

PYTHONPATH=src python scripts/build_composition_residuals.py \
  --composition data/audit/derived/cps_composition_2026_Q2.json \
  --rps-private-fixture data/audit/private/rps_subgroup_5q_audit.json \
  --period 2026-Q2 \
  --output data/audit/derived/composition_residuals_2026_Q2.json
```

Both outputs remain research artifacts until source rights, coverage diagnostics, and interpretation are reviewed.
