# GenAI at Work — U.S. AI Adoption Observatory

A rights-aware, auditable research and data product for studying how generative AI moves from **work adoption** into **routine use**, **AI-assisted working time**, and **self-reported time savings** in the United States.

This repository is the canonical public engineering and research surface for the reconstructed project. It contains the rights-safe application source, analysis code, registries, derived public results, methodology, validation records, product specifications, and the dependency-aware roadmap for the remaining work.

> Core research question: **How is generative AI moving from availability and adoption into actual work?**

The project does **not** estimate a single aggregate “AI impact” number and does **not** treat reported time savings as measured labor productivity.

## Current state

Release 1 is code-complete at the rights-safe source level and the permanent production-build gate is closed. The project is now advancing through three distinct kinds of remaining gate: rendered/manual product QA, production deployment audit, and the external RPS source-rights decision required for a full direct-observation observatory.

Verified at the current public state:

- canonical RPS metadata registry: **131 source series** = 5 national + 60 industry + 66 occupation;
- privately audited subgroup research panel: **630 cells** = (20 industries + 22 occupations) × 3 constructs × 5 quarters, Q2 2025–Q2 2026;
- deterministic longitudinal diagnostics and leave-one-out checks;
- rights-safe longitudinal results under `data/derived/longitudinal/`;
- official Q2 2025 and Q2 2026 CPS Basic Monthly inputs executed through the composition pipeline, with versioned worker-share, actual-main-job-hour, coverage, sensitivity, and reliability artifacts under `data/derived/composition/`;
- official May 2025 OEWS staffing data executed as an independent establishment-side composition robustness source, with cross-vintage and coverage diagnostics retained separately from CPS;
- occupation-adjusted RPS industry residuals **not yet published** because the compatible public RPS observation path remains rights-gated and the residual robustness gate must run on the authorized join;
- static FRED-to-public-JSON export retired;
- explicit web `DATA_MODE`; no implicit fallback into private data;
- permanent CI covering the public Python suite, compilation, Ruff, strict mypy, governance/privacy scans, locked `npm ci`, TypeScript, optimized production build, private-build scan, server startup, and public-route HTTP smoke tests;
- an automated rendered-browser QA workflow covering stable Chrome, Firefox, a WebKit engine proxy, responsive widths, keyboard entry, axe, runtime/console errors, Lighthouse, screenshots, and evidence artifacts;
- real Safari/iOS, screen-reader/manual interaction review, field performance where meaningful, and the deployment audit remain launch gates.

The private 630-cell RPS audit fixture is intentionally **not in this public repository**. See `docs/PRIVATE_RESEARCH_ASSETS.md`.

## Scientific result in one paragraph

Across the five audited waves, the relationship between work adoption and AI-assisted working time is more tightly organized by **occupation** than by **industry** in every wave. Adoption rankings are also substantially more stable over time than assisted-hours rankings at both aggregation levels. Across occupations, adoption explains more cross-sectional variation in reported savings than assisted hours in all five waves and all 110 leave-one-occupation-out comparisons. Across industries, the ordering between adoption and assisted hours as descriptors of reported savings changes by wave; the Q2 2026 result is therefore not treated as a universal law. All of these findings are descriptive, aggregate, and non-causal.

See `docs/RESULTS.md` for the complete result table and interpretation limits.

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
  registry/                       RPS and CPS registries/crosswalks
  audit/private/                  NEVER public; absent from this repository
