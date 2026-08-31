# Execution issue index

This file maps the open roadmap and governance gates to their GitHub execution issues. The issue tracker is operational; `docs/ROADMAP.md`, `docs/RELEASE_CHECKLIST.md`, and the validation records remain the normative methodological and release specifications.

## Release 1 launch gates

- **#2 — R1-G2: Browser, accessibility, responsive, and performance QA**  
  https://github.com/fraware/ai-adoption-us/issues/2
- **#3 — R1-G3: Rights-safe production deployment audit**  
  https://github.com/fraware/ai-adoption-us/issues/3

Release 1 engineering/build gate R1-G1 is complete. Public-launch language and a release tag remain blocked until #2 and #3 are complete.

## Data/source dependency

- **#4 — D-G1: Resolve direct RPS source rights and production feed**  
  https://github.com/fraware/ai-adoption-us/issues/4

The current public architecture remains `derived_only`; persistent raw FRED observation storage/export remains retired and `fred_live_no_store` remains fail-closed.

## Release 1.1 composition program

- **#5 — R1.1-G1: Execute official Q2 2026 CPS composition**  
  https://github.com/fraware/ai-adoption-us/issues/5
- **#6 — R1.1-G2: Composition robustness and persistence**  
  https://github.com/fraware/ai-adoption-us/issues/6
- **#7 — R1.1-G3: May 2025 OEWS independent composition robustness**  
  https://github.com/fraware/ai-adoption-us/issues/7
- **#8 — R1.1-G4: Experimental composition explorer**  
  https://github.com/fraware/ai-adoption-us/issues/8

Issue #8 is downstream of validated outputs from #5 and #6. No empirical composition residual is publishable merely because the UI exists.

## Later triangulation and mechanism research

- **#9 — R1.2: BTOS firm-side triangulation with construct alignment**  
  https://github.com/fraware/ai-adoption-us/issues/9
- **#10 — V2: Worker × occupation × industry × time mechanism research**  
  https://github.com/fraware/ai-adoption-us/issues/10

## Observatory and reproducibility infrastructure

- **#11 — Observatory: Versioned new-wave update and release pipeline**  
  https://github.com/fraware/ai-adoption-us/issues/11
- **#12 — Governance: Private fixture revision and longitudinal regeneration gate**  
  https://github.com/fraware/ai-adoption-us/issues/12

## Non-negotiable dependency rules

- R1-G2 and R1-G3 block public launch, but CPS/OEWS research does not block Release 1 engineering completion.
- Direct RPS rights/feed resolution runs in parallel; current public source behavior remains fail-closed until it is resolved.
- CPS adoption composition uses worker shares; assisted-hours and reported-savings composition use actual-main-job-hour shares.
- Unsupported composition cells fail closed.
- Composition residuals remain descriptive standardization gaps unless a separate identification strategy supports stronger claims.
- Private RPS audit observations never enter the public repository, build, or deployment artifact.
