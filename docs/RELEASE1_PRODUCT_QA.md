# Release 1 product QA — code-level pass

Date: 2026-08-30

This document records **code-level** product checks for the rights-safe Release 1 candidate. It does not substitute for a real browser, screen-reader, performance, or production-build audit.

## Implemented in this pass

### Information architecture

- Persistent release-status strip distinguishes `derived_only`, private `audit_snapshot`, and fail-closed live-source modes.
- Added a first-class **Sources** route to the primary navigation.
- Homepage is organized around durable five-wave evidence, measurement distinctions, the national-source boundary, and the unresolved industry wedge.
- Industry and occupation explorers use the same longitudinal visual grammar and explicit interpretive boundaries.
- Technical essay is constrained to a readable article width and uses numbered semantic sections.

### Accessibility-oriented code changes

- Skip-to-content link and focusable main-content target.
- Visible `:focus-visible` treatment for links, summaries, and horizontally scrollable tables.
- Reduced-motion media query.
- Tables use captions, column scopes, and row scopes.
- Horizontally scrollable tables are keyboard-focusable and explicitly labelled.
- Observable Plot graphics are wrapped in figures with captions and expose exact values through expandable HTML data tables.
- Plot containers redraw on width changes through `ResizeObserver` instead of assuming a desktop-only initial width.
- Scatter labels are selected by a stated rule (highest adoption / assisted-hours values) rather than input order.

### Rights and provenance communication

- Public release strip states that raw RPS observations are excluded.
- Sources page distinguishes RPS, CPS, OEWS, and BTOS roles and current evidence status.
- Methodology page explicitly separates direct measurements, derived diagnostics, composition counterfactuals, and causal/mechanism claims.
- Public and private evidence boundaries are described in user-facing language.
- `docs/source-provenance.md` now matches the fail-closed `derived_only` architecture rather than the retired static-FRED design.

### Editorial / construct discipline

- Reported time savings remain explicitly distinct from measured productivity.
- The Q2-2026 industry `R²(S~H) > R²(S~A)` ordering is described as a 3-of-5-wave result, not a structural law.
- Occupation–industry comparisons are phrased as aggregate alignment differences, not identified organizational mechanisms.
- A/H/S notation is defined in diagnostic-table captions.

## Checks that remain external gates

The following are **not verified** by this code-level pass:

1. Genuine `npm install` and `next build` in a network-capable environment.
2. Browser rendering in Safari, Chrome, Firefox, and mobile Safari.
3. Screen-reader traversal with VoiceOver/NVDA.
4. Lighthouse/Core Web Vitals performance audit.
5. Automated axe/WCAG browser scan.
6. Keyboard traversal of the fully rendered Observable Plot tooltip behavior.
7. Visual regression screenshots across target viewport widths.
8. Production deployment, headers, caching behavior, analytics/privacy configuration, and error monitoring.

No public-launch claim should imply those gates are complete until they are actually run.
