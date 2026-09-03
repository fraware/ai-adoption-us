# GenAI at Work — U.S. AI Adoption Observatory

A rights-aware, auditable research and data product for studying how generative AI moves from **work adoption** into **routine use**, **AI-assisted working time**, and **self-reported time savings** in the United States.

This repository is the canonical public engineering and research surface for the project. It contains the rights-safe application source, analysis code, registries, derived public results, methodology, validation records, product specifications, and release controls.

> Core research question: **How is generative AI moving from availability and adoption into actual work?**

The project does **not** estimate a single aggregate “AI impact” number and does **not** treat reported time savings as measured labor productivity.

## Current state

The Observatory v1 release pipeline is operational through exact-candidate staging. No Observatory release has been promoted yet. The current release process retrieves the authorized published-aggregate RPS source into a private candidate workspace, validates the registered source inventory, builds the bounded public observation view and derived diagnostics, composes the complete RPS/CPS/OEWS/BTOS baseline, and stops at an explicit human-review gate. Promotion additionally requires exact candidate identity, independently verified CI evidence, and the remaining trusted rehydration proof.

Verified in the current release architecture:

- canonical RPS metadata registry: **131 source series** = 5 national + 60 industry + 66 occupation;
- latest authorized live source candidate: **962 observations** across the registered 131-series source history, spanning Q3 2024–Q2 2026 where observations are available;
- complete common A/H/S subgroup window: **882 cells** = (20 industries + 22 occupations) × 3 constructs × 7 quarters, Q4 2024–Q2 2026;
- bounded public RPS view: 35 national-history observations across seven quarters, plus 60 latest industry and 66 latest occupation A/H/S observations for Q2 2026;
- deterministic longitudinal diagnostics, rank-stability analysis, and leave-one-group-out checks;
- official Q2 2025 and Q2 2026 CPS Basic Monthly inputs executed through the composition pipeline, with versioned worker-share, actual-main-job-hour, coverage, sensitivity, and reliability artifacts;
- occupation-adjusted RPS industry residuals produced as explicitly descriptive derived evidence, with no causal or productivity interpretation;
- official May 2025 OEWS staffing data executed as an independent establishment-side composition robustness source;
- preregistered BTOS–RPS industry triangulation produced under an explicit cross-construct interpretation boundary;
- explicit web `DATA_MODE`; no implicit fallback into private source data;
- permanent CI covering the public Python suite, compilation, Ruff, strict mypy, governance/privacy scans, locked `npm ci`, TypeScript, optimized production build, private-build scan, server startup, and public-route HTTP smoke tests;
- rendered-browser QA remains a separate launch-quality gate, together with the final deployment audit and explicit release review.

Private RPS source-input bytes are intentionally **not in this public repository** and are never copied into the public release bundle. See `docs/PRIVATE_RESEARCH_ASSETS.md`.

## Scientific result in one paragraph

Across all seven common A/H/S quarters from Q4 2024 through Q2 2026, the relationship between work adoption and AI-assisted working time is more tightly aligned across **occupations** than across **industries** under both Pearson and Spearman measures. Adoption rankings are more persistent than assisted-hours rankings in **20 of 21** quarter-pair comparisons at both aggregation levels. Across occupations, adoption explains more cross-sectional variation in reported savings than assisted hours in all **7 of 7** quarters and all **154 of 154** leave-one-occupation checks. Across industries, the ordering changes by quarter: assisted hours has the higher univariate R² in **4 of 7** quarters and adoption in **3 of 7**. These findings are descriptive, aggregate, and non-causal.

See `docs/RESULTS.md` for the full result table and interpretation limits.

## Repository map

```text
apps/web/                         Next.js data publication
  app/                            Routes: home, industries, occupations, methodology, sources, blog
  components/                     Plot and release-mode components
  lib/                            Data and derived-results loaders
  tests/browser/                  Rendered browser/accessibility QA
content/                          Editorial source notes
data/
  contracts/                      Canonical observation schema
  derived/longitudinal/           Rights-safe longitudinal results
  derived/composition/            Rights-safe CPS/OEWS composition and robustness evidence
  derived/btos_rps/               Rights-safe cross-source triangulation evidence
  registry/                       Source registries, crosswalks, release contracts, and claim inventory
  audit/private/                  NEVER public; absent from this repository
src/genai_at_work/                Python research/analysis library
scripts/                          Builders, validators, release tooling
tests/                            Scientific, governance, composition, and release tests
docs/                             Product, method, results, architecture, roadmap, handoff, QA
.github/workflows/                Release CI and candidate-review workflows
```

## Data modes

The web application requires an explicit `DATA_MODE`:

