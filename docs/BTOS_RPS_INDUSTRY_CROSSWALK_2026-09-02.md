# BTOS to RPS-20 industry crosswalk

Status date: **2026-09-02**  
Issue: **#9 — R1.2**  
Status: **taxonomy bridge defined; no BTOS observation or cross-source statistic produced**

## Decision

The observatory can align BTOS 2022-NAICS sector estimates to the canonical RPS 20-industry registry at the nominal industry level. This mapping does not imply equivalent survey universes, denominators, or units of analysis.

The versioned bridge is `data/registry/btos_rps_industry_crosswalk_v1.json`. Its target identifiers, indices, and names are inherited exactly from `data/registry/cps_industry_crosswalk_v2.json`; the project does not create a second industry ontology for BTOS.

## Coverage

The crosswalk contains 20 canonical RPS target rows:

- 19 have a nominal BTOS sector mapping;
- 15 are classified `primary` for cross-source triangulation;
- 4 are classified `limited` because the BTOS target population excludes material subindustries inside the broader RPS category;
- Public Administration is `excluded` because NAICS 92 is outside the BTOS target population.

The four `limited` rows are Agriculture, Transportation and Warehousing, Finance and Insurance, and Other Services. The exact source exclusions and reasons are stored with each row in the registry.

Current BTOS products are available by 2022 NAICS sector, while the canonical RPS industry registry has the same nominal ordering only after an explicit mapping. The tests therefore compare every `(entity_index, entity_id, entity_name)` tuple directly with the existing RPS registry instead of relying on display labels.

## Public Administration

RPS industry 20, Public Administration, has no BTOS counterpart. Its crosswalk row has a null BTOS sector code and is explicitly unsupported. No substitute sector or proxy may be imputed.

## Unclassified BTOS businesses

The registry also represents BTOS `XX` as an unsupported source category with no RPS target. When unclassified multi-location business mass appears in a source product, it must remain unclassified. It must not be redistributed across mapped RPS industries.

## Measurement boundary

A common sector label does not make BTOS and RPS the same measure:

- BTOS statistics are business-level estimates;
- RPS statistics are worker-level estimates.

Any eventual mapped comparison is therefore **business-versus-worker triangulation**, not direct validation of one common adoption rate.

## Required empirical join contract

Any code applying this crosswalk must:

1. join by explicit BTOS sector code and canonical RPS entity ID, never fuzzy label matching;
2. retain the comparability tier and its reason in derived records;
3. reject Public Administration as unsupported;
4. retain `XX` as unclassified;
5. record the exact BTOS period or supplement vintage;
6. preserve published uncertainty and suppression fields;
7. expose the business-versus-worker denominator mismatch at interpretation time.

The crosswalk does not authorize conversion of business percentages into worker percentages, silent employment weighting, a composite BTOS/RPS adoption score, or organizational/productivity/causal claims from sector-level association.

## Validation

Regression tests require:

- exact equality with the canonical 20 RPS target entities;
- a unique and complete 19-sector BTOS mapping set;
- a null/unsupported Public Administration row;
- exactly four limited-comparability sectors with their exclusions recorded;
- fail-closed treatment of `XX`;
- preservation of the no-composite and no-causal-interpretation rules.

## Next step

The bridge is ready for a source-reproduction checkpoint. Before any RPS comparison, the project must pin an official post-November-2025 BTOS core period or the official 2025–26 AI supplement, reproduce the relevant Census estimate and uncertainty/suppression behavior, and only then apply this crosswalk.

Sources:

- https://www.census.gov/programs-surveys/btos.html
- https://www.census.gov/hfp/btos/downloads/methodology/Business_Trends_and_Outlook_Survey_Methodology_V6.pdf
- https://www.census.gov/naics/reference_files_tools/2022_NAICS_Manual.pdf
