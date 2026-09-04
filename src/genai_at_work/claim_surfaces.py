"""Cryptographically bind governed publication surfaces to release claims.

Scientific artifacts alone do not identify the public claim that readers see. A
release claim therefore carries both its evidence digest and SHA-256 identities
for every registered source file that presents that claim. This module is used
only on repository-controlled publication surfaces; route labels or external URLs
are not accepted as substitutes for file identities.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, MutableMapping, Set
from pathlib import Path, PurePosixPath
from typing import Any

from genai_at_work.release_engine import canonical_digest, sha256_file

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ClaimSurfaceBindingError(ValueError):
    """Raised when a governed release claim is not bound to exact surface bytes."""


def claim_ids_from_inventory(inventory: Mapping[str, Any]) -> set[str]:
    """Return the exact unique claim IDs declared by a longitudinal claim inventory."""

    raw = inventory.get("claims")
    if not isinstance(raw, list) or not raw:
        raise ClaimSurfaceBindingError("Claim inventory must contain a non-empty claims list")
    result: set[str] = set()
    for index, row in enumerate(raw):
        if not isinstance(row, Mapping):
            raise ClaimSurfaceBindingError(f"claim_inventory.claims[{index}] must be an object")
        claim_id = row.get("claim_id")
        if not isinstance(claim_id, str) or not claim_id:
            raise ClaimSurfaceBindingError(
                f"claim_inventory.claims[{index}].claim_id must be a non-empty string"
            )
        if claim_id in result:
            raise ClaimSurfaceBindingError(f"Duplicate claim inventory ID: {claim_id}")
        result.add(claim_id)
    return result


def _surface_path(repo_root: Path, surface: str) -> Path:
    if "\\" in surface:
        raise ClaimSurfaceBindingError(f"Governed surface must use POSIX separators: {surface!r}")
    relative = PurePosixPath(surface)
    if relative.is_absolute() or not relative.parts or any(part in {"", ".", ".."} for part in relative.parts):
        raise ClaimSurfaceBindingError(f"Unsafe governed surface path: {surface!r}")
    root = repo_root.resolve()
    path = (root / Path(*relative.parts)).resolve()
    if path == root or root not in path.parents:
        raise ClaimSurfaceBindingError(f"Governed surface escapes repository root: {surface!r}")
    if not path.is_file():
        raise ClaimSurfaceBindingError(f"Governed surface file does not exist: {surface}")
    return path


def _target_claims(
    candidate: Mapping[str, Any], expected_claim_ids: Set[str]
) -> dict[str, MutableMapping[str, Any]]:
    raw = candidate.get("claims")
    if not isinstance(raw, list):
        raise ClaimSurfaceBindingError("Candidate claims must be a list")
    indexed: dict[str, MutableMapping[str, Any]] = {}
    for row in raw:
        if not isinstance(row, MutableMapping):
            continue
        claim_id = row.get("claim_id")
        if isinstance(claim_id, str) and claim_id in expected_claim_ids:
            if claim_id in indexed:
                raise ClaimSurfaceBindingError(f"Duplicate candidate claim ID: {claim_id}")
            indexed[claim_id] = row
    missing = expected_claim_ids - set(indexed)
    if missing:
        raise ClaimSurfaceBindingError(
            f"Candidate is missing governed claim IDs: {sorted(missing)}"
        )
    return indexed


def _surface_hashes(claim: Mapping[str, Any], repo_root: Path, claim_id: str) -> dict[str, str]:
    raw = claim.get("surfaces")
    if (
        not isinstance(raw, list)
        or not raw
        or not all(isinstance(value, str) and value for value in raw)
    ):
        raise ClaimSurfaceBindingError(f"Governed claim {claim_id} must name file surfaces")
    surfaces = [str(value) for value in raw]
    if len(set(surfaces)) != len(surfaces):
        raise ClaimSurfaceBindingError(f"Governed claim {claim_id} contains duplicate surfaces")
    return {surface: sha256_file(_surface_path(repo_root, surface)) for surface in surfaces}


def bind_claim_surfaces(
    candidate: MutableMapping[str, Any],
    repo_root: Path,
    *,
    expected_claim_ids: Set[str],
) -> None:
    """Bind exact repository surface bytes into every governed claim digest.

    ``evidence_value_digest`` preserves the builder's evidence-only identity.
    ``value_digest`` becomes the identity of that evidence as presented through
    the exact registered source files. Rebinding an already-bound claim is
    rejected so the operation remains explicit and one-way.
    """

    for claim_id, claim in _target_claims(candidate, expected_claim_ids).items():
        if "evidence_value_digest" in claim or "surface_sha256" in claim:
            raise ClaimSurfaceBindingError(f"Governed claim is already surface-bound: {claim_id}")
        evidence_digest = claim.get("value_digest")
        if not isinstance(evidence_digest, str) or _SHA256_RE.fullmatch(evidence_digest) is None:
            raise ClaimSurfaceBindingError(f"Governed claim {claim_id} has an invalid evidence digest")
        hashes = _surface_hashes(claim, repo_root, claim_id)
        claim["evidence_value_digest"] = evidence_digest
        claim["surface_sha256"] = hashes
        claim["value_digest"] = canonical_digest(
            {
                "evidence_value_digest": evidence_digest,
                "surface_sha256": hashes,
            }
        )


def validate_claim_surface_bindings(
    candidate: Mapping[str, Any],
    repo_root: Path,
    *,
    expected_claim_ids: Set[str],
) -> None:
    """Prove governed claim digests still identify the current repository bytes."""

    for claim_id, claim in _target_claims(candidate, expected_claim_ids).items():
        evidence_digest = claim.get("evidence_value_digest")
        if not isinstance(evidence_digest, str) or _SHA256_RE.fullmatch(evidence_digest) is None:
            raise ClaimSurfaceBindingError(
                f"Governed claim {claim_id} lacks a valid evidence_value_digest"
            )
        expected_hashes = _surface_hashes(claim, repo_root, claim_id)
        if claim.get("surface_sha256") != expected_hashes:
            raise ClaimSurfaceBindingError(
                f"Governed publication surface changed after claim binding: {claim_id}"
            )
        expected_digest = canonical_digest(
            {
                "evidence_value_digest": evidence_digest,
                "surface_sha256": expected_hashes,
            }
        )
        if claim.get("value_digest") != expected_digest:
            raise ClaimSurfaceBindingError(
                f"Governed claim digest does not match its evidence and surface bytes: {claim_id}"
            )
