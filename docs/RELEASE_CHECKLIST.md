# Release 1 publication contract

This document defines the gates for the first public Observatory release. It is deliberately durable: current publication status must be read from `data/registry/observatory_release_registry.json`, the validated release-only commit, the Pages deployment audit, and the formal GitHub tag/release. Checkboxes in prose are not used as a substitute for those machine-verifiable identities.

The project owner authorized the one-shot Release 1 publication sequence in `data/registry/release1_owner_authorization.json`. A separate human review step is not required. The authorization does not waive any scientific, rights, provenance, CI, source-identity, rehydration, promotion, deployment, or live-audit gate.

## A. Scientific integrity

Release 1 must preserve all of the following:

- work adoption, routine/recent use, assisted working time, and reported time savings remain distinct constructs;
- reported time savings are not presented as measured labor productivity;
- occupation-adjusted industry-context residuals remain descriptive standardization residuals, not identified organizational or causal effects;
- longitudinal claims remain synchronized to the seven-quarter Q4 2024–Q2 2026 common A/H/S evidence;
- governed longitudinal/source claims remain cryptographically bound to the exact public files that present them;
- CPS composition, OEWS robustness, and BTOS–RPS triangulation retain their registered measurement and interpretation boundaries.

The candidate builder, release diagnostics, claim-surface bindings, publication consistency tests, and owner-authorized release review collectively enforce this gate.

## B. Data rights and provenance

The public release must remain `DATA_MODE=derived_only`. Private RPS candidate inputs cannot enter the public Git tree, candidate-review package, promoted release, Pages artifact, or client build.

The public RPS observation product is bounded to the contracted national history plus latest industry/occupation A/H/S views. Historical subgroup databases, unrestricted bulk mirrors/downloads, generic source query APIs, respondent microdata, historical replication packages, and the separate task-index artifact remain outside the Release 1 authorization unless separately approved.

The source-rights basis and its evidentiary limitation remain recorded in `docs/source-rights/RPS_SOURCE_DECISION.md`. Attribution and source-series provenance must remain intact.

## C. Exact source and analytical candidate

A publishable Release 1 candidate must establish all of the following on canonical `main`:

- 131 registered work-focused RPS series: 5 national, 60 industry, 66 occupation;
- 962 observations in the currently verified registered source history, subject to fail-closed revision detection;
- 882 complete common A/H/S subgroup cells across seven quarters;
- construct-specific source-history topology and complete A/H/S common-window coverage;
- a bounded public observation artifact built from the same RPS source vintage as the longitudinal diagnostics;
- exact vintage bindings for RPS-dependent CPS/OEWS/BTOS evidence;
- all required RPS/CPS/OEWS/BTOS components and release diagnostics;
- immutable staging with gate status `BLOCKED_REVIEW_REQUIRED` and zero contract failures.

Any source revision, definition drift, coverage failure, diagnostic failure, rights change, claim-surface change, or release-registry advance must fail closed or force a new candidate.

## D. Code, product, and QA evidence

The exact final candidate commit must pass permanent Release candidate CI: public pytest, compileall, Ruff, strict mypy, governance/privacy scans, locked `npm ci`, TypeScript, optimized production build, private-build scan, production-server startup, and route smoke tests.

Rendered Chrome/Firefox/WebKit/mobile-proxy and native macOS Safari QA are retained as launch-quality evidence for the applicable final web state. A documentation/release-control-only final commit does not manufacture a claim of new browser testing when application code is unchanged. Any final application/UI change must rerun the applicable rendered/native QA before publication.

The GitHub Pages static artifact must build and audit successfully for the release-only authorization commit before deployment.

Physical iOS/Android testing, full human screen-reader traversal, full human keyboard traversal beyond automated contracts, manual color-only-meaning review, and field Core Web Vitals are outside the Release 1 evidence scope and are not claimed as completed.

## E. Owner-authorized exact review identity

Candidate review must produce one rights-safe package bound to the exact candidate commit and workflow run. The package must contain the sanitized candidate manifest, exact artifact hashes, stage identity, release diff, review package, publication gate, and an initially uncompleted attestation template. It must contain no private source inputs or source `local_path` values.

The Release 1 owner-authorized operator may complete scientific, editorial, source-rights, and CI review fields only after:

- the candidate gate has zero failures;
- exact candidate Release candidate CI is successful;
- the candidate review package is bound to the same commit/run;
- exact post-review source rehydration reproduces the reviewed scientific source identity, candidate manifest, and stage records.

The completed attestation records `review_mode=owner_authorized_automated_release_review`, the one-shot owner authorization ID, and `human_review_performed=false`. It is bound to the deterministic rehydration-identity SHA-256.

## F. Trusted exact rehydration

`scripts/rehydrate_observatory_v1_candidate.py` must re-fetch RPS on the exact reviewed candidate commit, verify the recorded predecessor release state, require the same scientific source identity, rebuild claim-surface hashes and the full global candidate, and reproduce the reviewed candidate/stage identities exactly.

A changed scientific source identity, repository evidence change, governed claim-file change, registry advance, candidate drift, or stage drift blocks promotion and requires a new candidate.

The rehydration identity is rights-safe and contains no private source bytes.

## G. Promotion integrity

Canonical low-level promotion remains disabled without the exact-rehydration capability. Promotion independently verifies the exact-commit CI evidence against `data/registry/observatory_release_ci_policy.json`.

A successful promotion may publish only declared public artifacts, must retain exact rehydration traceability, and must atomically advance the release registry. The resulting release-only Git commit may change only:

- `data/registry/observatory_release_registry.json`;
- one new immutable `data/releases/<release-id>/` tree.

`scripts/validate_observatory_publication_commit.py` must validate this append-only transition and require its parent to be the exact candidate commit.

## H. Deployment and live-origin audit

Ordinary `main` pushes may build Pages artifacts for QA but may not deploy the public Observatory release. Deployment is allowed only for a validated `Authorize Observatory release <release-id>` commit.

The release workflow must require all three Pages jobs to succeed for that exact commit:

- build and audit the GitHub Pages artifact;
- deploy GitHub Pages;
- audit the deployed Release 1 origin.

The live audit must bind the deployed site to the exact publication commit/release identity and retain the repository's rights/privacy boundaries.

## I. Formal publication

The one-shot owner-authorized Release 1 workflow may create the formal `v1.0.0` GitHub Release only after the immutable Observatory release has been promoted and the exact Pages deployment/live-origin audit has succeeded.

The workflow refuses to overwrite an existing `v1.0.0` release. The GitHub Release targets the validated publication commit and uses `docs/RELEASE1_NOTES.md` as the canonical notes body with the actual publication date stamped at release time.

After the first Observatory release is promoted, `release1_owner_authorization.json` is inert by contract; later releases require a separately authorized release decision.
