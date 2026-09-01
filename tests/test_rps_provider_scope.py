from __future__ import annotations

import json
from pathlib import Path

import pytest

from genai_at_work.rps_registry import is_known_excluded_title, parse_title

ROOT = Path(__file__).parents[1]


def _load(path: str) -> dict[str, object]:
    value = json.loads((ROOT / path).read_text())
    assert isinstance(value, dict)
    return value


def test_provider_catalog_scope_reconciles_137_to_canonical_131() -> None:
    scope = _load("data/registry/rps_provider_catalog_scope.json")
    manifest = _load("data/registry/rps_source_series_manifest.json")

    included = scope["included_national_series"]
    excluded = scope["intentionally_excluded_national_series"]
    observatory = scope["observatory_scope"]
    series = manifest["series"]

    assert isinstance(included, list)
    assert isinstance(excluded, list)
    assert isinstance(observatory, dict)
    assert isinstance(series, list)

    assert scope["provider_release_series_count"] == 137
    assert scope["observatory_registry_series_count"] == 131
    assert len(series) == 131
    assert len(included) == 5
    assert len(excluded) == 6
    assert observatory["national_series_count"] == 5
    assert observatory["industry_series_count"] == 60
    assert observatory["occupation_series_count"] == 66
    assert 5 + 60 + 66 == 131
    assert 11 + 60 + 66 == 137

    manifest_ids = {str(row["series_id"]) for row in series if isinstance(row, dict)}
    included_ids = {str(row["series_id"]) for row in included if isinstance(row, dict)}
    excluded_ids = {str(row["series_id"]) for row in excluded if isinstance(row, dict)}

    assert included_ids <= manifest_ids
    assert excluded_ids.isdisjoint(manifest_ids)
    assert len(manifest_ids) == 131


def test_all_six_out_of_scope_national_constructs_are_explicitly_excluded() -> None:
    titles = (
        "Generative Artificial Intelligence, Adoption Rate Overall: Working-Age Adults",
        "Generative Artificial Intelligence, Adoption Rate Outside of Work: Working-Age Adults",
        "Generative Artificial Intelligence, Use Last Week Overall: Working-Age Adults",
        "Generative Artificial Intelligence, Use Last Week Outside of Work: Working-Age Adults",
        "Generative Artificial Intelligence, Daily Use Overall: Working-Age Adults",
        "Generative Artificial Intelligence, Daily Use Outside of Work: Working-Age Adults",
    )
    assert all(is_known_excluded_title(title) for title in titles)


@pytest.mark.parametrize(
    "title",
    [
        "Generative Artificial Intelligence, Adoption Rate Overall: Working-Age Adults",
        "Generative Artificial Intelligence, Adoption Rate Outside of Work: Working-Age Adults",
        "Generative Artificial Intelligence, Use Last Week Overall: Working-Age Adults",
        "Generative Artificial Intelligence, Use Last Week Outside of Work: Working-Age Adults",
        "Generative Artificial Intelligence, Daily Use Overall: Working-Age Adults",
        "Generative Artificial Intelligence, Daily Use Outside of Work: Working-Age Adults",
    ],
)
def test_out_of_scope_national_constructs_cannot_be_parsed_as_supported_metrics(title: str) -> None:
    with pytest.raises(ValueError, match="Unsupported RPS metric title"):
        parse_title(title, set(), set())
