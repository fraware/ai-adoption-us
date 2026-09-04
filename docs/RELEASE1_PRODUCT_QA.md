# Release 1 product QA — cumulative pre-release evidence

Initial code-level pass: 2026-08-30  
Networked production-build update: 2026-08-31  
Automated rendered-browser update: 2026-09-01  
Explicit mobile-emulation update: 2026-09-03  
Native Safari and automated-interaction completion: 2026-09-03

> **Evidence status.** This document preserves cumulative product/browser QA performed on pre-release repository states. It is real engineering evidence, but it is not by itself proof that the final Observatory Release 1 identity passed those gates. Final launch status is governed by `docs/RELEASE_CHECKLIST.md`, which requires release-time evidence on the exact final candidate/authorization identities where specified.

## Scope of the completed QA evidence

The recorded pre-release work established:

- rights-safe `DATA_MODE=derived_only` production builds;
- stable Chrome, Firefox, and WebKit rendered-browser execution;
- explicit Pixel 7 / stable-Chrome and iPhone 15 Pro / WebKit emulation contexts;
- native macOS Safari desktop automation through SafariDriver;
- keyboard/navigation, resize, overflow, 404, console/runtime, axe, Lighthouse, and screenshot/trace contracts;
- private-data/build-tree exclusion checks;
- GitHub Pages static-export auditing as a separate deployment artifact gate.

Automated WebKit is not native iOS Safari. Automated accessibility checks are not full human assistive-technology review. Laboratory Lighthouse performance is not field Core Web Vitals.

The accepted Release 1 scope decision is recorded in:

- `docs/qa/2026-09-03-r1-g2-scope-decision.md`;
- `docs/qa/2026-09-03-r1-g2-native-safari-desktop-qa.md`;
- `docs/qa/2026-09-03-r1-g2-automated-native-completion.md`.

## Code-level accessibility and product provisions

The application includes:

- skip-to-content navigation and focusable main content;
- visible `:focus-visible` treatment;
- reduced-motion handling;
- semantic/captioned tables with keyboard-focusable overflow containers;
- chart-equivalent exact-value tables;
- responsive Plot containers using `ResizeObserver`;
- explicit measurement and interpretation boundaries in public evidence surfaces;
- Sources and Methodology routes as first-class product pages;
- fail-closed rights/data-mode disclosure.

These provisions remain subject to the exact final build and rendered QA contract; their historical implementation does not waive final validation.

## Historical networked-build evidence — 2026-08-31

GitHub Actions run `33411128343` demonstrated a genuine networked rights-safe public build. Permanent CI subsequently strengthened the contract with strict `mypy src`, locked `npm ci`, production-server startup, route smoke tests, private-path scans, and repository-governance checks.

This run is retained as historical provenance, not current release certification.

## Automated rendered-browser baseline — 2026-09-01

GitHub Actions run `33501320183`, associated with PR #19 source head `6ed9da2074c2ee042c88912e2c3bdb05806e88f7`, executed the then-current six public routes across stable Chrome and Playwright-managed Firefox/WebKit at representative responsive widths.

The baseline passed 48/48 cases. Seven Lighthouse reports completed successfully, with accessibility score 100 on each recorded report. Later QA expanded navigation, resize, 404, and mobile contracts.

WebKit in this matrix is an engine-compatibility signal, not native Safari/iOS evidence.

## Explicit mobile-emulation evidence — 2026-09-03

PR #61 added Pixel 7/stable-Chrome and iPhone 15 Pro/WebKit device contexts. The accepted mobile-emulation tranche passed 70/70 cases and generated actual touchscreen events through the browser automation interface.

An initial test-harness assumption around touch fingerprints was corrected before acceptance. That correction is historical QA provenance and was not treated as a product defect.

Detailed evidence remains in `docs/qa/2026-09-03-r1-g2-mobile-emulation-qa.md`.

## Native Safari desktop evidence — 2026-09-03

PR #62 added a macOS 15 workflow that launches the installed Safari application through SafariDriver, renders the primary routes, validates semantic/navigation/overflow/table-containment contracts, and captures native Safari screenshots.

This establishes native macOS Safari desktop automation for that repository state. It does not establish physical iPhone/iPad validation.

## Final automated/native interaction tranche — 2026-09-03

The accepted cross-engine matrix executed 100 Playwright instances:

- **91 passed**;
- **9 intentionally skipped**, because the explicit runtime plot-redraw contract ran once on stable Chrome at 1440 px instead of redundantly in every project.

The matrix included primary-navigation path transitions, runtime chart redraw after viewport resize, and an unknown production route returning an intelligible HTTP 404 surface without unexpected runtime/console failures.

All seven recorded Lighthouse accessibility reports scored 100, above the project's >=95 automated threshold. Performance values remain laboratory evidence only.

## Current scientific/product state versus historical QA copy

Some early QA reports refer to the former five-wave reconstruction because that was the empirical state under test at the time. The controlling Release 1 scientific state is now the seven-quarter Q4 2024–Q2 2026 common A/H/S evidence described in `docs/RESULTS.md`, together with the CPS/OEWS/BTOS composition/triangulation evidence in the current Observatory candidate architecture.

Historical QA wording must not be used to override current scientific results, source rights, or release status.

## Hosting and deployment boundary

The intended production site is:

`https://fraware.github.io/ai-adoption-us/`

GitHub Pages uses a static Next.js export in `derived_only` mode. Repository-defined dynamic response-header policy is not equivalent to platform-served GitHub Pages headers; the live deployment audit must record the platform state actually served.

Ordinary `main` pushes may build a Pages artifact for QA but cannot deploy the formal Observatory release. Deployment is restricted to a validated `Authorize Observatory release <release-id>` commit created after exact rehydration, human attestation, and immutable promotion.

## Residual evidence not claimed

Unless separately performed and recorded, Release 1 does not claim:

- physical iPhone/iPad or Android device testing;
- native iOS Safari validation beyond the documented emulation proxy;
- full human VoiceOver/NVDA traversal;
- complete human keyboard/visual accessibility inspection beyond automated contracts;
- field Core Web Vitals.

These are scope limitations, not hidden completed evidence.

## Release-language rule

Historical QA supports statements about the exact runs and repository states recorded here. It does **not** authorize a statement that the final Release 1 has launched or that the final release identity has passed every gate.

A formal public-release statement may be made only after the exact final candidate satisfies `docs/RELEASE_CHECKLIST.md`, is human-reviewed, exactly rehydrated, promoted into the immutable release registry/tree, deployed through the release-only authorization commit, live-audited, manually inspected for catastrophic errors, and tagged/released.
