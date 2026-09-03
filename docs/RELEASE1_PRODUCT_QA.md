# Release 1 product QA — code, build, automated rendered, and native Safari pass

Initial code-level pass: 2026-08-30  
Networked production-build update: 2026-08-31  
Automated rendered-browser update: 2026-09-01  
Explicit mobile-emulation update: 2026-09-03  
Native Safari and automated-interaction completion: 2026-09-03

This document records the code-level, networked production-build, automated rendered-browser, explicit mobile-emulation, and native Safari desktop QA completed for the rights-safe Release 1 candidate.

The automated cross-engine pass is real browser-engine execution, and the separate macOS workflow launches the installed native Safari application through SafariDriver. Automated execution **does not substitute for a real browser** or human assistive-technology review where those claims are desired. Under the project-owner scope decision dated 2026-09-03, human/manual QA and physical-device spot checks are outside the Release 1 launch gate and are therefore not claimed as completed evidence.

The current Release 1 R1-G2 evidence boundary is recorded in:

- `docs/qa/2026-09-03-r1-g2-scope-decision.md`;
- `docs/qa/2026-09-03-r1-g2-native-safari-desktop-qa.md`;
- `docs/qa/2026-09-03-r1-g2-automated-native-completion.md`.

## Implemented in the code-level pass

### Information architecture

- Persistent release-status strip distinguishes `derived_only`, private `audit_snapshot`, and fail-closed live-source modes.
- A first-class **Sources** route is present in primary navigation.
- Homepage is organized around durable five-wave evidence, measurement distinctions, the national-source boundary, and the unresolved industry wedge.
- Industry and occupation explorers use the same longitudinal visual grammar and explicit interpretive boundaries.
- Technical essay uses a constrained readable article width and numbered semantic sections.

### Accessibility-oriented code provisions

- Skip-to-content link and focusable main-content target.
- Visible `:focus-visible` treatment for links, summaries, and horizontally scrollable tables.
- Reduced-motion media query.
- Tables use captions, column scopes, and row scopes.
- Horizontally scrollable tables are keyboard-focusable and labelled.
- Observable Plot graphics are wrapped in figures with captions and expose exact values through expandable HTML data tables.
- Plot containers redraw on width changes through `ResizeObserver` instead of assuming a desktop-only initial width.
- Scatter labels are selected by a stated rule rather than input order.

### Rights and provenance communication

- Public release strip states that raw RPS observations are excluded.
- Sources page distinguishes RPS, CPS, OEWS, and BTOS roles and current evidence status.
- Methodology page separates direct measurements, derived diagnostics, composition counterfactuals, and causal/mechanism claims.
- Public/private evidence boundaries are described in user-facing language.
- `docs/source-provenance.md` matches the fail-closed `derived_only` architecture rather than the retired static-FRED design.
- `docs/source-rights/RPS_SOURCE_DECISION.md` records the published-aggregate RPS gate as **GRANTED — live aggregate observatory gate** as of 2026-09-02. That decision does not extend automatically to microdata, the separate occupation/task-index artifact, unrestricted bulk mirroring, or a full-source public API.

### Editorial and construct discipline

- Reported time savings remain explicitly distinct from measured productivity.
- The Q2-2026 industry `R²(S~H) > R²(S~A)` ordering is described as a **3-of-5-wave** result, not a structural law.
- Occupation–industry comparisons are phrased as aggregate alignment differences, not identified organizational mechanisms.
- A/H/S notation is defined near diagnostic tables.
- Composition/residual language remains descriptive and non-causal; unsupported design-based inference remains fail-closed.
- BTOS and RPS are presented as different firm-side and worker-side constructs rather than interchangeable adoption measures.

## Networked production-build evidence — 2026-08-31

The 2026-08-30 code-only QA explicitly listed **Genuine `npm install` and `next build`** as unverified external gates. That historical statement remains provenance; it is no longer the current state.

GitHub Actions run `33411128343` validated the rights-safe public handoff in a networked Ubuntu 24.04 environment.

Python/public surface:

- CPython 3.12.14;
- 52 tests passed at that historical checkpoint;
- 6 private-fixture-dependent tests skipped as expected;
- `compileall` passed;
- Ruff passed.

Web surface:

- Node 22.23.2;
- npm 10.9.8;
- TypeScript validation passed;
- Next.js 16.3.3 optimized production build passed;
- static generation completed for `/`, `/blog/after-adoption`, `/explore/industries`, `/explore/occupations`, `/methodology`, `/sources`, and the framework not-found route.

Permanent PR CI subsequently strengthened that proof by requiring strict `mypy src`, locked `npm ci`, production-server startup, route smoke tests, private-path build scans, and repository-governance checks.

## Automated rendered-browser baseline — 2026-09-01

The successful baseline execution is GitHub Actions run `33501320183`, associated with PR #19 source head `6ed9da2074c2ee042c88912e2c3bdb05806e88f7`.

