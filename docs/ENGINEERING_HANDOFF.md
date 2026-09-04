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

The residual is:

`observed industry value - occupation-composition counterfactual`

It is a descriptive standardization residual. It is not, by itself, an identified organizational effect, management-quality measure, efficiency measure, productivity effect, or causal mechanism.

## 3. Source and rights contracts

The public repository is rights-safe. Private RPS source-input bytes and respondent-level material are excluded from the public Git tree and public release bundle.

The current published-aggregate RPS source decision is recorded in `docs/source-rights/RPS_SOURCE_DECISION.md`. That reviewed scope does not automatically extend to respondent microdata, the separate task-index artifact, unrestricted bulk mirroring, a historical subgroup database, or a generic public raw-source API.

Public availability of a source is not sufficient evidence of redistribution permission.

Any new source or source adapter must document:

- provider and canonical source identity;
- retrieval time and source/release vintage;
- registered series/entity inventory;
- revision behavior and missing/schema-change handling;
- storage/cache and public-output boundaries;
- redistribution permission and attribution/disclaimer requirements;
- available uncertainty or methodology metadata.

Credentials, private source paths, and private source-input bytes must never appear in public review packages or client artifacts.

## 4. Current verified evidence surface

### RPS

The current source registry contains **131 work-focused series**: 5 national, 60 industry, and 66 occupation series.

The latest validated live candidate evidence contains **962 registered source observations** across the available source history. The complete common A/H/S subgroup panel contains **882 cells** across seven quarters, Q4 2024–Q2 2026:

`(20 industries + 22 occupations) × 3 constructs × 7 quarters = 882`.

The bounded public RPS observation contract exposes national history plus the latest authorized industry/occupation A/H/S views. It does not expose the private source snapshot or an unrestricted historical subgroup mirror.

### Longitudinal diagnostics

The current longitudinal result layer is synchronized to all seven common quarters. It includes cross-sectional A/H/S relationships, rank stability, regression diagnostics, and leave-one-group-out robustness.

The current descriptive headline result is that adoption and assisted-hours are more tightly aligned across occupations than industries over the common seven-quarter window, while occupation-level reported savings are more consistently aligned with adoption than assisted hours. Industry-level ordering varies by quarter. Exact values and interpretation limits live in `docs/RESULTS.md` and governed derived artifacts.

### CPS composition

Official Basic Monthly CPS inputs have been executed for Q2 2025 and Q2 2026. The repository contains versioned worker-share and actual-main-job-hour composition outputs, coverage diagnostics, sensitivity analyses, reliability checks, and evidence-tier metadata.

The Q4 2025 composition quarter is unavailable because October 2025 CPS data were not collected. Do not construct a synthetic full quarter from November–December records.

Custom pooled CPS composition vectors do not currently have a supported full design-based covariance model. Kish weight-dispersion measures, month-to-quarter movement, leave-one-month-out sensitivity, and cross-vintage stability are descriptive quality diagnostics, not design-based standard errors.

### OEWS robustness

Official May 2025 OEWS staffing data are used as an independent establishment-side composition robustness source. Coverage/population differences from CPS and RPS remain explicit, including partial-identification handling for unsupported cells.

### BTOS–RPS triangulation

The repository contains preregistered descriptive firm-side/worker-side triangulation. BTOS and RPS constructs remain distinct; cross-source agreement or disagreement is interpreted as triangulation across measurement objects, not as interchangeable measures.

## 5. Current release architecture

### Candidate construction

Release-sensitive changes build a complete Observatory candidate from canonical repository state and the authorized live RPS source. The source is retrieved into a private/external workspace, validated against the registered series contract, and assigned exact scientific/source identities.

The RPS component, bounded public observation view, longitudinal diagnostics, CPS/OEWS/BTOS evidence, and governed claim surfaces are composed into one candidate manifest.

### Claim-surface binding

Governed empirical claims are bound to the exact public files that present them. A change to a governed page/document, source client, source-refresh logic, release component, or relevant registry invalidates the candidate-review state and requires a new candidate.

### Staging and human review

