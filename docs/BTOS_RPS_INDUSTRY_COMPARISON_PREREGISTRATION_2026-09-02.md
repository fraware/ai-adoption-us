# BTOS ↔ RPS industry triangulation preregistration

Status date: **2026-09-02**  
Protocol: **`btos-rps-industry-triangulation-v1`**  
Status: **registered, not executed**

## Purpose

This protocol fixes the first BTOS-versus-RPS industry comparison before the project retrieves an authorized RPS industry observation vector or inspects the BTOS sector observations for the mechanically selected comparison cycle.

The comparison is deliberately narrow. It asks whether industries with higher **business-reported AI use** in BTOS also tend to have higher **worker-reported GenAI adoption for work** in RPS. It does not treat the two measures as the same adoption rate.

The machine-readable contract is `data/registry/btos_rps_comparison_protocol_v1.json`.

## Source boundary

### BTOS object

The BTOS measure is core Question 7, Answer 1 (`Yes`): whether the business used Artificial Intelligence in any of its business functions during the last two weeks.

The unit is an employer business. The estimate is not worker-weighted or employment-weighted.

### RPS object

The RPS measure is `adoption_work`: the share of employed adults age 18–64 in an industry who report using Generative AI for their job.

The RPS series is selected mechanically from `data/registry/rps_source_series_manifest.json`: exactly the industry rows with `metric_id = adoption_work`. Work-hours-assisted and reported-time-savings series are outside this comparison.

### Why this is triangulation, not validation

The sources differ in at least four dimensions:

1. **Unit:** employer business versus worker.
2. **Technology scope:** BTOS Artificial Intelligence versus RPS Generative AI.
3. **Denominator:** weighted responding businesses versus employed adults in an industry.
4. **Reference period:** BTOS asks about the previous two weeks; RPS is a quarterly worker survey measure.

A shared industry label therefore supplies a taxonomy bridge, not measurement equivalence.

## Period rule

RPS is conducted quarterly, and the currently available tracker period ends at **Q2 2026**. The first comparison therefore targets RPS Q2 2026 rather than the later BTOS cycle `202617` that was reproduced as the initial source checkpoint.

The named RPS wave is May 2026. Exact Q2 fieldwork start/end dates have not yet been resolved from an authoritative metadata source without retrieving the industry observation vector.

The selection rule is fixed before outcomes are inspected:

- If authoritative Q2 RPS fieldwork start/end dates are resolved first, compute the midpoint of that interval.
- Among post-November-17-2025 BTOS core cycles, choose the cycle whose **reference-period midpoint** is closest to the RPS midpoint.
- A tie selects the earlier BTOS cycle.
- The choice may not depend on BTOS estimates, suppression, sample size, sector coverage, or the resulting cross-source association.

If exact RPS fieldwork dates remain unavailable, the fallback anchor is **May 16, 2026**, the midpoint of the named May wave. Applying the same date-only rule to the pinned BTOS date metadata selects **cycle `202611`**:

- BTOS reference period: May 4–17, 2026
- collection: May 18–31, 2026
- publication: June 4, 2026

Only the date sheet was consulted to establish this fallback. The Question 7 / Answer 1 sector observations for cycle `202611` were not inspected when this protocol was registered.

## Primary sector set

The primary analysis begins with the 15 crosswalk rows classified `primary` in `data/registry/btos_rps_industry_crosswalk_v1.json`.

A sector enters the realized primary sample only if:

- it has an exact BTOS↔RPS mapped source key;
- its crosswalk comparability tier is `primary`;
- BTOS publishes a non-suppressed Q7/A1 estimate in the selected cycle; and
- an authorized, nonmissing RPS Q2 2026 `adoption_work` observation exists.

The analysis is **unweighted across industry categories**. Employment weighting would introduce a third weighting construct and would not make the two source denominators equivalent.

The minimum primary sample is **10 sectors**. Below 10, the protocol reports insufficient support and does not summarize cross-sector association with a correlation coefficient.

## Fixed exclusions and missingness rules

The primary analysis excludes all four `limited` crosswalk sectors regardless of their observed values:

- `11` Agriculture, Forestry, Fishing, and Hunting
- `48` Transportation and Warehousing
- `52` Finance and Insurance
- `81` Other Services, Except Public Administration

They may enter one separately labeled sensitivity analysis if every other eligibility rule is met.

BTOS `XX` remains unclassified and is never redistributed. RPS Public Administration remains excluded because BTOS has no NAICS 92 counterpart.

