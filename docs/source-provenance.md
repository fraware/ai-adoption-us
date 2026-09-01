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

Official Q2 2025 and Q2 2026 Basic Monthly CPS inputs have been executed through the validated composition pipeline. The public repository contains versioned composition and reliability artifacts for both quarters, including worker-share and actual-main-job-hour occupation weights, coverage/suppression diagnostics, and sensitivity evidence.

These CPS artifacts are **composition inputs and diagnostics**. They do not by themselves produce an occupation-adjusted RPS industry-context residual. That observed-versus-counterfactual join remains fail-closed until compatible RPS observations are available through a rights-cleared publication path and the residual robustness gate is rerun.

## OEWS

Source family: U.S. Bureau of Labor Statistics Occupational Employment and Wage Statistics.

Official May 2025 staffing data have been executed as an independent establishment-side robustness basis for occupation composition. The public repository contains versioned May 2025 OEWS composition outputs plus cross-vintage/coverage robustness artifacts.

OEWS does not reproduce the CPS/RPS worker-survey universe: it is establishment and wage-and-salary-worker oriented, with materially different coverage, including treatment of self-employment. It therefore remains robustness evidence rather than the primary composition basis. OEWS composition persistence or disagreement must be reported directly; OEWS weights do not identify organizational effects or productivity effects.

## BTOS

Source family: U.S. Census Bureau Business Trends and Outlook Survey.

Potential future role: firm-side or sector-side triangulation. Firm-use, business-function breadth, and worker-task use must remain distinct constructs. A sector-level BTOS measure must not be mechanically joined to RPS worker outcomes and interpreted as a causal organizational effect.

## Release invariant

Every public claim must identify which evidence class it belongs to:

1. direct measurement;
2. derived descriptive statistic;
3. composition evidence/counterfactual;
4. causal/mechanism claim.

The current public candidate contains class-1 RPS evidence only as source metadata and class-2 RPS evidence as derived longitudinal publication artifacts. It also contains rights-safe class-3 **composition-input and robustness evidence** from CPS/OEWS. It does **not** yet publish the RPS-dependent occupation-adjusted industry residual or any class-4 causal claim.
