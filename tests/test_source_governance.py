from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_static_fred_builder_is_retired():
    text = (ROOT / "scripts" / "build_rps.py").read_text()
    assert "Static FRED export is retired" in text
    assert "OUTPUT_DIR" not in text
    assert "FredClient" not in text


def test_rps_refresh_candidate_stays_private_and_fail_closed():
    script = (ROOT / "scripts" / "prepare_rps_refresh_candidate.py").read_text()
    module = (ROOT / "src" / "genai_at_work" / "rps_refresh.py").read_text()

    assert 'PRIVATE_ROOT = ROOT / "data" / "audit" / "private"' in script
    assert "Repository-local RPS refresh outputs may only be written under" in script
    assert "apps/web/public" not in script
    assert '"promotion_state": "source-candidate-only"' in module
    assert '"public_raw_observations_included": False' in module
    assert "Provider release inventory drift" in module
    assert "observations_retrieved" in module


def test_rps_observatory_candidate_stays_private_and_cannot_promote():
    script = (ROOT / "scripts" / "prepare_rps_observatory_candidate.py").read_text()
    module = (ROOT / "src" / "genai_at_work" / "rps_release.py").read_text()

    assert 'PRIVATE_ROOT = ROOT / "data" / "audit" / "private"' in script
    assert "Repository-local RPS release candidates may only be written under" in script
    assert '"promotion_performed": False' in script
    assert "global_baseline_warning" in script
    assert '"source_input_bytes_publication": False' in module
    assert "RPS longitudinal component only" in module
    assert "artifacts/longitudinal/" in module
    assert "apps/web/public" not in script
    assert "apps/web/public" not in module
    assert "FredClient" not in script
    assert "FredClient" not in module
    assert "observatory_release.py" not in script


def test_no_public_observation_bundle():
    assert not (ROOT / "apps" / "web" / "public" / "data" / "observations.json").exists()


def test_web_loader_requires_explicit_mode():
    text = (ROOT / "apps" / "web" / "lib" / "data.ts").read_text()
    assert "DATA_MODE must be explicitly set" in text
    assert 'mode === "audit_snapshot"' in text
    assert 'mode === "fred_live_no_store"' in text
    assert 'mode === "derived_only"' in text
    assert '"public", "data", "observations.json"' not in text


def test_private_audit_not_under_public_web_tree():
    public = ROOT / "apps" / "web" / "public"
    assert not any("rps_subgroup_5q_audit" in p.name for p in public.rglob("*"))


def test_derived_only_mode_is_explicit_and_rights_safe():
    text = (ROOT / "apps" / "web" / "lib" / "data.ts").read_text()
    assert 'mode === "derived_only"' in text
    assert 'return []' in text
    derived = ROOT / "data" / "derived" / "longitudinal" / "longitudinal_diagnostics.json"
    assert derived.exists()


def test_public_pages_use_derived_longitudinal_loader():
    for rel in [
        "apps/web/app/page.tsx",
        "apps/web/app/explore/industries/page.tsx",
        "apps/web/app/explore/occupations/page.tsx",
        "apps/web/app/blog/after-adoption/page.tsx",
    ]:
        assert "loadLongitudinalDiagnostics" in (ROOT / rel).read_text()


def test_longitudinal_web_contract_matches_derived_artifact():
    import json

    derived = json.loads(
        (ROOT / "data" / "derived" / "longitudinal" / "longitudinal_diagnostics.json").read_text()
    )
    assert set(derived["quarter_diagnostics"]) == {"industry", "occupation"}
    assert set(derived["rank_stability"]) == {"industry", "occupation"}
    assert set(derived["rank_stability_dominance"]) == {"industry", "occupation"}
    assert len(derived["input_scope"]["periods"]) == 5
    for entity_type in ("industry", "occupation"):
        assert set(derived["rank_stability"][entity_type]) == {"A", "H", "S"}
        assert len(derived["quarter_diagnostics"][entity_type]) == 5


def test_no_python_runtime_cache_is_tracked_or_packaged():
    import subprocess

    if (ROOT / ".git").exists():
        paths = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
    else:
        paths = [str(path.relative_to(ROOT)) for path in ROOT.rglob("*") if path.is_file()]
    assert not [path for path in paths if "__pycache__/" in path or path.endswith(".pyc")]


def test_rights_safe_export_script_has_fail_closed_private_boundary():
    text = (ROOT / "scripts" / "export_rights_safe.py").read_text()
    gitignore = (ROOT / ".gitignore").read_text()
    assert 'PRIVATE_PREFIXES = ("data/audit/private/",)' in text
    assert 'GENERATED_PROVENANCE_NAME = "RELEASE_PROVENANCE.json"' in text
    assert "rel == GENERATED_PROVENANCE_NAME" in text
    assert "duplicate archive member names" in text
    assert "exactly one generated provenance record" in text
    assert "refusing to export from a dirty Git working tree" in text
    assert '"raw_rps_observations_included": False' in text
    assert '"build_verified_by_export_process": False' in text
    assert "validate_zip(out)" in text
    assert "st_mode & 0o111" in text
    assert "data/audit/private/" in gitignore
