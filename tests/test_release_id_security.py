from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "observatory_release.py"


def _release_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("observatory_release_script", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load observatory release script for security test")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_release_id_accepts_only_safe_lowercase_slug():
    module = _release_script()
    assert module._safe_release_id("release-2026-q3", context="test") == "release-2026-q3"
    assert module._safe_release_id("r1.2_candidate", context="test") == "r1.2_candidate"

    for unsafe in (
        "../escape",
        "release/child",
        "/absolute",
        "..",
        ".hidden",
        "Release-2026-Q3",
        "release\\child",
        "release q3",
        "",
    ):
        with pytest.raises(SystemExit):
            module._safe_release_id(unsafe, context="test")
