# Handoff index

This file is the navigation aid for engineers/researchers taking over the project.

## Read in this order

1. `README.md` — project state, product identity, and invariants.
2. `VALIDATION_2026-08-31.md` — current public-handoff/networked validation record.
3. `docs/RESULTS.md` — what the empirical evidence currently supports.
4. `docs/ENGINEERING_HANDOFF.md` — implementation and review contracts.
5. `docs/ROADMAP.md` — remaining gates and detailed specifications.
6. `docs/ARCHITECTURE.md` — data/product trust boundaries.
7. `docs/methodology.md` — scientific definitions and denominators.
8. `docs/source-provenance.md` — provenance and rights.
9. `docs/REPRODUCIBILITY.md` — public/private reproducibility tiers.
10. `docs/RELEASE_CHECKLIST.md` — launch criteria and current gate status.
11. `docs/RELEASE1_PRODUCT_QA.md` — code/build QA versus rendered QA boundary.
12. `docs/DECISIONS.md` — rejected shortcuts that must stay rejected.
13. `VALIDATION_2026-08-30.md` — historical private reconstruction validation record.

## Current status by subsystem

| Subsystem | Status |
|---|---|
| Reconstruction identity | New research reconstruction; not represented as lost historical Phase-4 tree |
| RPS source registry | Implemented / validated metadata; 131 series |
| Five-wave private audit | Completed privately; 630 reviewed cells; raw fixture excluded publicly |
| Longitudinal diagnostics | Implemented / generated / deterministic |
| Industry explorer | Implemented |
| Occupation explorer | Implemented |
| Methodology and Sources pages | Implemented |
| Rights-safe public data mode | Implemented; `derived_only` |
| Public Python validation | 52 passed / 6 expected private-fixture skips in networked run 33411128343 |
| Private Python validation | 58 passed in frozen 2026-08-30 private reconstruction run |
| Ruff / compileall | Passed on networked public handoff |
| Genuine Next.js production build | **Passed** on 2026-08-31, Next.js 16.3.3 |
| Permanent PR CI | **Passed**; R1-G1 engineering gate complete on run 33414088473; later documentation-only head also green in 33414442837 |
| Strict mypy / locked `npm ci` / server smoke | **Passed** in permanent PR CI run 33414088473; remain enforced on every PR head |
| Browser/screen-reader audit | Outstanding |
| axe/Lighthouse/performance audit | Outstanding |
| Production deployment audit | Outstanding |
| CPS parser/composition code | Implemented / synthetic- and unit-tested |
| Real CPS Q2 2026 execution | Outstanding due official-input execution dependency |
| Composition residuals | Code implemented; **zero empirical residuals claimed** |
| May-2025 OEWS robustness | Outstanding from official BLS staffing input |
| Direct RPS rights/feed | Outstanding external action |
| BTOS triangulation | Future Release 1.2 |
| Mechanism research | Future v2 |

## Immediate takeover sequence

1. Keep permanent PR CI green on every exact head presented for merge; R1-G1 itself is complete.
2. Do not modify empirical claims merely to solve CI or presentation issues.
3. Execute R1-G2 browser/accessibility/performance QA and commit dated evidence.
4. Execute R1-G3 deployment audit before any public-launch claim.
5. Run D-G1 source-rights outreach in parallel.
6. Execute CPS composition only when official inputs are available and validated; do not let Release 1.1 block Release 1.

## Non-negotiable boundaries

- Adoption is not workflow penetration.
- Assisted hours are not hours saved.
- Reported savings are not measured productivity.
- Current correlations/regressions are descriptive and aggregate.
- An occupation-adjusted industry-context residual is not automatically an organizational effect.
- Adoption composition uses worker shares; assisted-hours and savings composition use actual-main-job-hour shares.
- Unsupported composition cells fail closed.
- Private RPS audit observations never enter a public repository/build/deployment artifact.
