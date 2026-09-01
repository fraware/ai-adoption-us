from __future__ import annotations

import json
from pathlib import Path

import pytest

from genai_at_work.rps_registry import is_known_excluded_title, parse_title

ROOT = Path(__file__).parents[1]
SUBGROUP_METRICS = {
    "adoption_work",
    "assisted_hours_share",
    "reported_time_savings_share",
}


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
    entity_type_counts = manifest["entity_type_counts"]

    assert isinstance(included, list) and all(isinstance(row, dict) for row in included)
    assert isinstance(excluded, list) and all(isinstance(row, dict) for row in excluded)
    assert isinstance(observatory, dict)
    assert isinstance(series, list) and all(isinstance(row, dict) for row in series)
    assert isinstance(entity_type_counts, dict)

    national = [row for row in series if row["entity_type"] == "national"]
    industries = [row for row in series if row["entity_type"] == "industry"]
    occupations = [row for row in series if row["entity_type"] == "occupation"]

    assert manifest["series_count"] == 131
    assert scope["observatory_registry_series_count"] == manifest["series_count"]
    assert len(series) == manifest["series_count"]
    assert entity_type_counts == {"national": 5, "industry": 60, "occupation": 66}
    assert len(national) == observatory["national_series_count"] == 5
    assert len(industries) == observatory["industry_series_count"] == 60
    assert len(occupations) == observatory["occupation_series_count"] == 66

    included_ids = {str(row["series_id"]) for row in included}
    excluded_ids = {str(row["series_id"]) for row in excluded}
    manifest_ids = {str(row["series_id"]) for row in series}
    national_ids = {str(row["series_id"]) for row in national}
    included_metrics = {str(row["metric_id"]) for row in included}
    national_metrics = {str(row["metric_id"]) for row in national}

    assert len(included_ids) == 5
    assert len(excluded_ids) == 6
    assert national_ids == included_ids
    assert national_metrics == included_metrics
    assert excluded_ids.isdisjoint(manifest_ids)
    assert len(manifest_ids) == 131
    assert scope["provider_release_series_count"] == len(manifest_ids) + len(excluded_ids) == 137

    industry_entities = {str(row["entity_id"]) for row in industries}
    occupation_entities = {str(row["entity_id"]) for row in occupations}
    assert len(industry_entities) == observatory["industry_count"] == 20
    assert len(occupation_entities) == observatory["occupation_count"] == 22
    assert {str(row["metric_id"]) for row in industries} == SUBGROUP_METRICS
    assert {str(row["metric_id"]) for row in occupations} == SUBGROUP_METRICS
    for entity_id in industry_entities:
        assert {str(row["metric_id"]) for row in industries if row["entity_id"] == entity_id} == SUBGROUP_METRICS
    for entity_id in occupation_entities:
        assert {str(row["metric_id"]) for row in occupations if row["entity_id"] == entity_id} == SUBGROUP_METRICS


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
