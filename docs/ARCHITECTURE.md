# Architecture and trust boundaries

## 1. System objective

GenAI at Work is simultaneously a research pipeline, a governed release system, and a public data publication. Its architecture preserves explicit boundaries among:

1. source metadata and rights decisions;
2. private source-input bytes used to build/reproduce candidates;
3. rights-safe public observation projections;
4. derived scientific evidence;
5. governed public claim surfaces;
6. immutable promoted releases;
7. the deployed web publication.

The central release invariant is identity continuity: the source vintage, scientific artifacts, public claims, promoted release, and deployed site must describe the same reviewed object.

## 2. Current high-level architecture

```text
Authorized RPS published aggregates (FRED/ALFRED)
                  │
                  ▼
       private refresh candidate
   rps_source_snapshot.json + hashes
                  │
                  ▼
       private RPS Observatory component
   ┌──────────────┼────────────────────┐
   │              │                    │
   ▼              ▼                    ▼
complete       seven-quarter       bounded public
source input   longitudinal        observation view
objects        diagnostics         (national history +
(private)      (derived)           latest subgroup A/H/S)
   │              │                    │
   └──────────────┴─────────────┬──────┘
                                │
                                ▼
                vintage-bound global candidate
          ┌────────────┬────────────┬────────────┐
          │            │            │            │
          ▼            ▼            ▼            ▼
        CPS          OEWS         BTOS      governed claim
     composition   robustness  triangulation  surface hashes
          │            │            │            │
          └────────────┴────────────┴────────────┘
                                │
                                ▼
                    immutable candidate stage
                                │
                 explicit release review gate
                                │
                owner-authorized Release 1 review
                                │
                                ▼
                 exact post-review rehydration
                                │
                source identity + candidate + stage
                     must reproduce exactly
                                │
                                ▼
                   immutable promoted release
                                │
                                ▼
                  release-only authorization commit
                                │
                                ▼
             exact-SHA GitHub Pages dispatch/deployment
                                │
                                ▼
                    live-origin audit + v1.0.0
```

## 3. Source and private-data boundary

`data/audit/private/` is the repository-local private workspace boundary. External private/transient workspaces are also permitted by the candidate builders.

Rules:

- private RPS source snapshots and complete historical source objects are never committed to the public repository;
- candidate `inputs/` are never copied into the promoted public release;
- public review packages contain no source `local_path`, private snapshot, or candidate `inputs/` directory;
- public availability of a source is not treated as authorization for unrestricted mirroring, bulk redistribution, or a generic source API;
- the current RPS permission basis and its limitations are recorded in `docs/source-rights/RPS_SOURCE_DECISION.md`.

The current public RPS contract permits a bounded attributed aggregate presentation view, not a complete historical subgroup database.

## 4. Public data mode

### `derived_only`

The Release 1 public mode. It can render:

- rights-safe derived publication evidence;
- the contracted bounded RPS observation view from the current promoted release.

The web resolver verifies the release-registry pointer, promoted release-manifest checksum, artifact path, artifact size, artifact SHA-256, and RPS source-vintage consistency before returning promoted data. Longitudinal diagnostics and bounded observations resolve from the same promoted release.

Before the first promoted release, the repository seven-quarter longitudinal artifact provides a research/QA fallback for derived diagnostics. The bounded observation view remains unavailable until a promoted release exists.

### `audit_snapshot`

Controlled private research mode. It can load explicitly supplied private audit material. It is not the public release path and there is no silent fallback into it.

### `fred_live_no_store`

Reserved server-side adapter mode. It remains separately governed and fail-closed. Release 1 does not depend on activating this runtime adapter because source acquisition occurs in the private release pipeline.

## 5. Scientific module boundaries

### RPS registry and refresh

`data/registry/rps_source_series_manifest.json` defines the 131-series work-focused scope:

- 5 national;
- 60 industry;
- 66 occupation.

`src/genai_at_work/rps_refresh.py` validates the official provider inventory, canonical metadata, excluded constructs, source definitions, observation domain, rights boundary, and stable scientific source identity.

### Longitudinal analysis

`src/genai_at_work/rps_release.py` and `rps_release_complete.py` own the deterministic descriptive RPS analysis:

- cross-sectional regressions;
- Pearson/Spearman A/H relationships;
- leave-one-group-out diagnostics;
- rank stability across all quarter pairs;
- cross-level comparisons;
- construct-specific source-history topology and the common complete A/H/S analytical window.

Current Release 1 analysis uses seven common quarters, Q4 2024–Q2 2026.

### Public RPS projection

`src/genai_at_work/rps_public_view.py` constructs the bounded attributed RPS observation artifact under `rps-public-observation-delivery-v1`:

- five national work-family metrics across the complete seven-quarter history;
- latest complete Q2 2026 A/H/S cross-sections for 20 industries;
- latest complete Q2 2026 A/H/S cross-sections for 22 occupations.

It does not publish historical subgroup panels or a generic query database.

### CPS composition and residuals

CPS supplies occupation-composition weights:

- adoption counterfactuals use worker shares;
- assisted-hours and reported-savings counterfactuals use actual-main-job-hour shares;
- usual-hours weights are sensitivity evidence.

The occupation-adjusted industry-context residual is a descriptive standardization residual:

