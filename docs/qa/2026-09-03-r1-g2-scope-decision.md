# R1-G2 Release 1 QA scope decision — 2026-09-03

## Decision

For Release 1, the project owner directed that **human/manual QA steps and physical-device spot checks are not launch-blocking requirements**.

Accordingly, R1-G2 is evaluated on reproducible automated evidence plus native desktop Safari automation. The following are outside the Release 1 launch gate:

- VoiceOver traversal;
- NVDA or another human-operated second screen reader;
- manual keyboard/focus inspection beyond automated keyboard contracts;
- manual tooltip/label/color review;
- manual heading/landmark review;
- physical iPhone/iOS Safari testing;
- physical Android/Chrome testing.

These items are **not recorded as completed**. They are explicitly out of scope for the Release 1 launch decision.

## Release 1 automated evidence bar

R1-G2 may close when the exact release head has passed all applicable automated checks below:

1. stable Chrome, Firefox and Playwright WebKit rendered matrix across the supported viewport/device projects;
2. explicit Pixel 7/Chrome and iPhone 15 Pro/WebKit emulation proxies, including delivered touch events;
3. native macOS Safari through the installed Safari application and SafariDriver;
4. route semantics, primary navigation presence and real navigation transitions;
5. no page-level horizontal overflow and contained table fallbacks;
6. automated skip-link/focus-entry and reduced-motion contracts;
7. axe with no serious/critical violations under the configured WCAG tags;
8. Lighthouse accessibility target >=95 and recorded performance lab metrics;
9. no uncaught runtime or browser-console errors on primary success-path routes;
10. explicit runtime responsive-plot redraw after a viewport resize;
11. a production 404/not-found failure-path contract;
12. ordinary release-candidate CI, rights-safe production build, private-data scan and route smoke tests.

## Interpretation boundary

Closing R1-G2 under this scope means the Release 1 product passed the recorded automated browser/accessibility/responsive/performance contract and native Safari desktop automation.

It does **not** establish conformance under human assistive-technology use, physical-device behavior, native iOS Safari, or manual visual/interaction review. Public release language must preserve that distinction.
