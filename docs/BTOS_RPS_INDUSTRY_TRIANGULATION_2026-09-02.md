# BTOS-RPS industry triangulation — Q2 2026

Date: 2026-09-02  
Protocol: `btos-rps-industry-triangulation-v1`  
Protocol canonical commit: `854db8d637e5f7896ef2f779692d9451d8971e55`

## Purpose

This is the first execution of the preregistered industry-level triangulation between Census BTOS business-reported AI use and RPS worker-reported GenAI adoption.

The analysis was not used to choose its period, sectors, or statistic. Those choices were fixed before the full cross-source pattern was assembled.

## Inputs

BTOS:

- cycle `202611`;
- reference period May 4–17, 2026;
- Q7/A1: business reports AI use in any business function during the last two weeks;
- employer-business denominator;
- source checkpoint: `data/derived/btos/btos_core_ai_202611.json`.

RPS:

- Q2 2026;
- metric `adoption_work`;
- employed adults aged 18–64 report whether they use Generative AI for their job;
- worker denominator;
- authorized aggregate source checkpoint: `data/registry/rps_industry_adoption_q2_2026_v1.json`.

The measures are related but non-equivalent. BTOS covers AI at the employer-business level and RPS covers GenAI use by workers. Their percentages must not be subtracted or interpreted as measurements of the same object.

## Eligibility

The primary analysis uses only crosswalk rows classified `primary` and requires a published, non-suppressed BTOS estimate plus a nonmissing authorized RPS observation.

Four exclusions follow directly from the preregistered rules:

- Agriculture is unavailable because BTOS sector `11` is suppressed in cycle `202611`;
- Management of Companies and Enterprises is unavailable because BTOS sector `55` is suppressed;
- Public Administration has no BTOS counterpart;
- BTOS `XX` is unclassified and is not redistributed.

The primary set therefore contains 14 sectors. The expanded sensitivity adds three usable limited-comparability sectors: Transportation and Warehousing, Finance and Insurance, and Other Services Except Public Administration. That sensitivity contains 17 sectors.

## Result

Primary, 14 sectors, unweighted:

- Spearman rank correlation: **0.704070833089**;
- Pearson correlation: **0.797472661352**.

Expanded comparability sensitivity, 17 sectors, unweighted:

- Spearman rank correlation: **0.815450797048**;
- Pearson correlation: **0.850095624804**.

These results indicate substantial descriptive cross-sector concordance in this snapshot: industries with higher business-reported AI use in BTOS also tend to have higher worker-reported GenAI adoption in RPS.

The expanded sensitivity produces a stronger association than the primary set. It is reported separately because its added sectors have documented universe mismatches; it does not replace the primary result.

## What this result does not establish

The analysis does not establish:

- that BTOS and RPS measure the same adoption construct;
- that differences between their percentages are meaningful percentage-point gaps;
- a causal relationship between firm AI adoption and worker GenAI use;
- an organizational effect;
- productivity, output, or time savings;
- statistical significance or a population correlation interval.

No p-value or correlation confidence interval is reported because the project does not yet have an approved covariance design covering both surveys for this statistic.

## Pre-analysis exposure disclosure

The canonical protocol already records that two RPS industry observations — Information and Management of Companies and Enterprises — were inadvertently surfaced during metadata verification before preregistration. No full RPS industry vector, selected-cycle BTOS vector, or cross-source statistic was assembled before the protocol was canonical. Those sectors were not removed or specially treated after the fact.

## Reproducibility

The committed artifact is:

`data/derived/btos_rps/industry_triangulation_q2_2026_v1.json`

The deterministic executor is:

`scripts/execute_btos_rps_industry_triangulation.py`

The implementation uses average ranks for ties and ordinary unweighted Pearson correlation. Regression tests require the exact eligible sector sets and reproduce the committed coefficients from the pinned source checkpoints.

## Publication status

The analysis is canonical and published at `/explore/industries`. The public presentation was merged in commit `75b94550be97c2e500db6c7b796330d0d8e90c40` after exact-head review. On that merge commit, the Python/empirical/governance suite, production TypeScript/build/private-data/route-smoke suite, and rendered Chrome/Firefox/WebKit plus axe and Lighthouse checks all passed.

The rendered publication preserves the construct mismatch beside the comparison and presents the 14-sector preregistered result as primary, with the 17-sector limited-comparability result labeled separately as a sensitivity. WebKit is an engine-level compatibility check and is not evidence of native Safari or iOS Safari validation.
