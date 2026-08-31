# Official CPS source check — 2026-08-31

## Purpose

This note records the official U.S. Census Bureau sources used in the final methodological review of the implemented CPS composition pipeline. It validates source-variable semantics and input availability only. It does **not** constitute execution of the April–June 2026 CPS composition analysis and does not create empirical composition results.

## Official sources

### Basic Monthly CPS 2026 public-use files

U.S. Census Bureau, **Basic Monthly CPS**:

https://www.census.gov/data/datasets/time-series/demo/cps/cps-basic.html

The 2026 section provides the annual data dictionary, industry/occupation code resources, and monthly public-use files, including April, May, and June 2026.

### Census Microdata API — CPS Basic Monthly

U.S. Census Bureau, **Current Population Survey (CPS) Basic Monthly**:

https://www.census.gov/data/developers/data-sets/census-microdata-api/cps/basic.html

The 2026 section exposes April, May, and June endpoints and variable catalogs. Census examples request `PEMLR`, `PWSSWGT`, and other person-level variables.

May 2026 example page:

https://api.census.gov/data/2026/cps/basic/may/examples.html

The examples include weighted tabulation using `PWSSWGT`.

### June 2026 variable catalog

U.S. Census Bureau Microdata Access variable catalog, **CPS Basic Monthly (2026 JUN)**:

https://data.census.gov/app/mdat/CPSBASIC202606/vars

The catalog identifies `PWSSWGT` as the second-stage/final-step weight and exposes the labor-force, industry, occupation, and hours variables used by the implementation.

## Implemented-variable contract reviewed

The final source-level audit reviewed the CPS implementation against the official variable definitions for:

- `PRTAGE` — age;
- `PREMPNOT` — employed/unemployed/not-in-labor-force recode; value `1` is employed;
- `PEMLR` — monthly labor-force status;
- `PWSSWGT` — final person/second-stage weight used by the project for worker and weighted-hour totals;
- `PRDTIND1` — detailed main-job industry recode;
- `PRDTOCC1` — detailed main-job occupation recode;
- `PEHRACT1` — hours actually worked at the main job;
- `PEHRUSL1` — usual hours at the main job.

## Project interpretation

The source review supports the current implementation contract:

- population restricted to employed adults aged 18–64;
- worker-share occupation weights for adoption composition;
- actual-main-job-hour-share occupation weights for assisted-hours and reported-savings composition;
- usual-hours weighting only as a separately labeled sensitivity;
- no substitution for Q4 2025, because October 2025 CPS collection was unavailable under the project’s quarter-availability contract.

## Boundary

This note verifies definitions and source availability. The project still claims:

- **zero** executed real Q2-2026 CPS composition estimates;
- **zero** empirical occupation-adjusted industry-context residuals;
- **zero** causal organizational or productivity effects.

Those claims may change only after the corresponding roadmap gates are executed and validated.