The retained artifact from that run is:

- artifact ID: `9797926404`;
- artifact name: `r1-g2-browser-qa-d034f29cfaf981656a291f004be5fc7f1d64d3fb`;
- artifact SHA-256: `c096aed747fd8fd7dd67195243185c1c5618e03c91e671c7747cf361783ebbf0`;
- retention at creation: 30 days.

The baseline Playwright suite passed 48/48 cases across all six public routes using stable Chrome at 375, 768, 1024, and 1440 px plus Playwright-managed Firefox and WebKit at 375 and 1440 px. WebKit in this matrix is an engine-compatibility signal only and is not the native-Safari evidence described later in this document.

For each route/project case, the suite verified successful document response, application-icon loading, expected semantic surfaces, primary-navigation links, no page-level horizontal overflow, visible table fallbacks inside horizontal-scroll wrappers, keyboard entry through the skip link, visible focus styling, skip-link transfer to `main`, reduced-motion behavior, no serious/critical axe violations under the configured WCAG tags, and no uncaught page or console errors.

At that historical baseline, full navigation clicking and explicit runtime chart redraw were not yet asserted. Those limitations were subsequently closed by the final 2026-09-03 automated tranche below.

### Historical Lighthouse baseline

Seven Lighthouse reports completed successfully: all six desktop routes plus the mobile homepage. Every accessibility report scored 100, above the configured >=95 launch threshold. Performance scores and timing values are CI laboratory evidence only and are **not field Core Web Vitals**.

The optimized `.next` directory was approximately 60 MB in the runner. That is build-output size, not a browser transfer-size claim.

### Provenance hardening after the baseline

The browser reporter was changed to read the pinned `@playwright/test` version directly from `apps/web/package.json` and fail closed if it cannot resolve it. A repository test guards that contract.

The browser workflow also triggers when `docs/qa/**`, `docs/RELEASE1_PRODUCT_QA.md`, or `docs/RELEASE_CHECKLIST.md` changes. This prevents final QA/checklist documentation from bypassing the rendered gate.

## Explicit mobile-emulation evidence — 2026-09-03

PR #61 added two explicit Playwright device contexts:

- Pixel 7 against the stable Chrome channel: viewport 412 × 839, screen 412 × 915, device scale factor 2.625, mobile/touch descriptor enabled;
- iPhone 15 Pro against Playwright WebKit: viewport 393 × 659, screen 393 × 852, device scale factor 3, mobile/touch descriptor enabled.

The accepted mobile-emulation tranche passed 70/70 cases. Each mobile route had to receive an actual `touchstart` event generated through Playwright's touchscreen API, in addition to phone-width and Android/iPhone identity checks.

The first proposed iPhone/WebKit expansion exposed a harness defect: the test incorrectly assumed that Playwright `hasTouch: true` required `navigator.maxTouchPoints > 0`, and a CSS coarse-pointer assertion relied on the same unsupported fingerprint inference. Those assertions were removed and replaced with the direct touch-behavior contract. This is recorded as a test-harness correction, not a product defect.

Detailed evidence is retained in `docs/qa/2026-09-03-r1-g2-mobile-emulation-qa.md`.

The mobile contexts remain defensible automated proxies. They are not evidence of native iOS Safari or physical Android/iPhone behavior, and those physical/native-iOS claims are outside the Release 1 scope decision.

## Native Safari desktop evidence — 2026-09-03

PR #62 added a separate native-Safari workflow on a GitHub-hosted macOS 15 runner.

The workflow:

- records macOS, Safari, and SafariDriver versions;
- enables the installed SafariDriver;
- starts the rights-safe Next.js production build in `DATA_MODE=derived_only`;
- opens a real W3C WebDriver session requesting `browserName: safari`;
- renders all six primary routes in the installed Safari application;
- validates expected path, semantic surfaces, primary navigation, page overflow, and table containment;
- captures native Safari screenshots and a machine-readable report.

The first inspected successful artifact recorded macOS 15.7.7, Safari 26.5.2, bundled SafariDriver 26.5.2, `browserName: Safari`, `platformName: macOS`, and `safari:useSimulator: false`.

The exact final automated/native source head `3391c39337519715e45d33c5d79053feb6038964` revalidated native Safari successfully in run `33742551142`.

Final native Safari artifact:

- artifact ID: `9888324310`;
- artifact name: `r1-g2-native-safari-c612a1a8d24f068f1eaa5caf1ade35c0299b53ac`;
- artifact SHA-256: `7b7176f31a87af9ab0104ab17fa8a4ce5c5a0403f641b0874f4c309ecefe0d3e`;
- size: 837,491 bytes;
- created: 2026-09-03T10:07:45Z;
- recorded expiry: 2026-10-03T10:07:44Z.

This closes the native **desktop Safari** requirement for Release 1. It does not establish native iOS Safari.

