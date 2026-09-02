from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from genai_at_work.btos_core import (
    BTOSResponseEstimate,
    extract_cycle_dates,
    extract_national_response,
    extract_sector_responses,
)

ROOT = Path(__file__).parents[1]
DEFAULT_SOURCE_REGISTRY = ROOT / "data" / "registry" / "btos_core_ai_202617_source_v1.json"
DEFAULT_CHECKPOINT = ROOT / "data" / "derived" / "btos" / "btos_core_ai_202617.json"
CROSSWALK = ROOT / "data" / "registry" / "btos_rps_industry_crosswalk_v1.json"


def _load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object in {path}")
    return value


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _require_equal(actual: object, expected: object, label: str) -> None:
    if actual != expected:
        raise ValueError(f"{label} mismatch: actual={actual!r}, expected={expected!r}")


def _resolve_repo_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def _load_pinned_workbook(source_dir: Path, source: dict[str, object], label: str) -> bytes:
    filename = source["filename"]
    if not isinstance(filename, str):
        raise ValueError(f"{label} source filename is not a string")
    path = source_dir / filename
    if not path.is_file():
        raise ValueError(f"{label} source workbook is missing: {path}")
    data = path.read_bytes()
    _require_equal(len(data), source["byte_size"], f"{label} byte size")
    _require_equal(_sha256(data), source["sha256"], f"{label} SHA-256")
    return data


def _response_payload(response: BTOSResponseEstimate) -> dict[str, object]:
    return {
        "estimate_pct": response.estimate_pct,
        "standard_error_pp": response.standard_error_pp,
        "suppression_code": response.suppression_code,
    }


def _validate_national_distribution(
    national_bytes: bytes,
    registry: dict[str, object],
    *,
    cycle: str,
    question_id: int,
) -> float:
    responses = [
        extract_national_response(
            national_bytes,
            cycle=cycle,
            question_id=question_id,
            answer_id=answer_id,
        )
        for answer_id in (1, 2, 3)
    ]
    if any(response.suppression_code is not None for response in responses):
        raise ValueError("national Q7 response distribution unexpectedly contains suppression")
    if any(response.estimate_pct is None for response in responses):
        raise ValueError("national Q7 response distribution contains a missing estimate")

    distribution_total = sum(float(response.estimate_pct) for response in responses)
    distribution_contract = registry.get("national_response_distribution")
    if distribution_contract is None:
        expected_total = 100.0
    elif isinstance(distribution_contract, dict):
        expected_answers = {
            1: distribution_contract.get("answer_1_yes_pct"),
            2: distribution_contract.get("answer_2_no_pct"),
            3: distribution_contract.get("answer_3_do_not_know_pct"),
        }
        for answer_id, response in zip((1, 2, 3), responses, strict=True):
            expected = expected_answers[answer_id]
            if expected is not None:
                _require_equal(response.estimate_pct, expected, f"national Q7/A{answer_id} estimate")
        expected_total = distribution_contract.get("published_total_pct", 100.0)
        if not isinstance(expected_total, int | float):
            raise ValueError("national response-distribution total is not numeric")
    else:
        raise ValueError("national_response_distribution must be an object when present")

    if abs(float(expected_total) - 100.0) > 0.15:
        raise ValueError(
            "registered national response total exceeds the maximum one-decimal rounding residual: "
            f"{expected_total}"
        )
    if abs(distribution_total - float(expected_total)) > 1e-9:
        raise ValueError(
            "national Q7 response distribution total differs from the registered published total: "
            f"actual={distribution_total}, expected={expected_total}"
        )
    return distribution_total


