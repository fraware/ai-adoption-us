# GenAI at Work — canonical observatory program plan

Status date: **2026-09-04**

## Purpose

This document is the top-level research and product program for the U.S. AI Adoption Observatory. Current release execution is governed by `docs/RELEASE_CHECKLIST.md`; current engineering contracts by `docs/ENGINEERING_HANDOFF.md`; current sequencing by `docs/ROADMAP.md`.

The observatory's core question is:

> How is generative AI moving from availability and adoption into actual work, reported benefit, and eventually realized economic outcomes in the United States?

The project does not collapse those stages into a generic AI score and does not treat self-reported time savings as measured productivity.

## Measurement ladder

The observatory keeps these objects distinct:

1. availability/access;
2. work adoption;
3. recent and routine use;
4. workflow penetration / AI-assisted working time;
5. self-reported counterfactual benefit;
6. composition-adjusted and cross-source descriptive evidence;
7. realized economic outcomes such as output, quality, wages, employment, and measured productivity.

Evidence at one layer does not automatically identify effects at a downstream layer.

## Current program state

The initial observatory baseline has advanced beyond the earlier reconstruction plan. The current repository contains and governs:

- authorized published-aggregate RPS retrieval through FRED;
- a 131-series work-focused registry and revision-aware source candidate;
- seven common A/H/S quarters, Q4 2024–Q2 2026, with 882 complete subgroup cells;
- a bounded public RPS observation product;
- deterministic longitudinal RPS diagnostics;
- official Q2 2025 and Q2 2026 CPS composition evidence;
- descriptive occupation-adjusted industry-context residuals;
- May 2025 OEWS composition robustness;
- preregistered Q2 2026 BTOS–RPS triangulation;
- governed claim-surface binding;
- exact candidate staging and rights-safe review packaging;
- exact post-review source rehydration;
- human-attestation-gated immutable promotion;
- append-only release registry/history;
- release-only GitHub Pages deployment authorization and live audit controls.

No formal Observatory release has yet been promoted or tagged. Release 1 is now an execution/review problem, not an architecture-definition problem.

## Program phases

| Phase | Objective | Current state |
| --- | --- | --- |
| P0 | Canonical measurement/governance baseline | **Complete** |
| P1 | Governed public Release 1 | **Final review/execution pending** |
| P2 | Occupation-composition explanation of industry variation | **Baseline evidence complete; uncertainty extensions remain** |
| P3 | CPS/OEWS/BTOS cross-source triangulation | **Release 1 descriptive baseline complete** |
| P4 | Task/exposure and worker/firm mechanism research | **Future; source/data/identification gated** |
| P5 | Longitudinal revision/release engine | **Core release machinery complete; first promoted lifecycle pending** |
| P6 | Realized economic outcomes | **Future; separate identification required** |
| P7 | Durable public/research infrastructure | **Post-release** |

## Research-question registry

