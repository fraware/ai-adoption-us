# Roadmap and remaining engineering/research specifications

## Executive sequence

The project advances in four tracks. Release 1 production completion is the immediate critical path; source-rights resolution and composition research proceed in parallel where dependencies permit.

| Stage | Status | Objective | Dependency | Definition of done |
|---|---|---|---|---|
| R1-G1 | **Complete — engineering gate** | Production web/CI gate | permanent PR CI | exact source candidate passed Python/governance/mypy + locked web build + server smoke tests |
| R1-G2 | Open | Browser/accessibility QA | R1-G1 | cross-browser, mobile, keyboard, screen-reader, axe/Lighthouse gates pass |
| R1-G3 | Open | Deployment audit | R1-G1/G2 | rights-safe production deployment verified against exact release commit |
| D-G1 | Open external dependency | Direct RPS source relationship | data owner | documented permission/feed or explicit production-rights decision |
| R1.1-G1 | Open data dependency | Real CPS Q2-2026 composition | official CPS bytes | worker/hour composition outputs with diagnostics |
| R1.1-G2 | Open | Residual robustness | R1.1-G1 | residuals pass suppression, sensitivity, temporal, and influence checks |
| R1.1-G3 | Optional robustness | OEWS robustness | official May-2025 OEWS | independent composition comparison |
| R1.1-G4 | Blocked on G1/G2 | Composition explorer | R1.1-G1/G2 | experimental UI + methodology + provenance |
| R1.2 | Future | BTOS triangulation | construct alignment | firm-side triangulation only where measurement is defensible |
| V2 | Future research | Mechanism research | richer data | worker × occupation × industry × time analyses |

The first genuine networked optimized Next.js build passed on 2026-08-31 in GitHub Actions run `33411128343`. The temporary bootstrap is retired. R1-G1 is now **complete at the engineering gate**: permanent PR run `33414088473` passed strict `mypy src`, `npm ci`, TypeScript, the rights-safe optimized build, production-server startup, all public-route smoke tests, governance/privacy scans, and the public Python suite. A later documentation-only head also passed the same permanent workflow in run `33414442837`. Any subsequent PR head must re-pass permanent CI before merge; this does not reopen the engineering gate unless code, build, governance, or empirical contracts change.

---

# Track 1 — Release 1 production completion

## R1-G1 — complete: permanent CI and exact merge-candidate verification

### What is already verified

GitHub Actions run `33411128343` established:

- public Python suite: 52 passed / 6 expected private-fixture skips;
- Python compilation: passed;
- Ruff: passed;
- Node 22.23.2 / npm 10.9.8;
- TypeScript: passed;
- Next.js 16.3.3 optimized production build: passed;
- all intended public routes generated in `DATA_MODE=derived_only`.

The committed web lockfile exists. Generated TypeScript build metadata has been removed from version control.

### Permanent merge requirements

Permanent `.github/workflows/ci.yml` must, from the actual PR tree:

1. reject any tracked `data/audit/private/` path;
2. reject bootstrap transfer material and tracked TypeScript build metadata;
3. verify canonical RPS registry cardinality;
4. install Python 3.12 package/development dependencies;
5. run public pytest suite;
6. run `compileall`;
7. run Ruff;
8. run strict `mypy src`;
9. perform Git whitespace integrity check;
10. install Node 22 dependencies with `npm ci` from the committed lockfile;
11. run TypeScript validation;
12. build with `DATA_MODE=derived_only`;
13. verify no private-data path appears in the production build tree;
14. start the production server;
15. HTTP-smoke-test `/`, `/blog/after-adoption`, `/explore/industries`, `/explore/occupations`, `/methodology`, and `/sources`.

GitHub Actions dependencies should remain pinned to immutable commit SHAs.

### Acceptance criteria

