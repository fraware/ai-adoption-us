# Release 1 R1-G3 deployment audit — 2026-09-03

Status: **PASS for the audited deployment boundary**

This record binds the Release 1 production-deployment audit to an exact Git commit, GitHub Actions run, static deployment artifact, and retained live-origin evidence artifact. It does not expand the scientific claims, source rights, browser evidence, or uncertainty guarantees of Release 1.

## Audited deployment

- Repository: `fraware/ai-adoption-us`
- Hosting target: GitHub Pages project site
- Public origin: `https://fraware.github.io/ai-adoption-us/`
- Audited commit: `78e02559390a2a96506d28068154876e9b4c0b21`
- Workflow: `GitHub Pages Release 1`
- Workflow run: `33771342350`
- GitHub Pages artifact: `9899755604`
- GitHub Pages artifact digest: `sha256:cda0fdea4a8ef64d83d24245fd0a15147f319bf06818528c21a753cd7400806b`
- Live-origin audit artifact: `9899773651`
- Live-origin audit artifact digest: `sha256:211aee8de7cc80a16bf5fa181b16df1bb9f4162a65fecbfcf0c66b03e53dd38c`
- Live audit timestamp: `2026-09-03T15:14:06Z`

## Production identity and data boundary

The deployed `/release-manifest.json` reported:

- `hostingTarget = github-pages`
- `dataMode = derived_only`
- `commitSha = 78e02559390a2a96506d28068154876e9b4c0b21`
- `siteBaseUrl = https://fraware.github.io/ai-adoption-us`
- `analytics = disabled`
- `clientMonitoring = disabled`
- `sourceBytesPublished = false`

The static artifact audit and the live-origin audit both passed. The deployed homepage and release manifest were checked for known private/raw/secret identifiers. The audit also required the following public paths to fail closed with HTTP 404:

- `/data/audit/private/rps_subgroup_5q_audit.json`
- `/rps_subgroup_5q_audit.json`
- `/api/rps/raw`

No raw RPS audit fixture or source bytes are represented as public Release 1 material.

## Public route and provenance checks

The live audit successfully fetched the homepage, industries explorer, occupations explorer, technical essay, methodology, sources/provenance, `robots.txt`, `sitemap.xml`, and `release-manifest.json`. The sitemap contained the intended public routes and `robots.txt` permitted crawling while pointing to the Release 1 sitemap.

The delivered homepage was checked for common third-party analytics and client-monitoring identifiers. None of the guarded analytics/monitoring identifiers were present. Release 1 therefore retains the documented posture of no third-party analytics/tracking SDK and no client-side monitoring SDK.

## Observed GitHub Pages transport and cache behavior

The live audit observed the platform-delivered homepage response with HTTP 200, `server: GitHub.com`, HTTPS HSTS (`strict-transport-security: max-age=31556952`), and `cache-control: max-age=600`. The release manifest was also served with HTTP 200 and `cache-control: max-age=600`.

These are observations of the GitHub Pages platform at audit time. Release 1 does not claim application control over GitHub Pages response headers or CDN caching policy. The static application retains its committed metadata/security posture, while transport headers and cache behavior remain platform-controlled.

## QA and scientific interpretation boundary

R1-G2 was already closed under the recorded automated/native scope before this deployment audit. Human screen-reader testing, physical-device checks, field Core Web Vitals, and application-controlled GitHub Pages security headers are not Release 1 evidence.

Reported time savings remain self-reported counterfactual savings rather than measured labor productivity. Occupation-adjusted industry-context residuals remain derived descriptive evidence rather than identified organizational, efficiency, productivity, or causal effects. Full design-based uncertainty for custom CPS composition vectors remains unsupported.

## Finalization rule

This audit establishes that the Release 1 deployment architecture can publish the rights-safe static product and verify the live origin against exact provenance. Any later release-finalization commit must pass the same GitHub Pages build, deployment, and live-origin audit before it can be used as the formal Release 1 tag target.
