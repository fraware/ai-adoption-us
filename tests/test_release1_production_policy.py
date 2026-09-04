from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_pages_static_export_and_non_pages_security_baseline_are_explicit():
    config = read("apps/web/next.config.mjs")
    layout = read("apps/web/app/layout.tsx")
    policy = read("docs/RELEASE1_PRODUCTION_POLICY.md")

    assert "GITHUB_PAGES === 'true'" in config
    assert "output: 'export'" in config
    assert "basePath: pagesBasePath" in config
    assert "assetPrefix: pagesBasePath" in config
    assert "trailingSlash: true" in config
    assert "poweredByHeader: false" in config

    for required in (
        "Content-Security-Policy",
        "Referrer-Policy",
        "X-Content-Type-Options",
        "X-Frame-Options",
        "Permissions-Policy",
        "Cross-Origin-Opener-Policy",
        "Strict-Transport-Security",
    ):
        assert required in config

    assert 'httpEquiv="Content-Security-Policy"' in layout
    assert 'referrer: "strict-origin-when-cross-origin"' in layout
    assert "does not support the framework `headers()` feature" in policy
    assert "must **not** claim application-controlled HTTP security headers" in policy


def test_public_indexing_surfaces_are_explicit_and_limited():
    robots = read("apps/web/app/robots.ts")
    sitemap = read("apps/web/app/sitemap.ts")
    assert 'allow: "/"' in robots
    assert "sitemap.xml" in robots
    assert 'dynamic = "force-static"' in robots
    assert 'dynamic = "force-static"' in sitemap
    for route in (
        '"/"',
        '"/explore/industries"',
        '"/explore/occupations"',
        '"/blog/after-adoption"',
        '"/methodology"',
        '"/sources"',
    ):
        assert route in sitemap
    assert "data/audit/private" not in sitemap
    assert "rps_subgroup" not in sitemap


def test_release_manifest_is_rights_safe_and_identity_bound():
    text = read("apps/web/app/release-manifest.json/route.ts")
    assert '"derived_only"' not in text
    assert "RELEASE_COMMIT_SHA" in text
    assert "GITHUB_PAGES" in text
    assert "VERCEL" not in text
    assert '"UNBOUND"' in text
    assert 'analytics: "disabled"' in text
    assert 'clientMonitoring: "disabled"' in text
    assert "sourceBytesPublished: false" in text
    for forbidden in ("FRED_API_KEY", "data/audit/private", "rps_subgroup_5q_audit"):
        assert forbidden not in text


def test_github_pages_workflow_builds_every_change_but_deploys_only_authorized_release():
    workflow = read(".github/workflows/pages.yml")
    assert "DATA_MODE: derived_only" in workflow
    assert "GITHUB_PAGES: 'true'" in workflow
    assert "NEXT_PUBLIC_SITE_URL: https://fraware.github.io/ai-adoption-us" in workflow
    assert "actions/upload-pages-artifact@7b1f4a764d45c48632c6b24a0339c27f5614fb0b" in workflow
    assert "actions/deploy-pages@d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e" in workflow
    assert "data/audit/private" in workflow
    assert "sourceBytesPublished" in workflow
    assert "startsWith(github.event.head_commit.message, 'Authorize Observatory release ')" in workflow
    assert "publication_sha:" in workflow
    assert "RELEASE_COMMIT_SHA: ${{ inputs.publication_sha || github.sha }}" in workflow
    assert 'scripts/validate_observatory_publication_commit.py --commit "$RELEASE_COMMIT_SHA"' in workflow
    assert "Dispatched publication SHA is not the current canonical main commit." in workflow
    assert "Manual Pages release dispatch requires publication_sha." in workflow
    assert "github.event_name != 'pull_request'" not in workflow
    assert "vercel" not in workflow.lower()


def test_github_pages_workflow_audits_the_live_deployment_after_deploy():
    workflow = read(".github/workflows/pages.yml")
    assert "live-audit:" in workflow
    assert "name: Audit deployed Release 1 origin" in workflow
    assert "needs: deploy" in workflow
    assert "DEPLOYED_PAGE_URL: ${{ needs.deploy.outputs.page_url }}" in workflow
    assert "EXPECTED_COMMIT_SHA: ${{ inputs.publication_sha || github.sha }}" in workflow
    assert "https://fraware.github.io/ai-adoption-us" in workflow
    assert "/release-manifest.json" in workflow
    assert "/data/audit/private/rps_subgroup_5q_audit.json" in workflow
    assert "/api/rps/raw" in workflow
    assert "application_controlled_http_security_headers=false" in workflow
    assert "r1-g3-live-pages-audit" in workflow
    assert "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02" in workflow


def test_production_environment_and_policy_are_explicit():
    env = read("apps/web/.env.example")
    policy = read("docs/RELEASE1_PRODUCTION_POLICY.md")
    lower_policy = policy.lower()
    assert "DATA_MODE=derived_only" in env
    assert "NEXT_PUBLIC_SITE_URL=https://fraware.github.io/ai-adoption-us" in env
    assert "RELEASE_COMMIT_SHA=" in env
    assert "GITHUB_PAGES=true" in env
    assert "no third-party analytics" in lower_policy
    assert "no client-side monitoring" in lower_policy
    assert "human/manual and physical-device spot checks remain outside release 1 scope" in lower_policy
    assert "Source: GitHub Actions" in policy
    assert "No alternate hosting service is selected or invoked" in policy
