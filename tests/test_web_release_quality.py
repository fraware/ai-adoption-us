import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
WEB = ROOT / "apps" / "web"


def read(rel: str) -> str:
    return (ROOT / rel).read_text()


def test_layout_has_accessible_navigation_and_source_surface():
    layout = read("apps/web/app/layout.tsx")
    assert 'className="skip-link"' in layout
    assert 'href="#main-content"' in layout
    assert 'id="main-content"' in layout
    assert 'aria-label="Primary navigation"' in layout
    assert 'href="/explore/industries"' in layout
    assert 'href="/explore/occupations"' in layout
    assert 'href="/blog/after-adoption"' in layout
    assert 'href="/methodology"' in layout
    assert 'href="/sources"' in layout


def test_global_styles_cover_keyboard_focus_motion_and_responsive_tables():
    css = read("apps/web/app/globals.css")
    assert ".skip-link" in css
    assert ":focus-visible" in css
    assert "prefers-reduced-motion" in css
    assert ".table-wrap" in css
    assert "overflow-x: auto" in css
    assert "min-width: 720px" in css


def test_all_primary_pages_export_metadata():
    for rel in [
        "apps/web/app/page.tsx",
        "apps/web/app/explore/industries/page.tsx",
        "apps/web/app/explore/occupations/page.tsx",
        "apps/web/app/methodology/page.tsx",
        "apps/web/app/sources/page.tsx",
        "apps/web/app/blog/after-adoption/page.tsx",
    ]:
        text = read(rel)
        assert "export const metadata" in text


def test_chart_components_expose_accessible_equivalents():
    scatter = read("apps/web/components/ScatterPlot.tsx")
    stability = read("apps/web/components/StabilityBars.tsx")
    timeseries = read("apps/web/components/TimeSeriesPlot.tsx")
    assert 'aria-label={ariaLabel}' in scatter
    assert "Show exact values" in scatter
    assert 'aria-label={title}' in stability
    assert "Show exact values" in stability
    assert 'aria-label="National longitudinal series"' in timeseries
    assert "Show exact values" in timeseries


def test_browser_version_report_uses_pinned_playwright_version():
    package = json.loads(read("apps/web/package.json"))
    reporter = read("apps/web/scripts/browser-version-report.mjs")
    assert package["devDependencies"]["@playwright/test"] == "1.62.1"
    assert 'packageJson.devDependencies?.["@playwright/test"]' in reporter
    assert "Unable to resolve pinned @playwright/test version" in reporter


def test_public_sources_page_states_current_composition_evidence_boundary():
    page = read("apps/web/app/sources/page.tsx")
    assert "Official Q2 2025 and Q2 2026 Basic Monthly" in page
    assert "composition inputs, not RPS residuals" in page
    assert "Robustness input validated" in page
    assert "Still outside Release 1 claims" in page
    assert "causal firm effects" in page
    assert "Sources, provenance" in page


def test_methodology_keeps_savings_distinct_from_productivity():
    page = read("apps/web/app/methodology/page.tsx")
    sources = read("apps/web/app/sources/page.tsx")
    assert "Reported time savings are not an observed measure of labor productivity" in page
    assert "occupation_" in page
    assert "adjusted_" in page
    assert "industry_" in page
    assert "context_" in page
    assert "residual" in page
    assert "CPS composition foundation has been executed and validated" in page
    assert "published-aggregate project use is recorded as permitted" in sources.lower()
    assert "live source-check schedule remains disabled" in sources


def test_explorers_use_registry_entity_names_instead_of_slug_labels():
    for rel in [
        "apps/web/app/explore/industries/page.tsx",
        "apps/web/app/explore/occupations/page.tsx",
    ]:
        text = read(rel)
        assert "loadEntityNames" in text
        assert 'replaceAll("-", " ")' not in text
