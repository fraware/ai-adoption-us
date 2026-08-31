# Engineering handoff — complete implementation specification

## 1. Mission

The repository is not a generic dashboard. It is an empirical publication whose credibility comes from preserving measurement distinctions and provenance while making the adoption-to-workflow-conversion problem legible.

The engineering/research team owns three simultaneous constraints:

1. **scientific correctness** — constructs and denominators cannot drift;
2. **rights safety** — private source observations cannot leak into public artifacts;
3. **product quality** — a sophisticated reader should be able to understand evidence, caveats, and provenance without opening the code.

## 2. Non-negotiable scientific contracts

### Metric semantics

`A` — work adoption/use, extensive margin.

`H` — share of work hours during which GenAI was actively used; a workflow-penetration measure, not time saved.

`S` — self-reported counterfactual hours saved as a share of work time; not measured labor productivity.

Do not rename `S/H` as efficiency. If used at all, describe it mechanically as **reported saved hours per actively assisted hour** and explain why it may exceed 1.

### Cross-sectional analysis

Every R²/correlation in the current result layer is descriptive and aggregate.

No significance language unless subgroup uncertainty becomes available and an explicit inferential procedure is implemented.

### Composition weighting

Adoption → CPS worker shares.

Assisted hours and savings → CPS actual-main-job-hour shares.

This distinction is a hard testable invariant. Do not reuse worker-share weights for H/S.

### Residual language

Canonical term: **occupation-adjusted industry-context residual**.

Forbidden interpretations absent a separate research design:

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

## 4. Current verified code and build surface

Python modules:

- `rps_registry.py` — canonical source identities;
- `longitudinal.py` — five-wave diagnostics;
- `cps.py` — CPS parsing/composition weights;
- `composition.py` — counterfactual/residual generation;
- `normalize.py`, `models.py`, `metrics/conversion.py` — canonical normalization/model utilities;
- `sources/fred.py` — source adapter logic with governance boundaries.

Scripts:

- `build_longitudinal.py`;
- `build_cps_composition.py`;
- `build_composition_residuals.py`;
- `export_rights_safe.py`;
- `validate_ts_structural.sh`;
- `build_rps.py` intentionally retired/fail-closed.

Web:

- narrative home;
- industry explorer;
- occupation explorer;
- technical essay;
- methodology;
- sources/provenance;
- release-mode disclosure;
- responsive Observable Plot charts;
- chart-equivalent HTML tables.

Networked public validation on 2026-08-31, GitHub Actions run `33411128343`:

- public Python suite: **52 passed / 6 expected private-fixture skips**;
- Python compilation: passed;
- Ruff: passed;
- TypeScript: passed;
- Node 22.23.2 / npm 10.9.8;
- Next.js 16.3.3 optimized production build: passed;
- all intended public routes generated.

Historical private validation on 2026-08-30 remains the evidence for the fixture-present **58-test** surface and byte-for-byte longitudinal regeneration. Do not conflate those two execution contexts.

## 5. Current result contracts

The generated longitudinal layer must preserve these assertions unless a legitimate source revision changes the audited input fixture:

- levels are separate: 20 industries and 22 occupations, each with A/H/S, over five waves = 630 private audited rows/cells in the frozen panel;
- occupation Pearson A-H > industry Pearson A-H in all five waves;
- occupation Spearman A-H > industry Spearman A-H in all five waves;
- occupation R²(S~A) > R²(S~H) in all five waves;
- occupation leave-one-out A beats H = **110/110**;
- industry H beats A for S in **3/5** waves, not 5/5;
- adoption rank stability > H stability in the frozen quarter-pair comparisons for both aggregation levels;
- adoption rank stability > S stability in the frozen quarter-pair comparisons for both levels.

Do not hard-code these in editorial prose independently of generated data where the application can load them from the derived artifact.

Any future source revision that changes the private fixture must trigger regeneration and explicit claim review; do not silently preserve old prose against new numbers.