def validate(
    source_dir: Path,
    *,
    source_registry_path: Path = DEFAULT_SOURCE_REGISTRY,
    checkpoint_path: Path = DEFAULT_CHECKPOINT,
) -> dict[str, object]:
    source_registry_path = _resolve_repo_path(source_registry_path)
    checkpoint_path = _resolve_repo_path(checkpoint_path)

    registry = _load_json(source_registry_path)
    checkpoint = _load_json(checkpoint_path)
    crosswalk = _load_json(CROSSWALK)

    _require_equal(checkpoint["checkpoint_id"], registry["checkpoint_id"], "checkpoint identity")
    _require_equal(checkpoint["cycle"], registry["cycle"], "checkpoint cycle")
    _require_equal(checkpoint["question_id"], registry["question_id"], "checkpoint question ID")
    _require_equal(checkpoint["answer_id"], registry["answer_id"], "checkpoint answer ID")

    source_files = registry["source_files"]
    if not isinstance(source_files, dict):
        raise ValueError("source_files registry entry is not an object")
    national_source = source_files["national"]
    sector_source = source_files["sector"]
    if not isinstance(national_source, dict) or not isinstance(sector_source, dict):
        raise ValueError("national/sector source registry entries are not objects")

    national_bytes = _load_pinned_workbook(source_dir, national_source, "national")
    sector_bytes = _load_pinned_workbook(source_dir, sector_source, "sector")

    cycle = registry["cycle"]
    question_id = registry["question_id"]
    answer_id = registry["answer_id"]
    if not isinstance(cycle, str) or not isinstance(question_id, int) or not isinstance(answer_id, int):
        raise ValueError("cycle/question_id/answer_id registry types are invalid")

    national = extract_national_response(
        national_bytes,
        cycle=cycle,
        question_id=question_id,
        answer_id=answer_id,
    )
    _require_equal(national.question, registry["question"], "national question text")
    _require_equal(national.answer, registry["answer"], "national answer text")

    national_checkpoint = checkpoint["national"]
    if not isinstance(national_checkpoint, dict):
        raise ValueError("checkpoint national entry is not an object")
    _require_equal(
        _response_payload(national),
        {
            "estimate_pct": national_checkpoint["estimate_pct"],
            "standard_error_pp": national_checkpoint["standard_error_pp"],
            "suppression_code": national_checkpoint["suppression_code"],
        },
        "national Q7/A1 checkpoint",
    )

    dates = extract_cycle_dates(national_bytes, cycle=cycle)
    date_payload = {
        "collection_start": dates.collection_start.isoformat(),
        "collection_end": dates.collection_end.isoformat(),
        "reference_start": dates.reference_start.isoformat(),
        "reference_end": dates.reference_end.isoformat(),
        "publication_date": dates.publication_date.isoformat(),
    }
    _require_equal(date_payload, registry["dates"], "cycle date metadata")

    distribution_total = _validate_national_distribution(
        national_bytes,
        registry,
        cycle=cycle,
        question_id=question_id,
    )

    actual_sectors = {
        response.sector_code: response
        for response in extract_sector_responses(
            sector_bytes,
            cycle=cycle,
            question_id=question_id,
            answer_id=answer_id,
        )
    }
    if None in actual_sectors:
        raise ValueError("sector workbook produced a response without a source key")

    sector_checkpoint = checkpoint["sectors"]
    if not isinstance(sector_checkpoint, list):
        raise ValueError("checkpoint sectors entry is not a list")
    expected_source_keys = {row["btos_sector_code"] for row in sector_checkpoint if isinstance(row, dict)}
    _require_equal(set(actual_sectors), expected_source_keys, "sector source-key set")

    crosswalk_entries = crosswalk["entries"]
    if not isinstance(crosswalk_entries, list):
        raise ValueError("crosswalk entries are not a list")
    mapped_by_source_key = {
        row["btos_sector_code"]: row
        for row in crosswalk_entries
        if isinstance(row, dict) and row.get("mapping_status") == "mapped"
    }

    published = 0
    suppressed = 0
    expected_suppressed_keys: set[str] = set()
    for row in sector_checkpoint:
        if not isinstance(row, dict):
            raise ValueError("checkpoint sector row is not an object")
        source_key = row["btos_sector_code"]
        if not isinstance(source_key, str):
            raise ValueError("checkpoint sector source key is not a string")
        actual = actual_sectors[source_key]
        _require_equal(
            _response_payload(actual),
            {
                "estimate_pct": row["estimate_pct"],
                "standard_error_pp": row["standard_error_pp"],
                "suppression_code": row["suppression_code"],
            },
            f"sector {source_key} Q7/A1 checkpoint",
        )
        _require_equal(actual.question, registry["question"], f"sector {source_key} question text")
        _require_equal(actual.answer, registry["answer"], f"sector {source_key} answer text")

        if row["suppression_code"] == "S":
            expected_suppressed_keys.add(source_key)
        if actual.suppression_code == "S":
            suppressed += 1
            if actual.estimate_pct is not None or actual.standard_error_pp is not None:
                raise ValueError(f"sector {source_key} suppression is not represented as null values")
        else:
            published += 1

        if source_key == "XX":
            _require_equal(row["entity_id"], None, "XX target entity")
            _require_equal(row["comparability"], "unclassified", "XX comparability")
            continue

        mapping = mapped_by_source_key.get(source_key)
        if mapping is None:
            raise ValueError(f"checkpoint sector {source_key} has no exact crosswalk mapping")
        for field in ("entity_index", "entity_id", "entity_name", "comparability", "naics_sector_span"):
            _require_equal(row[field], mapping[field], f"sector {source_key} {field}")

    _require_equal(
        published,
        len(sector_checkpoint) - len(expected_suppressed_keys),
        "published source-sector row count including XX",
    )
    _require_equal(suppressed, len(expected_suppressed_keys), "suppressed source-sector row count")
    suppressed_keys = {
        key for key, response in actual_sectors.items() if response.suppression_code == "S"
    }
    _require_equal(suppressed_keys, expected_suppressed_keys, "suppressed source-key set")

    unsupported_targets = checkpoint["unsupported_targets"]
    if not isinstance(unsupported_targets, list) or len(unsupported_targets) != 1:
        raise ValueError("checkpoint must contain exactly one unsupported target")
    public_admin = unsupported_targets[0]
    if not isinstance(public_admin, dict):
        raise ValueError("unsupported target is not an object")
    _require_equal(public_admin["entity_id"], "public-administration", "unsupported target entity")
    if "92" in actual_sectors:
        raise ValueError("BTOS source unexpectedly contains Public Administration sector 92")

    _require_equal(registry["rps_values_included"], False, "registry RPS inclusion flag")
    _require_equal(
        registry["cross_source_statistics_included"], False, "registry cross-source statistic flag"
    )
    _require_equal(checkpoint["rps_values_included"], False, "checkpoint RPS inclusion flag")
    _require_equal(
        checkpoint["cross_source_statistics_included"],
        False,
        "checkpoint cross-source statistic flag",
    )

    return {
        "status": "verified",
        "checkpoint_id": registry["checkpoint_id"],
        "cycle": cycle,
        "national": _response_payload(national),
        "national_q7_response_total_pct": distribution_total,
        "source_sector_rows": len(actual_sectors),
        "published_source_sector_rows_including_xx": published,
        "suppressed_source_sector_rows": suppressed,
        "suppressed_source_keys": sorted(suppressed_keys),
        "dates": date_payload,
        "national_sha256": national_source["sha256"],
        "sector_sha256": sector_source["sha256"],
        "source_registry": str(source_registry_path.relative_to(ROOT)),
        "checkpoint": str(checkpoint_path.relative_to(ROOT)),
        "note": "Source reproduction only; no RPS values or cross-source statistics validated.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a pinned BTOS core AI checkpoint.")
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--source-registry", type=Path, default=DEFAULT_SOURCE_REGISTRY)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    args = parser.parse_args()

    try:
        report = validate(
            args.source_dir,
            source_registry_path=args.source_registry,
            checkpoint_path=args.checkpoint,
        )
    except Exception as exc:
        failure = {
            "status": "failed",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(failure, indent=2) + "\n")
        print(f"BTOS core checkpoint validation failed: {type(exc).__name__}: {exc}")
        return 1

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
