from pathlib import Path

ROOT = Path(__file__).parents[1]
WEB = ROOT / "apps" / "web"


def read(rel: str) -> str:
    return (ROOT / rel).read_text()


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


def test_labelled_generic_home_groups_have_explicit_roles():
    home = read("apps/web/app/page.tsx")
    assert 'className="metric-row" role="group" aria-label="Five-wave evidence summary"' in home
    assert (
        'className="measurement-ladder" role="group" '
        'aria-label="Measurement ladder from adoption to realization"'
    ) in home


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


def test_public_sources_page_states_current_composition_evidence_boundary():
    page = read("apps/web/app/sources/page.tsx")
    assert "Official Q2 2025 and Q2 2026 Basic Monthly" in page
    assert "composition inputs, not RPS residuals" in page
    assert "Robustness input validated" in page
    assert "Still gated" in page
    assert "organizational effects" in page
    assert "Sources, provenance" in page


def test_methodology_keeps_savings_distinct_from_productivity():
    page = read("apps/web/app/methodology/page.tsx")
    assert "Reported time savings are not an observed measure of labor productivity" in page
    assert "occupation_" in page
    assert "adjusted_" in page
    assert "industry_" in page
    assert "context_" in page
    assert "residual" in page
    assert "CPS composition foundation has been executed and validated" in page
    assert "RPS observation path remains rights-gated" in page


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
    assert "rights-safe release" in text
    assert "does not redistribute that raw audit fixture" in text
    assert "fred_live_no_store" in text
    assert "Official Q2 2025 and Q2 2026 Basic Monthly CPS inputs have been executed" in text
    assert "Official May 2025 staffing data have been executed" in text
    assert "does **not** yet publish the RPS-dependent occupation-adjusted industry residual" in text


def test_navigation_routes_exist():
    expected = [
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