## 6. Permanent CI specification

The temporary bootstrap workflow is retired. `.github/workflows/ci.yml` is the permanent PR/main validation contract.

GitHub Actions dependencies are pinned to immutable commit SHAs.

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

The public checkout is expected to skip only tests whose sole required input is the deliberately excluded private fixture.

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

### Failure policy

A CI failure is evidence. Do not weaken scientific tests, typing, rights scans, source boundaries, or production dependencies merely to obtain a green check.

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
- production source disabled.

Never render zero for missing.

### Evidence labeling

Keep direct measurements, derived descriptive transformations, cross-survey composition counterfactuals, and causal/mechanism claims visibly distinct. Experimental composition content must not inherit the visual authority of direct RPS measurements without disclosure.

## 8. Release 1 completion work

The earlier production-compilation gate is closed by the 2026-08-31 networked build. The exact merge candidate still must pass permanent PR CI.

Current priority order:

1. permanent PR CI on the exact merge candidate;
2. browser/responsive QA;
3. keyboard and screen-reader QA;
4. axe/Lighthouse/performance and visual-regression QA;
5. deployment audit;
6. final source-citation/editorial proofread;
7. release notes, immutable release identity, and tag.

See `docs/ROADMAP.md` Track 1 and `docs/RELEASE_CHECKLIST.md` for acceptance criteria.

Composition must **not** block Release 1.

## 9. Release 1.1 composition work

Implement the CPS contracts in `docs/ROADMAP.md` Track 3.

The existing code is a starting implementation, not proof that real-data output is scientifically green.

Engineers/researchers must inspect:

- official source file schema against parser assumptions;
- value labels/codes;
- month/version consistency;
- input checksums;
- crosswalk coverage;
- weighting totals;
- worker-share versus hour-share differences;
- suppression output;
- actual-hours primary specification;
- usual-hours sensitivity;
- temporal/influence robustness.

Do not publish any empirical composition residual until those checks pass.

## 10. Required new artifacts for Release 1.1

When real CPS execution occurs, add:

- `data/derived/composition/<version>/composition.json`;
- `data/derived/composition/<version>/coverage.csv`;
- `data/derived/composition/<version>/sensitivity.csv`;
- `data/derived/composition/<version>/validation_checks.json`;
- `docs/validation/CPS_Q2_2026_VALIDATION.md`;
- input manifest with checksums/source URLs/retrieval dates;
- tests pinning representative mapped cells and fail-closed behavior.

The composition artifact should record the source commit, CPS months/checksums, crosswalk versions, weighting basis, coverage, suppression reason, and build identity.

## 11. Source-rights work

Create a durable source decision record rather than keeping permission status in email/chat.

Required file once contact occurs:

`docs/source-rights/RPS_SOURCE_DECISION.md`

Fields:

- provider/contact;
- date;
- scope requested;
- permission result;
- permitted storage;
- permitted transformation;
- permitted publication/redistribution;
- attribution language;
- update mechanism;
- uncertainty/microdata availability;
- engineering consequence.

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
- accessibility claims require screen-reader/keyboard/automated-browser evidence;
- performance claims require measured evidence;
- deployment must be tied to an exact commit/artifact identity;
- private paths and raw observations must be absent from the deployed artifact;
- the release must state the difference between direct evidence, derived diagnostics, and unexecuted experimental research.

## 14. Definition of the final vision

The long-run system is a versioned empirical observatory that can ingest new RPS waves, detect revisions, regenerate national/industry/occupation evidence, assess stability, optionally compute independently validated composition counterfactuals, and preserve analytical history.

The mature product should answer not just **who uses GenAI**, but **where adoption converts into routine use, actual working-time penetration, and reported benefit; where that conversion is unstable; and what subsequent research is needed to explain the wedge**.

Its credibility comes from refusing to collapse availability, adoption, workflow penetration, reported savings, and economic realization into one score or one causal story.