## Final automated/native interaction completion — 2026-09-03

The exact source head `3391c39337519715e45d33c5d79053feb6038964` passed all three independent required workflows:

1. Release candidate CI — run `33742551179` — success.
2. Native Safari desktop QA — run `33742551142` — success.
3. Rendered browser and accessibility QA — run `33742551185` — success.

### Final cross-engine test matrix

Run `33742551185` executed 100 Playwright instances:

- **91 passed**;
- **9 skipped intentionally** because the explicit runtime plot-redraw contract runs once on stable Chrome at 1440 px instead of redundantly on every project.

Recorded browser/tool versions:

- Playwright 1.62.1;
- stable Chrome 152.0.7977.64;
- Firefox 153.0;
- WebKit 26.5.

The final matrix includes all established route semantics, responsive overflow, table containment, skip-link/focus-entry, reduced-motion, axe, runtime/console, and mobile-touch contracts. It additionally requires:

- actual primary-navigation clicks, exact target-path transitions, semantic target rendering, and actual brand-link clicks back to `/`;
- an explicit viewport resize of the published BTOS–RPS industry scatter plot, followed by a required SVG-width redraw through the `ResizeObserver` contract;
- a deliberate unknown production route returning HTTP 404, rendering an intelligible 404/not-found surface, excluding the private audit path, and emitting no page errors or unexpected console errors.

The 404 test permits at most the one exact browser-generated Chromium/WebKit diagnostic associated with the intentionally failing top-level 404 request; all other console errors remain failures.

Final rendered-browser artifact:

- artifact ID: `9888453686`;
- artifact name: `r1-g2-browser-qa-c612a1a8d24f068f1eaa5caf1ade35c0299b53ac`;
- artifact SHA-256: `5550fd4ede8e5c46713ab690d4eef6d72babf79ed9db724183225ff86ec1717f`;
- size: 22,115,399 bytes;
- created: 2026-09-03T10:11:27Z;
- recorded expiry: 2026-10-03T10:11:26Z.

### Final Lighthouse evidence

| Report | Accessibility | Performance | LCP (ms) | CLS | TBT (ms) |
|---|---:|---:|---:|---:|---:|
| after-adoption desktop | 100 | 100 | 447 | 0.000 | 0 |
| home desktop | 100 | 100 | 506 | 0.000 | 0 |
| home mobile | 100 | 99 | 2267 | 0.000 | 44 |
| industries desktop | 100 | 100 | 503 | 0.000 | 0 |
| methodology desktop | 100 | 100 | 462 | 0.000 | 0 |
| occupations desktop | 100 | 100 | 491 | 0.000 | 0 |
| sources desktop | 100 | 100 | 446 | 0.000 | 0 |

All seven accessibility reports scored 100, above the >=95 automation threshold. The performance values remain lab evidence only; they are not field Core Web Vitals.

Detailed exact-head evidence is retained in `docs/qa/2026-09-03-r1-g2-automated-native-completion.md`.

## Release 1 scope decision and residual limitations

The project owner explicitly removed human/manual checks and physical-device spot checks from the Release 1 launch critical path on 2026-09-03. The decision is recorded in `docs/qa/2026-09-03-r1-g2-scope-decision.md`.

Accordingly, the following are **not Release 1 blockers and are not claimed as completed evidence**:

- **Screen-reader traversal** with VoiceOver;
- NVDA or another human-operated second screen reader;
- human-operated full keyboard/focus inspection beyond the automated contracts;
- manual chart tooltip/label/color/heading review;
- physical iPhone/iOS Safari testing;
- physical Android/Chrome testing;
- native iOS Safari beyond the accepted WebKit/iPhone emulation proxy.

The following remain genuine external/post-R1-G2 work:

- production deployment and deployed-artifact audit;
- deployment headers/security baseline;
- caching policy;
- analytics/privacy decision;
- monitoring/logging decision;
- canonical production URL/domain and metadata binding;
- deployed artifact identity/checksum;
- field Core Web Vitals after a real deployment and traffic source make them meaningful;
- durable private RPS backend activation and real backend recovery rehearsal, which are separate from the `derived_only` Release 1 public web path.

## Release-language rule

The Release 1 browser evidence supports the statement that the rights-safe production candidate compiled, served, and passed the recorded Chrome/Firefox/WebKit matrix, explicit Pixel 7 and iPhone 15 Pro device-emulation proxies, automated navigation/resize/404 interaction contracts, and native macOS Safari desktop automation.

It does **not** support claims of native iOS Safari, physical-device validation, human screen-reader usability, manual accessibility completion, field performance, or production-deployment correctness.

**No public-launch claim** should imply that any of those unperformed or deployment-specific checks were completed.

Published-aggregate RPS use is rights-cleared under the recorded project-owner attestation, but the separate durable live-refresh backend remains unactivated and the public Release 1 web path remains `derived_only`.
