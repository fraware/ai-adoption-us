# GenAI at Work — U.S. AI Adoption Observatory

A rights-aware, auditable research and data product for studying how generative AI moves from **work adoption** into **routine use**, **AI-assisted working time**, and **self-reported time savings** in the United States.

This repository is the canonical public engineering handoff for the reconstructed project. It contains the full rights-safe application source, analysis code, registries, derived public results, methodology, validation records, product specifications, and the detailed roadmap for the remaining work.

> Core research question: **How is generative AI moving from availability and adoption into actual work?**

The project does **not** estimate a single aggregate “AI impact” number and does **not** treat reported time savings as measured labor productivity.

## Current state

Release 1 is code-complete at the rights-safe source level. The genuine networked production-build gate is now closed; browser/accessibility and deployment validation remain before public launch.

Verified at the current public handoff state:

- canonical metadata registry: **131 source series** = 5 national + 60 industry + 66 occupation;
- privately audited subgroup research panel: **630 cells** = (20 industries + 22 occupations) × 3 constructs × 5 quarters, Q2 2025–Q2 2026;
- deterministic longitudinal diagnostics and leave-one-out checks;
- rights-safe derived results under `data/derived/longitudinal/`;
- CPS composition and residual pipeline implemented and unit-tested, but **not yet executed on real CPS data**;
- static FRED-to-public-JSON export retired;
- explicit web `DATA_MODE`; no implicit fallback into private data;
- code-level Release 1 accessibility/responsiveness pass complete;
- permanent GitHub Actions validation: **52 passed, 6 expected private-data tests skipped; compileall, Ruff, strict mypy, governance/privacy scans, and Git whitespace checks passed**;
- genuine networked web validation: Node **22.23.2**, npm **10.9.8**, Next.js **16.3.3**; locked `npm ci`, TypeScript, optimized `next build`, private-build scan, production-server startup, and public-route HTTP smoke tests passed in permanent PR CI run **33414088473**;
- browser/screen-reader QA and deployment audit remain launch gates.

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
content/                          Editorial source notes
data/
  contracts/                      Canonical observation schema
  derived/longitudinal/           Rights-safe generated results
  registry/                       RPS and CPS registries/crosswalks
  audit/private/                  NEVER public; absent from this repository
src/genai_at_work/                Python research/analysis library
scripts/                          Builders, validators, rights-safe exporter
tests/                            Scientific, governance, CPS, composition, web-release tests
docs/                             Product, method, results, architecture, roadmap, handoff
.github/workflows/                CI and genuine web-build validation
```

## Data modes

The web application requires an explicit `DATA_MODE`:

- `derived_only` — public rights-safe mode. Renders validated longitudinal diagnostics only; no raw RPS observation fixture.
- `audit_snapshot` — private research mode. Requires `data/audit/private/rps_subgroup_5q_audit.json`.
- `fred_live_no_store` — reserved for a future rights-reviewed server-side source adapter and currently fails closed.

There is no silent fallback between modes.

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

The builder is expected to reproduce the four committed longitudinal publication artifacts byte-for-byte.

Web application:

```bash
cd apps/web
npm ci
npm run lint
DATA_MODE=derived_only npm run build
DATA_MODE=derived_only npm run dev
```

The first genuine networked production build was completed in GitHub Actions on **2026-08-31**, run `33411128343`. Permanent PR run `33414088473` subsequently passed the stronger locked-install contract: strict mypy, `npm ci`, TypeScript, the rights-safe optimized build, private-build scan, production-server startup, and all public-route HTTP smoke tests. See `VALIDATION_2026-08-31.md`.

## Essential documents

Start here:

1. `docs/ENGINEERING_HANDOFF.md` — complete technical handoff and acceptance contracts.
2. `docs/RESULTS.md` — verified empirical results and precise interpretation limits.
3. `docs/ROADMAP.md` — remaining roadmap, priorities, dependencies, and definitions of done.
4. `docs/ARCHITECTURE.md` — system/data architecture and trust boundaries.
5. `docs/REPRODUCIBILITY.md` — exact build and regeneration contracts.
6. `docs/RELEASE_CHECKLIST.md` — launch checklist.
7. `docs/methodology.md` — scientific methodology.
8. `docs/product-spec.md` — product specification.
9. `docs/source-provenance.md` — source and rights provenance.
10. `VALIDATION_2026-08-31.md` — current public-handoff validation record, including the genuine production build.
11. `VALIDATION_2026-08-30.md` — prior reconstruction validation record retained for historical provenance.

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

## Release sequence

- **Release 1:** rights-safe national/industry/occupation observatory, methodology, sources, five-wave stability evidence, technical essay. Production build is green; browser/accessibility and deployment gates remain.
- **Release 1.1:** CPS occupation-composition counterfactuals and occupation-adjusted industry-context residuals after real CPS execution and robustness validation.
- **Release 1.2:** BTOS and other firm-side triangulation only where construct alignment is defensible.
- **Research v2:** worker × occupation × industry × time mechanism analysis, potentially incorporating tasks, firm policies, digital intensity, management practices, and other organizational complements.

The detailed specifications and acceptance criteria are in `docs/ROADMAP.md` and `docs/ENGINEERING_HANDOFF.md`.