| ID | Research question | Current evidence class | Status |
| --- | --- | --- | --- |
| Q1 | How fast is workplace GenAI adoption diffusing? | direct RPS aggregate measurement | supported over available registered history |
| Q2 | How does adoption relate to recent/routine use and workflow penetration? | direct RPS + longitudinal descriptive analysis | supported descriptively |
| Q3 | How persistent are occupation and industry differences over time? | derived longitudinal diagnostics | supported over seven common A/H/S quarters |
| Q4 | Why is adoption-to-assisted-hours coupling tighter across occupations than industries? | descriptive structural finding | mechanism unresolved |
| Q5 | How much broad industry variation is associated with occupational composition? | CPS cross-survey standardization | Release 1 descriptive evidence produced |
| Q6 | Does the occupation-adjusted industry-context residual persist across alternative composition evidence? | CPS/OEWS descriptive robustness | baseline robustness produced; no causal interpretation |
| Q7 | Do employer/business-side and worker-side AI measures co-move across industries? | BTOS–RPS cross-construct triangulation | Release 1 descriptive evidence produced |
| Q8 | How does theoretical/model-based task exposure compare with realized adoption? | task/occupation aggregate measurement | future; separate provenance/rights gate (#17) |
| Q9 | Which worker, task, occupation, industry, or firm factors explain conversion from adoption into use and benefit? | mechanism research | future; richer authorized data/identification required (#10) |
| Q10 | Under what conditions does AI use affect realized output, quality, wages, employment, or productivity? | causal/quasi-causal research | future; no current identification |

## Evidence classes

Every material public claim belongs to one of these classes:

1. **Direct measurement** — a source quantity with its original population, denominator, construct, period, and provenance.
2. **Derived descriptive statistic** — deterministic transformations such as correlations, regressions, rank stability, or influence diagnostics.
3. **Cross-survey standardization / triangulation** — results combining distinct source systems under explicit mapping, weighting, coverage, and interpretation contracts.
4. **Mechanism evidence** — analyses intended to separate explanatory channels without automatically identifying causal effects.
5. **Causal or quasi-causal estimate** — allowed only with an explicit estimand, identification strategy, assumptions, inference procedure, and external-validity boundary.

The product must not visually or linguistically collapse these classes.

## Source-vintage and claim contracts

Every release-relevant source vintage records, as applicable, provider/product identity, retrieval/release metadata, reference period, source/revision status, exact scientific/content identity, registered entity/series scope, taxonomy/crosswalk versions, rights/publication boundary, and build/release lineage.

Material empirical claims are linked to machine-readable evidence and governed public surfaces. The release architecture binds reviewed claim identities to both evidence digests and the exact repository files presenting those claims. A new source vintage or governed-file edit must identify affected claims and force renewed candidate review where required.

## Release 1 program

Release 1 is the governed public baseline. Its content is described in `docs/product-spec.md`, `docs/RESULTS.md`, and `docs/source-provenance.md`.

The remaining sequence is exact and fail-closed:

1. finalize public repository/documentation state;
2. rebuild the complete candidate on the resulting canonical `main` commit;
3. require exact candidate CI/QA evidence specified by the release checklist;
4. perform human scientific, editorial, and source-rights review against that exact rights-safe package;
5. run exact source rehydration and verify reviewed identity reproduction;
6. bind the human attestation to the deterministic rehydration identity and exact CI evidence;
7. promote one new immutable release and append the release registry;
8. validate the release-only authorization commit;
9. deploy from that exact commit and pass the live-origin audit;
10. perform final manual catastrophic-error/content inspection;
11. create the formal tag and GitHub Release.

No earlier successful deployment, candidate, or CI run substitutes for these final identities.

## Composition program

For industry `j`, occupation `o`, period `t`, and metric `m`, the Release 1 composition program uses:

- CPS worker shares for adoption counterfactuals;
- CPS actual-main-job-hour shares for assisted-hours and reported-savings counterfactuals;
- usual-hours shares as labeled sensitivity evidence;
- OEWS May 2025 staffing as an independent establishment-side robustness basis.

The descriptive residual remains:

`G(j,t,m) = observed(j,t,m) - occupation-composition counterfactual(j,t,m)`

`G` is not an identified organizational effect, quality measure, efficiency measure, productivity effect, or causal mechanism.

Design-based covariance-aware uncertainty for custom CPS composition vectors remains a separate research problem (#14). Existing stability/sensitivity diagnostics are not confidence intervals.

## Cross-source triangulation

RPS worker measures, CPS worker composition, OEWS establishment employment, and BTOS business AI use are complementary systems with distinct units, populations, denominators, constructs, reference periods, and vintages.

Cross-source disagreement is evidence to interpret, not noise to average into a synthetic score. Release 1 BTOS–RPS analysis is descriptive concordance only.

## Future task and mechanism research

Task/exposure work (#17) requires its own canonical artifact, provenance, taxonomy, weighting, suppression, uncertainty, and publication-rights contract. The current aggregate RPS permission does not automatically cover a separate task-index artifact.

Worker × task × occupation × industry/context × time mechanism research (#10) requires richer authorized data and a pre-specified design capable of addressing worker selection, task mix, context, sampling uncertainty, and measurement error.

Reported time savings remain distinct from measured economic outcomes. Any future output, wage, employment, TFP, or productivity claim requires a separate causal or quasi-causal design appropriate to the estimand.

## Mature public architecture

Post-release evolution may add dedicated trends, composition, measurement-reconciliation, task/research, data, or historical release surfaces. Such routes are product targets, not current shipped functionality until implemented, tested, rights-cleared, and included in a reviewed release.

The current shipped-surface contract is defined by `docs/product-spec.md` and the exact promoted release manifest.

## Non-negotiable invariants

- Adoption is not workflow penetration.
- Assisted hours are not hours saved.
- Reported hours saved are not measured labor productivity.
- Cross-sectional and longitudinal associations remain descriptive absent identification.
- Cross-survey counterfactuals expose mapping, weighting, coverage, and source differences.
- Unsupported cells fail closed.
- Worker shares are used for adoption composition; actual-main-job-hour shares are used for assisted-hours and reported-savings composition.
- Private RPS source-input bytes never enter the public repository or promoted release.
- Bounded RPS publication rights do not imply unrestricted source mirroring or a generic public query API.
- New source/repository evidence cannot silently preserve a stale claim or candidate identity.
- Every promoted release is immutable, review-bound, exactly rehydrated, and deployed only through the validated release authorization boundary.
