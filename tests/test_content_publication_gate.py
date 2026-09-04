from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_content_publication_commit.py"
WORKFLOW = ROOT / ".github" / "workflows" / "content-pages.yml"
RELEASE_WORKFLOW = ROOT / ".github" / "workflows" / "pages.yml"


def load_validator():
    spec = importlib.util.spec_from_file_location("content_publication_validator", VALIDATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_content_publication_path_allowlist_is_presentation_only():
    validator = load_validator()

    allowed = (
        "apps/web/app/page.tsx",
        "apps/web/app/design.css",
        "apps/web/app/blog/after-adoption/page.tsx",
        "apps/web/app/explore/industries/page.tsx",
        "apps/web/app/methodology/page.tsx",
        "apps/web/app/sources/page.tsx",
        "apps/web/components/ReleaseNotice.tsx",
        "apps/web/tests/browser/release-routes.spec.ts",
        "apps/web/scripts/native-safari-qa.mjs",
        "tests/test_public_copy_editorial_contract.py",
        ".github/workflows/content-pages.yml",
        "scripts/validate_content_publication_commit.py",
    )
    blocked = (
        "data/registry/observatory_release_registry.json",
        "data/releases/observatory-v1-review-x/release_manifest.json",
        "data/derived/longitudinal/longitudinal_diagnostics.json",
        "apps/web/lib/data.ts",
        "apps/web/lib/release.ts",
        "apps/web/lib/longitudinal.ts",
        "apps/web/package.json",
        "apps/web/package-lock.json",
        "apps/web/next.config.mjs",
        "src/genai_at_work/release_engine.py",
        "scripts/validate_observatory_publication_commit.py",
        ".github/workflows/pages.yml",
        ".github/workflows/ci.yml",
    )

    for path in allowed:
        assert validator._path_allowed(path), path
    for path in blocked:
        assert not validator._path_allowed(path), path


def test_content_workflow_is_manual_for_deployment_and_keeps_release_gate_separate():
    content = WORKFLOW.read_text(encoding="utf-8")
    release = RELEASE_WORKFLOW.read_text(encoding="utf-8")

    assert "content_publication_sha" in content
    assert "validate_content_publication_commit.py" in content
    assert "current canonical main commit" in content
    assert "Release candidate CI" in content
    assert "Rendered browser and accessibility QA" in content
    assert "Native Safari desktop QA" in content
    assert "if: github.event_name == 'workflow_dispatch'" in content
    assert "publication_mode=content_only_over_unchanged_promoted_evidence" in content

    assert "validate_observatory_publication_commit.py" in release
    assert "Authorize Observatory release " in release
    assert "validate_content_publication_commit.py" not in release


def test_content_validator_binds_current_release_and_hashes_artifacts():
    text = VALIDATOR.read_text(encoding="utf-8")

    assert "CURRENT_RELEASE_PROMOTED" in text
    assert "Authorize Observatory release {release_id}" in text
    assert "authorization_registry != registry" in text
    assert "Current immutable release directory changed" in text
    assert "sha256_file(manifest_path)" in text
    assert "sha256_file(path)" in text
    assert "deploy-sensitive or non-presentation changes" in text