A BTOS-suppressed sector remains suppressed. It is excluded pairwise and is never reconstructed, complemented, interpolated, or model-estimated. The project also may not switch BTOS cycles to improve sector coverage after observing suppression.

An unavailable RPS observation is excluded pairwise. No adjacent RPS quarter or alternative metric may be substituted.

## Statistics

### Primary: Spearman rank correlation

The primary statistic is unweighted Spearman rank correlation, using average ranks for ties.

Rank concordance is the primary object because level equality is poorly defined when one axis is business AI use and the other is worker GenAI adoption.

### Secondary: Pearson correlation

Unweighted Pearson correlation is reported only as a descriptive sensitivity to linear association.

The following are explicitly outside v1:

- percentage-point BTOS-minus-RPS “gaps”;
- identity-line calibration error;
- employment-weighted correlation;
- regression interpreted as an organizational effect;
- causal coefficients;
- composite adoption scores; and
- post-hoc deletion of sectors because they are influential or inconvenient.

## Uncertainty

Published BTOS standard errors remain attached to the individual BTOS sector estimates.

The current RPS provider registry does not establish the covariance matrix required for the 20-industry worker-adoption vector. More importantly, the fixed industry taxonomy is not being treated as an iid sample of industries from a superpopulation.

Therefore **v1 reports no p-values and no confidence intervals for Spearman ρ or Pearson r**. A later inferential model requires a new, prospectively committed protocol version.

## Reporting contract

The eventual output must show:

- the exact included-sector list and `n`;
- every excluded, suppressed, or missing sector and the prespecified reason;
- primary Spearman ρ;
- secondary Pearson r;
- the separately labeled limited-comparability sensitivity, if supported;
- a scatter plot whose axes use the full distinct construct names and **no identity line**;
- BTOS question wording/reference dates and RPS quarter/metric; and
- an explicit business-versus-worker, AI-versus-GenAI mismatch statement.

Agreement may be described only as cross-industry concordance. Disagreement may be described only as cross-industry discordance. Neither is evidence of causality, organizational performance, productivity, or measurement error by itself.

The project will not publish a one-cycle industry leaderboard from this triangulation.

## Limited pre-analysis exposure disclosure

This protocol is **not fully blinded**.

During metadata verification on September 2, 2026, search results inadvertently surfaced observation tables for two RPS industry series: **Information** and **Management of Companies and Enterprises**. A full RPS industry vector was not assembled; no candidate-cycle BTOS sector observations were inspected; and no cross-source correlation, ranking, regression, or gap statistic was calculated before registration.

Those two sectors will not be excluded or specially treated because of the exposure. They remain subject to exactly the same eligibility rules as every other sector. Removing them after exposure would itself create a discretionary analysis choice.

## Rights gate

The RPS provider registry still records `source_owner_permission_status = unresolved` and keeps direct observations fail-closed.

Consequently this protocol cannot be executed until the independent RPS rights decision explicitly authorizes the retrieval/storage needed for analysis and publication of the transformed cross-source result. Public discoverability of the RPS series is not treated as resolution of that gate.

## Versioning rule

Once authorized RPS industry observations or the selected-cycle BTOS sector observations are inspected, the following fields are immutable within v1:

- period selection;
- source metrics;
- sector eligibility;
- minimum `n`;
- weighting;
- primary/secondary statistics;
- suppression and missingness treatment; and
- interpretation language.

Any change requires a new protocol version with an explicit reason. v1 is never overwritten.

## Next execution sequence

1. Resolve the RPS rights gate.
2. Resolve exact Q2 2026 RPS fieldwork dates from metadata if possible without retrieving industry observations; otherwise invoke the registered May-midpoint fallback.
3. Freeze the BTOS cycle under the mechanical rule.
4. Reproduce that BTOS cycle from the already pinned official workbook, preserving SEs and suppression.
5. Only then retrieve the authorized RPS Q2 industry vector and execute the prespecified analysis.

## Sources

- `data/registry/btos_construct_scope_v1.json`
- `data/registry/btos_rps_industry_crosswalk_v1.json`
- `data/registry/rps_provider_catalog_scope.json`
- `data/registry/rps_source_series_manifest.json`
- https://sites.google.com/view/covid-rps/generative-ai
- https://www.stlouisfed.org/on-the-economy/2025/nov/state-generative-ai-adoption-2025
- https://fred.stlouisfed.org/release?rid=6
