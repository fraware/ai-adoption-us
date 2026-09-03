# Release 1 R1-G3 — GitHub Pages preflight

Date: 2026-09-03

This record captures repository-side GitHub Pages readiness before the first `main` deployment. It is not a live deployment audit.

## Target

- hosting target: GitHub Pages project site;
- canonical public base URL: `https://fraware.github.io/ai-adoption-us/`;
- public data mode: `derived_only`;
- Next.js deployment profile: static export with `/ai-adoption-us` base path;
- analytics: disabled;
- client monitoring: disabled.

## Static-export evidence

Pull-request run `33761923181` executed the first complete GitHub Pages build/audit on source head `4b4ca24bdc0d5955810a43f5d49b8288766a29fd`.

The **Build and audit GitHub Pages artifact** job passed locked dependency installation, TypeScript validation, Next.js static export, required-output checks, private-path/private-identifier scans, release-manifest validation, GitHub Pages base-path checks, and Pages artifact upload. The deploy job was intentionally skipped because the workflow was running for a pull request.

Retained preflight artifact:

- artifact ID: `9895843684`;
- artifact name: `github-pages`;
- artifact SHA-256: `9983c47f94dc69196d3637f8b2df9e58732052e12a7926adfea5bd390c7a8513`;
- size: 326,212 bytes;
- source head: `4b4ca24bdc0d5955810a43f5d49b8288766a29fd`.

Later branch heads must pass the same workflow again before merge. This artifact proves only that the first complete Pages profile was technically viable; it is not the final Release 1 deployment artifact.

## Security boundary

GitHub Pages is static hosting. The Pages artifact cannot carry the Next.js `headers()` response-header policy used in the non-Pages server profile. Release 1 therefore does not claim application-controlled response headers on the GitHub Pages deployment.

The static export retains an HTML CSP meta policy, referrer metadata, no third-party analytics or monitoring SDK, and no private RPS source material. The live audit must record the headers actually served by GitHub Pages.

## External prerequisite

GitHub Pages must be enabled with **Source: GitHub Actions** in repository settings. The normal workflow token cannot self-enable a disabled Pages site. If the repository setting is already active, the push-to-`main` deployment can proceed automatically. If it is not active, the deployment is expected to fail closed until the owner enables that setting.

No alternate hosting provider is authorized or invoked by this Release 1 workflow.
