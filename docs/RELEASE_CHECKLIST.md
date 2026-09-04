# Release checklist

Release 1 is launch-ready only when every release-time item below is resolved on the exact candidate/release identities. Historical QA and deployment records remain evidence about earlier repository states; they do not substitute for exact-head review, rehydration, promotion, or deployment evidence for the final release.

## A. Scientific integrity

- [x] Work adoption, routine/recent use, assisted working time, and reported time savings remain distinct constructs.
- [x] Reported time savings are not presented as measured labor productivity.
- [x] Occupation-adjusted industry-context residuals are presented as descriptive standardization residuals, not identified organizational or causal effects.
- [x] Current longitudinal public claims are synchronized to the seven-quarter Q4 2024–Q2 2026 common A/H/S evidence.
- [x] Current headline counts and relationships are derived from or reconciled against release artifacts rather than protected by five-wave prose literals.
- [x] Governed longitudinal/source claims are cryptographically bound to the exact public files that present them.
- [x] CPS composition, OEWS robustness, and BTOS–RPS triangulation retain their registered measurement/interpretation boundaries.
- [ ] Human scientific review completed against the exact final candidate-review package.

## B. Data rights and provenance

- [x] Public web mode is `DATA_MODE=derived_only`.
- [x] Private RPS candidate inputs are excluded from the public Git tree and promoted release artifacts.
- [x] The public RPS observation product is bounded to the contracted national history plus latest industry/occupation A/H/S views.
- [x] Historical subgroup database, unrestricted bulk mirror/download, generic source query API, respondent microdata, historical replication package, and separate task-index artifact remain outside the Release 1 authorization unless separately approved.
- [x] Current source-rights status and the evidence limitation are recorded in `docs/source-rights/RPS_SOURCE_DECISION.md`: published aggregate project use is treated as granted on the project owner's attestation; the underlying correspondence/agreement is not retained in the public repository or independently inspected in this code change.
- [x] Source attribution and source-series provenance are preserved.
- [ ] Human source-rights review completed against the exact final candidate-review package.

## C. Source and analytical candidate

- [x] Canonical RPS registry cardinality is 131 work-focused series: 5 national, 60 industry, 66 occupation.
- [x] Current live candidate evidence contains 962 registered source observations.
- [x] Common A/H/S subgroup panel contains 882 cells across seven quarters.
- [x] RPS component validates construct-specific source-history topology and requires complete A/H/S common-window coverage.
- [x] Bounded public observation artifact is built from the same RPS source vintage as the longitudinal diagnostics.
- [x] Repository RPS-dependent CPS/OEWS/BTOS evidence is explicitly bound to the candidate RPS vintage before global composition.
- [x] Global candidate contains the required RPS/CPS/OEWS/BTOS components and release diagnostics.
- [ ] Final global candidate rebuilt on canonical `main` after merge and staged with gate status `BLOCKED_REVIEW_REQUIRED` and zero contract failures.

## D. Public code and application validation

These gates must be evaluated on the exact final candidate commit; historical pass counts are not release evidence for a later head.

- [ ] Release candidate CI succeeds on the exact final candidate commit: public pytest suite, compileall, Ruff, strict mypy, governance/privacy scans, locked `npm ci`, TypeScript, optimized production build, private-build scan, production-server startup, and route smoke tests.
- [ ] Rendered browser/accessibility QA succeeds on the exact final candidate commit.
- [ ] Native macOS Safari QA succeeds on the exact final candidate commit.
- [ ] GitHub Pages static build/audit succeeds on the exact final candidate commit. The PR/main engineering build does not itself authorize deployment.

## E. Accessibility and product-quality scope

- [x] Skip-link/focus, reduced-motion, semantic landmarks, chart/table fallback, responsive containment, runtime resize, 404 behavior, and automated accessibility contracts are implemented.
- [x] Automated rendered QA covers the configured stable Chrome, Firefox, WebKit/mobile-proxy matrix and native macOS Safari workflow.
- **Out of Release 1 scope — not claimed as completed evidence:** physical iOS/Android device testing, full human screen-reader traversal, full human keyboard traversal beyond automated contracts, manual color-only-meaning review, and field Core Web Vitals.

## F. Exact staging and review identity

- [x] Staging binds the candidate manifest file SHA-256 and canonical digest, predecessor release-registry identity, release diff, review package, and gate status into one portable `stage_id`.
- [x] Candidate review package excludes private source inputs and contains an uncompleted human attestation template.
- [x] Review workflow cannot self-attest scientific/editorial/source-rights/CI completion or a future rehydration identity.
- [ ] Exact candidate-review workflow run selected and retained for the final candidate commit.
- [ ] Human editorial review completed against that exact candidate-review package.
- [ ] Human attestation lists the exact source/artifact/diagnostic/claim changes and exact final CI run IDs.

## G. Trusted exact rehydration

- [x] `scripts/rehydrate_observatory_v1_candidate.py` re-fetches RPS on the exact reviewed commit, checks the reviewed predecessor release state, and requires the same scientific source identity.
- [x] Rehydration rebuilds the RPS component, governed claim-surface hashes, vintage-bound global candidate, and immutable stage.
- [x] Rehydration requires byte-identical candidate-manifest identity and exact equality of the reviewed stage/diff/review/gate records.
- [x] A changed scientific source identity or any candidate/stage drift fails closed and requires renewed review.
- [x] Rehydration emits a rights-safe deterministic identity and no private source bytes.
- [ ] Phase-1 exact rehydration executed for the final reviewed candidate.
- [ ] Human attestation updated to bind the SHA-256 of that exact rehydration identity.
- [ ] Phase-2 promotion run repeats exact rehydration successfully before promotion.

## H. Promotion integrity

- [x] Canonical low-level promotion is fail-closed without the internal exact-rehydration capability.
- [x] Promotion independently verifies exact-commit CI evidence against the release CI policy.
- [x] Promoted release copies declared public artifacts only and retains no private candidate `inputs/`.
- [x] Promoted review record and registry entry retain exact rehydration traceability.
- [x] Post-promotion finalization is rollback-protected if rehydration sidecar/registry finalization fails.
- [ ] Explicit reviewed Release 1 promotion executed successfully.

## I. Publication-commit and deployment integrity

- [x] Public deployment is no longer a side effect of every `main` push.
- [x] The release authorization commit is constrained to the release registry plus one immutable `data/releases/<release-id>/` directory.
- [x] `scripts/validate_observatory_publication_commit.py` requires the authorization commit parent to be the exact reviewed candidate commit and verifies release/review/rehydration/artifact identities.
- [x] GitHub Pages deploy and live-audit jobs run only for a validated `Authorize Observatory release <release-id>` commit.
- [ ] Release-only authorization commit created and pushed after successful promotion.
- [ ] GitHub Pages deployment succeeds from that exact authorization commit.
- [ ] Live deployment audit succeeds and records the exact deployed commit/release identity.

## J. Final publication

- [x] Release notes document evidence, measurement boundaries, source-rights limits, hosting limits, and scientific limitations.
- [ ] Final public site manually inspected after the exact release deployment for catastrophic rendering/content errors.
- [ ] Formal GitHub Release/tag created only after the immutable Observatory release and live deployment audit are complete.

A checked implementation control means the control exists in code/tests. It does not mean its release-time execution has already occurred. Unchecked execution items must not be represented as completed in release notes, the public site, or external submission materials.
