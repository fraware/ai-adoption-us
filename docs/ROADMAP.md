# Roadmap and remaining engineering/research specifications

Status date: **2026-09-01**

This roadmap separates three things that must remain distinct:

1. **product/release gates** — whether the public observatory is actually ready to launch;
2. **measurement/evidence gates** — whether a statistic is reproducible and interpretable;
3. **source/rights gates** — whether the project is authorized to ingest, persist, and republish the observations needed for the intended product.

A completed engineering component does not imply that its downstream empirical join is authorized. A public data source does not imply redistribution rights. A descriptive robustness result does not imply causal identification.

## Executive sequence

Release 1 production QA and the RPS source-rights decision remain the two immediate critical paths. Composition, firm-side triangulation, task-level measurement, and observatory operations proceed in parallel only where their dependencies are satisfied.

| Stage | Status | Objective | Blocking dependency | Definition of done |
|---|---|---|---|---|
| R1-G1 | **Complete — engineering gate** | Permanent production CI | none | exact candidate passes Python/governance/type checks + locked optimized web build + production smoke tests |
| R1-G2 | **Open** | Browser/accessibility/performance QA | R1-G1 | cross-browser/mobile/keyboard/screen-reader/axe/Lighthouse review complete |
| R1-G3 | **Open** | Deployment audit | R1-G2 | rights-safe deployed artifact verified against exact release commit |
| D-G1 | **Open external dependency** | Direct RPS source relationship | authorized data owner | explicit live-feed/publication/storage decision recorded |
| R1.1-G1 | **Composition foundation complete; empirical join blocked** | CPS occupation composition + RPS counterfactual | D-G1 for RPS observations | validated composition plus authorized A/H/S counterfactuals/residuals |
| R1.1-G2 | **Methodology advanced; empirical residual robustness blocked** | Residual persistence/sensitivity | D-G1; formal uncertainty work #14 | authorized residuals survive predeclared sensitivity and stability suite |
| R1.1-G2b | **Open** | Design-based CPS composition uncertainty | suitable CPS variance method | defensible covariance-aware uncertainty for custom composition vectors |
| R1.1-G3 | **OEWS composition robustness complete; residual application blocked** | Independent establishment-side composition check | D-G1 for adoption counterfactual | CPS/OEWS comparison plus authorized residual robustness |
| R1.1-G4 | **Blocked** | Experimental composition explorer | D-G1 + R1.1-G2 | UI exposes only supported, stability-qualified residual evidence |
| R1.2 | **Future** | BTOS firm-side triangulation | construct alignment | firm-side evidence added only where measurement objects are explicit |
| R1.3-G1 | **New — source/provenance gated** | Realized task adoption versus AI exposure | occupation/task index provenance + rights | lawful, versioned aggregate task/occupation measurement layer |
| O-G1 | **Open** | Versioned new-wave/revision release pipeline | stable source paths + #11 | tested pipeline produces revision diffs and blocks contract-breaking releases |
| O-G2 | **Open** | Private-fixture regeneration governance | authorized private fixture + #12 | any fixture revision forces full dependent regeneration/review |
| V2 | **Future research** | Worker/task/occupation/industry mechanisms | authorized richer microdata + inference | pre-specified respondent-level design separates composition from context |

## Canonical progress checkpoint

The current canonical `main` includes the following completed foundations:

- permanent rights-safe release CI;
- official Q2 2026 CPS composition execution;
- official Q2 2025 CPS composition execution for a second comparable quarter;
- May 2025 OEWS occupation-composition robustness;
- partial-identification bounds for unpublished OEWS occupation cells;
- Q2 2025 versus Q2 2026 CPS composition stability diagnostics;
- monthly and leave-one-month-out CPS composition reliability diagnostics;
- versioned `cps-composition-evidence-v1` evidence-tier policy;
- canonical RPS source-rights decision record and three-gate permission request.

The current public product remains fail-closed for direct RPS observations. The existence of these composition foundations therefore does **not** imply that an occupation-adjusted RPS industry residual has been produced or may be published.

---

# Track 1 — Release 1 production completion

## R1-G1 — complete: permanent CI and exact merge-candidate verification

Permanent `.github/workflows/ci.yml` is the release engineering contract. Every candidate presented for merge must continue to:

1. reject tracked private-audit data and bootstrap transfer material;
2. verify canonical registry/governance constraints;
3. install the Python package and run the public test suite;
4. run Python compilation, Ruff, and strict `mypy src`;
5. verify Git whitespace integrity;
6. install locked Node dependencies with `npm ci`;
7. run TypeScript validation;
8. build the optimized site in rights-safe `DATA_MODE=derived_only`;
9. verify private-data paths are absent from the production build tree;
10. start the production server and smoke-test all public routes.

Do not weaken tests, strict typing, rights scans, or production dependencies to obtain a green build.

## R1-G2 — browser, responsive, accessibility, and performance QA

### Required matrix

Desktop:

- current Chrome;
- current Safari;
- current Firefox.

Mobile:

- mobile Safari / iOS;
- mobile Chrome / Android or defensible emulation.

Representative widths:

- ~375 px;
- ~768 px;
- ~1024 px;
- ~1440 px.

Assistive technology:

- VoiceOver;
- NVDA or another defensible second screen-reader environment.

### Route-level assertions

For `/`, `/explore/industries`, `/explore/occupations`, `/methodology`, `/sources`, and `/blog/after-adoption`:

- primary navigation and skip links work;
- keyboard focus order is logical and visible;
- headings/landmarks are coherent;
- charts resize without clipping;
- chart-equivalent tables remain usable;
- interactions do not trap keyboard users;
- reduced-motion preference is respected;
- critical meaning does not depend on color alone;
- no horizontal page overflow at supported widths;
- data/no-data/error states remain legible;
- no hydration/runtime error appears in the browser console.

### Automated and manual review

- axe: zero unresolved critical/serious violations;
- Lighthouse accessibility target ≥95, with remaining findings manually reviewed;
- performance and bundle-size regressions recorded;
- Core Web Vitals reviewed where the deployment context supports meaningful measurement;
- dated visual-regression screenshots captured for the primary route/viewport matrix.

### Definition of done

Commit a dated report under `docs/qa/` with browser/device versions, viewports, assistive technology, automated-tool versions, findings, fixes, screenshots/evidence references, and residual accepted limitations.

## R1-G3 — deployment audit

The deployed artifact must preserve repository rights/scientific boundaries.

Required checks:

- production `DATA_MODE` explicit;
- private-audit data absent from build context/deployed artifact;
- Sources/Provenance reachable;
- release-mode notice visible;
- no accidental raw-observation endpoint;
- secrets not client-exposed;
- metadata/robots/sitemap reviewed;
- security-header baseline recorded;
- 404/error pages reviewed;
- caching behavior documented;
- analytics/privacy configuration explicitly accepted or disabled;
- monitoring/logging decision documented;
- deployment commit and immutable deployment identity recorded.

After deployment audit, review final source citations, methodology links near empirical claims, editorial copy, release notes, and exact release tag.

Public-launch language begins only after R1-G2 and R1-G3 are complete.

---

# Track 2 — RPS source, rights, and research access

## D-G1 — direct source relationship

### Current state

The production-feed decision is unresolved. Public Tracker presentation, public download controls, FRED distribution, paper replication files, and research microdata access are not treated as equivalent permissions.

`docs/source-rights/RPS_PERMISSION_REQUEST.md` now separates three independent gates:

1. **live aggregate observatory gate** — current/future national, industry, and occupation Tracker observations;
2. **historical replication gate** — reuse terms for the published paper replication package;
3. **detailed task/occupation research gate** — access to later respondent/task/occupation research data.

### Live aggregate decision must cover

- machine-readable national, industry, and occupation observations;
- complete available history;
- prior vintages/revisions where available;
- future update cadence and preferred delivery mechanism;
- persistent interactive display rights;
- server/build storage and cache restrictions;
- downloadable CSV/JSON/Parquet redistribution;
- public API redistribution;
- redistribution of transformed aggregate results;
- attribution/disclaimer/branding requirements;
- survey instruments and methodology/change logs;
- subgroup sample sizes and uncertainty/inference assets.

### Historical replication decision must cover

- exact package contents and covered waves;
- license/reuse terms;
- reproduction of published estimates;
- external-data linkage;
- publication of new aggregate results;
- restrictions on redistribution of source microdata.

