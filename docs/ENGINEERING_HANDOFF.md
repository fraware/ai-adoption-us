# Engineering handoff — current implementation and acceptance contracts

## 1. Mission

GenAI at Work is not a generic dashboard. It is an empirical publication whose credibility depends on preserving measurement distinctions, source rights, reproducibility, and explicit limits on inference while making the adoption-to-workflow-conversion problem legible.

Engineering and research work must satisfy three simultaneous constraints:

1. **scientific correctness** — constructs and denominators cannot drift;
2. **rights safety** — private or uncleared source observations cannot leak into public artifacts;
3. **product quality** — a sophisticated reader should be able to understand evidence, caveats, and provenance without opening the code.

## 2. Non-negotiable scientific contracts

### Metric semantics

`A` — work adoption/use, extensive margin.

`H` — share of work hours during which GenAI was actively used; a workflow-penetration measure, not time saved.

`S` — self-reported counterfactual hours saved as a share of work time; not measured labor productivity.

Do not rename `S/H` as efficiency. If used at all, describe it mechanically as **reported saved hours per actively assisted hour** and explain why it may exceed 1.

### Cross-sectional analysis

Every R²/correlation in the current RPS result layer is descriptive and aggregate.

Do not use significance language unless subgroup uncertainty becomes available and an explicit inferential procedure is implemented.

### Composition weighting

Adoption → CPS worker shares.

Assisted hours and savings → CPS actual-main-job-hour shares.

This distinction is a hard testable invariant. Do not reuse worker-share weights for H/S.

Usual hours are a labeled sensitivity only.

### Residual language

Canonical term: **occupation-adjusted industry-context residual**.

Forbidden interpretations absent a separate identification strategy:

- organizational effect;
- organizational quality;
- organizational efficiency;
- productivity effect.

## 3. Source and rights contracts

The public repository is rights-safe.

Never commit:

`data/audit/private/rps_subgroup_5q_audit.json`

Public builds use `DATA_MODE=derived_only` unless a future source-rights decision explicitly changes the architecture.

Any new source adapter must document:

- provider;
- terms;
- storage/cache policy;
- redistribution permission;
- attribution/disclaimer requirements;
- source vintage;
- retrieval/revision behavior.

Do not reintroduce persistent FRED observation caching as a shortcut around unresolved rights.

The RPS source decision is split into three independent gates in `docs/source-rights/RPS_PERMISSION_REQUEST.md`:

1. current/future Tracker aggregate publication and delivery rights;
2. historical paper replication-package reuse;
3. detailed task/occupation respondent-data research access.

A positive answer on one gate does not imply permission on another.

## 4. Current verified implementation surface

Python/research modules cover:

- canonical RPS source identities;
- five-wave longitudinal diagnostics;
- CPS parsing and composition weighting;
- historical CPS layout handling;
- composition reliability;
- OEWS composition and cross-vintage robustness;
- composition evidence-tier logic;
- residual generation logic;
- canonical normalization/model utilities;
- fail-closed source adapter/governance behavior.

Primary execution scripts include:

- `build_longitudinal.py`;
- `execute_cps_composition.py`;
- `execute_cps_2025_composition.py`;
- `execute_cps_composition_reliability.py`;
- `execute_oews_composition.py`;
- `compare_oews_cps_vintages.py`;
- `build_composition_evidence_tiers.py`;
- `build_composition_residuals.py`;
- `export_rights_safe.py`;
- `build_rps.py`, intentionally retired/fail-closed.

Public web surface:

- narrative home;
- industry explorer;
- occupation explorer;
- technical essay;
- methodology;
- sources/provenance;
- release-mode disclosure;
- responsive Observable Plot charts;
- chart-equivalent HTML tables.

Release CI validates the public research/application surface with Python tests, compilation, Ruff, strict mypy, governance/privacy checks, locked `npm ci`, TypeScript, optimized `derived_only` production build, private-build scanning, production-server startup, and route smoke tests.

Rendered-browser QA is now a separate executable workflow using stable Chrome, Firefox, and a WebKit engine proxy at representative responsive widths with keyboard, overflow, axe, runtime/console, Lighthouse, screenshot, trace, browser-version, and build-size evidence.

WebKit evidence is not real Safari/iOS validation. Automated browser evidence is not screen-reader validation.

## 5. Current empirical/evidence state

### RPS longitudinal layer

The frozen five-wave private panel contains:

- 20 industries;
- 22 occupations;
- A/H/S;
- Q2 2025 through Q2 2026;
- 630 audited subgroup cells.

