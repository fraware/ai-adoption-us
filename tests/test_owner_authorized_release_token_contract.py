from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_owner_authorized_promotion_maps_actions_cli_token_to_ci_verifier_token() -> None:
    workflow = read(".github/workflows/observatory-owner-authorized-release.yml")
    wrapper = read("scripts/promote_rehydrated_observatory_v1.py")

    assert "GH_TOKEN: ${{ github.token }}" in workflow
    assert 'os.environ.get("GITHUB_TOKEN", "").strip()' in wrapper
    assert 'os.environ.get("GH_TOKEN", "").strip()' in wrapper
    assert 'os.environ["GITHUB_TOKEN"] = gh_token' in wrapper
    assert "_ensure_github_token_alias()" in wrapper
    assert "observatory_release.promote(delegated)" in wrapper
