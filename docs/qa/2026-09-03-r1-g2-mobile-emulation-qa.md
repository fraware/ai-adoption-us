# R1-G2 mobile emulation QA — 2026-09-03

Status: **automated mobile-emulation portion passed; R1-G2 remains open for native/manual gates**.

## Scope

This record extends the Release 1 browser QA contract with explicit mobile device-context emulation for the rights-safe `DATA_MODE=derived_only` build. It adds a Pixel 7 context executed against the stable Chrome channel and an iPhone 15 Pro context executed against Playwright WebKit.

These are automated compatibility proxies. The Android project is not a physical Android-device test. The iPhone/WebKit project is not native iOS Safari, a physical iPhone test, or evidence that Safari-specific platform integration is complete. Human assistive-technology testing also remains outside this automated record.

## Execution anchor

Pull request: `#61`  
Source head: `8147cabdc0e0104717762e7955c081de48458532`  
PR merge candidate checked out by Actions: `8bb7d5df1ec1bbb28f83323e4eb90f08ec151978`  
Successful rendered-browser workflow run: `33737876591`  
Successful release-candidate CI run on the same source head: `33737876597`

Retained rendered-QA artifact:

- ID: `9886672185`
- name: `r1-g2-browser-qa-8bb7d5df1ec1bbb28f83323e4eb90f08ec151978`
- SHA-256: `9d2b73748435c8a23a11d9f21e02aee390c4a5f0320b7a3e71dbc64a3f8862a1`
- size: 18,735,411 bytes
- created: 2026-09-03T09:21:29Z
- expiry recorded by GitHub: 2026-10-03T09:21:26Z

The artifact contains 156 files, including Playwright JSON/HTML output, screenshots, Lighthouse reports, browser/device metadata, server logs, and build/static-file inventories.

## Toolchain and browser provenance

Committed tool versions:

- `@playwright/test` 1.62.1
- `@axe-core/playwright` 4.13.0
- `lighthouse` 13.4.1
- Next.js 16.3.3

The successful run reported:

- stable Chrome 151.0.7922.173;
- Playwright-managed Firefox 153.0;
- Playwright WebKit 26.5.

The device reporter reads the pinned Playwright version directly from `package.json` and fails closed if it cannot resolve it.

## Rendered matrix

Existing engine/viewport projects remained in the matrix:

- Chrome: 375 × 812, 768 × 1024, 1024 × 900, 1440 × 1000;
- Firefox: 375 × 812, 1440 × 1000;
- WebKit: 375 × 812, 1440 × 1000.

Two explicit mobile device contexts were added:

- Pixel 7 / stable Chrome: viewport 412 × 839, screen 412 × 915, device scale factor 2.625, `isMobile=true`, `hasTouch=true`;
- iPhone 15 Pro / Playwright WebKit: viewport 393 × 659, screen 393 × 852, device scale factor 3, `isMobile=true`, `hasTouch=true`.

Result: **70 passed / 70 executed**.

Both mobile projects execute the same six primary-route contracts plus the industries publication/triangulation assertion used by the rest of the matrix.

## Mobile behavioral contract

For each primary route in the two mobile projects, the suite requires:

- a phone-width rendered context (`innerWidth <= 450`);
- expected Android or iPhone user-agent identity;
- delivery of an actual `touchstart` event generated through Playwright's touchscreen API;
- successful document and application-icon responses;
- one `main`, one `h1`, named primary navigation, and the expected primary links;
- no page-level horizontal overflow;
- visible tables contained in horizontal-scroll wrappers;
- fresh-document keyboard entry through the skip link with visible focus and transfer to `main`;
- reduced-motion behavior;
- zero unresolved axe violations with `serious` or `critical` impact under the configured WCAG tags;
- zero uncaught page errors and zero browser-console errors.

The touch probe runs after the fresh-document keyboard and axe checks so pointer/touch activity cannot contaminate the keyboard-entry evidence. Runtime and console assertions run after the touch probe so touch-triggered errors remain observable.

## Harness defect discovered and corrected

The first expanded run, `33736750083`, failed six iPhone/WebKit route cases because the proposed harness required `navigator.maxTouchPoints > 0`. The Playwright iPhone descriptor declared touch support, but the WebKit context exposed `maxTouchPoints = 0`.

That was an unsupported fingerprint assumption rather than a product failure. The harness also contained a CSS coarse-pointer assertion that was not part of Playwright's documented touch-emulation contract. Both fingerprint assumptions were removed. The final contract tests the behavior that matters directly: Playwright must be able to generate a touchscreen tap and the page must receive the resulting `touchstart` event.

The failed exploratory artifact remains useful provenance but is not passing evidence. Its artifact ID is `9886158000` and SHA-256 is `29dc79ab00f1640bb3eebf14174f5f8a5f33c45990b7f0f101aea408be229335`.

## Lighthouse

All six desktop routes plus the mobile homepage were audited in the successful run.

| Report | Accessibility | Performance | LCP (ms) | CLS | TBT (ms) |
|---|---:|---:|---:|---:|---:|
| after-adoption desktop | 100 | 100 | 459 | 0.000 | 0 |
| home desktop | 100 | 100 | 507 | 0.000 | 0 |
| home mobile | 100 | 100 | 1817 | 0.000 | 46 |
| industries desktop | 100 | 100 | 502 | 0.000 | 0 |
| methodology desktop | 100 | 100 | 461 | 0.000 | 0 |
| occupations desktop | 100 | 100 | 496 | 0.000 | 0 |
| sources desktop | 100 | 100 | 460 | 0.000 | 0 |

The automated accessibility threshold is 95. Every report scored 100. Performance measurements are CI laboratory observations and must not be relabelled as field Core Web Vitals.

The optimized `.next` directory was approximately 60 MB. That is build-output size, not browser transfer size.

## What this evidence closes

Within the automated R1-G2 matrix, this record establishes defensible mobile device-context proxies beyond narrow desktop-browser viewports:

- Android/Chrome: Pixel 7 descriptor against the stable Chrome binary, including touch-event delivery;
- iOS/WebKit: iPhone 15 Pro descriptor against Playwright WebKit, including touch-event delivery.

It does not convert those proxies into native-device evidence.

## Residual R1-G2 gates

R1-G2 remains open for:

- current native Safari desktop;
- native/physical iOS Safari behavior beyond the iPhone/WebKit automated proxy;
- physical Android/Chrome behavior beyond the Pixel 7 automated proxy, if required by final launch review;
- full keyboard-only route/navigation traversal beyond the automated skip-link contract;
- VoiceOver;
- NVDA or another defensible second screen-reader environment;
- manual chart resize, tooltip, and label interaction review;
- manual no-data/error-state intelligibility review;
- manual review that critical meaning does not depend on color alone;
- assistive-technology heading/landmark review;
- field performance evidence once a deployed traffic context makes it meaningful.

## Exact-head revalidation contract

This report, `docs/RELEASE1_PRODUCT_QA.md`, and `docs/RELEASE_CHECKLIST.md` are browser-QA workflow triggers. The documentation commits therefore require a fresh successful browser-QA run on the exact final PR head before merge.

To avoid a self-referential documentation loop, the exact final documentation-head SHA and its successful post-record browser-QA run are recorded in the PR conversation rather than by editing this report again.