- permanent PR CI remains green on every exact PR head presented for merge;
- only the documented private-fixture tests skip in the public checkout;
- `npm ci`, TypeScript, and optimized build exit 0;
- production server starts and all public routes return successful HTTP responses;
- no private fixture is required in `derived_only` mode;
- no bootstrap material or generated `.tsbuildinfo` file is tracked;
- no build claim exceeds what the workflow actually exercises.

### Failure policy

Do not weaken strict typing, test expectations, rights scans, TypeScript strictness, or production dependencies merely to make this gate green. Fix the underlying defect or leave the gate open with the exact blocker documented.

## R1-G2 — browser, responsive, accessibility, and performance QA

### Objective

Convert code-level accessibility/responsiveness intentions into validated rendered behavior.

### Required browser/device matrix

Desktop browsers:

- current Chrome;
- current Safari;
- current Firefox.

Mobile:

- mobile Safari or a real iOS browser where available;
- mobile Chrome/Android or equivalent real/emulated environment.

Target viewport widths:

- approximately 375 px;
- approximately 768 px;
- approximately 1024 px;
- approximately 1440 px.

Assistive technology:

- VoiceOver;
- NVDA or a defensible second screen-reader environment.

### Route-level assertions

For `/`, `/explore/industries`, `/explore/occupations`, `/methodology`, `/sources`, and `/blog/after-adoption`:

- primary navigation works;
- keyboard route/navigation is complete;
- skip link works;
- focus order is logical and visible;
- headings and landmarks are semantically coherent;
- charts render and resize without clipping;
- chart-equivalent HTML tables remain readable and navigable;
- tooltips/interactions do not trap keyboard users;
- reduced-motion preference is respected;
- no critical meaning requires color alone;
- no horizontal page overflow at supported viewport widths;
- data labels do not create material unreadability;
- no-data/error states explain why data are unavailable;
- no hydration/runtime error appears in browser console.

### Automated checks

- axe: zero critical/serious violations unless each remaining item is documented as a reviewed false positive;
- Lighthouse accessibility target ≥95, with every remaining issue manually reviewed;
- Lighthouse performance recorded;
- Core Web Vitals reviewed where the deployment environment permits meaningful measurement;
- bundle size and route complexity reviewed for severe regressions.

### Visual regression

Capture dated screenshots at the target viewport matrix for each primary route. Compare for clipping, typography breaks, chart/table overflow, unexpected layout shifts, and release-mode/provenance visibility.

### Definition of done

Commit a dated QA report under `docs/qa/` recording browser versions, devices/viewports, screen readers, automated tool versions, findings, fixes, screenshots/evidence references, and residual accepted limitations.

## R1-G3 — deployment audit

### Objective

Verify that the deployed artifact preserves the same rights, scientific, and reproducibility boundaries as the repository.

### Requirements

- production `DATA_MODE=derived_only` is explicit;
- `data/audit/private/` absent from build context and deployed artifact;
- Sources/Provenance page reachable;
- release-mode notice visible;
- no accidental raw-observation API/static endpoint;
- environment secrets are not client-exposed;
- canonical metadata, robots policy, and sitemap decision reviewed;
- HTTP security-header baseline established;
- 404/error pages reviewed;
- caching behavior understood and documented;
- analytics/privacy configuration explicitly accepted or disabled;
- error monitoring/logging decision documented;
- deployment commit recorded;
- public artifact/build checksum or equivalent immutable deployment identity recorded.

### Publication completion

After deployment audit:

- final source citations reviewed;
- methodology links present near empirical claims;
- editorial proofread completed;
- release notes summarize evidence and limitations;
- release tag points to the exact audited commit.

### Definition of done

A production release tag references the exact Git commit and a dated deployment-audit record. Public-launch language begins only after R1-G2 and R1-G3 are complete.

---

# Track 2 — direct RPS source and rights resolution

## D-G1 — direct source relationship

### Objective

Replace FRED-hosted third-party distribution as the long-run production backbone where possible, while preserving the current fail-closed rights architecture until a documented decision exists.

### Request from RPS / GenAI Adoption Tracker authors or data owners

