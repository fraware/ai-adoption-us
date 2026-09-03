# Release 1 production policy

Date: 2026-09-03

This document defines the repository-side production contract for the public **GenAI at Work** Release 1 deployment. The live deployment audit must verify the deployed system against this contract; platform defaults are not treated as evidence.

## 1. Public data mode

Release 1 production runs only with:

```text
DATA_MODE=derived_only
```

The public deployment must not contain `data/audit/private/`, raw RPS subgroup observations, private fixture files, or an endpoint that exposes those materials. The live RPS refresh/backend program is a separate operational track and is not activated by Release 1 deployment.

## 2. Deployment identity

The application exposes `/release-manifest.json`. The manifest is intentionally rights-safe and contains only:

- schema version;
- product identity;
- public data mode;
- deployed Git commit SHA;
- configured public site origin;
- analytics posture;
- client-monitoring posture.

For an accepted production deployment:

- `dataMode` must equal `derived_only`;
- `commitSha` must equal the audited Git commit and must not be `UNBOUND`;
- `siteOrigin` must equal the canonical production origin;
- `analytics` must equal `disabled`;
- `clientMonitoring` must equal `disabled`.

The deployment audit must also retain an immutable platform deployment identifier or a checksum/digest of the deployment artifact where the platform exposes one.

## 3. Canonical URL, robots, and sitemap

`NEXT_PUBLIC_SITE_URL` is the single configured production origin. It must be an HTTP(S) origin with no path, query, or fragment. Release 1 production should use HTTPS.

When configured, the origin supplies:

- Next.js `metadataBase`;
- the homepage canonical URL;
- Open Graph site URL;
- `robots.txt` host and sitemap declaration;
- absolute URLs in `sitemap.xml`;
- `/release-manifest.json` site identity.

The public pages are indexable. The sitemap contains only the six primary public content routes:

- `/`;
- `/explore/industries`;
- `/explore/occupations`;
- `/blog/after-adoption`;
- `/methodology`;
- `/sources`.

Private, audit, source-refresh, and internal QA paths must never be added to the sitemap.

## 4. HTTP security baseline

The application defines the following response-header baseline for all paths:

- `Content-Security-Policy` with same-origin defaults, no frames, no objects, no external connections, and only the inline script/style allowances currently required by the static Next.js application;
- `Referrer-Policy: strict-origin-when-cross-origin`;
- `X-Content-Type-Options: nosniff`;
- `X-Frame-Options: DENY`;
- a restrictive `Permissions-Policy` disabling camera, microphone, geolocation, payment, and USB;
- `Cross-Origin-Opener-Policy: same-origin`;
- `Strict-Transport-Security: max-age=31536000`;
- the default `X-Powered-By` header disabled.

The live audit must verify the actual production responses. If the deployment platform adds, removes, or overrides headers, the observed production behavior governs the audit result.

## 5. Caching policy

Release 1 does not add a blanket application-level `Cache-Control` header to all Next.js pages because that could override framework/platform handling of content-addressed assets. The intended behavior is:

- hashed `/_next/static/` assets may be cached immutably by the framework/platform;
- HTML and generated route responses must not be allowed to remain indefinitely stale after a production deployment;
- `/release-manifest.json` explicitly uses `public, max-age=0, must-revalidate` so deployment identity is always revalidated.

The live deployment audit must record the observed `Cache-Control`, `Age`, `ETag`, and relevant platform cache headers for the homepage, one hashed static asset, and `/release-manifest.json`. Any behavior that can serve a superseded release indefinitely fails the gate.

## 6. Analytics and privacy

Release 1 deliberately ships with **no third-party analytics, advertising, tracking pixel, consent framework, or analytics cookie**. No analytics SDK appears in the application dependency set or page source by design.

The production Content Security Policy restricts network connections to same-origin resources, providing an additional technical guard against silently adding external telemetry without changing this policy.

If analytics are introduced after Release 1, the privacy decision, dependency/configuration, user disclosure, and CSP must be reviewed as a separate change.

## 7. Monitoring and logging

Release 1 deliberately ships with **no client-side monitoring or error-reporting SDK**. The launch baseline relies on deployment-platform build/runtime/request logs and the existing reproducible CI/browser QA evidence.

The live audit must confirm that no monitoring SDK or external telemetry endpoint is present in the delivered client. Host-side operational logs must not ingest private RPS fixtures because those fixtures are absent from the public deployment boundary.

A future monitoring integration requires a separate privacy/security review.

## 8. Secrets

No secret may use a `NEXT_PUBLIC_` prefix. `NEXT_PUBLIC_SITE_URL` is public configuration, not a secret. The public release manifest must never expose environment variables other than the explicitly listed non-sensitive identity fields.

The live deployment audit must inspect delivered HTML/JavaScript and the release manifest for accidental secret/configuration leakage. The absence of private source files from the repository and optimized build remains a separate CI gate.

## 9. Failure paths

The automated R1-G2 browser suite already requires an unknown route to return HTTP 404, render an intelligible not-found surface, avoid private-path disclosure, and emit no unexpected runtime/console failures. R1-G3 additionally verifies this behavior on the deployed production origin.

## 10. Release 1 publication gate

A public Release 1 tag/release may be created only after all of the following are recorded:

1. R1-G2 is complete.
2. The production-hardening commit passes release CI and rendered browser QA.
3. A production deployment exists with exact commit identity.
4. The deployment audit verifies rights, headers, robots/sitemap, caching, privacy, monitoring, failure paths, and manifest identity.
5. Source citations and methodology links are checked against the deployed content.
6. Release notes state the scientific and evidence limitations without implying human screen-reader, native-iOS, physical-device, field-CWV, causal, or unsupported design-based evidence.

Human/manual and physical-device spot checks remain outside Release 1 scope under the 2026-09-03 R1-G2 scope decision.
