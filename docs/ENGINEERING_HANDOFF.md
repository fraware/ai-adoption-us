# Engineering handoff — current implementation and acceptance contracts

Status date: **2026-09-04**

## 1. Mission

GenAI at Work is an empirical publication and data product for studying how generative AI moves from work adoption into routine use, AI-assisted working time, and reported counterfactual time savings in the United States.

Engineering changes must satisfy three simultaneous requirements:

1. **scientific integrity** — constructs, populations, periods, weighting rules, and interpretation boundaries remain explicit;
2. **rights safety** — private or unauthorized source material never leaks into public artifacts;
3. **release integrity** — public claims and artifacts are tied to an exact reviewed source/candidate/repository identity before promotion and deployment.

A green build alone does not authorize publication.

## 2. Non-negotiable scientific contracts

### RPS constructs

`A` — work adoption/use, an extensive-margin measure.

`H` — share of work hours during which GenAI was actively used, a workflow-penetration measure.

`S` — self-reported counterfactual hours saved as a share of work time.

`A`, `H`, and `S` are distinct measurement objects. `S` is not measured labor productivity. A ratio such as `S/H`, if used, is only a mechanical ratio of reported saved hours to actively assisted hours; it is not an efficiency estimator.

### Cross-sectional and longitudinal interpretation

Current correlations, rank relationships, regressions, residuals, and triangulation outputs are descriptive aggregate evidence unless a separate inferential or causal design states otherwise.

Do not use significance, treatment-effect, productivity, organizational-quality, or causal language without a methodology that supports those estimands.

### Composition weighting

- adoption counterfactuals use CPS worker-share composition;
- assisted-hours and reported-savings counterfactuals use CPS actual-main-job-hour shares;
- usual hours remain a labeled sensitivity, not the primary H/S weighting basis;
- OEWS is an independent establishment-side robustness source, not a replacement for the primary CPS worker-survey composition basis.

Unsupported or suppressed composition cells fail closed. Do not silently renormalize them into apparently complete estimates.

### Residual language

Canonical term: **occupation-adjusted industry-context residual**.

`observed industry value - occupation-composition counterfactual`

It is a descriptive standardization residual. It is not, by itself, an identified organizational effect, management-quality measure, efficiency measure, productivity effect, or causal mechanism.

## 3. Source and rights contracts

The public repository is rights-safe. Private RPS source-input bytes and respondent-level material are excluded from the public Git tree and public release bundle.

The current published-aggregate RPS source decision is recorded in `docs/source-rights/RPS_SOURCE_DECISION.md`. That scope does not automatically extend to respondent microdata, the separate task-index artifact, unrestricted bulk mirroring, a historical subgroup database, or a generic public raw-source API.

Any new source or source adapter must document provider/source identity, retrieval and vintage metadata, registered scope, revision behavior, storage/publication boundaries, redistribution terms, attribution requirements, and available uncertainty/methodology metadata. Credentials and private source paths must never enter public review packages or client artifacts.

## 4. Current verified evidence surface

The canonical RPS source registry contains **131 work-focused series**: 5 national, 60 industry, and 66 occupation series. The latest validated source evidence contains **962 registered observations**. The complete common A/H/S subgroup panel contains **882 cells** across seven quarters, Q4 2024–Q2 2026:

`(20 industries + 22 occupations) × 3 constructs × 7 quarters = 882`.

The bounded public RPS contract exposes national history plus the latest authorized industry/occupation A/H/S views. It does not expose the private source snapshot or an unrestricted historical subgroup mirror.

The current longitudinal layer includes cross-sectional A/H/S relationships, rank stability, regression diagnostics, and leave-one-group-out robustness. Exact values and interpretation limits live in `docs/RESULTS.md` and governed derived artifacts.

Official Basic Monthly CPS inputs have been executed for Q2 2025 and Q2 2026. The repository contains versioned worker-share and actual-main-job-hour composition outputs, coverage diagnostics, sensitivity analyses, reliability checks, and evidence-tier metadata. Q4 2025 composition is unavailable because October 2025 CPS data were not collected.

Official May 2025 OEWS staffing data provide an independent establishment-side robustness basis. The repository also contains preregistered descriptive BTOS–RPS triangulation; BTOS and RPS remain distinct measurement objects.

## 5. Current release architecture

### Candidate construction and staging

Release-sensitive changes build a complete Observatory candidate from canonical repository state and the authorized live RPS source. Source bytes are retrieved only into a private/external workspace and validated against the registered source contract.

The RPS component, bounded public observation view, longitudinal diagnostics, CPS/OEWS/BTOS evidence, and governed claim surfaces are composed into one candidate manifest. Governed empirical claims are bound to the exact public files that present them.

