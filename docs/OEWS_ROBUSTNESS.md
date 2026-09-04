# OEWS robustness analysis

Release 1 uses the U.S. Bureau of Labor Statistics Occupational Employment and Wage Statistics (OEWS) as an independent establishment-side robustness source for the industry × occupation composition analysis.

OEWS is not combined with CPS into a single composition estimate. The two systems describe different populations and are useful precisely because they provide independent views of occupational structure.

## 1. Role in the observatory

The primary industry composition analysis uses the Current Population Survey (CPS), a household survey, to estimate the occupation mix of workers within industries.

OEWS provides an establishment-side alternative based on wage-and-salary employment. Release 1 uses May 2025 OEWS staffing data to ask two related questions:

1. How similar are broad industry occupation-composition vectors in OEWS and CPS?
2. Does an independent OEWS composition produce a similar directional conclusion when applied to RPS occupation-level work-adoption rates?

The second analysis is limited to workplace adoption because OEWS supplies employment counts, not the actual-work-hour composition needed for the RPS assisted-hours and reported-savings measures.

## 2. Source differences

CPS and OEWS should not be interpreted as measurements of the same worker universe.

Important differences include:

- CPS is household-based; OEWS is establishment-based;
- OEWS primarily covers wage-and-salary employment and excludes self-employed workers;
- OEWS excludes most agricultural employment;
- detailed treatment of government/public administration and private households differs;
- Release 1 compares a May 2025 OEWS vintage with CPS quarterly composition estimates.

These differences are treated as source sensitivity, not as errors to be averaged away.

## 3. Source provenance

The project uses independently acquired official May 2025 OEWS staffing data.

An earlier external research archive was reviewed during development because it contained OEWS-derived sensitivity outputs, but it did not redistribute the underlying staffing matrix. Those derived results were not reverse-engineered into this project. Release 1's OEWS analysis is based on the project's own official-source acquisition and versioned crosswalks.

Machine-readable industry and occupation mappings are stored under:

```text
data/registry/oews_industry_crosswalk_v1.json
data/registry/oews_occupation_crosswalk_v1.json
```

Derived OEWS composition and comparison artifacts are stored under `data/derived/composition/`.

## 4. Composition-vector comparison with CPS

The May 2025 OEWS analysis maps detailed staffing data into the same 22 broad occupation groups used for the CPS composition analysis.

A validation comparison between May 2025 OEWS and Q2 2026 CPS worker-share compositions found:

- 20 industries passed the OEWS 98% coverage requirement;
- 11 industries met the stricter primary-comparability criteria for the cross-source vector summary;
- median L1 distance: **0.2533**;
- median cosine similarity: **0.9737**;
- median Spearman rank correlation across occupation shares: **0.9492**;
- the largest occupation group matched in **7 of 11** primary comparisons.

These statistics show strong broad similarity in occupational structure while retaining meaningful source and vintage differences.

Agriculture and Public Administration are excluded from the primary cross-source summary because of source-universe differences. Other Services is treated as limited comparability because OEWS excludes private households.

## 5. OEWS-weighted RPS adoption benchmark

For each industry, the OEWS robustness analysis applies May 2025 occupation employment shares to RPS occupation-level workplace-adoption rates.

The resulting benchmark has the same descriptive form as the CPS worker-share benchmark:

```text
A_hat_OEWS(j,t) = Σ_o w_OEWS(j,o) × A_RPS(o,t)
```

and the corresponding residual is:

```text
OEWS residual(j,t) = observed RPS industry adoption(j,t)
                     - A_hat_OEWS(j,t)
```

This residual remains descriptive. It does not identify an organizational, management, productivity, or causal effect.

Q2 2025 is the closest temporal comparison to the May 2025 OEWS vintage. Q2 2026 is retained as a cross-vintage sensitivity.

## 6. Missing OEWS occupation cells

An unpublished OEWS industry × occupation cell is not treated as zero.

For an incomplete industry composition, the analysis compares published occupation employment with the published all-occupations employment total. Any residual employment mass is allowed to lie among the missing mapped occupation groups.

Because the adoption benchmark is linear, a feasible interval can be calculated by assigning the residual mass to the minimum or maximum RPS adoption value among the missing occupations.

If published occupation employment exceeds the reported all-occupations total, the procedure does not impose an undocumented rounding correction; the affected calculation is treated as unsupported.

Across the 40 industry-period OEWS adoption rows in the Release 1 analysis:

- 32 are point identified;
- 8 are partially identified;
- none is unsupported.

Among the 17 primary-comparability industries in each quarter, 14 are point identified and 3 are partially identified. The partially identified industries are Mining, Utilities, and Real Estate in both quarters.

The resulting intervals are narrow: the maximum primary residual interval width is approximately **0.0622 percentage points** in Q2 2025 and **0.0270 percentage points** in Q2 2026.

## 7. CPS–OEWS residual comparison

Across the 17 primary-comparability industries:

- CPS and OEWS residual signs agree for **16 of 17** industries in Q2 2025;
- they agree for **16 of 17** in Q2 2026;
- no primary OEWS result has an indeterminate residual sign.

Among the 14 point-identified primary industries:

| Quarter | Residual-rank Spearman | Median absolute CPS–OEWS residual difference |
| --- | ---: | ---: |
| Q2 2025 | **0.833** | **1.95 pp** |
| Q2 2026 | **0.969** | **2.86 pp** |

The directional disagreement changes by quarter:

- Q2 2025, Arts, Entertainment, and Recreation: CPS residual approximately **−0.232 pp**, OEWS residual approximately **+6.998 pp**;
- Q2 2026, Educational Services: CPS residual approximately **−0.842 pp**, OEWS residual approximately **+1.012 pp**.

These disagreements are retained in the evidence rather than suppressed.

## 8. Interpretation

The OEWS exercise supports a strong descriptive robustness statement: the direction and cross-industry ordering of workplace-adoption residuals are broadly similar under an independent establishment-side occupation composition, particularly in Q2 2026.

It does not establish equality of CPS and OEWS benchmark magnitudes. The median magnitude differences are evidence that source universe and composition definitions matter.

The result also does not establish that the remaining industry residual is an organizational effect. Occupation composition explains part of the cross-industry structure, but the residual can contain many unmeasured mechanisms and sampling variation.

## 9. Why OEWS is not used for H or S

RPS AI-assisted working time (`H`) and reported time savings (`S`) are work-hour-based constructs. Their primary CPS benchmarks therefore use actual main-job work-hour shares.

OEWS supplies employment counts, not an equivalent actual-hours composition. Substituting OEWS employment shares for the H/S work-hour weights would change the estimand, so Release 1 does not present that substitution as a robustness test.

## 10. Reproducibility

The relevant public artifacts are under:

```text
data/derived/composition/
```

including the OEWS composition packages and the RPS adoption robustness outputs.

The repository retains source identities, crosswalks, coverage diagnostics, point/partial-identification status, and derived comparison tables while excluding private RPS source-input files from the public release.

See [REPRODUCIBILITY.md](REPRODUCIBILITY.md) and [source-provenance.md](source-provenance.md) for the broader source and release model.
