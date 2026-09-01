# GenAI at Work — canonical observatory program plan

## Purpose

This document is the top-level research and product program for the U.S. AI Adoption Observatory. It complements, but does not replace, `docs/ROADMAP.md`, `docs/ENGINEERING_HANDOFF.md`, `docs/RELEASE_CHECKLIST.md`, and the dated validation records.

The observatory's core question is:

> How is generative AI moving from availability and adoption into actual work, reported benefit, and eventually realized economic outcomes in the United States?

The project is not a generic AI dashboard, a single "AI impact" score, or a publication that treats self-reported time savings as measured productivity.

## North-star causal and measurement ladder

The observatory keeps the following objects distinct:

1. availability/access;
2. work adoption;
3. recent use;
4. routine use;
5. workflow penetration / AI-assisted working time;
6. self-reported counterfactual benefit;
7. realized economic outcomes such as output, quality, wages, employment, and measured productivity.

Evidence about one layer does not automatically identify effects at a downstream layer.

## Program phases

| Phase | Objective | Completion standard |
|---|---|---|
| P0 | Canonical program and governance baseline | research questions, evidence classes, claims, vintages, and dependencies are explicit |
| P1 | Rights-cleared Release 1 observatory | approved RPS source path, complete defensible history, full public product, QA and deployment audit |
| P2 | Explain the industry wedge | official CPS composition executed, validated, sensitivity-tested, and interpreted conservatively |
| P3 | Cross-source measurement triangulation | CPS/OEWS/BTOS comparisons preserve population, unit, denominator, and construct differences |
| P4 | Mechanism research | worker × occupation × industry × time designs distinguish composition from context and selection |
| P5 | Longitudinal observatory engine | new waves/revisions generate deterministic diffs, claim review, and immutable releases |
| P6 | Economic realization research | stronger outcome claims require an explicit causal or quasi-causal identification strategy |
| P7 | Durable public infrastructure | versioned data, API/research interfaces, external reproducibility, and institutional update cadence |

## Research-question registry

| ID | Research question | Current evidence class | Status |
|---|---|---|---|
| Q1 | How fast is workplace GenAI adoption diffusing? | direct RPS measurement | active; production source rights unresolved |
| Q2 | Is adoption translating into recent and routine use? | direct RPS measurement | active; production source rights unresolved |
| Q3 | Is adoption translating into greater workflow penetration? | RPS direct measurement + descriptive subgroup analysis | supported descriptively |
| Q4 | How persistent are occupation and industry differences over time? | derived longitudinal diagnostics | supported on frozen five-wave audit panel |
| Q5 | Why is adoption-to-assisted-hours coupling tighter across occupations than industries? | descriptive structural finding | unresolved mechanism |
| Q6 | How much industry variation is explained by occupational composition? | CPS cross-survey standardization | execution in progress |
| Q7 | Does an occupation-adjusted industry-context residual persist across specifications and time? | cross-survey standardization / robustness | blocked on Q6 and compatible RPS observations |
| Q8 | Do establishment- and business-side AI measures agree with worker-side measures? | OEWS/BTOS triangulation | future |
| Q9 | Which task characteristics predict deeper AI integration? | O*NET/task mechanism analysis | future |
| Q10 | Which worker, firm, and contextual factors predict conversion from adoption into workflow penetration and benefit? | microdata mechanism analysis | future |
| Q11 | Under what conditions does AI use affect realized output, quality, wages, employment, or productivity? | causal/quasi-causal outcome research | future; no current identification |

## Evidence-class registry

Every public claim and visualization must be classifiable as one of:

1. **Direct measurement** — a reported survey or administrative quantity with its original population and denominator.
2. **Derived descriptive statistic** — deterministic transformation of direct measurements, including correlations, regressions, rank stability, and leave-one-out diagnostics.
3. **Cross-survey standardization / composition counterfactual** — a result combining distinct source systems under an explicit mapping and weighting contract.
4. **Model-based decomposition / mechanism evidence** — analysis intended to separate competing explanatory channels without automatically implying causality.
5. **Causal or quasi-causal estimate** — permitted only when an explicit identification strategy, estimand, assumptions, inference procedure, and external-validity boundary are stated.

The public product must not visually or linguistically collapse these evidence classes.

## Source-vintage registry contract

Every source vintage used for publication must record, where applicable:

- provider and dataset/product name;
- retrieval timestamp;
- source URL or delivery identity;
- file size and cryptographic checksum;
- observation/reference period;
- source revision status;
- questionnaire/instrument version;
- taxonomy/crosswalk versions;
- rights/storage/cache/redistribution status;
- build commit;
- superseded vintage, if any.

Previously frozen source vintages are retained; history is not silently overwritten.

## Claim-registry contract

Material empirical claims should be generated from, or explicitly linked to, versioned machine-readable evidence. For every claim that can change with new data, the observatory should eventually record:

- stable claim ID;
- publication surface(s);
- source artifact and field/query;
- current value/truth condition;
- evidence class;
- interpretation boundary;
- source vintage;
- last reviewed release;
- whether a new vintage changed the claim.

A new wave or revision must be able to identify every affected chart, table, and textual claim before publication.

## P1 — rights-cleared observatory completion

The direct RPS source-rights/feed gate is strategically product-critical even though Release 1 engineering can remain independent of it.

Required source decision:

- machine-readable national, industry, and occupation series;
- complete available history and historical revisions/vintages;
- future update cadence;
- storage/cache permission;
- interactive publication and redistribution permission;
- permission for transformed/derived subgroup outputs;
- attribution/disclaimer requirements;
- survey instrument and definition change log;
- subgroup uncertainty/replicate-weight methodology where available;
- microdata availability and permitted research use.