The generated longitudinal layer must preserve these assertions unless a legitimate source revision changes the audited input fixture:

- occupation Pearson A-H > industry Pearson A-H in all five waves;
- occupation Spearman A-H > industry Spearman A-H in all five waves;
- occupation R²(S~A) > R²(S~H) in all five waves;
- occupation leave-one-out A beats H = **110/110**;
- industry H beats A for S in **3/5** waves, not 5/5;
- adoption rank stability > H stability in every frozen quarter-pair comparison at both aggregation levels;
- adoption rank stability > S stability in every frozen quarter-pair comparison at both levels.

These results are descriptive, aggregate, and non-causal.

### CPS composition foundation

Real official CPS execution is complete for the current composition foundation:

- Q2 2026 primary composition package: `data/derived/composition/cps-q2-2026/`;
- Q2 2025 historical-layout comparison package: `data/derived/composition/cps-q2-2025/`;
- cross-quarter reliability evidence: `data/derived/composition/cps-q2-reliability/`.

The associated validation records are under `docs/validation/`.

This establishes composition inputs and reliability evidence. It does **not** establish an RPS industry residual.

### OEWS robustness foundation

Official May 2025 OEWS staffing data have been executed as an independent establishment-side robustness basis:

- `data/derived/composition/oews-may-2025/`;
- `data/derived/composition/oews-may-2025-cross-vintage/`.

Population and coverage differences from CPS/RPS remain explicit. OEWS is robustness evidence, not the primary worker-survey composition basis.

### Composition residual

The observed-versus-counterfactual RPS industry join remains blocked on the rights-cleared RPS observation path.

Do not publish an occupation-adjusted industry-context residual until:

1. the compatible RPS observation source is explicitly authorized for the required use;
2. the source vintage/construct alignment is documented;
3. the validated CPS composition weights are joined without violating the source-rights contract;
4. suppression/coverage propagates correctly;
5. actual-versus-usual-hours, influence, temporal, and other prespecified robustness checks pass;
6. uncertainty limitations are exposed.

## 6. Permanent CI specification

`.github/workflows/ci.yml` is the permanent PR/main validation contract.

Workflow dependencies must remain pinned to immutable commit SHAs.

### Python/governance job

Required:

- Python 3.12;
- public-tree scan rejects `data/audit/private/`;
- scan rejects bootstrap transfer material;
- scan rejects tracked TypeScript build metadata;
- canonical RPS registry cardinality check;
- install `.[dev]`;
- `pytest -q`;
- `python -m compileall -q src scripts`;
- `ruff check src tests scripts`;
- strict `mypy src`;
- `git diff --check`.

The public checkout may skip only tests whose sole required input is the deliberately excluded private fixture.

### Web job

Required:

- Node 22;
- `npm ci` from `apps/web/package-lock.json`;
- TypeScript validation;
- `DATA_MODE=derived_only` optimized production build;
- private-data build-tree scan;
- production-server startup;
- HTTP smoke tests for every public route;
- no private fixture required.

### Rendered-browser job

The R1-G2 automated baseline must exercise the optimized production candidate rather than a development server.

Required automated evidence includes:

- stable Chrome at approximately 375/768/1024/1440 px;
- Firefox at narrow/wide representative widths;
- WebKit engine proxy at narrow/wide representative widths;
- route response and semantic structure;
- primary navigation;
- page-level overflow;
- table containment/readability;
- skip-link keyboard entry and focus transfer;
- visible focus;
- reduced-motion behavior;
- serious/critical axe violations;
- uncaught runtime and browser-console errors;
- Lighthouse accessibility and performance evidence;
- screenshots/traces and exact browser versions.

A CI failure is evidence. Do not weaken scientific tests, typing, rights scans, source boundaries, accessibility assertions, or production dependencies merely to obtain a green check.

## 7. Product implementation standards

### Charts

Every core chart must have:

- descriptive title;
- metric definition/caveat near the chart;
- accessible HTML data equivalent;
- responsive width behavior;
- direct labels where practical;
- no decorative score/gauge metaphor.

### Tables

- semantic headers/scopes;
- explicit units;
- period/source context;
- stable sorting behavior;
- no leaderboard framing for unstable/noisy cells without stability context.

### No-data behavior

Missing/suppressed data must state **why** it is unavailable.

Examples:

- unsupported quarter;
- private fixture absent;
- coverage suppression;
- production source disabled;
- rights-gated observation path.

Never render zero for missing.

### Evidence labeling

Keep direct measurements, derived descriptive transformations, composition evidence/counterfactuals, and causal/mechanism claims visibly distinct. Experimental composition content must not inherit the visual authority of direct RPS measurements without disclosure.

