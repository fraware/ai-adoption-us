# Release 1 product QA — code, build, and automated rendered pass

Initial code-level pass: 2026-08-30  
Networked production-build update: 2026-08-31  
Automated rendered-browser update: 2026-09-01  
Explicit mobile-emulation update: 2026-09-03

This document records the code-level, networked production-build, and automated rendered-browser QA completed for the rights-safe Release 1 candidate. The automated pass is real browser-engine execution and now includes explicit Pixel 7/Chrome and iPhone 15 Pro/WebKit device contexts. It **does not substitute for** native Safari/iOS, physical-device validation, or human assistive-technology testing where those remain required.

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

### Editorial and construct discipline

- Reported time savings remain explicitly distinct from measured productivity.
- The Q2-2026 industry `R²(S~H) > R²(S~A)` ordering is described as a **3-of-5-wave** result, not a structural law.
- Occupation–industry comparisons are phrased as aggregate alignment differences, not identified organizational mechanisms.
- A/H/S notation is defined near diagnostic tables.
- Composition/residual language remains experimental and non-causal; zero real RPS-dependent residual values are claimed.

## Networked production-build evidence — 2026-08-31

The 2026-08-30 code-only QA explicitly listed **Genuine `npm install` and `next build`** as unverified external gates. That historical statement remains important provenance; it is no longer the current state.

GitHub Actions run `33411128343` validated the rights-safe public handoff in a networked Ubuntu 24.04 environment.

Python/public surface:

- CPython 3.12.14;
- 52 tests passed;
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

## Automated rendered-browser evidence — 2026-09-01

The successful baseline execution is GitHub Actions run `33501320183`, associated with PR #19 source head `6ed9da2074c2ee042c88912e2c3bdb05806e88f7`. GitHub checked out the PR merge candidate for execution, while artifact metadata records the source head separately.

The retained artifact from that run is:

- artifact ID: `9797926404`;
- artifact name: `r1-g2-browser-qa-d034f29cfaf981656a291f004be5fc7f1d64d3fb`;
- artifact SHA-256: `c096aed747fd8fd7dd67195243185c1c5618e03c91e671c7747cf361783ebbf0`;
- retention at creation: 30 days.

The artifact contains the Playwright JSON and HTML reports, screenshots for successful cases, Lighthouse JSON reports, browser-version metadata, production-server log, optimized build-size record, and largest-static-file inventory.

### Browser/viewport matrix

The baseline Playwright suite passed **48/48** cases across all six public routes:

- stable Chrome 151.0.7922.173 at 375, 768, 1024, and 1440 px;
- Playwright-managed Firefox 153.0 at 375 and 1440 px;
- Playwright WebKit 26.5 at 375 and 1440 px.

WebKit is an engine-compatibility signal only. It is **not** evidence that native Safari, macOS Safari, or iOS Safari QA is complete.

For each route/project case, the suite verifies successful document response, application-icon loading, expected semantic surfaces, primary-navigation links, no page-level horizontal overflow, visible table fallbacks inside horizontal-scroll wrappers, keyboard entry through the skip link, visible focus styling, skip-link transfer to `main`, reduced-motion behavior, no serious/critical axe violations under the configured WCAG tags, and no uncaught page or console errors.

The test does not currently click every navigation link, exercise every chart tooltip, or assert a redraw after an explicit runtime resize. Those manual/interaction checks remain open where the release checklist says so.

### Lighthouse evidence

Seven Lighthouse reports completed successfully: all six desktop routes plus the mobile homepage.

| Report | Accessibility | Performance | LCP (ms) | CLS | TBT (ms) |
|---|---:|---:|---:|---:|---:|
| after-adoption desktop | 100 | 100 | 445 | 0.000 | 0 |
| home desktop | 100 | 100 | 528 | 0.000 | 0 |
| home mobile | 100 | 100 | 1855 | 0.000 | 48 |
| industries desktop | 100 | 100 | 506 | 0.000 | 0 |
| methodology desktop | 100 | 100 | 459 | 0.000 | 0 |
| occupations desktop | 100 | 100 | 494 | 0.000 | 0 |
| sources desktop | 100 | 100 | 449 | 0.000 | 0 |

The accessibility launch gate in automation is `>=95`; every report scored 100. Performance scores and timing values are CI laboratory evidence only and are **not field Core Web Vitals**.

The optimized `.next` directory was approximately 60 MB in the runner. That is build-output size, not a browser transfer-size claim. The retained largest-static-file inventory is the appropriate artifact for client-bundle regression inspection.

### Visual evidence review

The retained successful screenshots were reviewed for the tested main-content states. No clipping, page-level horizontal spill, or obvious breakpoint failure was observed, including the previously failing 375-px methodology page in Chrome, Firefox, and WebKit.

The screenshots are captured after the skip-link exercise transfers focus to `main`, so they are useful responsive-content regression evidence but not a complete manual visual review of the header/navigation state.

