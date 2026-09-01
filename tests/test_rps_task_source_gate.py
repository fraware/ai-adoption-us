from __future__ import annotations

from json import loads
from pathlib import Path


REGISTRY = Path(__file__).parents[1] / "data" / "registry" / "rps_task_adoption_source_scope_v1.json"


def _load_registry() -> dict[str, object]:
    return loads(REGISTRY.read_text())


def test_task_adoption_registry_is_fail_closed() -> None:
    registry = _load_registry()
    rights = registry["rights"]

    assert registry["observation_values_included"] is False
    assert registry["analysis_status"] == "source-gated"
    assert registry["public_product_status"] == "blocked"
    assert rights["source_owner_permission_status"] == "unresolved"
    assert rights["explicit_asset_license_found"] is False
    assert rights["explicit_redistribution_permission_found"] is False
    assert rights["explicit_persistent_storage_permission_found"] is False


def test_task_adoption_assets_require_immutable_byte_provenance() -> None:
    registry = _load_registry()
    assets = registry["assets"]

    assert len(assets) == 2
    assert {asset["asset_type"] for asset in assets} == {
        "occupation_adoption_indices",
        "task_adoption_indices",
    }
    for asset in assets:
        assert asset["byte_sha256"] is None
        assert asset["byte_hash_status"].startswith("unresolved:")

    reproducibility = registry["reproducibility"]
    assert reproducibility["mutable_delivery_surface"] is True
    required = " ".join(reproducibility["required_before_ingestion"])
    assert "SHA-256" in required
    assert "O*NET database release" in required
    assert "reuse/storage/redistribution" in required


def test_task_taxonomy_vintage_cannot_be_silently_inferred() -> None:
    registry = _load_registry()
    task_asset = next(
        asset for asset in registry["assets"] if asset["asset_type"] == "task_adoption_indices"
    )

    taxonomy = task_asset["taxonomy"]
    assert taxonomy["framework"] == "O*NET work activities"
    assert taxonomy["database_release"] is None
    assert "INSERT EXACT O*NET DATABASE RELEASE" in taxonomy["database_release_status"]


def test_occupation_taxonomy_is_explicitly_2018_soc() -> None:
    registry = _load_registry()
    occupation_asset = next(
        asset
        for asset in registry["assets"]
        if asset["asset_type"] == "occupation_adoption_indices"
    )

    taxonomy = occupation_asset["taxonomy"]
    assert taxonomy["detailed_occupation"] == "2018 Standard Occupational Classification"
    assert taxonomy["census_occupation"] == "2018 Census occupation codes"


def test_construct_contract_preserves_exposure_adoption_boundary() -> None:
    contract = _load_registry()["construct_contract"]

    assert contract["E_task"].startswith("theoretical or model-based")
    assert contract["A_task"].startswith("realized worker-reported")
    assert contract["E_occ"].startswith("theoretical or model-based")
    assert contract["A_occ"].startswith("realized occupation-level")
    prohibited = set(contract["prohibited_collapses"])
    assert "exposure is not adoption" in prohibited
    assert "adoption is not productivity" in prohibited