Seek:

- machine-readable national, industry, and occupation series;
- historical revisions/vintages where available;
- future update cadence;
- explicit terms for independent interactive publication;
- whether transformed/derived subgroup results may be redistributed;
- permitted storage/cache behavior;
- attribution/disclaimer requirements;
- subgroup standard errors, replicate weights, or inference methodology;
- latest microdata availability;
- questionnaire/instrument change log.

### Required decision record

Commit `docs/source-rights/RPS_SOURCE_DECISION.md` recording:

- provider/contact;
- contact date(s);
- exact scope requested;
- granted/denied/unclear permissions;
- source delivery format;
- attribution requirements;
- cache/storage restrictions;
- permitted transformations;
- permitted publication/redistribution;
- update mechanism;
- uncertainty/microdata availability;
- engineering consequence.

### Definition of done

A source architecture decision is traceable to explicit permission/terms. Do not implement a persistent FRED cache as a shortcut around this gate.

---

# Track 3 — Release 1.1 composition analysis

## R1.1-G1 — execute Q2 2026 CPS composition

### Inputs

Official Basic Monthly CPS public-use files:

- April 2026;
- May 2026;
- June 2026.

Record source URLs, retrieval dates, file sizes, and checksums.

### Population

- age 18–64;
- employed population under the implemented CPS employment filter;
- RPS-compatible industry and occupation crosswalks.

### Weighting

For adoption:

`w_worker(j,o,t) = weighted workers(j,o,t) / weighted workers(j,t)`

For assisted hours and reported savings:

`w_hours(j,o,t) = weighted actual main-job hours(j,o,t) / weighted actual main-job hours(j,t)`

Do **not** reuse worker weights for H/S.

### Actual-hours rules

- employed-absent workers: zero actual main-job hours;
- active workers with invalid actual-hours values: do not impute;
- usual-hours specification: sensitivity only, separately labeled.

### Quarter pooling

Pool April/May/June with equal month factors under the current design unless a separately justified weighting design supersedes it.

Q4 2025 remains unavailable because October 2025 CPS was not collected; do not substitute November–December.

### Coverage and suppression

For each industry × metric:

- compute mapped weight coverage;
- fail closed when missing/unmapped share exceeds the 2% threshold under the current contract;
- propagate unsupported estimates as `null`;
- never renormalize an unsupported cell into apparent completeness without an explicitly labeled sensitivity analysis.

### Counterfactuals

`A_hat_occ(j,t) = Σ_o w_worker(j,o,t) * A(o,t)`

`H_hat_occ(j,t) = Σ_o w_hours(j,o,t) * H(o,t)`

`S_hat_occ(j,t) = Σ_o w_hours(j,o,t) * S(o,t)`

Residual:

`G(j,t,m) = observed(j,t,m) - predicted_occ(j,t,m)`

Canonical label:

**occupation-adjusted industry-context residual**

Forbidden interpretations absent a separate identification strategy:

- organizational effect;
- organizational quality;
- organizational efficiency;
- productivity effect.

### Required outputs

Generate a versioned composition artifact with fields at minimum:

- period;
- industry_id/name;
- metric;
- observed;
- predicted_from_occupation_composition;
- residual;
- weighting_basis;
- mapped_coverage;
- suppression_status/reason;
- CPS input months;
- CPS input checksums;
- crosswalk versions;
- source build timestamp/commit.

Also produce:

- coverage table;
- actual-vs-usual-hours sensitivity table;
- validation checks artifact;
- input manifest;
- dated validation report.

### Validation

- industry composition weights sum to 1 within tolerance for supported cells;
- worker and hour weights differ where expected;
- no negative weights;
- no silent missing-occupation dropping;
- Information and Professional/Scientific/Technical Services are not special-cased;
- every industry is processed symmetrically;
- influence/leave-one-occupation diagnostics run;
- actual-hours and usual-hours specifications compared;
- suppression propagates to output/UI;
- representative crosswalk cells are pinned by tests.

