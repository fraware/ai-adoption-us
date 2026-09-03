from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "pages.yml"


def test_live_pages_audit_uses_route_filename_mapping_consistently():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "tr '/.' '__'" in text
    assert "cp live-audit/_release-manifest_json.body.txt live-audit/release-manifest.json" in text
    assert "cp live-audit/_robots_txt.body.txt live-audit/robots.txt" in text
    assert "cp live-audit/_sitemap_xml.body.txt live-audit/sitemap.xml" in text
    assert "cat live-audit/_release-manifest_json.headers.txt >> live-audit/summary.txt" in text

    assert "live-audit/__release-manifest_json" not in text
    assert "live-audit/__robots_txt" not in text
    assert "live-audit/__sitemap_xml" not in text
