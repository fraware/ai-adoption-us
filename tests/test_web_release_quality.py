from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def normalized_lower(text: str) -> str:
    return " ".join(text.lower().split())


def test_layout_keeps_accessible_primary_navigation_and_source_link():
    layout = read("apps/web/app/layout.tsx")
    assert 'aria-label="Primary navigation"' in layout
    assert '<Link href="/explore">Explore</Link>' in layout
    assert '<Link href="/blog/after-adoption">Essay</Link>' in layout
    assert '<Link href="/methodology">Data &amp; methods</Link>' in layout
    assert '<Link href="/sources">Sources &amp; provenance</Link>' in layout
    assert 'className="skip-link"' in layout


def test_homepage_keeps_release_driven_hero_metrics_and_longitudinal_evidence():
    page = read("apps/web/app/page.tsx")
    normalized = normalized_lower(page)
    assert "loadPublicData" in page
    assert "loadLongitudinalDiagnostics" in page
    assert "latest.period" in page
    assert "work adoption" in normalized
    assert "assisted working time" in normalized
    assert "reported time savings" in normalized
    assert "crossLevelAlignedQuarters" in page
    assert "periods.length" in page


def test_explore_gateway_exists_and_links_to_both_analytical_views():
    page = read("apps/web/app/explore/page.tsx")
    assert '<Link href="/explore/occupations">' in page
    assert '<Link href="/explore/industries">' in page
    assert "loadLongitudinalDiagnostics" in page


def test_public_routes_exist():
    for relative in [
        "apps/web/app/page.tsx",
        "apps/web/app/explore/page.tsx",
        "apps/web/app/explore/industries/page.tsx",
        "apps/web/app/explore/occupations/page.tsx",
        "apps/web/app/methodology/page.tsx",
        "apps/web/app/sources/page.tsx",
        "apps/web/app/blog/after-adoption/page.tsx",
    ]:
        assert (ROOT / relative).is_file(), relative


def test_sources_page_keeps_rights_and_validation_boundaries():
    text = read("apps/web/app/sources/page.tsx")
    normalized = normalized_lower(text)
    assert "owner permission for published aggregate project use" in normalized
    assert "bounded attributed public views" in normalized
    assert "historical subgroup panels" in normalized
    assert "bulk download" in normalized
    assert "generic source-query access" in normalized
    assert "private source-input bytes" in normalized
    assert "outside current claims" in normalized
    assert "causal firm effects" in normalized
    assert "sources and release scope" in normalized
    assert "human screen-reader traversal" in normalized
    assert "outside current validation evidence" in normalized


def test_methodology_keeps_savings_distinct_from_productivity():
    page = read("apps/web/app/methodology/page.tsx")
    sources = read("apps/web/app/sources/page.tsx")
    normalized_page = normalized_lower(page)
    assert "reported time savings are survey-based counterfactual estimates" in normalized_page
    assert "labor productivity, output, gdp, and employer value added require direct outcome evidence" in normalized_page
    assert "occupation_" in page
    assert "adjusted_" in page
    assert "industry_" in page
    assert "context_" in page
    assert "residual" in page
    assert "the cps composition foundation uses official q2 2025 and q2 2026 inputs" in normalized_page
    assert "owner permission for published aggregate project use" in normalized_lower(sources)
    assert "DATA_MODE=derived_only" in page
    assert "private source-input bytes" in normalized_page


def test_explorers_use_registry_entity_names_instead_of_slug_labels():
    for rel in [
        "apps/web/app/explore/industries/page.tsx",
        "apps/web/app/explore/occupations/page.tsx",
    ]:
        text = read(rel)
        assert "loadEntityNames" in text
        assert 'replaceAll("-", " ")' not in text


def test_source_provenance_matches_rights_safe_architecture():
    text = read("docs/source-provenance.md")
    lower = text.lower()
    assert "complete historical subgroup source panel" in lower
    assert "unrestricted bulk mirror" in lower
    assert "generic source api" in lower
    assert "rps source files used during release preparation are acquired outside the public git history" in lower
    assert "project-owner attestation" in lower
    assert "not independently inspected" in lower
    assert "does not infer broader rights" in lower
    assert "release 1 includes validated composition analyses" in lower
