# GenAI at Work roadmap

Status date: **2026-09-04**

This roadmap records the current public-release path and the research work intentionally left open after Release 1. The exact launch gate is `docs/RELEASE_CHECKLIST.md`; this document describes sequencing and scope.

## Release 1: current state

The scientific and release architecture is implemented. The current candidate baseline includes the seven-quarter Q4 2024–Q2 2026 RPS A/H/S longitudinal panel, bounded public RPS observation view, Q2 2025 and Q2 2026 CPS composition evidence, descriptive occupation-adjusted industry residuals, May 2025 OEWS robustness, BTOS–RPS triangulation, governed claim-surface bindings, immutable staging, exact source rehydration, explicit promotion, and release-only deployment controls.

No Observatory release has been promoted yet. A successful merge or historical deployment is not Release 1 publication evidence.

### Immediate release sequence

| Gate | State | Definition of done |
| --- | --- | --- |
| Source retrieval reliability | **Implementation repaired; canonical execution required** | Authorized RPS/FRED retrieval completes under provider-rate pacing and the shared non-cancelling release queue. |
| Exact Observatory candidate | **Pending execution** | Candidate is rebuilt on canonical `main`, staged as `BLOCKED_REVIEW_REQUIRED`, and has zero contract failures. |
| Exact candidate CI/QA | **Pending final identity** | Required CI, Pages artifact audit, rendered-browser/accessibility QA, and native Safari evidence are bound to the exact final candidate as required by the checklist. |
| Human review | **Pending** | Scientific, editorial, and source-rights review is completed against the exact rights-safe candidate-review package. |
| Exact rehydration | **Pending** | Trusted re-fetch reproduces the reviewed scientific source identity, candidate manifest, stage, diff, review package, and gate records exactly. |
| Promotion | **Pending** | Human attestation is bound to the deterministic rehydration identity and exact CI evidence; one immutable Observatory release is promoted. |
| Release-only deployment | **Pending** | The validated authorization commit deploys through GitHub Pages and the live-origin audit succeeds. |
| Formal publication | **Pending** | Final manual catastrophic-error/content inspection passes, then the release tag and GitHub Release are created. |

The release remains blocked at the first incomplete gate. Later gates never substitute for an earlier failure.

## Source and rights track

### Published-aggregate RPS source

The project records published-aggregate RPS use as permitted under the project-owner attestation in `docs/source-rights/RPS_SOURCE_DECISION.md`. The public release remains bounded: source-input bytes stay private; public output is restricted to the reviewed observation/derived surfaces; respondent microdata, the separate task-index artifact, unrestricted bulk mirroring, a historical subgroup database, and a generic raw-source API remain outside the current authorization.

Issue #4 tracks completion of the production-feed lifecycle. The implemented feed now has registered series identity, source retrieval, provenance, revision-aware candidate generation, private-vintage handling, and reviewed release controls. The issue remains open until the canonical live path and Release 1 transition establish the full end-to-end definition of done.

## Release 1 scientific boundary

Release 1 is a descriptive measurement product. Its central distinctions remain contractual:

- adoption is distinct from routine use and AI-assisted working time;
- AI-assisted hours are distinct from counterfactual hours saved;
- reported time savings are distinct from measured labor productivity;
- occupation-adjusted industry residuals are descriptive standardization residuals, not identified organizational or causal effects;
- RPS worker-side constructs and BTOS firm-side constructs remain separate measurement objects;
- CPS composition diagnostics do not become design-based confidence intervals without a defensible covariance method;
- unsupported or suppressed cells fail closed instead of being silently renormalized into apparently complete estimates.

## Post-Release-1 work

The remaining open issues are intentional roadmap items, not unfinished claims required for the first public baseline.

### #14 — design-based uncertainty for CPS composition vectors

Develop a defensible covariance-aware uncertainty treatment for custom CPS industry × occupation composition vectors. Current Kish dispersion, monthly movement, leave-one-month-out sensitivity, and cross-vintage stability measures remain descriptive quality diagnostics until this work is complete.

### #8 — experimental composition explorer

A future `/explore/composition` surface may expose observed industry values, occupation-composition counterfactuals, residuals, weighting/coverage information, suppression reasons, and stability context. It must consume only validated versioned outputs and retain the descriptive interpretation boundary.

### #17 — realized task adoption versus AI exposure

A separate measurement layer may compare theoretical/model-based exposure with realized worker-reported adoption by task and occupation. It remains gated on exact source provenance and reuse/publication terms for the task/occupation indices. Exposure, realized adoption, assisted use, and reported savings remain separate constructs.

### #10 — worker × occupation × industry × time mechanism research

Longer-term mechanism work requires richer authorized data and a pre-specified design capable of separating task suitability, worker selection, occupation composition, and industry/firm context. Aggregate residuals do not establish organizational complementarity or causal mechanisms.

## Repository/release maintenance after launch

After Release 1:

1. every source revision or new wave receives a versioned source identity and revision assessment;
2. release-relevant changes rebuild a complete candidate instead of patching public output in place;
3. governed public claims remain bound to the exact repository files reviewed for the release;
4. exact rehydration and explicit human attestation remain prerequisites for promotion;
5. promoted release directories and registry history remain append-only;
6. dated historical validation/reconstruction records remain provenance, while current status lives in the README, this roadmap, and the release checklist.

## What does not block Release 1

Release 1 does not require respondent-level mechanism identification, the experimental composition explorer, task-level exposure/adoption analysis, or a new design-based CPS covariance method. Those are separately gated research/product extensions and must not be used to overstate the first baseline.