src/genai_at_work/                Python research/analysis library
scripts/                          Builders, validators, rights-safe exporter
tests/                            Scientific, governance, CPS, composition, web-release tests
docs/                             Product, method, results, architecture, roadmap, handoff, QA
.github/workflows/                Release CI and rendered-browser validation
```

## Data modes

The web application requires an explicit `DATA_MODE`:

- `derived_only` — public rights-safe mode. Renders approved derived publication evidence without the raw RPS observation fixture.
- `audit_snapshot` — private research mode. Requires `data/audit/private/rps_subgroup_5q_audit.json`.
- `fred_live_no_store` — reserved for a future rights-reviewed server-side source adapter and currently fails closed.

There is no silent fallback between modes.

## Composition evidence boundary

The repository now contains validated composition inputs, but that is not equivalent to a published RPS residual.

For industry `j`, occupation `o`, and period `t`:

- adoption composition uses CPS worker-share weights;
- assisted-hours and reported-savings composition use CPS actual-main-job-hour shares;
- usual hours are retained only as a labeled sensitivity;
- May 2025 OEWS is an independent establishment-side robustness source, not a replacement for CPS.

The canonical residual is:

`occupation-adjusted industry-context residual = observed industry value - occupation-composition counterfactual`

It remains unavailable in the public product until rights-cleared RPS observations can be joined to the validated composition inputs and the required robustness checks pass. It must not be labeled an organizational effect, organizational quality, efficiency, or productivity effect without a separate identification strategy.

## Validation

Python 3.12+:

```bash
python -m pip install -e '.[dev]'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src pytest -q
python -m compileall -q src scripts
ruff check src tests scripts
mypy src
```

For a private research checkout with the audit fixture restored:

```bash
PYTHONPATH=src python scripts/build_longitudinal.py \
  --fixture data/audit/private/rps_subgroup_5q_audit.json \
  --output-dir data/derived/longitudinal
```

The builder is expected to reproduce the committed longitudinal publication artifacts under the applicable frozen source vintage.

Web application:

```bash
cd apps/web
npm ci
npm run lint
DATA_MODE=derived_only npm run build
DATA_MODE=derived_only npm run dev
```

The first genuine networked production build was completed on **2026-08-31**. Permanent CI subsequently established the stronger locked-install contract: strict Python checks, `npm ci`, TypeScript, the rights-safe optimized build, private-build scan, production-server startup, and all public-route HTTP smoke tests. Rendered-browser QA is now a separate executable gate rather than an inferred property of the source code.

## Essential documents

Start here:

1. `docs/ENGINEERING_HANDOFF.md` — technical handoff and acceptance contracts.
2. `docs/RESULTS.md` — verified empirical results and precise interpretation limits.
3. `docs/ROADMAP.md` — current roadmap, priorities, dependencies, and definitions of done.
4. `docs/ARCHITECTURE.md` — system/data architecture and trust boundaries.
5. `docs/REPRODUCIBILITY.md` — build and regeneration contracts.
6. `docs/RELEASE_CHECKLIST.md` — launch checklist.
7. `docs/methodology.md` — scientific methodology.
8. `docs/product-spec.md` — product specification.
9. `docs/source-provenance.md` — source and rights provenance.
10. `docs/source-rights/RPS_PERMISSION_REQUEST.md` — decision-grade RPS rights/feed request.
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
- Private RPS audit observations never enter a public build artifact.
- Public availability of a source does not by itself authorize persistent storage, mirroring, API redistribution, or independent republication.

## Release sequence

- **Release 1:** rights-safe national/industry/occupation measurement publication, methodology, sources, five-wave stability evidence, and technical essay. Engineering build is green; rendered/manual QA and deployment remain open. Direct observation surfaces remain governed by the RPS source-rights decision.
- **Release 1.1:** validated CPS/OEWS composition foundation plus occupation-standardized RPS industry analysis and the experimental composition explorer after the authorized RPS join and residual robustness gates pass.
- **Release 1.2:** BTOS and other firm-side triangulation only where construct alignment is defensible.
- **Release 1.3:** realized task/occupation adoption versus theoretical or model-based AI exposure, conditional on provenance and publication rights for the task/occupation indices.
- **Research v2:** worker × task × occupation × industry/context × time mechanism analysis with explicit separation between descriptive decomposition and causal identification.

The detailed specifications and acceptance criteria are in `docs/ROADMAP.md` and `docs/ENGINEERING_HANDOFF.md`.
