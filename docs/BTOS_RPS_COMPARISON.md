# BTOS–RPS industry comparison

Release 1 uses the U.S. Census Bureau Business Trends and Outlook Survey (BTOS) as an employer-side comparison for worker-reported generative-AI adoption in the RPS.

The analysis is deliberately cross-source and descriptive. BTOS and RPS measure different populations, technologies, denominators, and reference periods, so their percentages are not treated as estimates of the same quantity.

## 1. What the two sources measure

### BTOS

BTOS is a high-frequency survey of U.S. employer businesses. Release 1 uses the post-November-2025 core AI question asking whether a business used artificial intelligence in any of its business functions during the previous two weeks.

The estimate is business-weighted among responding businesses. It is not worker-weighted or employment-weighted.

### RPS

The RPS measure is `adoption_work`: the share of employed adults aged 18–64 in an industry who report using generative AI for their job.

### Construct differences

The comparison therefore differs along at least four dimensions:

| Dimension | BTOS | RPS |
| --- | --- | --- |
| Unit | Employer business | Worker |
| Technology | Artificial intelligence | Generative AI |
| Denominator | Survey-weighted responding businesses | Employed adults in an industry |
| Reference period | Previous two weeks | Quarterly worker-survey measure |

A common industry label provides a classification bridge, not measurement equivalence.

## 2. BTOS measurement break

The BTOS core AI question changed in November 2025. The earlier question referred to AI use in producing goods or services; the newer version asks about AI use in any business function.

Census reports a level shift associated with this wording change and publishes the newer measure as a separate time series. The project does not splice the pre-change and post-change series into a single continuous adoption measure.

Primary source:

- U.S. Census Bureau, BTOS AI question wording update: https://www.census.gov/hfp/btos/downloads/AI%20Question%20Wording%20Updates.pdf

## 3. Period selection

The first cross-source comparison targets RPS Q2 2026.

The BTOS period was selected using a date rule fixed before inspecting the cross-source results: choose the post-wording-change BTOS cycle whose reference-period midpoint is closest to the RPS Q2 2026 fieldwork midpoint. Because exact RPS fieldwork dates were not available from the metadata reviewed at the time, the prespecified fallback used May 16, 2026, the midpoint of the named May RPS wave.

That rule selects BTOS cycle **202611**:

- reference period: May 4–17, 2026;
- collection period: May 18–31, 2026;
- publication: June 4, 2026.

The analysis uses BTOS Question 7, Answer 1 (`Yes`): business use of AI in any business function during the previous two weeks.

## 4. BTOS source reproduction

For cycle 202611, the official national workbook reports:

- Yes: **20.6%**;
- published standard error for Yes: **0.29 percentage points**;
- No: 69.6%;
- Do not know: 9.9%.

The published one-decimal response shares sum to 100.1%, which is retained as source rounding rather than renormalized.

The source workbooks used for the validated checkpoint were identified by exact file size and SHA-256:

```text
National.xlsx
  size: 95,940 bytes
  SHA-256: 0db08921d1feaf2f1ee6516a4118424183941d5460d2330a9659cacbe1046dc7

Sector.xlsx
  size: 1,480,216 bytes
  SHA-256: d4e4ef99e958c66bc8b044489e36a6468f93307a1b8216f96e92dbdba8a44e78
```

The public download URLs are mutable, so the repository records source identity separately from the URL. Raw workbook bytes are not committed to the repository.

## 5. Industry crosswalk

BTOS uses 2022 NAICS sector classifications. RPS uses a 20-industry grouping. The project therefore uses a versioned crosswalk under:

```text
data/registry/btos_rps_industry_crosswalk_v1.json
```

The primary analysis begins with sectors classified as directly comparable under that crosswalk. A separate sensitivity may include sectors with known universe or classification mismatches.

The following cases require explicit treatment:

- BTOS `XX` is unclassified and is not redistributed across industries;
- Public Administration has no BTOS counterpart because NAICS 92 lies outside the BTOS target population;
- suppressed BTOS sectors remain suppressed;
- an unavailable RPS value is excluded pairwise rather than replaced by another quarter or measure.

For cycle 202611, Census suppresses BTOS values for Agriculture (`11`) and Management of Companies and Enterprises (`55`).

## 6. Prespecified analysis

The comparison was defined before the full BTOS–RPS sector pattern was assembled.

### Primary statistic

The primary statistic is the unweighted Spearman rank correlation across eligible industry categories. Rank association is emphasized because equality of percentage levels is not meaningful across the two measurement systems.

### Secondary statistic

Unweighted Pearson correlation is reported as a descriptive sensitivity to linear association.

The analysis does not report:

- BTOS-minus-RPS percentage-point gaps;
- an identity-line calibration error;
- an employment-weighted combined score;
- a regression interpreted as an organizational effect;
- p-values or confidence intervals for the cross-industry correlation.

The fixed set of industries is not treated as an independent random sample from a superpopulation, and the project does not have a joint survey covariance design for the correlation statistic.

## 7. Release 1 result

The primary comparison contains **14 sectors** after applying the prespecified comparability, suppression, and availability rules.

| Analysis | n | Spearman correlation | Pearson correlation |
| --- | ---: | ---: | ---: |
| Primary comparable sectors | 14 | **0.7041** | **0.7975** |
| Expanded comparability sensitivity | 17 | **0.8155** | **0.8501** |

The expanded sensitivity adds three usable limited-comparability sectors: Transportation and Warehousing, Finance and Insurance, and Other Services Except Public Administration.

The result indicates substantial descriptive cross-sector concordance in this snapshot: sectors with higher business-reported AI use in BTOS also tend to have higher worker-reported GenAI adoption in RPS.

The stronger association in the expanded sensitivity does not replace the primary result because the added sectors have documented comparability limitations.

## 8. Interpretation limits

The comparison does not establish:

- that BTOS and RPS measure the same adoption construct;
- that differences between their percentage levels are meaningful gaps;
- a causal relationship between firm AI adoption and worker GenAI use;
- organizational quality or management effects;
- productivity, output, or reported time savings;
- a population-level inferential correlation.

Agreement is described as cross-industry concordance, not validation of one source by the other.

## 9. Reproducibility

The released comparison artifact is:

```text
data/derived/btos_rps/industry_triangulation_q2_2026_v1.json
```

The deterministic analysis script is:

```text
scripts/execute_btos_rps_industry_triangulation.py
```

Machine-readable source, crosswalk, and analysis definitions are stored under `data/registry/`, including:

- `btos_core_ai_202611_source_v1.json`;
- `btos_rps_industry_crosswalk_v1.json`;
- `btos_rps_comparison_protocol_v1.json`.

The machine-readable protocol remains as provenance for the prespecified Release 1 analysis; this document is the human-readable explanation of the method and result.

## 10. Primary sources

- BTOS overview: https://www.census.gov/hfp/btos/about
- BTOS data: https://www.census.gov/hfp/btos/data
- BTOS methodology: https://www.census.gov/hfp/btos/downloads/methodology/Business_Trends_and_Outlook_Survey_Methodology_V6.pdf
- BTOS AI wording change: https://www.census.gov/hfp/btos/downloads/AI%20Question%20Wording%20Updates.pdf
- BTOS API documentation: https://www.census.gov/hfp/btos/downloads/BTOS%20API%20Reference%20Documentation.pdf
