# CPS live-ingestion correction and execution changelog — 2026-09-01

## Purpose

This note records a material implementation correction discovered only when the existing CPS pipeline was executed against real official 2026 Census public-use files.

## What the pre-execution implementation assumed

The reconstructed CPS reader expected official `apr26pub.csv`, `may26pub.csv`, and `jun26pub.csv` distributions to expose a header row containing the canonical variable names used by the analysis (`PRTAGE`, `PREMPNOT`, `PEMLR`, `PWSSWGT`, `PRDTIND1`, `PRDTOCC1`, `PEHRACT1`, `PEHRUSL1`). Unit tests used small headered CSV fixtures and therefore validated the internal parsing/weighting contract without validating that assumption about the external Census file format.

## What real execution established

The live April 2026 CSV path failed the required-column check. The failure occurred before any composition estimate was generated and therefore created no empirical result.

The production research path was then reconciled to the official Census 2026 Basic CPS public-use record layout and the compressed fixed-width monthly files. The byte locations used by the parser are pinned from the official layout document:

- `PRTAGE`: 122–123;
- `PEMLR`: 180–181;
- `PEHRUSL1`: 218–219;
- `PEHRACT1`: 243–244;
- `PREMPNOT`: 393–394;
- `PRDTIND1`: 472–473;
- `PRDTOCC1`: 476–477;
- `PWSSWGT`: 613–622, with four implied decimal places.

The authoritative live inputs are therefore the official `apr26pub.dat.gz`, `may26pub.dat.gz`, and `jun26pub.dat.gz` files plus the 2026 Census record layout.

## Engineering correction

`src/genai_at_work/cps.py` now exposes an explicit 2026 fixed-width ingestion path. `scripts/build_cps_composition.py` and the richer execution script use that same path. The headered CSV reader remains only as a deterministic fixture/explicit-conversion utility and is no longer represented as the authoritative live Census ingestion mechanism.

## Scientific consequence

The correction changes the external ingestion implementation, not the estimands:

- age 18–64;
- employed under the registered `PREMPNOT=1` contract;
- civilian/RPS-compatible industry and occupation crosswalks;
- `PWSSWGT` final person weights with equal month pooling;
- worker-share composition for adoption;
- actual-main-job-hour-share composition for assisted hours and reported savings;
- usual hours only as a separately labeled sensitivity;
- 98% fail-closed coverage gate.

The first official-data execution after the correction passed the population, mapping, weighting, and numerical sanity checks documented in `docs/validation/CPS_Q2_2026_COMPOSITION_EXECUTION.md`.

## General lesson for the observatory

A unit-tested transformation is not evidence that an external source adapter matches the real source distribution. Future source integrations require at least one exact-vintage live-file execution before the adapter is treated as validated, with the external schema or record-layout identity frozen in provenance.