Staging creates immutable candidate/stage identities, a release diff, review package, and fail-closed publication gate. A clean changed candidate has gate status `BLOCKED_REVIEW_REQUIRED` with zero contract failures. The candidate-review workflow produces rights-safe review evidence and an uncompleted attestation template; it cannot authorize publication itself.

### Release 1 owner authorization

`data/registry/release1_owner_authorization.json` records a one-shot project-owner authorization for the first Observatory release. A separate human review step is not required. The authorization does not waive any machine-verifiable scientific, editorial, source-rights, CI, source-identity, rehydration, promotion, deployment, or live-audit gate.

The owner-authorized release operator may complete the release review only after:

- the exact candidate review package has zero contract failures;
- exact-candidate Release candidate CI succeeds;
- exact source rehydration reproduces the reviewed scientific source identity, candidate manifest, and stage identities.

The immutable review record binds the owner authorization ID and explicitly records `human_review_performed=false`.

### Exact rehydration and promotion

Promotion never trusts a stale source snapshot. `scripts/rehydrate_observatory_v1_candidate.py` re-fetches the authorized source on the exact candidate commit, verifies predecessor release state, requires the same scientific source identity, rebuilds the full candidate and stage, and requires exact equality with the reviewed identities.

Any source, repository-evidence, claim-surface, candidate, stage, or predecessor drift fails closed and requires a new candidate.

Canonical low-level promotion is unavailable without the exact-rehydration capability. Promotion verifies exact-commit CI independently, copies only declared public artifacts into a new immutable release directory, and atomically advances the append-only release registry.

### Publication commit, Pages deployment, and formal release

The release-only publication commit may change only:

- `data/registry/observatory_release_registry.json`;
- one new immutable `data/releases/<release-id>/` tree.

`scripts/validate_observatory_publication_commit.py` verifies the append-only transition, exact candidate parent, release/review/rehydration identities, artifact hashes, and—for the first release—the one-shot owner-authorization binding.

The owner-authorized operator pushes that validated commit to `main`, then explicitly dispatches `.github/workflows/pages.yml` with the exact publication SHA. Pages independently verifies that the SHA is the current `main` tip and a valid publication commit before deployment. The release is formally published as `v1.0.0` only after the Pages artifact audit, deployment, and live-origin audit all succeed.

The Release 1 authorization is inert after the first promoted release; later releases require a separate authorization decision.

## 6. FRED operational contract

FRED documents a maximum API rate of two requests per second. The production `FredClient` paces request starts below that ceiling using a monotonic clock.

All release-critical workflows that retrieve the authorized live FRED source share the concurrency group `authorized-rps-fred-source` with cancellation disabled. Candidate review, independent live validation, and exact rehydration/promotion must never execute simultaneous full-source retrievals inside this repository.

HTTP 429 and selected transient failures retain bounded retry/backoff and fail closed after exhaustion.

## 7. Permanent CI contract

`.github/workflows/ci.yml` is the permanent PR/main software and governance contract. It requires the public Python suite, compilation, Ruff, strict mypy, governance/privacy checks, locked Node installation, TypeScript, optimized `derived_only` build, private-data build-tree scan, production-server startup, public-route smoke tests, and Git whitespace validation.

Workflow dependencies remain pinned to immutable action commit SHAs. Do not weaken tests, typing, scans, dependency locking, or release checks to obtain a green result.

## 8. Browser, accessibility, and deployment evidence

Rendered QA and native Safari QA are separate from ordinary unit/build CI. Automated WebKit is not equivalent to native Safari/iOS, and automated accessibility checks are not equivalent to full human screen-reader review.

Release 1 claims only the evidence actually recorded by the applicable workflows. A final documentation/release-control-only change does not create a claim of new browser testing when application code is unchanged; any application/UI change must rerun the applicable rendered/native QA before publication.

Physical mobile-device testing, complete human assistive-technology traversal, and field Core Web Vitals remain outside the Release 1 evidence unless separately performed and recorded.

## 9. Contribution and review expectations

See `CONTRIBUTING.md` and `.github/pull_request_template.md`.

Every substantial pull request should state scientific/public-claim impact, source/rights impact, validation evidence, and release impact. Documentation that changes interpretation of an empirical result is treated as a scientific change for review purposes.

Historical validation and reconstruction records remain provenance and are explicitly labeled historical. Current operational truth lives in the README, `docs/ROADMAP.md`, `docs/RELEASE_CHECKLIST.md`, the release registry, and immutable release manifests.

## 10. Release definition of done

Release 1 is complete only when the durable contract in `docs/RELEASE_CHECKLIST.md` is satisfied on the exact final identities: clean candidate review package, exact-candidate CI, owner-authorized automated release review, exact rehydration, immutable promotion, validated release-only commit, exact-SHA Pages deployment/live audit, and formal `v1.0.0` creation. No separate human review or manual site-inspection gate is required for Release 1.
