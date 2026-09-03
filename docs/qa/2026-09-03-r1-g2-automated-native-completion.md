# R1-G2 automated/native completion — 2026-09-03

## Release 1 scope

This record evaluates R1-G2 under the Release 1 scope decision in `docs/qa/2026-09-03-r1-g2-scope-decision.md`.

Human/manual QA and physical-device checks are outside the Release 1 launch gate. They are **not claimed as completed**. The evidence below establishes only the reproducible automated browser/accessibility/responsive/performance contract plus native macOS Safari desktop automation.

## Exact final source head

- pull request: #62
- source head: `3391c39337519715e45d33c5d79053feb6038964`
- base at PR creation: `a7787d3b4784ad9a90dd3f0831f9ef8d784b653b`

The three independent required workflows all completed successfully on this exact source head:

1. Release candidate CI — run `33742551179` — **success**.
2. Native Safari desktop QA — run `33742551142` — **success**.
3. Rendered browser and accessibility QA — run `33742551185` — **success**.

GitHub Actions executed pull-request merge candidates for the browser jobs; the workflow metadata and retained artifacts preserve source head `3391c39337519715e45d33c5d79053feb6038964`.

## Cross-engine rendered evidence

Run `33742551185` executed **100 Playwright test instances**:

- **91 passed**;
- **9 skipped intentionally** because the explicit runtime plot-redraw test is designed to run once on the stable-Chrome 1440 project rather than redundantly on every browser/project.

Browser/tool provenance recorded by the run:

- Playwright 1.62.1;
- stable Chrome 152.0.7977.64;
- Playwright Firefox 153.0;
- Playwright WebKit 26.5;
- Pixel 7 / stable-Chrome mobile emulation: 412 × 839 viewport, touch enabled;
- iPhone 15 Pro / WebKit mobile emulation: 393 × 659 viewport, touch enabled.

For the six primary routes, the suite verifies the established semantics, keyboard skip-link entry, responsive overflow/table containment, reduced-motion, axe, runtime/console, and mobile touch contracts.

The final R1-G2 tranche additionally verifies:

- every primary-navigation link through an actual click, target pathname transition, semantic target render, and actual brand-link click back to `/`;
- an actual `ResizeObserver`-driven redraw of the published BTOS–RPS industry scatter plot after an explicit viewport resize;
- an unknown production route returns HTTP 404, renders an intelligible `404`/`not found` surface, does not expose the private audit path, and produces no page errors or unexpected console errors.

The intentional 404 contract treats the single browser-generated Chromium/WebKit `404 (Not Found)` console diagnostic as expected for the deliberately failing top-level navigation; any other console error still fails the test.

### Final rendered artifact

- artifact ID: `9888453686`;
- artifact name: `r1-g2-browser-qa-c612a1a8d24f068f1eaa5caf1ade35c0299b53ac`;
- artifact SHA-256: `5550fd4ede8e5c46713ab690d4eef6d72babf79ed9db724183225ff86ec1717f`;
- size: 22,115,399 bytes;
- created: 2026-09-03T10:11:27Z;
- recorded expiry: 2026-10-03T10:11:26Z.

## Lighthouse evidence

All seven final reports passed the configured accessibility threshold of >=95:

| Report | Accessibility | Performance | LCP (ms) | CLS | TBT (ms) |
|---|---:|---:|---:|---:|---:|
| after-adoption desktop | 100 | 100 | 447 | 0.000 | 0 |
| home desktop | 100 | 100 | 506 | 0.000 | 0 |
| home mobile | 100 | 99 | 2267 | 0.000 | 44 |
| industries desktop | 100 | 100 | 503 | 0.000 | 0 |
| methodology desktop | 100 | 100 | 462 | 0.000 | 0 |
| occupations desktop | 100 | 100 | 491 | 0.000 | 0 |
| sources desktop | 100 | 100 | 446 | 0.000 | 0 |

These are CI laboratory measurements for regression review, **not field Core Web Vitals**.

The optimized `.next` build directory was approximately 60 MB. That value is build-output size, not browser transfer size.

## Native Safari desktop evidence

Run `33742551142` revalidated the native Safari harness on the exact final source head.

The native workflow launches the installed Safari application through the built-in SafariDriver and W3C WebDriver protocol; Playwright WebKit is not substituted for Safari in this job.

All six primary routes passed the native Safari route/semantic/navigation-presence/overflow/table-containment contract.

### Final native Safari artifact

- artifact ID: `9888324310`;
- artifact name: `r1-g2-native-safari-c612a1a8d24f068f1eaa5caf1ade35c0299b53ac`;
- artifact SHA-256: `7b7176f31a87af9ab0104ab17fa8a4ce5c5a0403f641b0874f4c309ecefe0d3e`;
- size: 837,491 bytes;
- created: 2026-09-03T10:07:45Z;
- recorded expiry: 2026-10-03T10:07:44Z.

The earlier native artifact inspection recorded macOS 15.7.7, Safari 26.5.2 and the bundled SafariDriver 26.5.2 family. The exact final-head artifact is retained separately above; R1-G2 does not infer native iOS behavior from this desktop execution.

## Ordinary release/build evidence

Release-candidate run `33742551179` passed on the same exact source head, including:

- public Python/empirical/governance tests;
- compilation;
- Ruff;
- strict mypy;
- whitespace integrity;
- TypeScript validation;
- optimized `DATA_MODE=derived_only` production build;
- optimized-build private-data scan;
- production-server route smoke tests.

## R1-G2 conclusion

Under the explicit Release 1 scope decision, the automated/native R1-G2 contract is **satisfied on source head `3391c39337519715e45d33c5d79053feb6038964`**.

This conclusion does not claim:

- VoiceOver or NVDA/human screen-reader validation;
- manual keyboard/focus/tooltip/color/heading review;
- physical Android or iPhone testing;
- native iOS Safari;
- field Core Web Vitals;
- production-deployment correctness.

Those claims remain outside this R1-G2 evidence record. Production deployment and deployment-specific rights/security/provenance checks remain governed by R1-G3.
