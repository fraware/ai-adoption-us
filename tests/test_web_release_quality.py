import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
WEB = ROOT / "apps" / "web"


def read(rel: str) -> str:
    return (ROOT / rel).read_text()


def normalized_lower(text: str) -> str:
    return " ".join(text.lower().split())


def test_layout_has_accessible_navigation_and_source_surface():
    layout = read("apps/web/app/layout.tsx")
    assert 'className="skip-link"' in layout
    assert 'href="#main-content"' in layout
    assert 'href="/sources"' in layout
    assert 'aria-label="Primary navigation"' in layout
    assert 'className="site-footer"' in layout


def test_app_icon_and_cross_engine_wrap_contract_exist():
    methodology = read("apps/web/app/methodology/page.tsx")
    assert (WEB / "app" / "icon.svg").exists()
    assert "occupation_<wbr />adjusted_<wbr />industry_<wbr />context_<wbr />residual" in methodology


def test_home_keeps_headline_metrics_accessible_and_longitudinal_evidence_dynamic():
    home = read("apps/web/app/page.tsx")
    assert 'className="hero-metrics" role="group"' in home
    assert 'aria-label="Latest national headline measures"' in home
    assert "loadLongitudinalDiagnostics" in home
    assert "crossLevelAlignedQuarters" in home
    assert "periods.length" in home


def test_css_has_keyboard_reduced_motion_and_small_screen_rules():
    css = read("apps/web/app/globals.css")
    assert ":focus-visible" in css
    assert "prefers-reduced-motion" in css
    assert "@media (max-width: 680px)" in css
    assert ".table-wrap:focus-visible" in css
    assert "overflow-wrap: anywhere" in css


def test_plots_expose_nonvisual_data_tables():
    scatter = read("apps/web/components/ScatterPlot.tsx")
    timeseries = read("apps/web/components/TimeSeriesPlot.tsx")
    for text in (scatter, timeseries):
        assert "<figure" in text
        assert "<figcaption>" in text
        assert "<details" in text
        assert "<caption>" in text
        assert 'scope="col"' in text


def test_plots_reflow_with_resize_observer():
    for rel in [
        "apps/web/components/ScatterPlot.tsx",
        "apps/web/components/TimeSeriesPlot.tsx",
    ]:
        text = read(rel)
        assert "ResizeObserver" in text
        assert ".observe(host)" in text
        assert "observer.disconnect()" in text


def test_browser_version_report_uses_pinned_playwright_version():
    package = json.loads(read("apps/web/package.json"))
    reporter = read("apps/web/scripts/browser-version-report.mjs")
    assert package["devDependencies"]["@playwright/test"] == "1.62.1"
    assert 'packageJson.devDependencies?.["@playwright/test"]' in reporter
    assert "Unable to resolve pinned @playwright/test version" in reporter


def test_public_sources_page_states_current_composition_rps_and_qa_boundaries():
    page = read("apps/web/app/sources/page.tsx")
    normalized = normalized_lower(page)
    assert "official q2 2025 and q2 2026 basic monthly public-use files" in normalized
    assert "actual-main-job-hour occupation weights" in normalized
    assert "establishment robustness" in normalized
    assert "oews · 2025-05" in normalized
    assert "authorized aggregate release path" in normalized
    assert "bounded attributed public views" in normalized
    assert "owner permission for published aggregate project use" in normalized
    assert "derived aggregate analysis" in normalized
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
    release_notice = read("apps/web/components/ReleaseNotice.tsx")
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
    assert "private source-input bytes" in normalized_lower(release_notice)


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
    assert "authorized release pipeline" in lower
    assert "private candidate workspace" in lower
    assert "contracted attributed aggregate presentation view" in lower
    assert "complete historical subgroup source panel" in lower
    assert "bulk download" in lower
    assert "generic query api" in lower
    assert "private source-input" in lower
    assert "project-owner attestation" in lower
    assert "not independently inspected" in lower
    assert "does not infer unrecorded contractual terms" in lower
    assert "Official Q2 2025 and Q2 2026 Basic Monthly CPS inputs have been executed" in text
    assert "Official May 2025 staffing data have been executed" in text
    assert "occupation-adjusted RPS industry-context residual artifacts" in text
    assert "derived descriptive diagnostics" in text
    assert "no class-4 causal claim" in lower


def test_navigation_routes_exist():
    expected = [
        "apps/web/app/explore/page.tsx",
        "apps/web/app/explore/industries/page.tsx",
        "apps/web/app/explore/occupations/page.tsx",
        "apps/web/app/blog/after-adoption/page.tsx",
        "apps/web/app/methodology/page.tsx",
        "apps/web/app/sources/page.tsx",
    ]
    assert all((ROOT / rel).exists() for rel in expected)


def test_release_qa_does_not_overclaim_browser_validation():
    text = read("docs/RELEASE1_PRODUCT_QA.md")
    assert "does not substitute for a real browser" in text
    assert "Genuine `npm install` and `next build`" in text
    assert "Screen-reader traversal" in text
    assert "No public-launch claim" in text
