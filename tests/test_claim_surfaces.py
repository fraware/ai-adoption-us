from __future__ import annotations

from pathlib import Path

import pytest

from genai_at_work.claim_surfaces import (
    ClaimSurfaceBindingError,
    bind_claim_surfaces,
    claim_ids_from_inventory,
    validate_claim_surface_bindings,
)
from genai_at_work.release_engine import canonical_digest, sha256_file


def _candidate(surface: str = "public/page.txt") -> dict[str, object]:
    evidence_digest = canonical_digest({"artifact": "sha256:test-evidence"})
    return {
        "claims": [
            {
                "claim_id": "public-claim",
                "surfaces": [surface],
                "value_digest": evidence_digest,
            }
        ]
    }


def test_binding_hashes_exact_surface_bytes_and_changes_claim_identity(tmp_path: Path) -> None:
    surface = tmp_path / "public" / "page.txt"
    surface.parent.mkdir()
    surface.write_text("reviewed claim bytes\n")
    candidate = _candidate()
    original_digest = candidate["claims"][0]["value_digest"]  # type: ignore[index]

    bind_claim_surfaces(candidate, tmp_path, expected_claim_ids={"public-claim"})
    claim = candidate["claims"][0]  # type: ignore[index]

    assert claim["evidence_value_digest"] == original_digest
    assert claim["surface_sha256"] == {"public/page.txt": sha256_file(surface)}
    assert claim["value_digest"] != original_digest
    validate_claim_surface_bindings(
        candidate,
        tmp_path,
        expected_claim_ids={"public-claim"},
    )


def test_surface_mutation_after_binding_fails_closed(tmp_path: Path) -> None:
    surface = tmp_path / "public" / "page.txt"
    surface.parent.mkdir()
    surface.write_text("reviewed bytes\n")
    candidate = _candidate()
    bind_claim_surfaces(candidate, tmp_path, expected_claim_ids={"public-claim"})

    surface.write_text("changed after review binding\n")
    with pytest.raises(ClaimSurfaceBindingError, match="changed after claim binding"):
        validate_claim_surface_bindings(
            candidate,
            tmp_path,
            expected_claim_ids={"public-claim"},
        )


def test_binding_rejects_surface_path_escape(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("outside\n")
    candidate = _candidate("../outside.txt")

    with pytest.raises(ClaimSurfaceBindingError, match="Unsafe governed surface path"):
        bind_claim_surfaces(candidate, tmp_path, expected_claim_ids={"public-claim"})


def test_inventory_claim_ids_are_exact_and_unique() -> None:
    inventory = {
        "claims": [
            {"claim_id": "a", "surface": "a"},
            {"claim_id": "b", "surface": "b"},
        ]
    }
    assert claim_ids_from_inventory(inventory) == {"a", "b"}

    duplicate = {"claims": [{"claim_id": "a"}, {"claim_id": "a"}]}
    with pytest.raises(ClaimSurfaceBindingError, match="Duplicate claim inventory ID"):
        claim_ids_from_inventory(duplicate)
