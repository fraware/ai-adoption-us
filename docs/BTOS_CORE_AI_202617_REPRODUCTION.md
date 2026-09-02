# BTOS core AI cycle 202617 source reproduction

Status date: **2026-09-02**  
Track: **R1.2 — BTOS firm-side triangulation**  
Status: **source-reproduction checkpoint only; no RPS comparison**

## Purpose

This checkpoint freezes and independently validates one post-wording-change Business Trends and Outlook Survey core AI observation before any BTOS-to-RPS comparison is attempted.

The target is cycle `202617`, Question 7, Answer 1 (`Yes`):

> In the last two weeks, did this business use Artificial Intelligence (AI) in any of its business functions?

The full source wording, including Census examples, is pinned in `data/registry/btos_core_ai_202617_source_v1.json` and validated byte-for-byte against the official workbook.

This is a **business-level** statistic. It is not worker adoption, AI-assisted working time, hours saved, productivity, or an organizational effect.

## Pinned source vintage

The repository online source probe acquired the official Census workbooks on 2026-09-02 and recorded exact bytes:

| Source | Bytes | SHA-256 |
| --- | ---: | --- |
| `National.xlsx` | 95,940 | `0db08921d1feaf2f1ee6516a4118424183941d5460d2330a9659cacbe1046dc7` |
| `Sector.xlsx` | 1,480,216 | `d4e4ef99e958c66bc8b044489e36a6468f93307a1b8216f96e92dbdba8a44e78` |

The Census download URLs are mutable delivery surfaces. These hashes define the checkpoint vintage. If the live files later change, validation must fail on hash drift and force an explicit revision/new-vintage decision. The project must not silently regenerate this historical checkpoint from changed bytes.

Raw workbook bytes are not committed to the public Git tree.

## Cycle identity and dates

The official `Collection and Reference Dates` sheet identifies cycle `202617` as:

- collection: **2026-08-10 through 2026-08-23**;
- reference period: **2026-07-27 through 2026-08-09**;
- publication: **2026-08-27**.

These dates are extracted from the workbook's Excel serial values by the source validator and compared with the committed source registry.

## National reproduction

For Question 7 / Answer 1, the official national workbook reports:

- estimate: **22.4%**;
- published standard error: **0.36 percentage points**.

As an additional structural check, the validator independently extracts all three Question 7 national response estimates for cycle `202617`:

- Yes: 22.4%;
- No: 68.2%;
- Do not know: 9.4%.

They sum to exactly 100.0% at the published precision.

The committed derived checkpoint stores only the target `Yes` observation. The other two values are used as validation evidence, not as new observatory metrics.

## Sector reproduction

The source-native sector output contains 20 Question 7 / Answer 1 rows:

- 19 published BTOS sector keys that map nominally to the RPS-20 industry registry;
- one `XX` unclassified source category.

Seventeen of the 19 mapped sectors have published numeric estimates. Two mapped sectors are source-suppressed:

- `11` — Agriculture, Forestry, Fishing and Hunting;
- `55` — Management of Companies and Enterprises.

For those rows, both the estimate and standard error are represented as `null` with `suppression_code = "S"`. They are not inferred from response complements, neighboring periods, other sectors, or any model.

The published `XX` observation is retained as unclassified source evidence with no RPS target. It is never redistributed across industries.

RPS Public Administration has no BTOS counterpart because NAICS 92 is outside the BTOS target population. The derived checkpoint represents it as an unsupported target and does not impute a value.

## Exact source-key rule

The checkpoint uses the corrected crosswalk contract `btos-2022-naics-rps-v1.1`. `btos_sector_code` is the exact value in the Census `Sector.xlsx` `Sector` column. Descriptive NAICS spans are separate metadata.

In particular:

- Manufacturing: source key `31`, NAICS span `31-33`;
- Retail Trade: source key `44`, NAICS span `44-45`;
- Transportation and Warehousing: source key `48`, NAICS span `48-49`.

The validator joins only on the exact source key and canonical entity ID. Fuzzy labels and NAICS span labels are prohibited join mechanisms.

## Executable validation contract

`src/genai_at_work/btos_core.py` provides a dependency-free XLSX reader/extractor for the required source sheets. It handles both shared-string and inline-string workbook encodings, exact cycle columns, published percentages, `S` suppression, and Excel date serials.

`scripts/validate_btos_core_checkpoint.py` performs the release-evidence check. Given the workbooks downloaded by the existing online source probe, it requires:

1. exact pinned file sizes and SHA-256 hashes;
2. exact Question 7 / Answer 1 question and answer identity;
3. national estimate and published SE equality;
4. exact collection/reference/publication dates;
5. national Question 7 response shares summing to 100%;
6. the exact 20 sector-source key set;
7. equality of every sector estimate, SE, and suppression marker;
8. exactly two suppressed source keys, `11` and `55`;
9. exact crosswalk entity/comparability/span metadata for all 19 mapped sectors;
10. fail-closed `XX` and Public Administration behavior;
11. explicit absence of RPS values and cross-source statistics.

The workflow writes a machine-readable validation report into the same short-lived evidence artifact as the downloaded workbooks.

## What this checkpoint establishes

It establishes that the project can acquire, identify, parse, version, and reproduce a released BTOS core AI measure with the publisher's standard errors and suppression behavior while preserving the business-level measurement object.

It does **not** establish:

- a worker-level adoption rate;
- comparability of BTOS and RPS denominators;
- an industry organizational effect;
- productivity impact;
- causal inference;
- a longitudinal BTOS trend across the November 2025 wording break;
- a BTOS/RPS correlation or composite score.

No one-cycle sector ranking should be presented as a substantive research result from this checkpoint.

## Next gate

After this checkpoint passes exact-head and post-merge validation, any BTOS-versus-RPS triangulation must be designed separately. It must pre-specify the comparison period, eligible comparability tiers, treatment of suppressed and `XX` rows, descriptive statistics, and interpretation language before looking for a favorable cross-source pattern. The unresolved RPS source-rights gate continues to apply independently.