`observed industry value - occupation-composition counterfactual`

It is not an identified organizational, efficiency, productivity, or causal effect.

### OEWS robustness

May 2025 OEWS staffing evidence provides an independent establishment-side composition robustness basis. Its population differs from CPS and is kept separate instead of pooled into one synthetic weight system.

### BTOS triangulation

BTOS–RPS industry comparison is preregistered descriptive cross-construct triangulation. Employer-business AI use and worker GenAI adoption retain distinct units, denominators, technology scope, and reference periods.

## 6. Claim-surface trust boundary

Scientific artifact hashes alone do not prove that the public page presents the reviewed claim. `src/genai_at_work/claim_surfaces.py` binds each governed longitudinal/source claim to SHA-256 hashes of the exact repository files that present it.

The RPS candidate converts each governed claim identity into a digest over:

- its evidence-only claim digest; and
- the exact registered surface-file hashes.

Global composition revalidates these bindings. Any governed-file edit after candidate construction fails candidate composition/rehydration and requires a new review.

## 7. Global candidate composition

`src/genai_at_work/observatory_baseline.py` composes the complete v1 candidate from the private RPS component and repository-bound CPS/OEWS/BTOS evidence.

`src/genai_at_work/observatory_rps_bindings.py` prevents repository artifacts derived from RPS from silently referring to another RPS vintage. It requires exact binding coverage for every RPS-dependent baseline artifact before global composition.

The global candidate contains private `inputs/` for release reproducibility and rights-safe `artifacts/` eligible for promotion. The generic release engine validates both but copies only declared public artifacts into the immutable promoted release.

## 8. Stage, review, and rehydration boundary

`scripts/observatory_release.py stage` builds a portable stage identity from:

- current release-registry predecessor identity;
- candidate manifest file SHA-256;
- candidate canonical digest;
- release-diff digest;
- review-package digest;
- gate status.

The candidate-review workflow uploads only rights-safe review evidence and leaves scientific/editorial/source-rights/CI attestation fields uncompleted. It cannot self-authorize publication or pre-attest a future rehydration identity.

For Release 1, `data/registry/release1_owner_authorization.json` records a one-shot project-owner authorization for an automated release review. The release operator may complete the review attestation only after the exact candidate has zero release-contract failures, exact-commit CI succeeds, and exact source rehydration reproduces the reviewed scientific source, candidate, and stage identities. The release record states `human_review_performed=false` and binds the owner authorization ID.

`scripts/rehydrate_observatory_v1_candidate.py` is the post-review trust boundary. It runs on the exact reviewed commit, verifies the predecessor release state, re-fetches RPS, requires the same scientific source identity, rebuilds the complete candidate, re-stages it, and requires exact equality with the reviewed candidate/stage records.

A changed source value, source definition, repository evidence artifact, governed claim file, candidate manifest, stage identity, or release predecessor blocks promotion and forces renewed review.

## 9. Promotion and deployment boundary

Canonical promotion is available only through `scripts/promote_rehydrated_observatory_v1.py`. The low-level release engine rejects direct promotion against the canonical release registry/tree unless it receives the internal exact-rehydration capability.

The owner-authorized Release 1 workflow requires:

1. a successful exact candidate-review workflow run on canonical `main`;
2. successful exact-commit Release candidate CI;
3. an exact rehydration identity reproducing the reviewed source/candidate/stage state;
4. an owner-authorized automated attestation bound to that identity;
5. immutable release promotion;
6. a release-only commit whose parent is the exact candidate commit;
7. independent validation of that publication commit;
8. explicit dispatch of the exact publication SHA to the Pages workflow;
9. successful Pages artifact audit, deployment, and live-origin audit;
10. formal `v1.0.0` creation only after those deployment gates pass.

The owner authorization is first-release-only. Once the release registry contains a promoted release, the Release 1 operator becomes inert. Later releases require a separately authorized release decision.

The resulting publication Git commit may change only:

- `data/registry/observatory_release_registry.json`;
- `data/releases/<release-id>/...`.

`scripts/validate_observatory_publication_commit.py` validates this transition, requires the commit parent to be the exact reviewed candidate commit, and for the first release verifies the owner-authorization fields in the immutable review record.

GitHub Pages may build on ordinary pushes and pull requests for QA. Deployment occurs only for a validated `Authorize Observatory release <release-id>` commit, either directly on an eligible push or through the exact-SHA `workflow_dispatch` path used when the release commit originates from the release operator. The dispatched path independently verifies that the supplied SHA is the current `main` tip and passes the publication-commit validator before deploying.

## 10. Fail-closed principles

The system prefers explicit unavailability or renewed review over convenience. Examples:

- source scientific identity changes after review → new candidate review required;
- governed public claim file changes after binding → candidate invalid;
- release registry advances after review → rehydration invalid;
- unsupported CPS period → unavailable;
- composition support breach → unsupported/null evidence;
- incomplete source family → candidate build failure;
- unverified or broadened rights scope → publication blocked;
- no promoted release → no bounded RPS public view;
- direct canonical low-level promotion → blocked;
- publication commit contains unrelated code/content → deployment blocked;
- dispatched Pages SHA is not the canonical `main` tip → deployment blocked;
- first-release review record lacks the owner authorization binding → publication commit invalid.
