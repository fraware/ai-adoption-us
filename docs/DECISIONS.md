# Key decisions and rejected shortcuts

This log records consequential choices so future engineers do not accidentally reintroduce previously rejected designs.

## 1. Public static FRED observation bundle — rejected

The early architecture wrote source observations into a public static JSON file. That path was retired.

Current rule: public Release 1 uses derived-only diagnostics; private audit observations remain private.

## 2. “Efficiency” terminology for S/H — rejected

`S/H` is not an efficiency measure. Reported savings are counterfactual self-reports and can exceed actively assisted time.

## 3. Industry residual = organizational effect — rejected

Occupation-adjusted residuals are standardization residuals. They do not identify organization-level causality.

## 4. Latest-quarter leaderboard as primary product — rejected

Five-wave stability analysis showed adoption rankings are much more persistent than assisted-hours rankings. The product must display trajectory/stability context.

## 5. Q2 industry H > A relationship as general law — rejected

The ordering changes across waves. It is a Q2 result and a 3-of-5-wave pattern, not a stable structural law.

## 6. Reusing worker-share composition weights for H/S — rejected

Adoption uses worker shares. H/S use actual-work-hour shares.

## 7. Q4 2025 CPS two-month substitute — rejected

October 2025 CPS was not collected. Under the predetermined three-month quarter design, Q4 2025 is unavailable.

## 8. External OEWS derived artifact as staffing input — rejected

An inspected public research archive published OEWS-derived sensitivities but not the underlying staffing matrix. Its derived outputs were not reverse-engineered into this project.

## 9. Composition blocking Release 1 — rejected

Release 1 is useful and scientifically coherent without cross-survey composition. Composition ships only after its own gates pass.

## 10. Single composite AI-readiness/productivity score — rejected

The product preserves adoption, routine use, assisted hours, and reported savings as separate constructs.
