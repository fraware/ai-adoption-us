from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def load_script(relative: str, module_name: str) -> ModuleType:
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def test_canonical_low_level_promotion_requires_rehydration_capability(tmp_path: Path):
    release = load_script("scripts/observatory_release.py", "observatory_release_policy_test")

    canonical = argparse.Namespace(
        registry=ROOT / "data/registry/observatory_release_registry.json",
        releases_root=ROOT / "data/releases",
    )
    with pytest.raises(SystemExit, match="Direct canonical Observatory promotion is disabled"):
        release._require_rehydrated_canonical_promotion(canonical)

    verified = argparse.Namespace(
        registry=canonical.registry,
        releases_root=canonical.releases_root,
        _rehydration_verified=True,
    )
    release._require_rehydrated_canonical_promotion(verified)

    isolated = argparse.Namespace(
        registry=tmp_path / "registry.json",
        releases_root=tmp_path / "releases",
    )
    release._require_rehydrated_canonical_promotion(isolated)


def test_rehydration_operator_rebuilds_exact_reviewed_identity_and_fails_on_source_drift():
    script = read("scripts/rehydrate_observatory_v1_candidate.py")

    assert "Trusted rehydration must run on the exact reviewed candidate commit" in script
    assert "Release registry advanced after review" in script
    assert "FRED_API_KEY is required for trusted source rehydration" in script
    assert "build_refresh_snapshot(" in script
    assert "Live RPS scientific source identity changed after review" in script
    assert "build_rps_observatory_release_candidate(" in script
    assert "bind_claim_surfaces(" in script
    assert "compose_v1_global_baseline_bound(" in script
    assert "Rehydrated private candidate manifest bytes differ from review" in script
    assert "Rehydrated sanitized candidate manifest differs from review" in script
    assert "Rehydrated stage manifest differs from the reviewed stage manifest" not in script
    assert '_assert_exact_json(stage_root / "stage_manifest.json"' in script
    assert '"status": "REHYDRATED_EXACT_CANDIDATE"' in script
    assert '"source_input_bytes_included": False' in script


def test_rehydrated_wrapper_binds_identity_before_opening_internal_promotion_kernel():
    wrapper = read("scripts/promote_rehydrated_observatory_v1.py")

    assert "validate_rehydration_identity(" in wrapper
    assert 'attestation.get("rehydration_identity_sha256") != identity_sha' in wrapper
    assert "_rehydration_verified=True" in wrapper
    assert "observatory_release.promote(delegated)" in wrapper
    assert 'review_record["rehydration_status"] = "REHYDRATED_EXACT_CANDIDATE"' in wrapper
    assert 'review_record["source_rehydrated_before_promotion"] = True' in wrapper
    assert 'matches[0]["rehydration_identity_sha256"] = identity_sha' in wrapper
    assert "registry_before = args.registry.read_bytes()" in wrapper
    assert "_rollback(" in wrapper


def test_candidate_review_cannot_self_attest_future_rehydration():
    workflow = read(".github/workflows/observatory-candidate-review.yml")

    assert "'exact_rehydration_required': True" in workflow
    assert "'rehydration_identity_sha256': ''" in workflow
    assert "Workflow may not pre-attest a future rehydration identity" in workflow
    assert "data/registry/observatory_release_registry.json" not in workflow.split("paths:", 1)[1].split("workflow_dispatch:", 1)[0]


def test_promotion_workflow_is_two_phase_and_commits_only_release_state():
    workflow = read(".github/workflows/observatory-promotion.yml")

    assert "- rehydrate" in workflow
    assert "- promote" in workflow
    assert "Observatory rehydration/promotion must be dispatched on main" in workflow
    assert "review_run_id must be a positive integer" in workflow
    assert "Review package commit" in workflow
    assert "scripts/rehydrate_observatory_v1_candidate.py" in workflow
    assert "observatory-rehydration-identity-${{ github.run_id }}-${{ github.sha }}" in workflow
    assert "attestation_json is required for operation=promote" in workflow
    assert "Attestation must bind the SHA-256 of the exact rehydration identity" in workflow
    assert "scripts/promote_rehydrated_observatory_v1.py" in workflow
    assert 'git add data/registry/observatory_release_registry.json "data/releases/$release_id"' in workflow
    assert 'git commit -m "Authorize Observatory release $release_id"' in workflow
    assert "scripts/validate_observatory_publication_commit.py --commit HEAD" in workflow
    assert "git push origin HEAD:main" in workflow
    assert "data/audit/private" not in workflow


def test_publication_commit_validator_requires_append_only_new_release_transition():
    validator = read("scripts/validate_observatory_publication_commit.py")

    assert 'expected_subject = f"Authorize Observatory release {release_id}"' in validator
    assert "Publication commit parent is not the exact human-reviewed candidate commit" in validator
    assert 'review.get("rehydration_status") != "REHYDRATED_EXACT_CANDIDATE"' in validator
    assert "Review record does not bind the rehydration identity" in validator
    assert "Publication commit must advance to a new immutable release ID" in validator
    assert "attempts to rewrite a release directory that already existed in its parent" in validator
    assert "exactly one append-only release row" in validator
    assert "changed release-registry fields outside the governed release transition" in validator
    assert 'release_prefix = f"data/releases/{release_id}/"' in validator
    assert "Publication commit contains unrelated changed paths" in validator
    assert "Publication commit did not advance the release registry" in validator
    assert "Publication commit did not add the immutable release directory" in validator


