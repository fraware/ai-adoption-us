# Roadmap and remaining engineering/research specifications

## Executive sequence

The project should advance in four tracks, with Release 1 production validation first and composition/mechanism research in parallel where dependencies permit.

| Stage | Objective | Dependency | Definition of done |
|---|---|---|---|
| R1-G1 | Production web build | npm/network | clean install + real Next.js build + CI green |
| R1-G2 | Browser/accessibility QA | R1-G1 | cross-browser, mobile, screen-reader, axe/Lighthouse gates pass |
| R1-G3 | Deployment audit | R1-G1/G2 | rights-safe production deployment verified |
| D-G1 | Direct RPS source relationship | external | documented permission/feed or explicit production rights decision |
| R1.1-G1 | Real CPS Q2-2026 composition | official CPS bytes | worker/hour composition outputs with diagnostics |
| R1.1-G2 | Residual robustness | R1.1-G1 | residuals pass suppression, sensitivity, influence checks |
| R1.1-G3 | OEWS robustness | official May-2025 OEWS | independent composition comparison |
| R1.1-G4 | Composition explorer | R1.1-G1/G2 | experimental UI + methodology + provenance |
| R1.2 | BTOS triangulation | construct alignment | firm-side triangulation only where measurement is defensible |
| V2 | Mechanism research | richer data | worker×occupation×industry×time analyses |

---

# Track 1 — Release 1 production completion

## R1-G1 — genuine dependency installation and Next.js build

### Objective

Close the one major software gate that could not be exercised in the reconstruction runtime.

### Required implementation

1. Run a clean install in `apps/web`.
2. Commit a package lockfile after reviewing the resolved dependency graph.
3. Run TypeScript/lint.
4. Run `DATA_MODE=derived_only npm run build`.
5. Start the production server and smoke-test all routes.
6. Add/maintain GitHub Actions CI so every PR runs both Python and web build gates.

### Acceptance criteria

- `npm ci` succeeds from a clean checkout once a lockfile exists;
- `npm run lint` succeeds;
- `npm run build` exits 0;
- all routes compile;
- no private fixture is required in `derived_only` mode;
- no server/browser console error on route smoke test;
- CI result is visible on PRs.

### Failure policy

Do not weaken TypeScript strictness or stub production dependencies to make this gate green. Fix the actual source/build issue.

## R1-G2 — browser, responsive, and accessibility QA

### Objective

Convert code-level accessibility intentions into validated product behavior.

### Required test matrix

Browsers: Chrome, Safari, Firefox; mobile Safari/Chrome or equivalent emulation plus at least one real mobile browser if available.

Viewports: ~375, ~768, ~1024, ~1440 px.

Assistive technology: VoiceOver and NVDA (or an equivalent second screen reader).

### Route-level assertions

For `/`, `/explore/industries`, `/explore/occupations`, `/methodology`, `/sources`, `/blog/after-adoption`:

- keyboard route/navigation complete;
- skip link works;
- focus order logical;
- charts resize without clipping;
- chart-equivalent HTML tables remain readable;
- headings/landmarks sensible;
- tooltips/interactions do not trap keyboard users;
- reduced-motion preference respected;
- no content requires color alone;
- no horizontal page overflow at supported viewport widths.

### Automated checks

- axe: zero critical/serious violations unless documented false positive;
- Lighthouse accessibility target ≥95, with every remaining issue manually reviewed;
- Lighthouse performance recorded, with no severe regression from route complexity.

### Definition of done

A dated browser/accessibility QA report is committed under `docs/qa/` with browser versions, devices/viewports, findings, fixes, and residual accepted limitations.

## R1-G3 — deployment audit

### Objective

Verify that the deployed artifact preserves the same rights and scientific boundaries as the repository.

### Requirements

- production `DATA_MODE=derived_only` explicit;
- no `data/audit/private/` path in build context/artifact;
- Sources/Provenance page reachable;
- release-mode notice visible;
- no accidental raw observation API/static endpoint;
- environment secrets not client-exposed;
- canonical metadata, robots, sitemap decision reviewed;
- HTTP security headers baseline established;
- error/404 pages reviewed;
- deployment commit and artifact checksum recorded.

### Definition of done

A production release tag references the exact Git commit and deployment audit record.

---

# Track 2 — direct RPS source and rights resolution

## D-G1 — direct source relationship

### Objective

Replace FRED-hosted third-party distribution as the long-run production backbone where possible.

### Request from RPS/GenAI Adoption Tracker authors or data owners

Seek:

- machine-readable national, industry, and occupation series;
- historical revisions/vintages where available;
- future update cadence;
- explicit terms for independent interactive publication;
- whether transformed/derived subgroup results may be redistributed;
- subgroup standard errors, replicate weights, or inference methodology;
- latest microdata availability;
- questionnaire/instrument change log.

### Definition of done

Commit `docs/source-rights/RPS_SOURCE_DECISION.md` recording:

- contact/date;
- granted/denied/unclear permissions;
- source delivery format;
- attribution requirements;
- cache/storage restrictions;
- production architecture decision.

Do not implement a persistent FRED cache as a shortcut around this gate.

---

# Track 3 — Release 1.1 composition analysis

## R1.1-G1 — execute Q2 2026 CPS composition

