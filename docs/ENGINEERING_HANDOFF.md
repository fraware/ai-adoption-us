# Engineering handoff — complete implementation specification

## 1. Mission

The repository is not a generic dashboard. It is an empirical publication whose credibility comes from preserving measurement distinctions and provenance while making the adoption-to-workflow-conversion problem legible.

The engineering team owns three simultaneous constraints:

1. **scientific correctness** — constructs/denominators cannot drift;
2. **rights safety** — private source observations cannot leak into public artifacts;
3. **product quality** — a sophisticated reader should be able to understand evidence, caveats, and provenance without opening the code.

## 2. Non-negotiable scientific contracts

### Metric semantics

`A` — work adoption/use, extensive margin.

`H` — share of work hours during which GenAI was actively used; a workflow-penetration measure, not time saved.

`S` — self-reported counterfactual hours saved as a share of work time; not measured labor productivity.

Do not rename `S/H` as efficiency. If used at all, describe it mechanically as reported saved hours per actively assisted hour and explain why it may exceed 1.

### Cross-sectional analysis

Every R²/correlation in the current result layer is descriptive and aggregate.

No significance language unless subgroup uncertainty becomes available and an explicit inferential procedure is implemented.

### Composition weighting

Adoption → CPS worker shares.

Assisted hours and savings → CPS actual-main-job-hour shares.

This distinction is a hard testable invariant.

### Residual language

Canonical term: **occupation-adjusted industry-context residual**.

Forbidden interpretations absent separate research design:

- organizational effect;
- organizational quality;
- organizational efficiency;
- productivity effect.

## 3. Source/rights contracts

The public repository is rights-safe.

Never commit:

`data/audit/private/rps_subgroup_5q_audit.json`

Public builds must use `DATA_MODE=derived_only` unless a future source-rights decision explicitly changes the architecture.

Any new source adapter must document:

- provider;
- terms;
- storage/cache policy;
- redistribution permission;
- attribution;
- source vintage;
- retrieval/revision behavior.

## 4. Current verified code surface

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

## 5. Current result contracts

The generated longitudinal layer must preserve these assertions unless a source revision legitimately changes the input fixture:

- 20 industries × 22 occupations? No: levels are separate; 20 industries and 22 occupations, each with A/H/S, over five waves = 630 rows total.
- occupation Pearson A-H > industry Pearson A-H in all five waves;
- occupation Spearman A-H > industry Spearman A-H in all five waves;
- occupation R²(S~A) > R²(S~H) in all five waves;
- occupation leave-one-out A beats H = 110/110;
- industry H beats A for S in 3/5 waves, not 5/5;
- adoption rank stability > H stability in 10/10 quarter pairs for both aggregation levels;
- adoption rank stability > S stability in 10/10 quarter pairs for both levels.

Do not hard-code these in editorial prose independently of generated data where the application can load them from the derived artifact.

## 6. CI specification

Required PR checks:

### Python

- Python 3.12;
- install `.[dev]`;
- `pytest -q`;
- `python -m compileall -q src scripts`;
- `ruff check src tests scripts`;
- `mypy src` once the current type surface is green enough to make this gating rather than advisory.

### Web

- Node version compatible with Next 16;
- clean dependency install;
- TypeScript check;
- `DATA_MODE=derived_only npm run build`;
- no private fixture required.

### Governance

- scan repository/build tree for `data/audit/private`;
- verify canonical registry cardinality/identity;
- verify generated public derived artifacts committed intentionally.

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

Missing/suppressed data must state *why* it is unavailable.

Examples:

- unsupported quarter;
- private fixture absent;
- coverage suppression;
- production source disabled.

Never render zero for missing.

## 8. Release 1 completion work

Implement exactly the gates in `docs/ROADMAP.md` Track 1.

Priority order:

1. real Next build / lockfile / CI;
2. browser QA;
3. screen-reader + axe/Lighthouse;
4. deployment audit;
5. editorial finalization;
6. release tag.

Composition must **not** block Release 1.

## 9. Release 1.1 composition work

Implement exactly the CPS contracts in `docs/ROADMAP.md` Track 3.

The existing code is the starting implementation, not proof that the real-data output is scientifically green.

Engineers/researchers must inspect:

- source file schema against parser assumptions;
- value labels/codes;
- month/version consistency;
- crosswalk coverage;
- weighting totals;
- suppression output;
- sensitivity results.

Do not publish any real composition residual until those checks pass.

## 10. Required new artifacts for Release 1.1

When real CPS execution occurs, add:

- `data/derived/composition/<version>/composition.json`;
- `data/derived/composition/<version>/coverage.csv`;
- `data/derived/composition/<version>/sensitivity.csv`;
- `data/derived/composition/<version>/validation_checks.json`;
- `docs/validation/CPS_Q2_2026_VALIDATION.md`;
- input manifest with checksums and source URLs;
- tests pinning representative mapped cells and fail-closed behavior.

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
- permitted publication;
- attribution language;
- update mechanism;
- uncertainty/microdata availability;
- engineering consequence.

## 12. Review standard

A PR touching empirical logic should answer:

1. What estimand/construct changes?
2. What denominator changes?
3. What source/version changes?
4. What generated results change?
5. Are old results invalidated or merely extended?
6. Does the rights boundary change?
7. What new test prevents regression?

A PR touching presentation should state whether any claim or number changed. If yes, it is not “presentation-only.”

## 13. Definition of final vision

The long-run system is a versioned empirical observatory that can ingest new RPS waves, detect revisions, regenerate national/industry/occupation evidence, assess stability, optionally compute independently validated composition counterfactuals, and preserve analytical history.

The final product should answer not just **who uses GenAI**, but **where adoption converts into actual working-time penetration and reported benefit, where that conversion is unstable, and what subsequent research is needed to explain the wedge**.