### Detailed research decision must cover

- current/later respondent or task microdata access process;
- task/occupation codebooks and taxonomy vintages;
- permissible CPS/O*NET/OEWS or other linkage;
- respondent clustering/inference assets;
- publication restrictions for aggregate derived results.

### Definition of done

`docs/source-rights/RPS_SOURCE_DECISION.md` contains an authorized response with exact scope, dates, delivery format, storage/publication/redistribution terms, attribution, uncertainty assets, research-access status, and engineering consequence.

Until then:

- public RPS observation mode remains fail-closed;
- do not build a persistent FRED cache as a workaround;
- do not infer rights from public availability;
- do not mark outreach as sent without a verifiable sent-message record.

---

# Track 3 — Release 1.1 composition analysis

## R1.1-G1 — CPS composition foundation complete; RPS join pending

### Completed composition work

Official Basic Monthly CPS inputs have been executed for:

- Q2 2026: April, May, June 2026;
- Q2 2025: April, May, June 2025.

The composition contract remains:

### Population

- age 18–64;
- employed population under the implemented CPS employment filter;
- RPS-compatible industry and occupation crosswalks.

### Weighting

For adoption:

`w_worker(j,o,t) = weighted workers(j,o,t) / weighted workers(j,t)`

For assisted hours and reported savings:

`w_hours(j,o,t) = weighted actual main-job hours(j,o,t) / weighted actual main-job hours(j,t)`

Never reuse worker weights for H/S.

### Actual-hours rules

- employed-absent workers: zero actual main-job hours;
- active workers with invalid actual-hours values: no imputation;
- usual-hours specification: sensitivity only and separately labeled;
- equal month factors under the current quarter-pooling design.

Q4 2025 remains unavailable because October 2025 CPS was not collected; November–December must not be substituted for a missing quarter.

### Coverage and support

- compute mapped worker/hour coverage by industry and metric;
- fail closed when missing/unmapped share breaches the current 2% contract;
- unsupported estimates remain null;
- no silent renormalization into apparent completeness.

### Pending authorized empirical join

When compatible RPS industry/occupation observations are authorized, compute:

`A_hat_occ(j,t) = Σ_o w_worker(j,o,t) * A(o,t)`

`H_hat_occ(j,t) = Σ_o w_hours(j,o,t) * H(o,t)`

`S_hat_occ(j,t) = Σ_o w_hours(j,o,t) * S(o,t)`

and

`G(j,t,m) = observed(j,t,m) - predicted_occ(j,t,m)`

Canonical label: **occupation-adjusted industry-context residual**.

Forbidden interpretations absent a separate identification design:

- organizational effect;
- organizational quality;
- organizational efficiency;
- productivity effect.

## R1.1-G2 — residual robustness and persistence

The composition-side reliability layer is substantially advanced, but this gate cannot be completed until authorized observed RPS industry/occupation values permit the counterfactual/residual itself to be generated.

Required residual checks remain:

1. actual-hours versus usual-hours sensitivity;
2. coverage-threshold sensitivity;
3. leave-one-occupation-out influence;
4. finer occupation mappings where defensible;
5. class-of-worker/coverage sensitivity where available;
6. replication in every supported quarter;
7. rank/sign persistence across waves;
8. dominance by individual occupations or crosswalk cells;
9. uncertainty or partial-identification treatment appropriate to each source.

Do not publish a one-quarter residual leaderboard.

Every displayed residual must expose weighting basis, coverage, suppression status, stability/influence context, and its descriptive standardization interpretation.

## R1.1-G2b — formal CPS composition uncertainty

Issue #14 tracks a separate inferential problem: the custom CPS industry × occupation composition vectors need uncertainty treatment that respects the complex rotating-panel design.

Current diagnostics include person-month counts, final-weight dispersion, monthly movement, leave-one-month-out perturbations, and cross-vintage stability. These are quality-control diagnostics, **not** design-based standard errors or confidence intervals.

A defensible future method must address:

- official replicate/GVF or another justified CPS variance path;
- covariance among occupation shares that sum to one;
- repeated households/rotation-group overlap;
- quarter pooling and quarter-to-quarter comparisons;
- uncertainty propagation into occupation-standardized RPS quantities;
- validation against published CPS estimates where a sufficiently comparable benchmark exists.

