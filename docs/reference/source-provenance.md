# Source provenance and publication boundary

## RPS / FRED

Primary measurement family: Real-Time Population Survey Generative AI Adoption Tracker by Bick, Blandin, and Deming, surfaced through FRED series.

The canonical work-focused registry contains **131 source-series metadata records**:

- 5 national work-use constructs;
- 20 industries × 3 constructs = 60 industry records;
- 22 occupations × 3 constructs = 66 occupation records.

The private research candidate retains a reviewed five-wave subgroup fixture for reproducibility and regression testing. The rights-safe release **does not redistribute that raw audit fixture**. Its default `DATA_MODE=derived_only` exposes source metadata and derived longitudinal diagnostics only.

Production ingestion remains gated pending a fresh source-rights review and a rights-cleared direct feed or explicit permission. The repository does not silently fall back from a production source to private audit data. `fred_live_no_store` remains fail-closed in this candidate.

Do not imply endorsement by the Federal Reserve Bank of St. Louis. Preserve source attribution and source-series links. Re-check current FRED/API and third-party series terms before enabling any production adapter; do not treat a historical rights review as permanent.

## CPS

Source family: U.S. Census Bureau / Bureau of Labor Statistics Current Population Survey Basic Monthly public-use microdata.

Purpose: industry-by-occupation composition weights.

- adoption counterfactuals use worker shares;
- assisted-hours and reported-savings counterfactuals use actual main-job-hour shares;
- usual hours are a labeled sensitivity only;
- Q4 2025 remains unavailable because October 2025 CPS was not collected; no two-month substitute is allowed.

The composition pipeline is implemented and tested, but **no real CPS composition values or residuals are claimed in the current release candidate** because the required April–June 2026 input files have not been executed in the validated runtime.

## OEWS

May 2025 OEWS staffing data are reserved as a possible independent robustness basis for occupation composition. A third-party public repository with derived OEWS sensitivity outputs was inspected, but its exact staffing input was not distributed. Those derived outputs were therefore rejected as empirical inputs to this project.

## BTOS

Source family: U.S. Census Bureau Business Trends and Outlook Survey.

Potential future role: firm-side or sector-side triangulation. Firm-use, business-function breadth, and worker-task use must remain distinct constructs. A sector-level BTOS measure must not be mechanically joined to RPS worker outcomes and interpreted as a causal organizational effect.

## Release invariant

Every public claim must identify which evidence class it belongs to:

1. direct measurement;
2. derived descriptive statistic;
3. composition counterfactual;
4. causal/mechanism claim.

The current public candidate contains classes 1 only as source metadata and classes 2 as derived publication artifacts. Empirical class-3 CPS residuals and class-4 causal claims are not yet published.
