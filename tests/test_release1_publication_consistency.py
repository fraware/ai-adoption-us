from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_public_release_surfaces_do_not_revert_to_candidate_language():
    release_notice = read("apps/web/components/ReleaseNotice.tsx")
    home = read("apps/web/app/page.tsx")
    sources = read("apps/web/app/sources/page.tsx")
    methodology = read("apps/web/app/methodology/page.tsx")

    assert "Release 1 · rights-bounded public evidence" in release_notice
    assert "private source-input bytes" in release_notice
    assert "unrestricted historical subgroup data" in release_notice
    assert "Public candidate · derived diagnostics only" not in release_notice
    assert "public candidate" not in home.lower()
    assert "public candidate" not in sources.lower()
    assert "public candidate" not in methodology.lower()


def test_sources_page_matches_current_r1_source_and_qa_state():
    sources = read("apps/web/app/sources/page.tsx")
    lower = sources.lower()

    assert "published triangulation" in lower
    assert "future triangulation" not in lower
    assert "published-aggregate project use is recorded as permitted" in lower
    assert "authorized aggregate release path" in lower
    assert "bounded presentation view" in lower
    assert "historical" in lower and "subgroup panel" in lower
    assert "generic source query api" in lower
    assert "native\n          macos safari" in lower
    assert "human screen-reader traversal" in lower
    assert "not release 1 evidence" in lower
    assert "github pages is the release 1 hosting target" in lower


def test_methodology_matches_executed_composition_boundary():
    methodology = read("apps/web/app/methodology/page.tsx")
    lower = methodology.lower()

    assert "cps composition foundation has been executed and validated" in lower
    assert "official q2 2025 and q2 2026" in lower
    assert "occupation-adjusted industry-context residual evidence" in lower
    assert "derived descriptive" in lower
    assert "design-based" in lower
    assert "rps join gated" not in lower
    assert "until source permissions are resolved" not in lower


def test_essay_matches_executed_composition_and_dynamic_longitudinal_evidence():
    essay = read("apps/web/app/blog/after-adoption/page.tsx")
    lower = essay.lower()

    assert "official cps q2 2025 and q2 2026 inputs provide" in lower
    assert "occupation-adjusted industry-context residual diagnostics" in lower
    assert "full design-based uncertainty" in lower
    assert "periods.length" in essay
    assert "adoption_rank_corr_gt_assisted_hours_rank_corr" in essay
    assert "five audited waves" not in lower
    assert "full five-wave window" not in lower
    assert "until the required cps microdata are executed" not in lower
    assert '<Link href="/methodology">' in essay
    assert '<Link href="/sources">' in essay


def test_release1_bounded_view_and_live_adapter_boundaries_are_distinct():
    release_notice = read("apps/web/components/ReleaseNotice.tsx")
    home = read("apps/web/app/page.tsx")
    sources = read("apps/web/app/sources/page.tsx")

    # The application-controlled live adapter remains separately gated.
    assert "live adapter remains fail-closed until its operational activation gates pass" in release_notice

    # Release 1 may carry only the contracted rights-bounded observation artifact.
    assert "bounded public observation view is unavailable in this build" in home.lower()
    assert "bounded presentation view" in sources.lower()
    assert "seven complete national-history quarters through q2 2026" in sources.lower()
    assert "latest complete industry and" in sources.lower()
    assert "occupation a/h/s cross-sections" in sources.lower()
    assert "unrestricted static database" in sources.lower()
    assert "bulk download product" in sources.lower()
    assert "generic source query api" in sources.lower()


def test_derived_only_resolves_observations_and_diagnostics_from_one_promoted_release():
    release = read("apps/web/lib/release.ts")
    data = read("apps/web/lib/data.ts")
    longitudinal = read("apps/web/lib/longitudinal.ts")

    assert "observatory_release_registry.json" in release
    assert "current_release_manifest_sha256" in release
    assert "PROMOTED_AFTER_EXPLICIT_REVIEW" in release
    assert "Promoted release artifact checksum mismatch" in release

    assert 'PUBLIC_VIEW_ARTIFACT_ID = "rps-public-observation-view"' in data
    assert 'if (mode === "derived_only") return loadPromotedPublicView();' in data
    assert "historical_subgroup_panel_included !== false" in data
    assert "generic_query_api_included !== false" in data
    assert "source_vintage_id !== result.value.source_vintage_id" in data

    assert 'LONGITUDINAL_ARTIFACT_ID = "rps-longitudinal-diagnostics"' in longitudinal
    assert "readCurrentReleaseJsonArtifact<LongitudinalDiagnostics>" in longitudinal
    assert "Longitudinal diagnostics are not bound to the promoted RPS source vintage" in longitudinal


def test_repository_longitudinal_fallback_matches_current_live_source_identity():
    diagnostics = read("data/derived/longitudinal/longitudinal_diagnostics.json")
    assert '"2024-Q4"' in diagnostics
    assert '"2025-Q1"' in diagnostics
    assert '"quarter_pairs": 21' in diagnostics
    assert '"source_content_sha256": "fe8bffa7cacd029cc23e2ba7e310d925e8c05322f6d53bd89e8234f02e825b73"' in diagnostics
    assert '"input_private_fixture_rows"' not in diagnostics
    assert '"checkpoint_date"' not in diagnostics


def test_governed_longitudinal_surfaces_do_not_reintroduce_five_wave_state():
    surfaces = [
        "apps/web/app/page.tsx",
        "apps/web/app/explore/industries/page.tsx",
        "apps/web/app/explore/occupations/page.tsx",
        "apps/web/app/blog/after-adoption/page.tsx",
        "README.md",
        "docs/RESULTS.md",
        "docs/source-provenance.md",
    ]
    stale_phrases = (
        "five-wave",
        "five wave",
        "five audited waves",
        "all five",
        "10/10 quarter-pair",
        "110/110",
        "630 cells",
    )
    for relative in surfaces:
        lower = read(relative).lower()
        for phrase in stale_phrases:
            assert phrase not in lower, f"{relative} reintroduced stale longitudinal state: {phrase}"