### Inputs

Official Basic Monthly CPS public-use files:

- April 2026;
- May 2026;
- June 2026.

### Population

- age 18–64;
- employed population under the implemented CPS employment filter;
- RPS-compatible industry and occupation crosswalks.

### Weighting

For adoption:

`w_worker(j,o,t) = weighted workers(j,o,t) / weighted workers(j,t)`

For assisted hours and reported savings:

`w_hours(j,o,t) = weighted actual main-job hours(j,o,t) / weighted actual main-job hours(j,t)`

Do not reuse worker weights for H/S.

### Actual-hours rules

- employed-absent workers: zero actual main-job hours;
- active workers with invalid actual-hours values: do not impute;
- usual-hours specification: sensitivity only, separately labeled.

### Quarter pooling

Pool April/May/June with equal month factors under the current design.

Q4 2025 remains unavailable because October 2025 CPS was not collected; do not substitute November–December.

### Coverage/suppression

For each industry×metric:

- compute mapped weight coverage;
- fail closed when missing/unmapped share exceeds the 2% threshold;
- propagate unsupported estimates as `null`;
- never renormalize an unsupported cell into apparent completeness without an explicit sensitivity analysis.

### Counterfactuals

`A_hat_occ(j,t) = Σ_o w_worker(j,o,t) * A(o,t)`

`H_hat_occ(j,t) = Σ_o w_hours(j,o,t) * H(o,t)`

`S_hat_occ(j,t) = Σ_o w_hours(j,o,t) * S(o,t)`

Residual:

`G(j,t,m) = observed(j,t,m) - predicted_occ(j,t,m)`

Canonical label:

**occupation-adjusted industry-context residual**

Never: organizational effect, organizational quality, efficiency, productivity.

### Outputs

Generate a versioned composition artifact with fields at minimum:

- period;
- industry_id/name;
- metric;
- observed;
- predicted_from_occupation_composition;
- residual;
- weighting_basis;
- mapped_coverage;
- suppression_status;
- CPS input months;
- CPS input checksums;
- crosswalk versions;
- source build timestamp/commit.

### Validation

- industry composition weights sum to 1 within tolerance for supported cells;
- worker and hour weights differ where expected;
- no negative weights;
- no silent missing-occupation dropping;
- Information/PST are not special-cased;
- every industry is processed symmetrically;
- influence/leave-one-occupation diagnostics run;
- actual-hours and usual-hours specifications compared.

## R1.1-G2 — residual robustness and persistence

Before publication, test:

1. sign and magnitude under actual vs usual hours;
2. sensitivity to coverage threshold;
3. leave-one-occupation-out influence;
4. finer occupation mappings where defensible;
5. class-of-worker/coverage differences where available;
6. temporal replication in every CPS-supported quarter;
7. uncertainty or partial-identification intervals if source precision supports them.

Do not publish a residual leaderboard from one quarter without stability diagnostics.

## R1.1-G3 — independent May-2025 OEWS robustness

### Objective

Use official BLS May-2025 national industry-specific occupational employment data as an independent establishment-side composition source.

### Important difference

OEWS is not the primary composition basis because it is establishment/wage-and-salary-worker oriented and does not reproduce the RPS/CPS worker survey universe. Treat it as robustness only.

### Requirements

- download official May-2025 OEWS staffing input from BLS;
- record file checksum and release date;
- map detailed occupations to the same 22 major groups;
- map industries to the 20 RPS groups;
- document self-employed/coverage differences;
- compute employment-share adoption counterfactual independently;
- compare direction and magnitude with CPS worker-share results.

### Definition of done

A residual is materially more credible if its sign/ranking persists under both CPS and OEWS despite their coverage differences. Disagreement must be reported, not averaged away.

## R1.1-G4 — composition explorer

Only begin after G1/G2 are scientifically green.

Route: `/explore/composition`.

Required UI:

- explicit **Experimental composition analysis** banner;
- observed vs occupation-composition counterfactual;
- residual;
- quarter selector limited to supported periods;
- metric selector;
- weighting-basis disclosure;
- CPS/OEWS source and coverage metadata;
- suppression reason shown directly;
- actual vs usual-hours sensitivity where relevant;
- no causal language.

---

# Track 4 — Release 1.2 and mechanism research

## R1.2 — BTOS triangulation

Use BTOS only when the firm-side construct aligns defensibly with the RPS construct under comparison.

Requirements:

- document exact BTOS question/denominator;
- harmonize sector taxonomy explicitly;
- treat BTOS as firm/business-side evidence, not worker-level equivalent;
- avoid combining incompatible adoption constructs into one score.

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
- education/earnings;
- software and digital intensity;
- management practices;
- regulatory burden;
- capital intensity;
- firm-side AI investment/use;
- worker selection and class of worker.

### Identification standard

Do not call an industry residual organizational complementarity until a design conditions on occupation/task composition and has a defensible strategy for remaining confounding and measurement error.

### Long-run observatory

The mature product should support versioned new-wave updates:

1. ingest/source metadata update;
2. audit/revision detection;
3. regenerate derived diagnostics;
4. compare against previous frozen vintage;
5. run stability/influence checks;
6. publish only after automated and human review;
7. retain versioned analytical history.
