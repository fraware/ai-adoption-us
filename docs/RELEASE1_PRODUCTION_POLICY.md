# Release 1 production policy

Date: 2026-09-03

This document defines the repository-side production contract for the public **GenAI at Work** Release 1 deployment on GitHub Pages. The live deployment audit must verify the deployed site against this contract; repository configuration and platform assumptions are not themselves deployment evidence.

## 1. Hosting and public data mode

Release 1 uses GitHub Pages as a static host at the default project site:

```text
https://fraware.github.io/ai-adoption-us/
```

The production build runs only with:

```text
DATA_MODE=derived_only
GITHUB_PAGES=true
NEXT_PUBLIC_SITE_URL=https://fraware.github.io/ai-adoption-us
```

`GITHUB_PAGES=true` enables the Next.js static-export profile with `output: export`, `basePath: /ai-adoption-us`, `assetPrefix: /ai-adoption-us`, and trailing-slash routes. The public deployment must not contain `data/audit/private/`, raw RPS subgroup observations, private fixture files, or an endpoint exposing those materials. The live RPS refresh/backend program remains a separate operational track and is not activated by Release 1 deployment.

## 2. Deployment identity

The static export contains `/release-manifest.json`. The manifest is intentionally rights-safe and contains only non-sensitive deployment identity:

- schema version;
- product identity;
- hosting target (`github-pages`);
- public data mode;
- exact Git commit SHA supplied at build time;
- configured public site base URL;
- analytics posture;
- client-monitoring posture;
- an explicit declaration that source bytes are not published.

For an accepted production deployment:

- `dataMode` must equal `derived_only`;
- `commitSha` must equal the audited Git commit and must not be `UNBOUND`;
- `siteBaseUrl` must equal `https://fraware.github.io/ai-adoption-us`;
- `analytics` and `clientMonitoring` must equal `disabled`;
- `sourceBytesPublished` must equal `false`.

The GitHub Pages deployment workflow/run ID and uploaded Pages artifact identity are retained as the immutable platform-side deployment evidence.

## 3. Canonical URL, robots, and sitemap

`NEXT_PUBLIC_SITE_URL` is the canonical public site base URL and may include the GitHub Pages project path. It must use HTTP(S) and contain no query or fragment. Release 1 uses HTTPS.

The configured base URL supplies:

- Next.js metadata base and homepage canonical URL;
- Open Graph site URL;
- `robots.txt` host and sitemap declaration;
- absolute URLs in `sitemap.xml`;
- `/release-manifest.json` site identity.

The sitemap contains only the six primary public content routes beneath `/ai-adoption-us`:

- `/`;
- `/explore/industries`;
- `/explore/occupations`;
- `/blog/after-adoption`;
- `/methodology`;
- `/sources`.

Private, audit, refresh, and QA paths are excluded.

## 4. Security baseline and GitHub Pages limitation

GitHub Pages is static hosting. Next.js static export does not support the framework `headers()` feature, so Release 1 must **not** claim application-controlled HTTP security headers on the deployed Pages responses.

The application still uses two defenses that survive static export:

- a restrictive HTML `Content-Security-Policy` meta policy covering default/base/form/object/image/font/style/script/connect sources;
- `Referrer-Policy: strict-origin-when-cross-origin` expressed through document metadata.

A CSP meta element cannot provide all response-header protections; in particular, frame-ancestor enforcement and headers such as `X-Content-Type-Options`, `X-Frame-Options`, `Permissions-Policy`, `Cross-Origin-Opener-Policy`, or application-selected HSTS are outside the application's control on GitHub Pages. The live audit records the headers GitHub actually serves and treats them as platform behavior, not repository guarantees.

The non-Pages Next.js profile retains a stricter response-header configuration for local/self-hosted validation, but those headers are not Release 1 GitHub Pages evidence.

## 5. Caching policy

