# Deployment

The public GenAI at Work site is a static Next.js application hosted on GitHub Pages.

**Production site:** https://fraware.github.io/ai-adoption-us/

This guide documents the current hosting configuration and the checks maintainers should understand when deploying the site. Scientific release preparation is covered separately in [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md).

## Build configuration

The GitHub Pages build uses:

```text
DATA_MODE=derived_only
GITHUB_PAGES=true
NEXT_PUBLIC_SITE_URL=https://fraware.github.io/ai-adoption-us
```

`GITHUB_PAGES=true` enables the static-export configuration required for the `/ai-adoption-us` project path, including the appropriate base path and asset prefix.

`NEXT_PUBLIC_SITE_URL` is public configuration, not a secret. It supplies the canonical site URL used by page metadata, Open Graph metadata, `robots.txt`, and `sitemap.xml`.

## Public routes

The published site includes the primary research routes:

- `/`;
- `/explore/industries`;
- `/explore/occupations`;
- `/blog/after-adoption`;
- `/methodology`;
- `/sources`.

Private research, source-acquisition, audit, and QA paths are not part of the public site.

## Public data mode

Production runs in `derived_only` mode. The deployment may contain released public observations and derived artifacts, but it must not contain:

- private RPS source-input files;
- respondent-level data;
- private audit fixtures;
- credentials;
- private storage paths;
- third-party source material outside the documented publication scope.

The public build should not automatically switch to a private data source when a released value is unavailable.

## Release identity

The static export contains a rights-safe release manifest used to identify the deployed build. A production deployment should correspond to a version recorded in `data/registry/observatory_release_registry.json` and `data/releases/`.

The deployment audit should verify that the live site's release identity matches the version intended for publication rather than assuming that a successful build or Pages job proves that the newest content is being served.

## GitHub Pages workflow

The repository's Pages workflow performs the following high-level sequence:

1. checks out the repository version to deploy;
2. installs locked dependencies;
3. builds the static site in `derived_only` mode;
4. validates the exported artifact;
5. uploads the static output as a GitHub Pages artifact;
6. deploys the validated artifact;
7. checks the live origin after deployment.

GitHub Pages must be configured with **Source: GitHub Actions** in repository settings.

## Security model

GitHub Pages is static hosting. The application therefore cannot control every HTTP response header that a self-hosted Next.js server could set.

The static application includes browser-level policies that survive export, but response headers served by GitHub Pages are platform behavior. Documentation should not claim that the application controls headers such as HSTS, `X-Frame-Options`, `Permissions-Policy`, or other server-set policies unless the deployed platform actually provides and guarantees them.

The non-Pages development/server configuration may use stronger response-header settings for local validation; those settings should not be presented as properties of the GitHub Pages deployment.

## Caching

GitHub Pages controls CDN caching behavior. The application does not define the platform's production cache lifetime.

After deployment, the live audit should verify that the current release manifest and representative static assets resolve correctly. If a previous version remains cached, publication should not be treated as complete until the intended version is served.

## Privacy and telemetry

Release 1 ships without third-party analytics, advertising, tracking pixels, or client-side error-reporting SDKs.

Any future analytics or monitoring integration should receive an explicit privacy and security review before deployment, including an update to the site's network policy and public privacy documentation where appropriate.

## Secrets

No secret should use a `NEXT_PUBLIC_` prefix because those variables are included in browser-visible builds by design.

Public configuration such as `NEXT_PUBLIC_SITE_URL` and a release commit identifier is not secret. Server-only credentials used during source acquisition or release preparation must never enter the static web build.

## Error handling

The static export includes a `404.html` page. Deployment checks should verify that unknown public URLs resolve to the intended not-found experience and do not disclose private filesystem paths or internal source information.

## Deployment verification

For a production release, verify at least:

- the expected release/version identity;
- all primary routes;
- the project-path base URL and static assets;
- `robots.txt` and `sitemap.xml`;
- the not-found page;
- absence of private data and secret markers from the exported artifact;
- expected privacy/telemetry behavior;
- representative desktop and mobile rendering.

A successful GitHub Actions job is necessary operational evidence, but the live origin should also be inspected before announcing a release.