After source resolution, audit all 131 canonical series for earliest/latest observation, missing quarters, revisions, definition changes, and maximal defensible common panels. The frozen five-wave reconstruction remains a historical validation panel and must not silently become a claim about a longer rights-cleared history.

Release 1 product completion then includes the national trend surface, full industry and occupation explorers, a `/data` publication surface, generated provenance links, the flagship technical essay, rendered accessibility/browser QA, deployment audit, release provenance, and immutable tag.

## P2 — CPS occupation-composition program

Primary question:

> How much of broad industry variation in adoption, AI-assisted working time, and reported savings can be accounted for by occupational composition?

Primary weighting contracts:

`A_hat(j,t) = sum_o w_worker(j,o,t) * A(o,t)`

`H_hat(j,t) = sum_o w_hours_actual(j,o,t) * H(o,t)`

`S_hat(j,t) = sum_o w_hours_actual(j,o,t) * S(o,t)`

with usual-hours weights used only as a separately labeled sensitivity.

For any metric `m`, the descriptive difference

`G(j,t,m) = observed(j,t,m) - predicted_from_occupation_composition(j,t,m)`

is labeled only **occupation-adjusted industry-context residual**.

It is not an identified organizational effect, organizational quality measure, efficiency measure, or productivity effect.

### P2 execution sequence

1. Retrieve official April, May, and June 2026 Basic Monthly CPS public-use files.
2. Freeze source URLs, retrieval metadata, file sizes, and SHA-256 checksums.
3. Validate source schema and value semantics against official Census documentation.
4. Apply the registered 18–64 employed population contract and equal month factors.
5. Produce worker-share, actual-main-job-hour-share, and usual-hours sensitivity composition weights.
6. Enforce mapping/validity coverage gates without silent renormalization.
7. Record unsupported cells as null with explicit suppression reasons.
8. Validate weight sums, non-negativity, industry symmetry, worker/hour-weight differences, and representative crosswalk mappings.
9. Join only to an authorized, compatible RPS occupation vintage for occupation-composition counterfactuals.
10. Run actual-versus-usual-hours, coverage-threshold, leave-one-occupation, crosswalk, and temporal robustness analyses.
11. Use May 2025 OEWS as an independent establishment-side robustness source, not as the primary worker-survey composition basis.
12. Publish an experimental composition explorer only after the scientific gates are green.

## P3 — measurement matrix

Every cross-source comparison should expose at minimum:

`(unit, population, denominator, question, reference period, construct, taxonomy, vintage)`.

RPS worker use, CPS worker composition, OEWS establishment employment, BTOS business use, and O*NET task characteristics are complementary evidence systems, not interchangeable measurements. Disagreement across them is an empirical result and must not be averaged away into a synthetic AI score.

## P4 — mechanism program

Preferred future data structure:

`worker × occupation × industry/context × time`.

Candidate mechanism layers include task structure, employer tool provision/policy, firm size, remote-work feasibility, education, earnings, software/digital intensity, management practices, regulatory context, capital intensity, class of worker, and worker selection.

Descriptive fixed-effect/decomposition models remain non-causal until a separate identification strategy is justified.

## P5 — longitudinal release engine

For each new source wave or revision, the production process should:

1. register the incoming source vintage and rights status;
2. detect changes to previously frozen observations and definitions;
3. regenerate derived artifacts deterministically;
4. produce observation, diagnostic, ranking, and claim diffs;
5. rerun stability, influence, suppression, and regression-contract checks;
6. identify affected charts/tables/text;
7. require explicit scientific/editorial review;
8. publish only after CI and human review pass;
9. retain the prior analytical history;
10. create an immutable release identity.

## P6 — realized economic outcomes

Reported time savings are not measured labor productivity. Any future claim about output, quality, wages, employment, hours, TFP, or productivity requires a separate design with an explicit estimand and credible identification strategy, such as randomized deployment, a defensible natural experiment, staggered adoption with justified assumptions, matched administrative data, or another design appropriate to the question.

## Product target architecture

The mature publication should converge toward:

- `/` — state of GenAI at work;
- `/trends` — national diffusion and use intensity;
- `/explore/occupations` — occupation structure and longitudinal change;
- `/explore/industries` — industry structure and longitudinal change;
- `/explore/composition` — experimental occupation-standardized industry analysis;
- `/measurements` — cross-survey measurement reconciliation;
- `/research` — technical findings and publications;
- `/data` — versioned data/derived artifacts and eventually API access;
- `/methodology` — constructs, populations, denominators, uncertainty, crosswalks;
- `/sources` — source rights, provenance, and vintages;
- `/releases` — immutable historical observatory releases.

## Immediate critical path

Two tracks proceed in parallel:

**Research path:** execute the real April–June 2026 CPS composition pipeline and produce a dated validation package. Counterfactual residuals remain blocked until a compatible authorized RPS occupation vintage is available.

**Product/data path:** resolve the direct RPS source-rights/feed decision, audit the complete available history, and then finish the full observational product.

Browser/deployment QA remains required for public launch, but final launch certification should be performed against the actual release candidate after the principal data/product path stabilizes.

## Non-negotiable invariants

- Adoption is not workflow penetration.
- Assisted hours are not hours saved.
- Reported hours saved are not measured labor productivity.
- Cross-sectional correlations are descriptive absent identification.
- Cross-survey counterfactuals expose mapping, weighting, coverage, and source differences.
- Unsupported cells fail closed.
- Worker shares are used for adoption composition; actual-main-job-hour shares are used for assisted-hours and reported-savings composition.
- Private RPS audit observations never enter a public repository or deployment artifact.
- A new source vintage cannot silently preserve an old claim when the underlying evidence changed.
