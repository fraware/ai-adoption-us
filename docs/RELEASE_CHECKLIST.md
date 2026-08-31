# Release checklist

A release is not launch-ready until every applicable item below is explicitly resolved.

## A. Scientific integrity

- [ ] Product language preserves all invariants in `docs/product-spec.md`.
- [ ] No claim calls reported savings measured productivity.
- [ ] No cross-sectional residual is labeled an organizational effect.
- [ ] Latest-quarter rankings are accompanied by stability context.
- [ ] Every displayed statistic comes from a generated artifact or directly defined transformation.
- [ ] Private-source revisions trigger full longitudinal regeneration.
- [ ] CPS/Release 1.1 content is disabled until real CPS execution is complete.

## B. Data rights and provenance

- [ ] Public build uses `DATA_MODE=derived_only`.
- [ ] `data/audit/private/` absent from Git and deployment bundle.
- [ ] Release export boundary test passes.
- [ ] Source/provenance page accurately describes each source class.
- [ ] Any future FRED live adapter has explicit reviewed rights behavior and required attribution/disclaimer.
- [ ] Direct RPS permission/feed status recorded.

## C. Python/research validation

- [ ] `pytest -q` passes on private research checkout.
- [ ] public checkout passes all non-private tests and only expected private tests skip.
- [ ] `compileall` passes.
- [ ] longitudinal derived artifacts regenerate byte-for-byte privately.
- [ ] registry cardinality = 131 and identities complete.
- [ ] `git diff --check` passes.

## D. Web production build

- [ ] lockfile generated and reviewed.
- [ ] clean install succeeds.
- [ ] `DATA_MODE=derived_only npm run build` succeeds.
- [ ] no private paths bundled.
- [ ] production server starts successfully.
- [ ] no hydration/runtime errors in browser console.

## E. Browser QA

Test at minimum:

- [ ] current Chrome desktop;
- [ ] current Safari desktop;
- [ ] current Firefox desktop;
- [ ] iOS Safari-sized viewport;
- [ ] Android/Chrome-sized viewport;
- [ ] 375 px width;
- [ ] tablet width;
- [ ] large desktop width.

For every route:

- [ ] navigation works;
- [ ] no horizontal page overflow;
- [ ] tables remain usable;
- [ ] plots redraw after resize;
- [ ] no data labels overlap beyond acceptable bounds;
- [ ] all no-data/error states are intelligible.

## F. Accessibility

- [ ] keyboard-only route/navigation test;
- [ ] visible focus states;
- [ ] skip link works;
- [ ] VoiceOver test;
- [ ] NVDA or equivalent test;
- [ ] axe automated scan;
- [ ] Lighthouse accessibility audit;
- [ ] chart data table equivalent is usable;
- [ ] no critical meaning encoded only by color;
- [ ] heading hierarchy and landmarks reviewed.

## G. Performance and reliability

- [ ] Lighthouse performance audit;
- [ ] Core Web Vitals reviewed;
- [ ] bundle size reviewed;
- [ ] route-level error handling verified;
- [ ] static/SSR behavior understood;
- [ ] deployment headers/security baseline reviewed;
- [ ] monitoring/logging decision documented.

## H. Publication

- [ ] canonical domain selected;
- [ ] page metadata/title/description reviewed;
- [ ] source citations reviewed;
- [ ] methodology links present from empirical claims;
- [ ] final editorial proofread;
- [ ] release commit/tag created;
- [ ] release notes summarize evidence and limitations;
- [ ] public artifact checksum recorded.