## R1.1-G2 — residual robustness and persistence

Before publication, test:

1. sign and magnitude under actual vs usual hours;
2. sensitivity to coverage threshold;
3. leave-one-occupation-out influence;
4. finer occupation mappings where defensible;
5. class-of-worker/coverage differences where available;
6. temporal replication in every CPS-supported quarter;
7. uncertainty or partial-identification intervals if source precision supports them;
8. rank/sign persistence across available waves;
9. whether results are dominated by a small number of occupations or crosswalk cells.

Do not publish a residual leaderboard from one quarter without stability diagnostics.

## R1.1-G3 — independent May-2025 OEWS robustness

### Objective

Use official BLS May-2025 national industry-specific occupational employment data as an independent establishment-side composition source.

### Important population difference

OEWS is not the primary composition basis because it is establishment/wage-and-salary-worker oriented and does not reproduce the RPS/CPS worker-survey universe. Treat it as robustness only.

### Requirements

- download official May-2025 OEWS staffing input from BLS;
- record file checksum and release date;
- map detailed occupations to the same 22 major groups;
- map industries to the 20 RPS groups;
- document self-employed/coverage differences;
- compute employment-share adoption counterfactual independently;
- compare direction and magnitude with CPS worker-share results;
- report disagreements rather than averaging them away.

### Definition of done

A residual becomes materially more credible if its sign/ranking persists under CPS and OEWS despite their coverage differences. Non-persistence is an empirical result and must remain visible.

## R1.1-G4 — composition explorer

Begin only after G1/G2 are scientifically green.

Route: `/explore/composition`.

Required UI:

- explicit **Experimental composition analysis** banner;
- observed vs occupation-composition counterfactual;
- occupation-adjusted industry-context residual;
- quarter selector limited to supported periods;
- metric selector;
- weighting-basis disclosure;
- CPS/OEWS source and coverage metadata;
- suppression reason shown directly;
- actual vs usual-hours sensitivity where relevant;
- stability/influence context;
- no causal or productivity language.

---

# Track 4 — Release 1.2 and mechanism research

## R1.2 — BTOS triangulation

Use BTOS only when the firm-side construct aligns defensibly with the RPS construct under comparison.

Requirements:

- document exact BTOS question and denominator;
- document survey population and time reference;
- harmonize sector taxonomy explicitly;
- treat BTOS as firm/business-side evidence, not a worker-level equivalent;
- avoid combining incompatible adoption constructs into one composite score;
- disclose any period/taxonomy mismatch directly.

## V2 — explain the industry-context wedge

### Research target

Move from industry/occupation aggregates toward worker × occupation × industry × time.

Conceptual models may include:

`Y_iojt = α_o + γ_j + τ_t + X_i β + ε_iojt`

with outcomes including adoption, assisted use, and reported savings.

Candidate mechanism variables:

- O*NET task structure / AI suitability;
- employer tool provision and policy;
- firm size;
- remote-work feasibility;
- education and earnings;
- software/digital intensity;
- management practices;
- regulatory burden;
- capital intensity;
- firm-side AI investment/use;
- worker selection and class of worker.

### Identification standard

Do not call an industry residual organizational complementarity until a design conditions on occupation/task composition and has a defensible strategy for remaining confounding, selection, sampling uncertainty, and measurement error.

Cross-sectional correlations/regressions remain descriptive absent a separate identification strategy.

## Long-run observatory

The mature product should support versioned new-wave updates:

1. ingest/source metadata update;
2. source-rights check;
3. audit/revision detection;
4. regenerate derived diagnostics;
5. compare against the previous frozen vintage;
6. run stability/influence checks;
7. review changed claims and charts;
8. publish only after automated and human review;
9. retain versioned analytical history and release provenance.

The long-run product should answer not only who uses GenAI, but where adoption converts into routine use, working-time penetration, and reported benefit; where that conversion is unstable; and which next research design could explain the remaining wedge.