The application cannot define GitHub Pages CDN response caching policy. The live audit therefore records observed `Cache-Control`, `Age`, `ETag`, `Last-Modified`, and relevant GitHub/Fastly cache headers for:

- the homepage;
- one hashed `/_next/static/` asset beneath the project base path;
- `/release-manifest.json`.

Release correctness is established primarily through immutable deployment identity and post-deployment URL verification, not by assuming a particular GitHub Pages TTL. A deployment that continues serving a prior `release-manifest.json` after the Pages deployment is reported successful fails the audit until convergence is verified.

## 6. Analytics and privacy

Release 1 ships with **no third-party analytics, advertising, tracking pixel, consent framework, analytics cookie, or client telemetry SDK**. No analytics dependency is present in the application dependency set by design.

The static CSP meta policy restricts network connections to same-origin resources, providing an additional client-side guard against silently adding external telemetry without changing the policy.

Any later analytics integration requires a separate privacy/security review.

## 7. Monitoring and logging

Release 1 ships with **no client-side monitoring or error-reporting SDK**. Operational visibility is limited to GitHub Actions build/deployment evidence and whatever aggregate request/availability information GitHub Pages itself exposes. No private RPS fixtures can enter host logs because those fixtures are excluded from the public source/build boundary.

A future monitoring integration requires separate privacy/security review.

## 8. Secrets

No secret may use a `NEXT_PUBLIC_` prefix. `NEXT_PUBLIC_SITE_URL` is public configuration. `RELEASE_COMMIT_SHA` is a public deployment identity, not a secret.

CI injects a synthetic server-only secret marker during ordinary production-build tests and verifies it is absent from HTML and client assets. The Pages static-export workflow separately scans the `out/` artifact for private paths, source observations, and forbidden markers before upload.

## 9. Failure paths

R1-G2 already requires an unknown route to return a coherent not-found surface under the Node production server. GitHub Pages static export produces `404.html`; the Pages artifact audit requires that file to exist and the live deployment audit verifies an unknown Pages URL resolves to the expected 404 surface without private-path disclosure.

## 10. GitHub Pages deployment workflow

The repository uses a custom GitHub Actions workflow that:

1. checks out the exact commit;
2. installs locked dependencies;
3. builds with `DATA_MODE=derived_only` and `GITHUB_PAGES=true`;
4. verifies the static artifact and release manifest;
5. uploads `apps/web/out` as the GitHub Pages artifact;
6. deploys only on pushes to `main`.

GitHub Pages must be enabled with **Source: GitHub Actions** in repository settings. The normal `GITHUB_TOKEN` cannot enable Pages when it is disabled. The official `configure-pages` action documents that automatic enablement requires a stronger token carrying administration/pages-write permissions. The current repository connector is therefore not treated as authority to self-enable Pages.

If the repository setting is already enabled, deployment can proceed automatically after merge. If it is disabled, the workflow's deployment step is expected to fail closed until the repository owner enables **Settings → Pages → Source: GitHub Actions**. No alternate hosting service is selected or invoked by this Release 1 workflow.

## 11. Release 1 publication gate

A public Release 1 tag/release may be created only after all of the following are recorded:

1. R1-G2 is complete.
2. The production-hardening commit passes release CI, rendered browser QA, native Safari QA, and the GitHub Pages static-export build.
3. GitHub Pages reports a successful deployment of that exact commit.
4. The live site audit verifies data mode, artifact identity, base-path routing, robots/sitemap, failure paths, platform-served headers/caching, privacy/telemetry posture, and release-manifest identity.
5. Source citations and methodology links are checked against the deployed content through automated/public-surface inspection where feasible.
6. Release notes state the scientific and evidence limitations without implying human screen-reader, native-iOS, physical-device, field-CWV, causal, design-based, or application-controlled GitHub Pages response-header evidence.

Human/manual and physical-device spot checks remain outside Release 1 scope under the 2026-09-03 R1-G2 scope decision.
