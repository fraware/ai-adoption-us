from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_security_header_baseline_is_repository_defined():
    text = read("apps/web/next.config.mjs")
    for required in (
        "Content-Security-Policy",
        "Referrer-Policy",
        "X-Content-Type-Options",
        "X-Frame-Options",
        "Permissions-Policy",
        "Cross-Origin-Opener-Policy",
        "Strict-Transport-Security",
        "poweredByHeader: false",
    ):
        assert required in text
    assert "connect-src 'self'" in text
    assert "frame-ancestors 'none'" in text
    assert "object-src 'none'" in text


def test_public_indexing_surfaces_are_explicit_and_limited():
    robots = read("apps/web/app/robots.ts")
    sitemap = read("apps/web/app/sitemap.ts")
    assert 'allow: "/"' in robots
    assert "sitemap.xml" in robots
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
    assert '"derived_only"' not in text  # must report the actual deployment env, not hard-code success
    assert "RELEASE_COMMIT_SHA" in text
    assert "VERCEL_GIT_COMMIT_SHA" in text
    assert '"UNBOUND"' in text
    assert 'analytics: "disabled"' in text
    assert 'clientMonitoring: "disabled"' in text
    assert "Cache-Control" in text
    for forbidden in ("FRED_API_KEY", "data/audit/private", "rps_subgroup_5q_audit"):
        assert forbidden not in text


def test_production_environment_and_policy_are_explicit():
    env = read("apps/web/.env.example")
    policy = read("docs/RELEASE1_PRODUCTION_POLICY.md")
    assert "DATA_MODE=derived_only" in env
    assert "NEXT_PUBLIC_SITE_URL=" in env
    assert "RELEASE_COMMIT_SHA=" in env
    assert "no third-party analytics" in policy.lower()
    assert "no client-side monitoring" in policy.lower()
    assert "human/manual and physical-device spot checks remain outside Release 1 scope" in policy