### Provenance hardening after the baseline run

The baseline artifact correctly recorded browser versions but its `playwrightVersion` field was null because the reporter relied on an npm environment variable that was not populated in that invocation. The reporter has been changed to read the pinned `@playwright/test` version directly from `apps/web/package.json` and fail closed if it cannot resolve it. A repository test guards that contract.

The browser workflow now also triggers when `docs/qa/**`, `docs/RELEASE1_PRODUCT_QA.md`, or `docs/RELEASE_CHECKLIST.md` changes. This prevents a final QA/checklist documentation commit from bypassing the rendered gate. A post-documentation successful run must therefore be checked on the exact final PR head before merge.

## Explicit mobile-emulation evidence — 2026-09-03

PR #61 extends the automated matrix with two explicit Playwright device contexts:

- Pixel 7 against the stable Chrome channel: viewport 412 × 839, screen 412 × 915, device scale factor 2.625, mobile/touch descriptor enabled;
- iPhone 15 Pro against Playwright WebKit: viewport 393 × 659, screen 393 × 852, device scale factor 3, mobile/touch descriptor enabled.

The accepted source head `8147cabdc0e0104717762e7955c081de48458532` passed release-candidate CI run `33737876597` and rendered-browser run `33737876591`. The rendered workflow checked out merge candidate `8bb7d5df1ec1bbb28f83323e4eb90f08ec151978`.

The expanded browser suite passed **70/70** cases. Both mobile projects run the six route-level semantic/responsive/accessibility/runtime contracts plus the industries publication/triangulation assertion. In addition to phone-width and Android/iPhone identity checks, each mobile route must receive an actual `touchstart` event generated through Playwright's touchscreen API.

The touch probe runs after fresh-document keyboard and axe checks, preserving the keyboard-entry evidence while still placing touch-triggered runtime or console errors inside the final error assertions.

The retained passing artifact is:

- artifact ID: `9886672185`;
- artifact name: `r1-g2-browser-qa-8bb7d5df1ec1bbb28f83323e4eb90f08ec151978`;
- artifact SHA-256: `9d2b73748435c8a23a11d9f21e02aee390c4a5f0320b7a3e71dbc64a3f8862a1`;
- size: 18,735,411 bytes;
- creation time: 2026-09-03T09:21:29Z;
- recorded expiry: 2026-10-03T09:21:26Z.

The successful run reported Playwright 1.62.1, Chrome 151.0.7922.173, Firefox 153.0, and WebKit 26.5. Its seven Lighthouse reports all scored 100 accessibility and 100 performance; the mobile-home lab metrics were LCP 1817 ms, CLS 0.000, and TBT 46 ms. These remain laboratory measurements, not field Core Web Vitals.

### Mobile harness correction

The first expanded run (`33736750083`) failed only the six iPhone/WebKit route contracts because the proposed harness assumed that Playwright's touch-enabled device context must expose `navigator.maxTouchPoints > 0`. The WebKit context did not satisfy that browser-fingerprint assumption. A CSS coarse-pointer assertion relied on the same kind of unsupported fingerprint inference.

Those assertions were removed. The accepted test measures touch behavior directly by installing a `touchstart` listener, issuing a Playwright touchscreen tap, and requiring the page to receive the event. The corrected matrix then passed 70/70. This is recorded as a harness defect discovered by the expanded matrix, not as a product defect.

The detailed evidence and residual limitations are recorded in `docs/qa/2026-09-03-r1-g2-mobile-emulation-qa.md`.

## Checks that remain external/manual gates

The automated pass materially closes the automated portion of R1-G2. The following are still open unless separately recorded:

1. Native current Safari desktop validation.
2. Native/physical iOS Safari validation beyond the iPhone 15 Pro/WebKit automated compatibility proxy.
3. Physical Android/Chrome validation beyond the Pixel 7/stable-Chrome automated compatibility proxy, if required by final launch review.
4. Full keyboard-only traversal beyond the automated skip-link entry contract, including interactive chart/table affordances.
5. **Screen-reader traversal** with VoiceOver and NVDA or a defensible second screen reader.
6. Manual chart resize/tooltip/label interaction review.
7. Manual review that no critical meaning depends only on color.
8. Manual heading/landmark review with assistive technology.
9. Field performance/Core Web Vitals once a real deployment and traffic source make them meaningful.
10. Production deployment, headers, caching, artifact identity, analytics/privacy, secrets, and monitoring review.

## Release-language rule

A successful optimized build plus automated rendered QA establishes that the tested rights-safe build compiled, served, and passed the recorded automated browser/accessibility matrix, including the two documented mobile-emulation proxies. It does **not** establish native Safari/iOS behavior, physical-device behavior, human screen-reader usability, field performance, deployment correctness, RPS source-rights resolution, or a completed RPS-dependent composition residual.

**No public-launch claim** should imply those gates are complete until dated execution evidence exists.
