# Release 1 product QA — code and production-build pass

Initial code-level pass: 2026-08-30  
Networked production-build update: 2026-08-31

This document records the **code-level product QA** completed for the rights-safe Release 1 candidate plus the first genuine networked production build. It **does not substitute for a real browser**, screen-reader, automated accessibility, performance, visual-regression, or deployment audit.

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

These are implementation provisions, not proof that the rendered experience is accessible. The rendered checks remain open below.

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
- Composition/residual language remains experimental and non-causal; zero real CPS residual values are claimed.

## Networked production-build evidence — 2026-08-31

The 2026-08-30 code-only QA explicitly listed **Genuine `npm install` and `next build`** as unverified external gates. That historical statement remains important provenance; it is no longer the current state.

GitHub Actions run `33411128343` subsequently validated the rights-safe public handoff in a networked Ubuntu 24.04 environment.

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

This closes the earlier **genuine production build unverified** gate.

Permanent PR CI now strengthens that proof by requiring:

- strict `mypy src`;
- `npm ci` from the committed lockfile;
- production-server startup;
- HTTP route smoke tests;
- governance checks for private paths, bootstrap residue, and generated TypeScript metadata.

## Checks that remain external/rendered gates

The following are **not verified** by the code/build pass and must remain explicitly open:

1. Browser rendering/interaction in current Safari, Chrome, and Firefox.
2. Mobile rendering in iOS Safari and Android/Chrome or defensible equivalents.
3. Keyboard-only traversal of the fully rendered application, including chart/table interactions.
4. Screen-reader traversal with VoiceOver and NVDA or a defensible second screen reader.
5. Automated axe/WCAG browser scan.
6. Lighthouse accessibility audit.
7. Lighthouse performance/Core Web Vitals review.
8. Visual-regression screenshots across the target viewport matrix.
9. Browser-console hydration/runtime error review.
10. Production deployment, headers, caching, artifact identity, analytics/privacy, secrets, and monitoring review.

## Release-language rule

A successful optimized build means the application compiles and prerenders under the tested rights-safe configuration. It does **not** establish browser accessibility, real-user performance, deployment correctness, source-rights resolution, CPS composition validity, or causal interpretation.

No public-launch claim should imply those gates are complete until dated execution evidence is committed.