Do not label Kish weight-dispersion effective n as a CPS design-based effective sample size.

## R1.1-G3 — OEWS independent composition robustness

### Completed foundation

May 2025 OEWS industry-specific occupational employment has been mapped into the same 20 industry × 22 major-occupation structure and compared with CPS worker composition.

The source-universe difference is first-class:

- CPS/RPS are worker-survey constructs;
- OEWS covers wage-and-salary employment in covered establishments and excludes self-employed workers;
- OEWS is therefore robustness evidence, not a synchronized worker-universe replacement.

Unpublished OEWS occupation cells are handled with partial-identification bounds rather than zero imputation. Current results show that the unresolved published-cell mass is too small to explain the observed CPS/OEWS composition differences.

The current evidence-tier policy retains full unfiltered results and treats one highly unstable thin CPS domain—Management of Companies and Enterprises—as sensitivity-only for primary composition comparisons.

### Remaining RPS-dependent application

After D-G1 resolves compatible observations:

- compute CPS-based and OEWS-based adoption composition counterfactuals independently;
- compare sign/magnitude/rank of the resulting descriptive residuals;
- preserve disagreements rather than averaging sources;
- retain source-universe caveats next to every comparison.

Persistence across both sources strengthens a descriptive standardization finding. Non-persistence is itself a result.

## R1.1-G4 — composition explorer

Route: `/explore/composition`.

Begin only when the underlying empirical residual has passed R1.1-G2 and the necessary publication rights exist.

Required UI:

- explicit **Experimental composition analysis** banner;
- observed versus occupation-composition counterfactual;
- occupation-adjusted industry-context residual;
- quarter/metric selector limited to supported observations;
- weighting-basis disclosure;
- CPS/OEWS source and coverage metadata;
- suppression reason shown directly;
- actual-versus-usual-hours sensitivity where relevant;
- stability/influence context;
- reliability tier where material;
- no causal or productivity language.

---

# Track 4 — Release 1.2 and Release 1.3 measurement triangulation

## R1.2 — BTOS firm-side triangulation

BTOS is a distinct firm/business evidence layer. For every measure used, document:

- exact question wording and denominator;
- survey population;
- reference period;
- sector taxonomy/crosswalk;
- whether the object is firm use, business-function breadth, worker-task use, investment, or something else;
- questionnaire-version changes and period mismatches.

Do not treat a firm/business measure as a worker-level equivalent. Do not combine incompatible constructs into a composite score. Do not mechanically join a sector-level firm measure to worker outcomes and label the result an organizational effect.

## R1.3-G1 — realized task adoption versus AI exposure

The 2026 RPS task-level research introduces a new measurement boundary upstream of the existing adoption-to-benefit chain:

**theoretical/model-based AI exposure or capability ≠ realized worker-reported adoption**.

Issue #17 governs this aggregate evidence layer. It is intentionally separate from respondent-level V2 mechanism research.

### Source gate

The official RPS Generative AI page advertises an `Occupation and Task Adoption Indices` resource. Before ingestion:

- resolve exact canonical artifact URL and publisher;
- record retrieval date, hash, version/vintage, format, and documentation;
- determine explicit storage/reuse/publication terms;
- identify survey waves, sample, weighting, task taxonomy, SOC/O*NET vintage, aggregation formula, suppression rules, and uncertainty assets;
- keep this artifact's rights distinct from the live Tracker gate unless an authorized term explicitly covers both.

An advertised index is not treated as permission to mirror it.

### Construct contract

Keep these objects separate:

- `E_task` / `E_occ`: theoretical/model-based exposure or capability;
- `A_task`: realized worker-reported task adoption;
- `A_occ`: realized occupation-level work adoption;
- `H`: share of work hours actively using GenAI;
- `S`: self-reported counterfactual hours-saved share.

### Proposed aggregate analyses

Subject to source/provenance resolution:

1. reproduce source headline quantities before new analysis;
2. pin a fixed task/occupation taxonomy and crosswalk;
3. compare multiple exposure measures separately rather than constructing a composite score;
4. report Pearson/Spearman relationships, calibration, rank disagreement, and support/coverage;
5. label high-exposure/low-adoption or low-exposure/high-adoption differences only as descriptive **exposure-adoption gaps**;
6. diagnose generic-task classification and task-prevalence weighting effects;
7. test stability across index vintages/waves if available;
8. document within-occupation heterogeneity as a limitation of aggregate occupation measures.

