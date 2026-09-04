# Product specification

Status date: **2026-09-04**

## 1. Objective

GenAI at Work is a technical data publication built around one question:

> How is generative AI moving from availability and adoption into actual work?

The product does not estimate a single aggregate “AI impact” number. It exposes distinct stages of workplace diffusion and use, the measurement objects behind them, composition-adjusted descriptive evidence, and the limits of what those data support.

## 2. Audience

Primary audiences are AI researchers, economists and labor-market researchers, firm leaders designing AI deployment, policy researchers, and technically sophisticated journalists or investors. The public interface should remain legible to informed general readers without weakening the scientific distinctions.

## 3. Editorial contract

The site should make fewer claims than a conventional dashboard and expose more of the measurement machinery.

At the point of interpretation, a reader should be able to determine:

1. what is measured;
2. the relevant population and denominator;
3. whether the quantity is directly reported, reconstructed, self-reported counterfactual, composition-adjusted, or cross-source descriptive evidence;
4. the source/vintage and relevant coverage boundary;
5. what cannot be inferred from the result.

The core editorial invariants are:

- adoption is distinct from workflow penetration;
- assisted hours are distinct from reported hours saved;
- reported savings are distinct from measured labor productivity;
- composition-adjusted residuals are descriptive standardization residuals, not identified organizational effects;
- BTOS employer AI use and RPS worker GenAI adoption are distinct cross-source constructs;
- unsupported or suppressed evidence is shown as unavailable, not silently completed.

## 4. Release 1 public surface

### `/` — AI at Work

The landing page is a narrative research publication rather than a KPI grid. It presents the national adoption/use sequence, longitudinal evidence, selected industry/occupation relationships, and direct paths to methodology and provenance.

### `/explore/industries`

The industry evidence surface presents the supported RPS A/H/S cross-section and derived industry analysis, including the occupation-composition counterfactual/residual evidence where the release contract supports it. Any residual is labeled as descriptive and accompanied by the relevant weighting, coverage, and interpretation boundary.

### `/explore/occupations`

The occupation evidence surface exposes the corresponding supported RPS A/H/S evidence and longitudinal context, enabling comparison between occupation and industry structures without treating the two aggregation levels as interchangeable.

### `/methodology`

A first-class scientific-method page covering source populations, construct definitions, denominator semantics, composition weighting, uncertainty limitations, cross-survey alignment, classification/crosswalk rules, revisions, rights boundaries, and reproducibility.

### `/sources`

A first-class provenance surface identifying the RPS/FRED, CPS, OEWS, and BTOS evidence families; public/private source boundaries; attribution; and the distinction between bounded public observation products and private source-input material.

### `/blog/after-adoption`

A technical essay interpreting the release evidence under the same claim and measurement contracts as the data surfaces. Governed numerical/source claims are bound to the reviewed repository files through the release claim-surface mechanism.

### Public data boundary

Release 1 does **not** provide an unrestricted historical subgroup database, generic raw-source query API, or bulk mirror of the private RPS source candidate.

The promoted release may expose only the reviewed rights-safe artifacts declared in its immutable release manifest. For RPS observations, the Release 1 contract is bounded to the attributed national-history presentation plus the latest complete industry and occupation A/H/S views. Derived CPS/OEWS/BTOS and longitudinal artifacts are published only when declared by the reviewed release.

## 5. Evidence included in Release 1

The governed Release 1 baseline includes:

- seven-quarter common RPS A/H/S longitudinal diagnostics, Q4 2024–Q2 2026;
- bounded national-history and latest Q2 2026 industry/occupation RPS presentation views;
- Q2 2025 and Q2 2026 CPS industry × occupation composition evidence;
- occupation-adjusted industry-context residual diagnostics with descriptive-only interpretation;
- May 2025 OEWS establishment-side composition robustness;
- preregistered Q2 2026 BTOS–RPS descriptive triangulation;
- methodology, provenance, and technical-essay surfaces bound to the same reviewed release architecture.

This is the first-release scope. CPS composition and BTOS triangulation are no longer deferred to hypothetical Release 1.1/1.2 stages.

## 6. Interaction and visual design

The visual system should read as an editorial research publication rather than a SaaS dashboard.

- charts are used only where they improve interpretation;
- labels and annotations state measurement meaning and caveats directly;
- color encodes variables or selection, not decorative status;
- tables provide accessible equivalents for core visual evidence;
- layouts remain usable at supported responsive widths;
- keyboard focus, semantic structure, reduced motion, and contrast remain part of the release QA contract;
- no ranking or leaderboard treatment is applied to unsupported/unstable cells.

The actual release UI is authoritative over speculative controls described in earlier design notes. New routes or controls require implementation, tests, accessibility review, and release-contract inclusion before being represented as shipped product functionality.

## 7. Data modes

The public web application uses explicit `DATA_MODE` selection.

- `derived_only` is the public rights-safe mode. It renders approved derived evidence and, when available in the promoted release, the bounded RPS observation view.
- `audit_snapshot` is private research mode for explicitly supplied private audit material and is never the public release path.
- `fred_live_no_store` remains a separately governed server-side adapter mode and is not an implicit public fallback.

There is no silent fallback among modes.

## 8. Release and trust model

A product build is not a publication authorization.

The public Release 1 object is defined by:

1. an exact canonical repository commit;
2. a validated scientific source vintage;
3. a complete global Observatory candidate;
4. governed claim-surface hashes;
5. an immutable stage and zero-failure review gate;
6. explicit human scientific/editorial/source-rights review;
7. exact post-review source rehydration reproducing the reviewed candidate/stage identities;
8. human attestation bound to the deterministic rehydration identity and exact CI evidence;
9. immutable promotion into the release registry/tree;
10. a validated release-only authorization commit;
11. GitHub Pages deployment and live-origin audit from that authorization commit.

Only after those gates pass is the formal tag/GitHub Release created.

## 9. Post-Release-1 product work

The first release deliberately leaves several extensions outside the launch gate:

- a dedicated experimental composition explorer (#8);
- design-based uncertainty for custom CPS composition vectors (#14);
- task/exposure versus realized-adoption evidence under its separate provenance/rights gate (#17);
- richer worker × task × occupation × industry/time mechanism research (#10).

These extensions must preserve the same construct, rights, provenance, uncertainty, and release disciplines. Their open issue status does not imply that Release 1 is incomplete.
