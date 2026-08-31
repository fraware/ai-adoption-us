# Data rights and publication modes

This project separates **source accessibility** from **redistribution permission**.

## RPS / FRED

The RPS series surfaced through FRED are marked as copyrighted and citation-required. The repository does not treat public visibility as permission to redistribute a static copy of the observation database.

The project therefore maintains:

- `audit_snapshot`: private research fixtures used for reproducibility and validation;
- `fred_live_no_store`: server-side live retrieval with `cache: no-store`, only after a current terms review and with required attribution/disclaimer;
- a metadata-only source registry that can safely power navigation to the original series pages.

The long-run preferred publication path is an explicit direct-feed or redistribution permission from the underlying GenAI Adoption Tracker / RPS data owners. Until that is documented, public downloadable RPS observation files remain disabled.

## CPS

CPS public-use microdata are used as analytical inputs for composition weights. Derived composition results are stored under `data/audit/derived/` during research validation, not under the web application's public directory. Publication of a derived result requires the RPS side of the calculation to have a rights-cleared production path as well as passing scientific coverage gates.

## Operational permission request

A permission request should ask specifically whether the project may: (1) reproduce the relevant RPS series values in an interactive public website, (2) serve machine-readable derived or raw series values to users, (3) cache values for performance/reproducibility, and (4) publish derived industry/occupation counterfactuals with attribution. The answer and any conditions should be archived before changing production mode.
