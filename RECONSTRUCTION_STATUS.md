# Reconstruction status — 2026-08-30

This repository is a **new private research candidate**, reconstructed from the last executable Phase-1 source tree plus persisted later specifications, recoverable registries, and independently audited five-wave subgroup evidence. It is not represented as the lost historical Phase-4 repository.

## What is now executable

- Private five-wave RPS subgroup fixture: **630 reviewed cells** (20 industries + 22 occupations × adoption / assisted-hours / reported-savings × Q2 2025–Q2 2026).
- Canonical RPS metadata registry: **131 source series** = 5 national + 60 industry + 66 occupation.
- Deterministic longitudinal analysis and leave-one-out/rank-stability diagnostics.
- Byte-for-byte regeneration of the four committed longitudinal publication artifacts from the private fixture.
- Explicit rights-safe `derived_only` website mode alongside private `audit_snapshot` mode.
- Fail-closed source architecture; no public static FRED observation bundle.
- Reconstructed CPS worker/hour composition pipeline and occupation-adjusted residual engine with fail-closed suppression semantics.
- Reproducible rights-safe export script that excludes private audit material.

## Fresh local validation

- Python: **58/58 tests pass**.
- Python compilation: passes.
- Dependency-light strict TypeScript structural validation: passes.
- Git whitespace/hygiene check: passes.
- Genuine Next.js production build: **unverified** because npm registry DNS is unavailable in this runtime.

## Scientific boundary

The five-wave RPS findings are descriptive aggregate results. They do not identify organizational effects, productivity effects, or causal mechanisms. The CPS composition code is implemented, but **no real CPS composition values or residuals have been produced** because the official April–June 2026 input bytes are inaccessible in this runtime.

## Still open

- rights-cleared direct RPS production feed or explicit permission;
- execution of the CPS composition pipeline on official monthly microdata;
- optional May-2025 OEWS robustness run from independently obtained official staffing input;
- genuine Next.js dependency installation and `next build`;
- browser-level accessibility/screen-reader validation, performance audit, genuine production build, and deployment audit.

A code-level Release 1 product pass is complete: source/provenance navigation, explicit release-mode disclosure, responsive chart redraws, chart-data tables, keyboard focus treatment, reduced-motion handling, registry-backed entity names, methodology/evidence-class clarification, and editorial tightening. See `docs/RELEASE1_PRODUCT_QA.md`.
