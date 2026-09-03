from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_public_release_surfaces_do_not_revert_to_candidate_language():
    release_notice = read("apps/web/components/ReleaseNotice.tsx")
    home = read("apps/web/app/page.tsx")
    sources = read("apps/web/app/sources/page.tsx")
    methodology = read("apps/web/app/methodology/page.tsx")

    assert "Release 1 · rights-safe derived evidence" in release_notice
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


def test_essay_no_longer_claims_cps_composition_is_unexecuted():
    essay = read("apps/web/app/blog/after-adoption/page.tsx")
    lower = essay.lower()

    assert "official cps q2 2025 and q2 2026 inputs now provide" in lower
    assert "occupation-adjusted industry-context residual diagnostics" in lower
    assert "full design-based uncertainty" in lower
    assert "until the required cps microdata are executed" not in lower
    assert '<Link href="/methodology">' in essay
    assert '<Link href="/sources">' in essay


def test_release1_direct_feed_language_matches_activation_state():
    release_notice = read("apps/web/components/ReleaseNotice.tsx")
    home = read("apps/web/app/page.tsx")
    sources = read("apps/web/app/sources/page.tsx")

    assert "live adapter remains fail-closed until its operational activation gates pass" in release_notice
    assert "direct national observation feed is not activated in Release 1" in home
    assert "live source-check schedule remains disabled" in sources
