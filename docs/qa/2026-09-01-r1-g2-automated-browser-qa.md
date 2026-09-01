# R1-G2 automated browser QA — 2026-09-01

Status: **automated portion passed; R1-G2 remains open for native/manual gates**.

## Scope

This record covers the automated browser, accessibility, responsive-layout, runtime-error, and Lighthouse portion of Release 1 gate R1-G2 for the rights-safe `DATA_MODE=derived_only` build.

It does not claim completion of native Safari/iOS Safari, Android-device behavior, VoiceOver, NVDA/second screen-reader testing, manual chart interaction, or field Core Web Vitals.

## Execution anchor

Successful baseline workflow run: `33501320183`  
PR: `#19`  
Source head: `6ed9da2074c2ee042c88912e2c3bdb05806e88f7`  
PR merge candidate checked out by Actions: `d034f29cfaf981656a291f004be5fc7f1d64d3fb`

Retained workflow artifact:

- ID: `9797926404`
- name: `r1-g2-browser-qa-d034f29cfaf981656a291f004be5fc7f1d64d3fb`
- SHA-256: `c096aed747fd8fd7dd67195243185c1c5618e03c91e671c7747cf361783ebbf0`
- size: 11,335,162 bytes
- created: 2026-09-01T11:16:44Z
- expiry recorded by GitHub: 2026-10-01T11:16:43Z

The artifact contains Playwright JSON/HTML output, success screenshots, Lighthouse JSON, browser-version metadata, server log, optimized build-size output, and largest-static-file inventory.

## Toolchain

Committed package versions:

- `@playwright/test` 1.62.1
- `@axe-core/playwright` 4.13.0
- `lighthouse` 13.4.1
- Next.js 16.3.3

The successful baseline artifact reported:

- stable Chrome 151.0.7922.173
- Playwright-managed Firefox 153.0
- Playwright WebKit 26.5

The baseline artifact's `playwrightVersion` metadata field was null because the initial reporter depended on an npm environment variable that was absent. This was treated as an evidence-provenance defect. The reporter now reads the pinned package version directly from `package.json` and fails closed if resolution fails; a repository test guards the behavior. The correction does not change the interpretation of the successful baseline browser results.

## Route and viewport matrix

Routes:

- `/`
- `/explore/industries`
- `/explore/occupations`
- `/methodology`
- `/sources`
- `/blog/after-adoption`

Projects:

- Chrome: 375 × 812, 768 × 1024, 1024 × 900, 1440 × 1000
- Firefox: 375 × 812, 1440 × 1000
- WebKit: 375 × 812, 1440 × 1000

Result: **48 passed / 48 executed**.

WebKit is an engine-level compatibility check. It is not evidence of native Safari or iOS Safari completion.

## Automated assertions

For every route/project combination the suite requires:

- successful document response;
- a loadable application icon;
- one `main` and one `h1`;
- named primary-navigation and footer surfaces;
- expected primary-navigation links present;
- no page-level horizontal overflow;
- every rendered table visible and inside a horizontal-scroll wrapper;
- skip link as first keyboard focus target from a fresh page;
- visible focus outline on the skip link;
- skip-link activation moves focus to `#main-content`;
- reduced-motion media produces `scroll-behavior: auto` and zero skip-link transition duration;
- zero unresolved axe violations with `serious` or `critical` impact under the configured WCAG 2.x tags;
- zero uncaught page errors;
- zero browser-console errors.

This contract does not claim that every navigation link is clicked, every chart tooltip is exercised, or runtime chart redraw is explicitly asserted after a scripted viewport resize.

## Defects found and corrected during execution

1. Missing application favicon/resource generated a route-level 404. A Next application icon was added and the browser suite now verifies icon metadata and a successful resource response.
2. Two labelled generic containers produced accessibility-tree ambiguity. They now expose explicit `group` roles.
3. The methodology page overflowed at 375 px in Firefox and WebKit. Initial suspicion focused on the long residual identifier; artifact inspection showed the actual overflow came from the H1 word `interpretation`. The final fix reduced narrow-screen H1 sizing instead of hiding overflow. The residual identifier retains deterministic `<wbr>` break opportunities as a defensive text-layout measure.
4. Browser-version provenance omitted Playwright's version. The reporter now reads the exact pinned dependency from the committed package manifest and fails closed if it cannot do so.

The final responsive fix was accepted only after the full 48-case matrix passed.

## Lighthouse

All six desktop routes plus the mobile homepage were audited.

| Report | Accessibility | Performance | LCP (ms) | CLS | TBT (ms) |
|---|---:|---:|---:|---:|---:|
| after-adoption desktop | 100 | 100 | 445 | 0.000 | 0 |
| home desktop | 100 | 100 | 528 | 0.000 | 0 |
| home mobile | 100 | 100 | 1855 | 0.000 | 48 |
| industries desktop | 100 | 100 | 506 | 0.000 | 0 |
| methodology desktop | 100 | 100 | 459 | 0.000 | 0 |
| occupations desktop | 100 | 100 | 494 | 0.000 | 0 |
| sources desktop | 100 | 100 | 449 | 0.000 | 0 |

The automated accessibility threshold is 95. Every report scored 100.

These performance measurements are CI laboratory observations. They are not field Core Web Vitals and do not establish deployed real-user performance.

## Visual evidence review

The retained success screenshots were reviewed across the route/project matrix. No clipping, material overlap, page-level horizontal spill, or obvious breakpoint failure was observed in the captured main-content states. The previously failing 375-px methodology layout is clean in Chrome, Firefox, and WebKit.

Because the screenshots are captured after the skip-link test has moved focus into `main`, they are not a complete manual review of the header/navigation state. That limitation remains open.

## Residual gates

R1-G2 remains open for:

- native current Safari desktop;
- real or defensible iOS Safari;
- real or defensible Android/Chrome device behavior;
- full keyboard-only traversal of interactive affordances beyond the automated skip-link contract;
- VoiceOver;
- NVDA or defensible second screen reader;
- manual chart resize/tooltip/label interaction review;
- manual color-only-meaning review;
- assistive-technology heading/landmark review;
- field performance evidence after deployment.

## Exact-head revalidation contract

The browser-QA workflow now triggers on this `docs/qa/**` record and the two release QA/checklist files in addition to web-code changes. Therefore the final PR documentation head must receive its own successful browser-QA run before merge.

The exact final PR-head SHA and post-record workflow run are recorded in the PR conversation once that run completes instead of editing this file again and creating a self-referential infinite revalidation loop.