Potential later product layer:

`capability/exposure → realized task adoption → occupation/work adoption → assisted-hours penetration → reported savings`

This is an explanatory measurement sequence, not a readiness or impact score.

---

# Track 5 — V2 mechanism research

## V2 — explain the remaining context wedge

The preferred richer-data structure is now:

`worker × task × occupation × industry/context × time`.

The new task-level evidence means `task suitability` must not be represented by a single occupation-level exposure control. The preferred conceptual sequence is:

`worker characteristics / prior adoption propensity → task assignment + realized task adoption → occupation → industry/firm context → depth of use / reported savings`.

Candidate mechanism variables include:

- task content and expertise level under a versioned O*NET/SOC mapping;
- worker prior adoption propensity and correlated multi-task use;
- employer tool provision/policy;
- firm size;
- remote-work feasibility;
- education and earnings;
- software/digital intensity;
- management practices;
- regulatory context;
- capital intensity;
- firm-side AI investment/use;
- worker selection and class of worker.

### Identification standard

Before stronger mechanism claims:

- condition on occupation and task composition where the estimand requires it;
- model respondent-level correlation when workers report multiple tasks;
- separate exposure/capability measures from realized adoption;
- address remaining worker/firm selection and measurement error;
- use inference appropriate to the authorized microdata/sample design;
- state the estimand and external-validity boundary before results are generated.

Do not label an aggregate industry-context residual organizational complementarity merely because it survives occupation standardization. Cross-sectional regressions remain descriptive absent a separate identification strategy.

---

# Track 6 — observatory operations and reproducibility governance

## O-G1 — versioned new-wave and revision pipeline

Issue #11 converts the project from a one-time validated release into a controlled longitudinal observatory.

For every new source wave or revision, the production/research process must:

1. ingest through a rights-approved source path or update source metadata only;
2. record source vintage, retrieval time, and revision status;
3. run rights/permission checks before persistence/publication;
4. detect changes to frozen observations, definitions, or taxonomies;
5. regenerate all dependent derived artifacts;
6. compare them with the previous frozen vintage;
7. run stability, influence, coverage, and regression-contract checks;
8. identify every chart/table/text claim affected by the change;
9. require explicit scientific/editorial review;
10. publish a versioned release only after CI and review;
11. retain immutable analytical history and provenance.

Engineering requirements include deterministic inputs/outputs, no silent data-mode fallback, a structured revision-diff artifact, claim-to-number traceability, and fail-closed behavior on source-definition, rights, missing-series, or coverage changes.

Definition of done: a documented/tested update command can process a synthetic/new test vintage, generate an auditable revision diff, and block publication when a contract changes.

## O-G2 — private fixture revision and regeneration gate

Issue #12 governs the private RPS audit fixture. The fixture remains outside the public repository, while public CI must continue to pass without it.

Whenever an authorized private fixture is added or revised:

- verify expected identity/version/checksum;
- retain the previous frozen version rather than silently replacing history;
- run the complete fixture-present private test suite;
- regenerate every dependent longitudinal artifact;
- compare generated outputs against the previous freeze;
- produce a structured diff for changed cells, diagnostics, rankings, and claims;
- require review of every affected public chart/table/text statement;
- create a new dated validation and source-vintage record;
- block publication if the fixture is incomplete, rights change, definitions change, or diagnostics fail.

Definition of done: fixture revision cannot occur without mandatory regeneration/review and an auditable revision record.

---

# Long-run observatory contract

The mature product should support the O-G1/O-G2 controls as permanent operating infrastructure, not one-time release chores.

The public experience should make measurement boundaries visible rather than compressing them into a score. Where supported by rights and evidence, the reader should be able to follow:

`capability/exposure → adoption → routine use → work-hour penetration → reported time savings → separately identified economic outcomes`.

The observatory should answer not only who uses GenAI, but where one layer converts into the next, where that conversion is unstable, what composition explains, what remains unexplained, and which stronger research design would be needed before mechanism or productivity claims are justified.