Staging creates immutable candidate/stage identities, a release diff, review package, and fail-closed publication gate. A valid unreviewed candidate has gate status `BLOCKED_REVIEW_REQUIRED` with zero contract failures.

The candidate-review workflow produces rights-safe artifacts and an uncompleted attestation template. It cannot self-attest scientific, editorial, source-rights, CI, or rehydration completion.

### Exact rehydration

Promotion does not trust a stale source snapshot. The trusted workflow re-fetches the source on the exact reviewed repository commit and requires the same scientific source identity. It rebuilds the candidate and stage and requires exact equality with the reviewed candidate/stage records.

Any source-identity or candidate/stage drift fails closed and requires renewed review.

### Promotion

Promotion requires a human attestation bound to the deterministic exact-rehydration identity and independently verified exact-commit CI evidence. Only declared public artifacts are copied into a new immutable release directory. Private candidate inputs remain excluded.

The release registry is append-only. A promoted release cannot rewrite an existing release ID.

### Publication commit and deployment

Public deployment is not triggered by arbitrary `main` pushes. The promotion workflow creates a single authorization commit constrained to:

- the Observatory release registry; and
- one new immutable `data/releases/<release-id>/` directory.

The publication-commit validator verifies that the release did not exist in the parent, the registry transition appends exactly one release, the release manifest points to the correct predecessor, the parent is the exact reviewed candidate commit, and release/review/rehydration/artifact identities agree.

GitHub Pages deploys only after that authorization commit passes validation. A live-origin audit must then bind the deployed state to the release identity before formal publication.

## 6. FRED operational contract

FRED documents a maximum API rate of two requests per second. The production `FredClient` therefore paces request starts below that ceiling using a monotonic clock.

All release-critical workflows that retrieve the authorized live FRED source share the repository concurrency group `authorized-rps-fred-source` with cancellation disabled. Candidate review, independent live validation, and exact rehydration/promotion must never run simultaneous full-source retrievals inside this repository.

HTTP 429 and selected transient failures retain bounded retry/backoff and fail closed after exhaustion. Do not remove rate pacing or workflow serialization as a convenience optimization.

## 7. Permanent CI contract

`.github/workflows/ci.yml` is the permanent PR/main software and governance contract.

The Python/governance job requires:

- Python 3.12;
- public-tree governance/privacy scan;
- canonical RPS registry checks;
- install `.[dev]`;
- full public pytest suite;
- Python compilation;
- Ruff;
- strict `mypy src`;
- Git whitespace validation.

The web job requires:

- Node 22;
- locked `npm ci`;
- TypeScript validation;
- `DATA_MODE=derived_only` optimized production build;
- private-data build-tree scan;
- production-server startup;
- public-route HTTP smoke tests.

Workflow dependencies are pinned to immutable action commit SHAs. Do not weaken tests, typing, scans, dependency locking, or release checks to obtain a green result.

## 8. Browser, accessibility, and deployment evidence

Rendered QA and native Safari QA are separate from ordinary unit/build CI. Automated WebKit is not equivalent to native Safari/iOS, and automated accessibility checks are not equivalent to full human screen-reader review.

Release 1 claims only the evidence actually recorded by the applicable workflows and checklist. Physical mobile-device testing, complete human assistive-technology traversal, and field Core Web Vitals remain outside the current automated evidence unless separately performed and recorded.

## 9. Contribution and review expectations

See `CONTRIBUTING.md` and `.github/pull_request_template.md`.

Every substantial pull request should state its scientific/public-claim impact, source/rights impact, validation evidence, and release impact. Documentation that changes how an empirical result is interpreted is treated as a scientific change for review purposes.

Historical validation and reconstruction records remain provenance and are explicitly labeled historical. Current operational truth lives in the README, `docs/ROADMAP.md`, `docs/RELEASE_CHECKLIST.md`, the release registry, and immutable release manifests.

## 10. Release definition of done

Release 1 is complete only after every release-time item in `docs/RELEASE_CHECKLIST.md` is satisfied on the exact final identities, including human review, exact rehydration, promotion, release-only deployment, live audit, final manual inspection, and formal GitHub tag/Release creation.
