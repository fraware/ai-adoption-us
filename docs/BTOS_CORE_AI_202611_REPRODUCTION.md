# BTOS core AI cycle 202611 reproduction

Status date: **2026-09-02**  
Status: **source reproduction complete on branch; no RPS vector or cross-source statistic included**

## Why cycle 202611 was selected

The first BTOS↔RPS industry comparison was preregistered before the selected-cycle BTOS sector outcomes were inspected. Protocol v1 became canonical on `main` at commit `854db8d637e5f7896ef2f779692d9451d8971e55`.

The protocol targets RPS Q2 2026 and requires the BTOS cycle whose reference-period midpoint is closest to the authoritative RPS fieldwork midpoint. A metadata-only primary-source review on September 2, 2026 established the quarterly RPS cadence and a May 2026 wave but did not resolve authoritative exact May fieldwork start/end dates without retrieving industry outcomes.

The preregistered fallback therefore applies: use **May 16, 2026** as the midpoint of the named May wave and select the closest BTOS reference-period midpoint. This mechanically selects cycle **202611**:

- reference period: May 4–17, 2026;
- collection: May 18–31, 2026;
- publication: June 4, 2026.

The selection rule was invoked before inspecting the cycle-202611 Question 7 / Answer 1 sector observations. The cycle outcomes were inspected only after the preregistration had merged and its post-merge CI was green.

The immutable protocol remains `data/registry/btos_rps_comparison_protocol_v1.json`. Current execution state is tracked separately in `data/registry/btos_rps_comparison_execution_state_v1.json`; protocol v1 is not rewritten after outcome inspection.

## Source vintage

The reproduction uses the same already-pinned official Census workbook bytes as the baseline cycle-202617 checkpoint:

- `National.xlsx`: 95,940 bytes; SHA-256 `0db08921d1feaf2f1ee6516a4118424183941d5460d2330a9659cacbe1046dc7`
- `Sector.xlsx`: 1,480,216 bytes; SHA-256 `d4e4ef99e958c66bc8b044489e36a6468f93307a1b8216f96e92dbdba8a44e78`

The public download URLs are mutable. Validation therefore requires these exact hashes; a future file change is treated as a new source vintage or revision, not as a silent update to this checkpoint.

No raw workbook bytes are committed to the public Git tree.

## Exact measure

The checkpoint reproduces BTOS core Question 7, Answer 1 (`Yes`):

> In the last two weeks, did this business use Artificial Intelligence (AI) in any of its business functions?

The unit is the employer business. This is not worker-weighted or employment-weighted and is not equivalent to the RPS worker-reported GenAI adoption measure.

## National reproduction

For cycle `202611`, the official workbook reports:

- **Yes:** 20.6%
- **published standard error for Yes:** 0.29 percentage points
- **No:** 69.6%
- **Do not know:** 9.9%

The three published one-decimal response shares sum to **100.1%**. This is preserved as a source-rounding residual. The project does not renormalize, rescale, or alter any component to force a 100.0% total.

This differs from the later cycle-202617 checkpoint, whose three published shares happen to sum to 100.0%. The validator therefore checks each checkpoint against its own source-published response total while allowing only a small one-decimal rounding residual.

## Sector reproduction and suppression

The sector workbook again contains 20 Q7/A1 source rows: 19 mapped industry sectors plus `XX` unclassified.

Two source keys are suppressed by Census and remain fail-closed:

- `11` — Agriculture, Forestry, Fishing, and Hunting
- `55` — Management of Companies and Enterprises

For both, the committed estimate and standard error are `null` with `suppression_code = "S"`. No value is inferred from adjacent periods, response complements, sector totals, models, or any other source.

`XX` remains an unclassified source category with no RPS target. Its cycle-202611 source value is retained only as source-native BTOS information and is never redistributed across mapped industries.

Public Administration remains unsupported because NAICS 92 is outside the BTOS target population. No proxy is imputed.

## Readiness under the preregistered comparison protocol

The BTOS side of the prespecified eligibility rule is now known:

- primary-comparability crosswalk pool: 15 sectors;
- primary sectors with a published non-suppressed BTOS value: 14;
- primary BTOS suppression: source key `55`;
- limited-comparability pool: 4 sectors;
- limited sectors with a published non-suppressed BTOS value: 3;
- limited BTOS suppression: source key `11`.

These counts do **not** establish the final comparison sample. RPS eligibility has not been evaluated because the RPS industry observation vector remains behind the independent source-rights gate.

No correlation, sector pair list, scatter plot, ranking, gap, regression, or other BTOS↔RPS result has been computed.

## Executable validation

The shared validator `scripts/validate_btos_core_checkpoint.py` now accepts an explicit source registry and checkpoint. It continues to validate the baseline `202617` checkpoint by default and can independently validate `202611`.

For each checkpoint the validator requires:

1. exact pinned source byte sizes and SHA-256 hashes;
2. checkpoint/cycle/question/answer identity;
3. national estimate and published standard error;
4. collection, reference, and publication dates;
5. all three national Q7 response shares and their registered published total;
6. exact sector-source key coverage;
7. every published estimate, standard error, and suppression marker;
8. exact crosswalk metadata for mapped sectors;
9. fail-closed `XX` and Public Administration handling; and
10. explicit absence of RPS values and cross-source statistics.

The online BTOS workflow validates **both** `202617` and `202611` against freshly downloaded official Census workbook bytes in the same run. Either checkpoint failing blocks the source workflow.

## Scientific boundary

This checkpoint establishes only the BTOS business-side input selected under the preregistered timing rule. It does not establish worker adoption, a common adoption scale, productivity, an organizational effect, causality, or cross-source agreement.

The protocol’s next permitted empirical step is unchanged: resolve the independent RPS rights gate. Until that decision is resolved, the project must not retrieve the full RPS industry observation vector or compute the preregistered cross-source statistics.

## Sources

- `data/registry/btos_rps_comparison_protocol_v1.json`
- `data/registry/btos_rps_comparison_execution_state_v1.json`
- `data/registry/btos_core_ai_202611_source_v1.json`
- `data/derived/btos/btos_core_ai_202611.json`
- `data/registry/btos_rps_industry_crosswalk_v1.json`
- https://www.census.gov/hfp/btos/data
- https://www.census.gov/hfp/btos/data_downloads
- https://sites.google.com/view/covid-rps/generative-ai