- `derived_only` — public rights-safe mode. Renders approved derived publication evidence and, when present in the promoted release bundle, the bounded attributed RPS observation view. It does not expose private source-input bytes, a historical subgroup database, or a generic source query API.
- `audit_snapshot` — private research mode for explicitly supplied private audit material; it is not the public release path.
- `fred_live_no_store` — reserved for a separately governed server-side source adapter and is not used as an implicit fallback by the public application.

There is no silent fallback between modes.

## Composition evidence boundary

For industry `j`, occupation `o`, and period `t`:

- adoption composition uses CPS worker-share weights;
- assisted-hours and reported-savings composition use CPS actual-main-job-hour shares;
- usual hours are retained only as a labeled sensitivity;
- May 2025 OEWS is an independent establishment-side robustness source, not a replacement for CPS.

The canonical residual is:

`occupation-adjusted industry-context residual = observed industry value - occupation-composition counterfactual`

The residual is published only as a descriptive diagnostic. It must not be labeled an organizational effect, organizational quality, efficiency, productivity, or a causal effect without a separate identification strategy. Custom pooled CPS composition vectors also do not receive design-based confidence intervals unless an approved survey-covariance method is supplied.

## Validation

Python 3.12+:

```bash
python -m pip install -e '.[dev]'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src pytest -q
python -m compileall -q src scripts
ruff check src tests scripts
mypy src
```

The authorized release pipeline builds source candidates only in private/external workspaces. Public-tree governance checks reject private RPS inputs from the repository and public client build.

Web application:

```bash
cd apps/web
npm ci
npm run lint
DATA_MODE=derived_only npm run build
DATA_MODE=derived_only npm run dev
```

Permanent CI enforces the stronger locked-install contract: strict Python checks, `npm ci`, TypeScript, the rights-safe optimized build, private-build scan, production-server startup, and all public-route HTTP smoke tests. Candidate promotion separately verifies CI runs against the exact repository, candidate commit, branch, workflow, event, and successful conclusion.

## Essential documents

Start here:

1. `docs/ENGINEERING_HANDOFF.md` — technical handoff and acceptance contracts.
2. `docs/RESULTS.md` — verified empirical results and interpretation limits.
3. `docs/ROADMAP.md` — current roadmap, priorities, dependencies, and definitions of done.
4. `docs/ARCHITECTURE.md` — system/data architecture and trust boundaries.
5. `docs/REPRODUCIBILITY.md` — build and regeneration contracts.
6. `docs/RELEASE_CHECKLIST.md` — launch checklist.
7. `docs/methodology.md` — scientific methodology.
8. `docs/product-spec.md` — product specification.
9. `docs/source-provenance.md` — source and rights provenance.
10. `docs/source-rights/RPS_PERMISSION_REQUEST.md` — historical source-rights decision record.
11. `VALIDATION_2026-08-31.md` — historical public-handoff validation record.

## Product invariants

These must remain true in every release:

- Adoption is not workflow penetration.
- Assisted hours are not hours saved.
- Reported hours saved are not measured labor productivity.
- Industry residuals are not automatically organizational effects.
- Cross-sectional correlations are descriptive absent a separate identification strategy.
- Small/noisy subgroup cells must not become leaderboards without stability diagnostics.
- Worker-share weights are used for adoption composition; work-hour-share weights are used for assisted-hours and reported-savings composition.
- Suppressed or unsupported composition cells fail closed; they are never silently renormalized into apparently complete estimates.
- Private RPS source-input observations never enter a public build artifact.
- The bounded public observation contract does not authorize an unrestricted historical subgroup database, bulk export, or generic query API.
- Public availability of a source does not by itself authorize storage, mirroring, API redistribution, or independent republication beyond the reviewed rights contract.

## Release sequence

- **Observatory v1 / Release 1:** bounded national history and latest industry/occupation A/H/S views; seven-quarter longitudinal diagnostics; CPS occupation-composition evidence and descriptive residuals; OEWS robustness; BTOS–RPS triangulation; methodology, provenance, and technical essay. Exact-candidate staging is operational; explicit human review, exact rehydration, promotion, rendered/manual QA, and deployment audit remain gates.
- **Post-Release 1:** stronger uncertainty treatment where supported, richer composition or task views only under explicit provenance and rights contracts, and mechanism-oriented analysis that maintains the distinction between descriptive decomposition and causal identification.
- **Research v2:** worker × task × occupation × industry/context × time mechanism analysis with stronger identification, uncertainty, and outcome evidence.

The detailed specifications and acceptance criteria are in `docs/ROADMAP.md` and `docs/ENGINEERING_HANDOFF.md`.
