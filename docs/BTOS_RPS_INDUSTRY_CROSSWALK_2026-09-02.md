# BTOS to RPS-20 industry crosswalk

Status date: **2026-09-02**  
Issue: **#9 — R1.2**  
Status: **taxonomy bridge corrected against exact Census source keys; no BTOS/RPS cross-source statistic produced**

## Decision

The observatory can align BTOS 2022-NAICS sector estimates to the canonical RPS 20-industry registry at the nominal industry level. This mapping does not imply equivalent survey universes, denominators, or units of analysis.

The versioned bridge is `data/registry/btos_rps_industry_crosswalk_v1.json`. Its target identifiers, indices, and names are inherited exactly from `data/registry/cps_industry_crosswalk_v2.json`; the project does not create a second industry ontology for BTOS.

## Exact source-key correction

Direct inspection of the official Census `Sector.xlsx` acquired by the repository source probe exposed an important distinction between the file's join keys and the descriptive NAICS span labels.

For three aggregated sectors, the exact values in the workbook `Sector` column are:

| RPS industry | Exact `Sector.xlsx` key | NAICS span label |
| --- | --- | --- |
| Manufacturing | `31` | `31-33` |
| Retail Trade | `44` | `44-45` |
| Transportation and Warehousing | `48` | `48-49` |

The original bridge stored the span labels in `btos_sector_code`. That was incompatible with the bridge's own exact-join rule. The corrected contract now defines:

- `btos_sector_code` as the exact source-file join key;
- `naics_sector_span` as descriptive taxonomy metadata.

Production code must never substitute `naics_sector_span` for `btos_sector_code`.

The source-key correction is bound to the official `Sector.xlsx` SHA-256 `d4e4ef99e958c66bc8b044489e36a6468f93307a1b8216f96e92dbdba8a44e78`, retrieved by the repository source probe on 2026-09-02. The inspected Question 7 / Answer 1 sector blocks for cycle `202617` contain the 19 mapped source keys plus `XX`.

## Coverage

The crosswalk contains 20 canonical RPS target rows:

- 19 have a nominal BTOS sector mapping;
- 15 are classified `primary` for cross-source triangulation;
- 4 are classified `limited` because the BTOS target population excludes material subindustries inside the broader RPS category;
- Public Administration is `excluded` because NAICS 92 is outside the BTOS target population.

The four `limited` rows are Agriculture, Transportation and Warehousing, Finance and Insurance, and Other Services. The exact source exclusions and reasons are stored with each row in the registry.

## Public Administration

RPS industry 20, Public Administration, has no BTOS counterpart. Its crosswalk row has a null BTOS source key and `naics_sector_span = "92"`. No substitute sector or proxy may be imputed.

## Unclassified BTOS businesses

The registry represents BTOS `XX` as an unsupported source category with no RPS target. When unclassified multi-location business mass appears in a source product, it must remain unclassified. It must not be redistributed across mapped RPS industries.

## Measurement boundary

A common sector label does not make BTOS and RPS the same measure:

- BTOS statistics are business-level estimates;
- RPS statistics are worker-level estimates.

Any eventual mapped comparison is therefore **business-versus-worker triangulation**, not direct validation of one common adoption rate.

## Required empirical join contract

Any code applying this crosswalk must:

1. join by exact `btos_sector_code` and canonical RPS entity ID, never by NAICS span labels or fuzzy display labels;
2. retain the comparability tier and its reason in derived records;
3. reject Public Administration as unsupported;
4. retain `XX` as unclassified;
5. record the exact BTOS period and source-file hash;
6. preserve published uncertainty and suppression fields;
7. expose the business-versus-worker denominator mismatch at interpretation time.

The crosswalk does not authorize conversion of business percentages into worker percentages, silent employment weighting, a composite BTOS/RPS adoption score, or organizational/productivity/causal claims from sector-level association.

## Validation

Regression tests require:

- exact equality with the canonical 20 RPS target entities;
- the exact 19 source keys observed in `Sector.xlsx`;
- separation of the `31`/`44`/`48` source keys from their broader NAICS span labels;
- a null/unsupported Public Administration row;
- exactly four limited-comparability sectors with their exclusions recorded;
- fail-closed treatment of `XX`;
- preservation of the no-composite and no-causal-interpretation rules.

## Next step

After this correction passes permanent CI, the project can proceed to the first source-reproduction checkpoint: pin cycle `202617` from the verified national and sector workbooks, reproduce Question 7 / Answer 1 estimates with their published standard errors and suppression markers, and validate the sector extraction against this exact-key crosswalk. No RPS comparison should be made at that checkpoint.

Sources:

- https://www.census.gov/programs-surveys/btos.html
- https://www.census.gov/hfp/btos/downloads/methodology/Business_Trends_and_Outlook_Survey_Methodology_V6.pdf
- https://www.census.gov/naics/reference_files_tools/2022_NAICS_Manual.pdf
