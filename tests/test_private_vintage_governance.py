from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_private_vintage_cli_cannot_write_to_public_repository_paths() -> None:
    script = (ROOT / "scripts" / "archive_rps_private_vintage.py").read_text()

    assert 'PRIVATE_ROOT = ROOT / "data" / "audit" / "private"' in script
    assert "Repository-local RPS private-vintage archives may only be written under" in script
    assert "external operator-controlled private mount" in script
    assert "Refusing to archive an RPS vintage from a dirty Git working tree" in script
    assert "store_rps_private_vintage" in script
    assert "apps/web/public" not in script
    assert "actions/upload-artifact" not in script
    assert "observatory_release.py" not in script


def test_private_vintage_manifest_is_explicitly_private_and_nonpublic() -> None:
    module = (ROOT / "src" / "genai_at_work" / "private_vintage.py").read_text()
    store = (ROOT / "src" / "genai_at_work" / "private_vintage_store.py").read_text()

    assert '"storage_scope": "private"' in module
    assert '"public_archive": False' in module
    assert '"public_bulk_redistribution_approved": False' in module
    assert "archive_event_id" in module
    assert "source_content_sha256" in module
    assert "O_EXCL" in store
    assert "immutable comparison provenance cannot be rewritten" in store
    assert "0o700" in store
    assert "0o600" in store
    assert "apps/web/public" not in module
    assert "apps/web/public" not in store
