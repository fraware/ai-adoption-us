# Source provenance and publication boundary

## RPS / FRED

Primary measurement family: Real-Time Population Survey Generative AI Adoption Tracker by Bick, Blandin, and Deming, surfaced through FRED series.

The canonical work-focused registry contains **131 source-series metadata records**:

- 5 national work-use constructs;
- 20 industries × 3 constructs = 60 industry records;
- 22 occupations × 3 constructs = 66 occupation records.

The authorized release pipeline retrieves the registered published aggregate series through the official FRED API into a private candidate workspace. The latest verified live candidate binds 962 source observations across the available registered history. The complete common A/H/S subgroup analytical window contains 882 cells across seven quarters, Q4 2024–Q2 2026.

The public `derived_only` release boundary is narrower than the private source candidate. It permits the contracted attributed aggregate presentation view—seven-quarter national history plus the latest complete Q2 2026 industry and occupation A/H/S cross-sections—and derived publication artifacts. It does not authorize or publish the complete historical subgroup source panel as a public database, bulk download, generic query API, or private source-input bundle.

The repository does not silently fall back from the authorized source path to private audit data. Source-input files are hash-bound inside private release candidates and excluded from rights-safe review and promoted public bundles.

Do not imply endorsement by the Federal Reserve Bank of St. Louis. Preserve source attribution and source-series links. Rights and source terms remain versioned release inputs: a material definition, distribution, or rights change must fail closed and trigger renewed review.

## CPS

Source family: U.S. Census Bureau / Bureau of Labor Statistics Current Population Survey Basic Monthly public-use microdata.

Purpose: industry-by-occupation composition weights.

- adoption counterfactuals use worker shares;
- assisted-hours and reported-savings counterfactuals use actual main-job-hour shares;
- usual hours are a labeled sensitivity only;
- Q4 2025 remains unavailable because October 2025 CPS was not collected; no two-month substitute is allowed.

Official Q2 2025 and Q2 2026 Basic Monthly CPS inputs have been executed through the validated composition pipeline. The public repository contains versioned composition and reliability artifacts for both quarters, including worker-share and actual-main-job-hour occupation weights, coverage/suppression diagnostics, and sensitivity evidence.

The global Observatory v1 candidate also includes occupation-adjusted RPS industry-context residual artifacts produced from the authorized RPS source vintage and the validated CPS composition inputs. These residuals remain **derived descriptive diagnostics**. They do not identify organizational quality, management effects, efficiency, productivity, or any causal mechanism. Design-based confidence intervals for the custom pooled CPS composition vectors remain unsupported unless a separately approved survey-covariance method is implemented.

## OEWS

Source family: U.S. Bureau of Labor Statistics Occupational Employment and Wage Statistics.

Official May 2025 staffing data have been executed as an independent establishment-side robustness basis for occupation composition. The public repository contains versioned May 2025 OEWS composition outputs plus cross-vintage/coverage robustness artifacts, and the Observatory v1 candidate binds those reviewed artifacts into the same global release.

OEWS does not reproduce the CPS/RPS worker-survey universe: it is establishment and wage-and-salary-worker oriented, with materially different coverage, including treatment of self-employment. It therefore remains robustness evidence rather than the primary composition basis. OEWS composition persistence or disagreement must be reported directly; OEWS weights do not identify organizational effects or productivity effects.

## BTOS

Source family: U.S. Census Bureau Business Trends and Outlook Survey.

The Observatory v1 industry evidence includes the preregistered Q2 2026 BTOS–RPS descriptive triangulation. BTOS measures responding employer businesses reporting AI use in any business function during the last two weeks. RPS measures employed adults reporting Generative AI use for their jobs. Their units, denominators, technology scope, and reference periods differ.

The primary comparison therefore reports cross-sector concordance only. It does not treat the two percentages as interchangeable, compute an identity-line gap, or infer productivity, organizational quality, or a causal effect from their correlation. Suppressed BTOS sectors are not reconstructed or redistributed.

## Release invariant

Every public claim must identify which evidence class it belongs to:

1. direct source construct or contracted aggregate presentation view;
2. derived descriptive statistic;
3. composition evidence/counterfactual or cross-source descriptive triangulation;
4. causal/mechanism claim.

The Observatory v1 candidate contains bounded class-1 RPS aggregate presentation evidence, class-2 longitudinal RPS diagnostics, and class-3 CPS/OEWS composition plus BTOS–RPS triangulation evidence. It contains no class-4 causal claim. Any future widening of the source, query, redistribution, uncertainty, or causal boundary requires an explicit new release contract and review.
