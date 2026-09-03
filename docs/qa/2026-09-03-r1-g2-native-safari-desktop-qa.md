# R1-G2 native Safari desktop QA — 2026-09-03

## Scope

This record covers automated Release 1 rendering in the **native Safari desktop application** on a GitHub-hosted macOS runner. It is distinct from the Playwright WebKit compatibility proxy already used in the cross-engine matrix.

It does **not** establish native iOS Safari behavior, physical-device behavior, human screen-reader usability, or manual interaction review.

## Exact execution

- pull request: #62
- source head tested: `6bc0a33515ccedb9bee3d4fd5d546023e7e41b67`
- workflow: `Native Safari desktop QA`
- workflow run: `33739938301`
- job: `SafariDriver on macOS 15`
- result: **success**
- retained artifact ID: `9887312193`
- retained artifact name: `r1-g2-native-safari-ff028e52d6b8bd0e0b63da21ef31fa2338932a5e`
- artifact SHA-256: `c5e98f2028218346da3e75d0e067e474622a22c18fd16377dce00e38cf01cc07`
- artifact size: 837,494 bytes
- artifact created: 2026-09-03T09:39:10Z
- recorded expiry: 2026-10-03T09:39:08Z

The workflow checked out the pull-request merge candidate while the artifact and report preserve the tested source-head context separately. A documentation-head revalidation is required before merge.

## Native environment

The retained artifact records:

- macOS 15.7.7, build `24G720`;
- Safari 26.5.2;
- SafariDriver: `Included with Safari 26.5.2 (20624.2.5.18.7)`;
- WebDriver capability `browserName`: `Safari`;
- WebDriver capability `browserVersion`: `26.5.2`;
- WebDriver capability `platformName`: `macOS`;
- WebDriver capability `safari:platformVersion`: `15.7.7`;
- WebDriver capability `safari:useSimulator`: `false`.

The harness communicates directly with the built-in SafariDriver through the W3C WebDriver protocol and requests a `browserName: safari` session. It does not substitute Playwright WebKit or another browser engine for Safari.

## Route matrix

All six public Release 1 routes passed:

1. `/`
2. `/explore/industries`
3. `/explore/occupations`
4. `/methodology`
5. `/sources`
6. `/blog/after-adoption`

For each route the retained report records:

- document ready state `complete`;
- exact expected pathname;
- Safari user-agent identity (`Version/26.5.2 Safari/605.1.15`);
- exactly one primary-navigation landmark;
- exactly one `main`;
- exactly one `h1`;
- exactly one site footer;
- no missing expected primary-navigation links;
- no page-level horizontal overflow;
- visible tables, where present, contained in the expected table wrapper.

The measured document width was 1,425 CSS px in the native Safari session, with `scrollWidth == clientWidth` on every route.

## Screenshots and logs

The retained artifact contains native Safari screenshots for all six routes plus:

- `native-safari-report.json`;
- `macos-version.txt`;
- `safari-version.txt`;
- `safaridriver-version.txt`;
- `safaridriver.log`;
- production `server.log`.

The production server was Next.js 16.3.3 and became ready successfully on `127.0.0.1:3000`.

## Interpretation

This execution closes the Release 1 requirement for a current **native Safari desktop** rendering signal, subject to successful revalidation on the exact final documentation head.

It must not be cited as evidence for native iOS Safari, physical devices, VoiceOver/NVDA, or human/manual accessibility review.
