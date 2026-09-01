# GenAI at Work research landscape — 2026-09-01

## Purpose

This note records the nearest current research to the observatory's scientific program so that new analyses extend the literature instead of rediscovering results already established by the RPS authors or adjacent work.

This is a research-positioning document, not a claim that the cited papers are the only relevant literature.

## 1. Bick, Blandin, and Deming — The Rapid Adoption of Generative AI

Published in *Management Science* in 2026; earlier NBER Working Paper 32966.

Primary references:

- https://doi.org/10.1287/mnsc.2025.02523
- https://www.nber.org/papers/w32966

Core contribution relevant to this project:

- establishes nationally representative RPS measurement of generative-AI adoption and use;
- compares diffusion with PCs and the internet;
- documents occupation and industry heterogeneity;
- measures use intensity and reported time savings;
- includes early task-use questions;
- validates RPS sample composition against CPS;
- restricts the RPS/CPS comparison sample to the civilian population ages 18–64.

The published article advertises supplemental data files; Adam Blandin's research page describes the published version as including microdata and a replication package. The NBER page exposes a data appendix. Exact package contents and reuse terms remain to be inspected before incorporation into this repository.

Implication: basic descriptive claims that workplace GenAI adoption is widespread, heterogeneous by occupation/industry, and associated with meaningful reported time savings are prior art, not the observatory's novel contribution.

## 2. Bick, Blandin, Deming, and Schumacher — What Work Does Generative AI Do?

NBER Working Paper 35677, August 2026; Federal Reserve Bank of St. Louis Working Paper 2026-017.

Primary references:

- https://www.nber.org/papers/w35677
- https://doi.org/10.20955/wp.2026.017

The paper links nationally representative worker survey data to detailed occupations and tasks and constructs occupation- and task-level GenAI adoption indexes.

Key findings reported by the authors:

- adoption is widespread across occupations and tasks but remains shallow within most of them;
- at least one in five workers use GenAI in a large majority of occupations and a substantial share of tasks, while adoption remains below one half in most occupation/task cells;
- task/occupation exposure measures explain meaningful but incomplete variation in actual adoption;
- substantial adoption heterogeneity remains among workers doing similar work;
- survey-based task-use measures differ conceptually and empirically from platform chat-log measures, which tend to classify activity into more generic tasks.

Implication: simply joining RPS adoption to O*NET tasks or constructing task-level adoption indexes would duplicate current work. Any task-based extension in GenAI at Work must target a different estimand or evidence object, such as conversion from adoption into assisted working time or reported benefit, longitudinal persistence, worker/context heterogeneity conditional on task structure, or cross-source validation.

## 3. Bick, Blandin, Deming, Fuchs-Schündeln, and Jessen — Mind the Gap: AI Adoption in Europe and the U.S.

NBER Working Paper 34995 / Spring 2026 Brookings Papers on Economic Activity work.

Primary references:

- https://www.nber.org/papers/w34995
- https://www.brookings.edu/articles/mind-the-gap-ai-adoption-in-europe-and-the-us/

Relevant findings:

- U.S. worker AI adoption exceeds adoption in the European comparison countries in the authors' 2026 survey;
- worker demographics and firm composition explain part of international adoption gaps;
- employer encouragement, tool provision, and personnel-management practices are strongly associated with worker adoption;
- industry AI adoption is positively associated with recent productivity growth, but the authors explicitly do not establish causality;
- worker-side and firm-side adoption measures are not treated as equivalent constructs.

Implication: employer policy and management practices are already empirically implicated in adoption. An occupation-adjusted industry gap in this observatory cannot be presented as discovering that organizational context exists. The research contribution must be narrower and stronger: quantify the residual after explicit occupation composition standardization, test its persistence and influence structure, and then evaluate competing mechanisms with richer data.

## 4. What remains differentiated and scientifically valuable

### A. Adoption-to-workflow conversion

The observatory separates:

`adoption -> recent/routine use -> share of working time actively assisted -> reported counterfactual benefit`.

The existing nearest literature is much richer on adoption than on the stability and cross-level structure of this conversion chain. The frozen five-wave results already suggest that occupation structure organizes adoption-to-assisted-hours coupling more tightly than broad industry structure.

### B. Longitudinal structural stability

The observatory tests which relationships persist across survey waves instead of promoting one current cross-section into a structural claim.

Key objects include:

- rank stability by metric;
- stability of adoption-to-assisted-hours coupling;
- wave dependence of adoption/assisted-hours relationships with reported savings;
- influence and leave-one-out robustness;
- revision/vintage sensitivity once a rights-cleared live history is available.

### C. Occupation-standardized industry analysis

The CPS program asks a specific composition question that is distinct from documenting raw industry heterogeneity:

> How much of broad industry variation in adoption, assisted working time, and reported savings is mechanically accounted for by occupational composition?

This requires separate worker-share weights for adoption and actual-main-job-hour-share weights for assisted hours/reported savings. The remaining difference is a descriptive **occupation-adjusted industry-context residual**, not an organizational or productivity effect.

### D. Conversion heterogeneity conditional on tasks

A future microdata program should not ask only who adopts within the same task structure. A stronger extension is:

> Conditional on occupation/task structure and adoption, what predicts conversion into routine use, deeper assisted working time, and reported benefit?

Candidate mechanisms include employer encouragement/tool provision, workflow design, firm size, digital intensity, worker characteristics, remote-work feasibility, and management practices. These hypotheses must be tested against the current literature rather than presented as new concepts.

### E. Measurement reconciliation

RPS worker measures, CPS worker composition, OEWS establishment staffing, BTOS firm/business measures, O*NET task descriptors, and platform-log measures describe different units and constructs. The observatory can make those differences explicit through a common measurement schema:

`(unit, population, denominator, question, reference period, construct, taxonomy, vintage)`.

The objective is not to average incompatible measurements into an AI score. Disagreement across sources is itself evidence.

## 5. Current research thesis for GenAI at Work

The strongest current program is therefore:

> Workplace GenAI diffusion has advanced quickly, but adoption is only the extensive margin. The economically informative frontier is how adoption converts into repeated use, working-time penetration, and reported benefit; how stable those conversion patterns are; and how much apparent industry variation is composition versus additional context.

The observatory should make this conversion process measurable over time, with explicit source populations, denominators, uncertainty limits, and evidence classes.

## 6. Novelty discipline

Before labeling any future analysis a new contribution, check it against at minimum:

- the current RPS/GenAI Adoption Tracker papers and replication materials;
- contemporary worker-side AI-use surveys;
- firm-side Census/BTOS research;
- task/exposure and platform-log measurement work;
- productivity and labor-market outcome studies using stronger identification strategies.

A result is not novel because it is newly implemented in this repository. Novelty requires a distinct question, estimand, dataset linkage, longitudinal test, robustness design, or identification strategy relative to existing work.
