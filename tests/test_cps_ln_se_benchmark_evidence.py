from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "data" / "derived" / "composition" / "cps-ln-se-benchmark-2026-07"


def _json(name: str) -> object:
    return json.loads((EVIDENCE / name).read_text())


def _sha256(name: str) -> str:
    return hashlib.sha256((EVIDENCE / name).read_bytes()).hexdigest()


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def test_canonical_benchmark_pins_official_estimate_se_and_public_use_gap() -> None:
    benchmark = _json("benchmark.json")
    assert isinstance(benchmark, dict)
    assert benchmark["series_id"] == "LNU02032201"
    assert benchmark["year"] == 2026
    assert benchmark["period"] == "M07"
    assert benchmark["published_estimate_thousands"] == 69913.0
    assert benchmark["published_standard_error_thousands"] == 560.0
    assert benchmark["reconstructed_estimate_thousands"] == 69877.39283459983
    assert benchmark["reconstruction_difference_thousands"] == -35.60716540017165
    assert benchmark["absolute_reconstruction_difference_standard_errors"] == (
        0.06358422392887796
    )
    assert benchmark["published_rounding_matches"] is False
    assert benchmark["project_validation_threshold_standard_errors"] == 1.0
    assert benchmark["public_use_discrepancy_within_project_threshold"] is True
    assert benchmark["project_threshold_is_bls_or_census_rule"] is False
    assert benchmark["weight_variable"] == (
        "PWCMPWGT composited final weight with four implied decimals"
    )


def test_standard_error_observation_is_exact_bls_api_aspect() -> None:
    observation = _json("standard_error_observation.json")
    assert observation == {
        "aspect_type": "Standard Error",
        "footnote_code": "",
        "period": "M07",
        "series_id": "LNU02032201",
        "value": 560.0,
        "year": 2026,
    }


def test_validation_keeps_same_period_and_no_pooled_quarter_boundary() -> None:
    validation = _json("validation_checks.json")
    assert isinstance(validation, dict)
    assert validation["status"] == "pass"
    assert validation["official_standard_error_present"] is True
    assert validation["public_use_discrepancy_within_project_threshold"] is True
    assert validation["published_rounding_reproduced"] is False
    assert validation["cross_month_covariance_available"] is False
    assert validation["pooled_quarter_design_based_interval_supported"] is False
    assert validation["raw_cps_file_published"] is False
    assert validation["raw_bls_api_response_published"] is False


def test_input_manifest_preserves_exact_canonical_run_transport_snapshot() -> None:
    manifest = _json("input_manifest.json")
    assert isinstance(manifest, dict)
    assert manifest["source_build_commit"] == "f9bcc48350a5acf923b8de1982092caf34542172"
    api = manifest["bls_public_api"]
    cps = manifest["cps_public_use"]
    assert isinstance(api, dict)
    assert isinstance(cps, dict)
    assert api["response_sha256"] == (
        "64a597f049d1793f788d0deaea1e089bfce9cd92de116ffd4634d186a231756a"
    )
    assert api["response_size_bytes"] == 3837
    assert api["raw_response_published"] is False
    assert cps["sha256"] == (
        "a97d4908014689f29c2f833c01289c6564c8a27c0b5358562dd111eb33e05247"
    )
    assert cps["file_size_bytes"] == 9502622
    assert cps["raw_file_published"] is False


def test_source_identity_separates_transport_bytes_from_scientific_content() -> None:
    identity = _json("source_identity.json")
    assert isinstance(identity, dict)
    scientific = identity["bls_scientific_content"]
    assert isinstance(scientific, dict)
    assert _canonical_sha256(scientific) == (
        "8f1e05bf9a3dd4692fc2c91fcaf386e85f83f219cca4b0641f3c9b6699949ab5"
    )
    assert identity["bls_scientific_content_sha256"] == _canonical_sha256(scientific)
    assert identity["scientific_content_equal"] is True
    assert identity["transport_response_bytes_equal"] is False
    review = identity["canonical_review_transport"]
    repeat = identity["canonical_main_repeat_transport"]
    assert isinstance(review, dict)
    assert isinstance(repeat, dict)
    assert review["bls_api_transport_response_sha256"] == (
        "64a597f049d1793f788d0deaea1e089bfce9cd92de116ffd4634d186a231756a"
    )
    assert repeat["bls_api_transport_response_sha256"] == (
        "c4f2fa5e6322f3ef6d3f6fe8a246d0997aa72738fae2690b44b74c1309094f6b"
    )
    assert review["bls_api_transport_response_sha256"] != repeat[
        "bls_api_transport_response_sha256"
    ]


def test_provenance_binds_live_run_artifact_and_canonical_file_hashes() -> None:
    provenance = _json("provenance.json")
    assert isinstance(provenance, dict)
    execution = provenance["live_execution"]
    assert isinstance(execution, dict)
    assert execution["github_run_id"] == "33691440205"
    assert execution["github_head_sha"] == "f9bcc48350a5acf923b8de1982092caf34542172"
    assert execution["artifact_id"] == "9870172427"
    assert execution["artifact_digest"] == (
        "sha256:6d299bc5d7a403bbf4503728705051c3cbde7b1c7b1d2dfaf8dc1e020e24ecd1"
    )
    scientific_identity = provenance["upstream_scientific_identity"]
    assert isinstance(scientific_identity, dict)
    assert scientific_identity["bls_api_scientific_content_sha256"] == (
        "8f1e05bf9a3dd4692fc2c91fcaf386e85f83f219cca4b0641f3c9b6699949ab5"
    )
    hashes = provenance["canonical_evidence_sha256"]
    assert isinstance(hashes, dict)
    for name, expected in hashes.items():
        assert _sha256(str(name)) == expected


def test_canonical_evidence_contains_no_raw_source_payloads() -> None:
    assert not (EVIDENCE / "jul26pub.dat.gz").exists()
    assert not (EVIDENCE / "ln.aspect").exists()
    assert not (EVIDENCE / "bls_api_response.json").exists()
    assert not (EVIDENCE / "failure.json").exists()