def test_publication_commit_validator_accepts_new_release_and_rejects_rewrite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    validator = load_script(
        "scripts/validate_observatory_publication_commit.py",
        "observatory_publication_validator_dynamic_test",
    )
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.name", "test")
    _git(repo, "config", "user.email", "test@example.test")

    registry_path = repo / "data/registry/observatory_release_registry.json"
    releases_root = repo / "data/releases"
    parent_registry = {
        "schema_version": 1,
        "current_release_id": None,
        "current_release_manifest_sha256": None,
        "releases": [],
        "status": "NO_OBSERVATORY_RELEASE_PROMOTED_YET",
    }
    _write_json(registry_path, parent_registry)
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "Candidate commit")
    candidate_commit = _git(repo, "rev-parse", "HEAD").lower()

    release_id = "release-1"
    release_root = releases_root / release_id
    artifact_path = release_root / "artifacts/result.json"
    artifact_path.parent.mkdir(parents=True)
    artifact_path.write_text('{"value": 1}\n')
    identity_path = release_root / "rehydration_identity.json"
    identity = {
        "candidate_commit": candidate_commit,
        "release_id": release_id,
        "source_input_bytes_included": False,
        "status": "REHYDRATED_EXACT_CANDIDATE",
    }
    _write_json(identity_path, identity)
    identity_sha = _sha256(identity_path)
    review = {
        "candidate_commit": candidate_commit,
        "rehydration_identity_sha256": identity_sha,
        "rehydration_status": "REHYDRATED_EXACT_CANDIDATE",
    }
    _write_json(release_root / "review_record.json", review)
    manifest = {
        "release_id": release_id,
        "release_status": "PROMOTED_AFTER_EXPLICIT_REVIEW",
        "supersedes_release_id": None,
        "promoted_at": "2026-09-04T09:00:00Z",
        "data_mode": "derived_only",
        "artifacts": [
            {
                "path": "artifacts/result.json",
                "sha256": _sha256(artifact_path),
            }
        ],
    }
    manifest_path = release_root / "release_manifest.json"
    _write_json(manifest_path, manifest)
    manifest_sha = _sha256(manifest_path)
    promoted_registry = {
        "schema_version": 1,
        "current_release_id": release_id,
        "current_release_manifest_sha256": manifest_sha,
        "status": "CURRENT_RELEASE_PROMOTED",
        "releases": [
            {
                "release_id": release_id,
                "manifest_sha256": manifest_sha,
                "promoted_at": manifest["promoted_at"],
                "supersedes_release_id": None,
                "data_mode": "derived_only",
                "candidate_commit": candidate_commit,
                "rehydration_status": "REHYDRATED_EXACT_CANDIDATE",
                "rehydration_identity_sha256": identity_sha,
            }
        ],
    }
    _write_json(registry_path, promoted_registry)
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", f"Authorize Observatory release {release_id}")

    monkeypatch.setattr(validator, "ROOT", repo)
    monkeypatch.setattr(validator, "REGISTRY", registry_path)
    monkeypatch.setattr(validator, "RELEASES_ROOT", releases_root)
    result = validator.validate("HEAD")
    assert result["status"] == "PUBLICATION_COMMIT_VALID"
    assert result["candidate_commit"] == candidate_commit

    previous_publication_commit = _git(repo, "rev-parse", "HEAD").lower()
    artifact_path.write_text('{"value": 2}\n')
    manifest["artifacts"][0]["sha256"] = _sha256(artifact_path)
    _write_json(manifest_path, manifest)
    manifest_sha = _sha256(manifest_path)
    identity["candidate_commit"] = previous_publication_commit
    _write_json(identity_path, identity)
    identity_sha = _sha256(identity_path)
    review["candidate_commit"] = previous_publication_commit
    review["rehydration_identity_sha256"] = identity_sha
    _write_json(release_root / "review_record.json", review)
    promoted_registry["current_release_manifest_sha256"] = manifest_sha
    promoted_registry["releases"][0].update(
        {
            "manifest_sha256": manifest_sha,
            "candidate_commit": previous_publication_commit,
            "rehydration_identity_sha256": identity_sha,
        }
    )
    _write_json(registry_path, promoted_registry)
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", f"Authorize Observatory release {release_id}")

    with pytest.raises(
        validator.PublicationCommitError,
        match="must advance to a new immutable release ID",
    ):
        validator.validate("HEAD")


def test_pages_deploys_only_after_validated_release_authorization_commit():
    workflow = read(".github/workflows/pages.yml")
    condition = (
        "github.event_name == 'push' && github.ref == 'refs/heads/main' && "
        "startsWith(github.event.head_commit.message, 'Authorize Observatory release ')"
    )

    assert workflow.count(condition) >= 2
    assert "scripts/validate_observatory_publication_commit.py --commit \"$GITHUB_SHA\"" in workflow
    assert "github.event_name != 'pull_request'" not in workflow