## 8. Release 1 completion work

The production compilation/build gate is complete. Remaining launch work is evidence-based, not cosmetic.

Current product gates:

1. complete the automated rendered-browser baseline on the exact merge candidate;
2. perform real Safari/iOS and appropriate Android/Chrome review;
3. perform VoiceOver plus a second screen-reader review;
4. manually review chart interaction, labels/tooltips, color dependence, and visual regression;
5. record meaningful performance evidence where deployment permits it;
6. complete the production deployment audit;
7. perform final source-citation/editorial review;
8. create immutable release identity/tag only after the applicable gates close.

The RPS source-rights decision proceeds in parallel and governs whether the full direct-observation observatory can be published. A technically deployable `derived_only` site is not evidence that direct observation rights exist.

## 9. Release 1.1 composition work

The **composition foundation is executed**. The remaining Release 1.1 scientific work is the RPS-dependent empirical join and its robustness, not rerunning the already-completed inputs as if they did not exist.

Before any public residual/explorer:

- confirm authorized compatible RPS occupation and industry observations;
- bind the exact RPS vintage and construct definitions;
- join adoption with worker-share composition and H/S with actual-hour-share composition;
- propagate unsupported CPS mapping/validity coverage as null;
- compare actual-hours and usual-hours specifications;
- run leave-one-occupation/influence checks;
- test temporal persistence wherever compatible composition periods exist;
- incorporate formal uncertainty or partial-identification bounds where supported;
- keep CPS/OEWS population differences visible;
- avoid a one-quarter residual leaderboard.

The experimental composition explorer remains blocked until the residual evidence is scientifically green.

## 10. Source-rights work

`docs/source-rights/RPS_SOURCE_DECISION.md` is the governing decision record once an authorized response exists.

Record:

- provider/contact;
- date;
- exact language/attachments/links;
- scope requested;
- permission result by gate;
- permitted storage/cache behavior;
- permitted transformation;
- permitted display/redistribution/API behavior;
- attribution/disclaimer language;
- update mechanism;
- uncertainty/microdata availability;
- engineering consequence.

Do not mark outreach as sent based on intent or an unverified mail-history assumption.

## 11. Observatory governance

The project is intended to be a longitudinal observatory, not a one-time static release.

For every new RPS wave/source revision:

1. verify source rights/terms;
2. record source vintage and retrieval identity;
3. detect revisions to previously frozen observations/definitions;
4. regenerate dependent artifacts;
5. compare against the prior freeze;
6. identify every changed chart/text claim;
7. run stability/influence/regression contracts;
8. require explicit scientific/editorial review;
9. publish only after CI and review pass;
10. retain immutable analytical history.

Any authorized private RPS fixture revision must also force full longitudinal regeneration and claim review. The private fixture remains outside the public repository.

## 12. Review standard

A PR touching empirical logic must answer:

1. What estimand/construct changes?
2. What denominator changes?
3. What source/version changes?
4. What generated results change?
5. Are old results invalidated or merely extended?
6. Does the rights boundary change?
7. What new test prevents regression?

A PR touching presentation must state whether any claim or number changed. If yes, it is not “presentation-only.”

A PR touching source ingestion must state storage/cache/redistribution implications before code review can treat it as routine engineering.

## 13. Release/deployment review standard

Before a public release:

- rendered browser behavior must be tested, not inferred from source code;
- accessibility claims require automated plus real assistive-technology evidence;
- performance claims require measured evidence;
- deployment must be tied to an exact commit/artifact identity;
- private paths and uncleared raw observations must be absent from the deployed artifact;
- the release must state the difference between direct evidence, derived diagnostics, produced composition inputs, gated residuals, and unexecuted causal/mechanism research.

## 14. Final vision

The long-run system is a versioned empirical observatory that can ingest authorized new RPS waves, detect revisions, regenerate national/industry/occupation evidence, assess stability, combine those observations with independently validated composition evidence where lawful and scientifically aligned, and preserve analytical history.

The evolving measurement sequence is:

**capability/exposure → realized task adoption → work adoption → routine use/workflow penetration → reported savings → separately identified economic outcomes**.

The mature product should answer not just **who uses GenAI**, but where adoption converts into actual work, where that conversion is stable or unstable, how much aggregate industry variation can be explained by occupation composition, and which subsequent research design is required to explain the remaining wedge.

Its credibility comes from refusing to collapse availability, exposure, adoption, workflow penetration, reported savings, and economic realization into one score or one causal story.
