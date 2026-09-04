# GenAI at Work — U.S. AI Adoption Observatory

GenAI at Work is a public research and data project that tracks how generative AI is entering U.S. work: who uses it, how regularly it is used, how much working time is AI-assisted, and how much time workers report saving.

The project is built around a simple measurement principle: **AI adoption is not the same thing as intensive use, reported time savings, or measured productivity.** Those are different empirical objects and should be analyzed separately.

**Public site:** https://fraware.github.io/ai-adoption-us/  
**Current release:** `v1.0.0`, published 4 September 2026

## What the observatory measures

The observatory distinguishes five stages of workplace AI diffusion:

| Measure | Question | Interpretation |
| --- | --- | --- |
| Availability / capability | Can an AI system perform or assist a task? | Technical or theoretical capability, not realized use |
| Work adoption | Who reports using generative AI for their job? | Extensive-margin workplace use |
| Recent / routine use | How regularly is generative AI used for work? | Frequency of realized use |
| AI-assisted working time | What share of working time involves AI assistance? | Depth of workflow use |
| Reported time savings | How much additional time do users believe the same work would have taken without AI? | Self-reported counterfactual time savings, not measured productivity |

Future work may connect these measures to realized outcomes such as output, wages, employment, or firm performance, but Release 1 does not estimate those effects.

## Main findings in Release 1

Release 1 covers seven common quarterly observations from Q4 2024 through Q2 2026 for 20 industries and 22 occupations.

Three findings are especially robust within that descriptive window:

1. **Adoption and AI-assisted working time are more tightly aligned across occupations than across industries.** Pearson and Spearman correlations between the two measures are higher across occupations in all seven quarters.
2. **Across occupations, adoption is a more consistent descriptor of reported time savings than AI-assisted hours.** `R²(S~A) > R²(S~H)` in all seven quarters and in all 154 leave-one-occupation-out checks.
3. **Adoption rankings are more persistent than AI-assisted-hours rankings.** This holds in 20 of 21 quarter-pair comparisons for both industries and occupations.

These are aggregate, descriptive relationships. They do not identify causal effects of AI use, organizational quality, or productivity.

See [docs/RESULTS.md](docs/RESULTS.md) for the full tables and interpretation limits.

## Data sources

The observatory combines four complementary U.S. data systems:

- **RPS / Generative AI Adoption Tracker** — workplace generative-AI adoption, use frequency, AI-assisted work hours, and reported time savings.
- **Current Population Survey (CPS)** — worker-level industry × occupation composition and working-time weights used to construct occupation-composition benchmarks for industries.
- **Occupational Employment and Wage Statistics (OEWS)** — establishment-side occupation × industry staffing data used as an independent robustness check.
- **Business Trends and Outlook Survey (BTOS)** — employer-reported recent AI use used for cross-source industry comparison.

The sources measure different populations and constructs. The analysis preserves those differences instead of merging them into a single AI-adoption indicator.

Detailed provenance and use constraints are documented in [docs/source-provenance.md](docs/source-provenance.md).

## Industry composition analysis

A central question is whether industry-level differences in workplace AI use are partly explained by differences in occupational composition.

For industry `j`, occupation `o`, and quarter `t`, the project constructs occupation-composition benchmarks using CPS data:

```text
adoption benchmark       = Σ occupation worker share × occupation adoption
assisted-hours benchmark = Σ occupation work-hour share × occupation assisted-hours share
savings benchmark        = Σ occupation work-hour share × occupation reported-savings share
```

The difference between an observed industry value and its occupation-composition benchmark is reported as an **occupation-adjusted industry residual**.

This residual is descriptive. It is not interpreted as a firm effect, management effect, efficiency estimate, or causal effect.

See [docs/methodology.md](docs/methodology.md) for the full methodology.

## Repository structure

```text
apps/web/                 Next.js public data website
content/                  Editorial and publication content
data/
  contracts/              Observation and artifact schemas
  derived/                Versioned public analysis outputs
  registry/               Source, taxonomy, rights, and release metadata
  releases/               Published release artifacts
src/genai_at_work/        Python analysis and data-processing library
scripts/                  Reproduction, validation, and publication utilities
tests/                    Scientific, data-integrity, and software tests
docs/                     Methodology, results, provenance, and technical documentation
.github/workflows/        Continuous integration and publication workflows
```

The public repository intentionally excludes source material that the project is not authorized to redistribute.

## Reproduce the public code

### Python

Requirements: Python 3.12+

```bash
python -m pip install -e '.[dev]'
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src pytest -q
python -m compileall -q src scripts
ruff check src tests scripts
mypy src
```

### Web application

```bash
cd apps/web
npm ci
npm run lint
DATA_MODE=derived_only npm run build
DATA_MODE=derived_only npm run dev
```

Some source-dependent analyses require reacquiring official upstream data because not every source file can be redistributed in this repository. Reproduction instructions and the distinction between public and source-dependent workflows are documented in [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md).

## Documentation

The documentation is organized by reader need in [docs/README.md](docs/README.md).

Recommended starting points:

- [Results](docs/RESULTS.md)
- [Methodology](docs/methodology.md)
- [Source provenance](docs/source-provenance.md)
- [Data model](docs/data-model.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Reproducibility](docs/REPRODUCIBILITY.md)
- [Release 1 notes](docs/RELEASE1_NOTES.md)
- [Roadmap](docs/ROADMAP.md)

## Scientific interpretation limits

Release 1 does **not** establish:

- measured labor-productivity effects;
- output, TFP, GDP, wage, or employment effects;
- causal effects of generative-AI adoption or use intensity;
- organizational or management effects from industry residuals;
- equivalence between worker-reported RPS measures and employer-reported BTOS measures;
- full design-based confidence intervals for custom pooled CPS composition vectors.

The project reports unsupported quantities as unavailable instead of filling them through undocumented assumptions.

## Data access and reuse

Third-party data remain subject to their original terms and the source-specific decisions documented in this repository. Public availability of a dataset is not treated as automatic permission for unrestricted mirroring or redistribution.

Private RPS source-input files and private audit material are excluded from the public repository. The published release contains only the observations and derived outputs covered by the documented public-use boundary.

See [docs/PRIVATE_RESEARCH_ASSETS.md](docs/PRIVATE_RESEARCH_ASSETS.md) and [docs/source-rights/RPS_SOURCE_DECISION.md](docs/source-rights/RPS_SOURCE_DECISION.md).

## Contributing

Contributions are welcome when they preserve the project's measurement definitions, provenance, source-use constraints, and interpretation limits. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

The repository's original code and documentation are licensed under the [MIT License](LICENSE).

Third-party data and source materials remain subject to their original terms and the source-specific rights decisions documented in this repository. The MIT License does not override those third-party terms.
