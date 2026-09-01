# May 2025 OEWS vs Q2 2026 CPS composition robustness

## Status

This checkpoint compares **worker/employment-share occupation composition** across two independent source systems:

- May 2025 BLS Occupational Employment and Wage Statistics (OEWS), employer-side wage-and-salary employment estimates;
- Q2 2026 Basic Monthly CPS, household-side worker composition already validated by the project.

It does not compare OEWS employment shares with CPS actual-hour shares and does not generate any RPS adoption counterfactual or industry-context residual.

## Execution

- OEWS industries requested: **20**
- canonical civilian occupation groups: **22**
- BLS series requested: **460**
- BLS API requests: **19**
- missing/suppressed series: **16**
- OEWS industries meeting the 98% coverage gate: **20/20**
- primary-comparability industries with supported CPS and OEWS vectors: **11**

## Primary comparison contract

Agriculture is excluded from the primary summary because OEWS excludes most agricultural employment. Public Administration is excluded because the OEWS government aggregate is not definitionally identical to the CPS/RPS Public Administration group. Other Services is retained only as a limited-comparability diagnostic because OEWS excludes private households.

Across every industry, OEWS excludes self-employed workers while CPS includes the broader worker population under the project's current filter. The vintages also differ: May 2025 OEWS versus Q2 2026 CPS. The comparison is therefore a robustness test of occupational structure across independent sources and vintages, not a same-population replication.

## Primary diagnostics

- median L1 distance: **0.25325221201813486**
- median cosine similarity: **0.973706182811574**
- median Spearman rank correlation: **0.9491812535290797**
- same largest occupation group: **7/11** primary comparisons

These diagnostics should be interpreted together. They quantify agreement in the 22-dimensional occupation-composition vectors and do not by themselves determine whether any downstream RPS composition-adjusted residual is robust.

## Next gate

If the OEWS composition vectors pass coverage and show adequate structural agreement with CPS on the primary-comparability set, the future RPS occupation-standardization analysis should report CPS as the main household-side specification and OEWS as an independent employer-side worker-composition sensitivity. The RPS join remains blocked until a compatible authorized RPS occupation vintage is available.
