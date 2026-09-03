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

## Historical networked-build evidence — 2026-08-31

The 2026-08-30 code-only QA explicitly listed **Genuine `npm install` and `next build`** as unverified external gates. That historical statement remains provenance; it is no longer the current state.

GitHub Actions run `33411128343` validated the rights-safe public handoff in a networked Ubuntu 24.04 environment. Permanent CI subsequently strengthened that proof by requiring strict `mypy src`, locked `npm ci`, production-server startup, route smoke tests, private-path build scans, and repository-governance checks.

## Automated rendered-browser baseline — 2026-09-01

The successful baseline execution is GitHub Actions run `33501320183`, associated with PR #19 source head `6ed9da2074c2ee042c88912e2c3bdb05806e88f7`.

The baseline Playwright suite passed 48/48 cases across all six public routes using stable Chrome at 375, 768, 1024, and 1440 px plus Playwright-managed Firefox and WebKit at 375 and 1440 px. WebKit in this matrix is an engine-compatibility signal only and is not the native-Safari evidence described later in this document.

At that historical baseline, full navigation clicking and explicit runtime chart redraw were not yet asserted. Those limitations were subsequently closed by the final 2026-09-03 automated tranche below.

Seven Lighthouse reports completed successfully: all six desktop routes plus the mobile homepage. Every accessibility report scored 100. Performance scores and timing values are CI laboratory evidence only and are **not field Core Web Vitals**.

## Explicit mobile-emulation evidence — 2026-09-03

PR #61 added Pixel 7/stable-Chrome and iPhone 15 Pro/WebKit device contexts. The accepted mobile-emulation tranche passed 70/70 cases. Each mobile route had to receive an actual `touchstart` event generated through Playwright's touchscreen API, in addition to phone-width and Android/iPhone identity checks.

The first proposed iPhone/WebKit expansion exposed a harness defect: the test incorrectly assumed that Playwright `hasTouch: true` required `navigator.maxTouchPoints > 0`, and a CSS coarse-pointer assertion relied on the same unsupported fingerprint inference. Those assertions were removed and replaced with a direct touch-behavior contract. This is recorded as a test-harness correction, not a product defect.

Detailed evidence is retained in `docs/qa/2026-09-03-r1-g2-mobile-emulation-qa.md`.

## Native Safari desktop evidence — 2026-09-03

PR #62 added a separate native-Safari workflow on a GitHub-hosted macOS 15 runner. The workflow records the Safari environment, launches the installed Safari application through SafariDriver, renders all six primary routes, validates semantic surfaces/navigation/overflow/table containment, and captures native Safari screenshots.

The exact final R1-G2 head passed native Safari, release-candidate CI, and the rendered browser/accessibility matrix. Issue #2 is closed under the agreed automation/native Release 1 scope.

## Final automated/native interaction completion — 2026-09-03

The final accepted cross-engine matrix executed 100 Playwright instances:

- **91 passed**;
- **9 skipped intentionally** because the explicit runtime plot-redraw contract runs once on stable Chrome at 1440 px instead of redundantly on every project.

The matrix additionally requires:

- actual primary-navigation clicks, target-path transitions, and brand-link transitions back to `/`;
- an explicit viewport resize of the published BTOS–RPS industry scatter plot followed by an SVG redraw through the `ResizeObserver` contract;
- a deliberate unknown production route returning HTTP 404 with an intelligible fail-closed surface and no unexpected runtime/console failures.

All seven final Lighthouse accessibility reports scored 100, above the >=95 automation threshold. Performance values remain laboratory evidence only.

## Release 1 hosting target — GitHub Pages

Release 1 is now targeted exclusively at the GitHub Pages project site:

```text
https://fraware.github.io/ai-adoption-us/
```

The public deployment profile is a Next.js static export with `DATA_MODE=derived_only`, a `/ai-adoption-us` base path, and a build-time rights-safe release manifest. GitHub Pages is static hosting and therefore cannot provide the application-controlled Next.js response-header policy used by the non-Pages server QA profile. The Pages deployment audit must record actual platform-served headers and must not claim that repository-defined response headers were deployed.

The GitHub Pages static-export workflow is a separate R1-G3 gate. A successful browser/server QA run does not establish that the Pages artifact builds or deploys correctly.

## Release 1 scope decision and residual limitations

The project owner explicitly removed human/manual checks and physical-device spot checks from the Release 1 launch critical path on 2026-09-03. Accordingly, the following are **not Release 1 blockers and are not claimed as completed evidence**:

- **Screen-reader traversal** with VoiceOver or NVDA;
- human-operated full keyboard/focus inspection beyond the automated contracts;
- manual chart tooltip/label/color/heading review;
- physical iPhone/iOS Safari testing;
- physical Android/Chrome testing;
- native iOS Safari beyond the accepted WebKit/iPhone emulation proxy.

The following remain R1-G3 deployment work until separately evidenced:

- successful GitHub Pages static export on the exact release candidate;
- GitHub Pages repository enablement with Source: GitHub Actions;
- successful Pages deployment of the exact commit;
- deployed artifact/run identity;
- live base-path, robots/sitemap, manifest, 404, headers/caching, and privacy/telemetry audit;
- field Core Web Vitals only if/when real deployment traffic later makes them meaningful.

## Release-language rule

The Release 1 browser evidence supports the statement that the rights-safe candidate compiled, served, and passed the recorded Chrome/Firefox/WebKit matrix, explicit Pixel 7 and iPhone 15 Pro device-emulation proxies, automated navigation/resize/404 interaction contracts, and native macOS Safari desktop automation.

It does **not** support claims of native iOS Safari, physical-device validation, human screen-reader usability, manual accessibility completion, field performance, or GitHub Pages deployment correctness.

**No public-launch claim** should imply those omitted evidence classes were completed. Published-aggregate RPS use is rights-cleared under the recorded project-owner attestation, but the separate durable live-refresh backend remains unactivated and the public Release 1 web path remains `derived_only`.
