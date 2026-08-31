from __future__ import annotations

from genai_at_work.models import EntityType
from genai_at_work.rps_registry import (
    is_known_excluded_title,
    learn_entity_labels,
    parse_title,
)


def test_learn_labels_and_parse_opaque_series_by_title() -> None:
    release = [
        {
            "id": "RPSGENAIUSAGESHAREIND9",
            "title": "Generative Artificial Intelligence, Adoption Rate for Work: Information",
        },
        {
            "id": "RPSGENAIUSAGESHAREOCC3",
            "title": "Generative Artificial Intelligence, Adoption Rate for Work: Computer and Mathematical Occupations",
        },
    ]
    industries, occupations = learn_entity_labels(release)
    metric, entity_type, entity = parse_title(
        "Generative Artificial Intelligence, Work Hours Assisted: Information",
        industries,
        occupations,
    )
    assert metric == "assisted_hours_share"
    assert entity_type is EntityType.INDUSTRY
    assert entity == "Information"


def test_known_excluded_national_construct() -> None:
    assert is_known_excluded_title(
        "Generative Artificial Intelligence, Daily Use Overall: Working-Age Adults"
    )
