from __future__ import annotations

from collections.abc import Callable
from typing import Any

import httpx
import pytest

import genai_at_work.sources.fred as fred_module
from genai_at_work.sources.fred import FredClient, FredError


def _response(status: int, payload: dict[str, Any] | None = None) -> httpx.Response:
    request = httpx.Request("GET", "https://api.stlouisfed.org/fred/series")
    return httpx.Response(status, request=request, json=payload or {})


def _install_sequence(
    monkeypatch: pytest.MonkeyPatch,
    sequence: list[httpx.Response | Exception],
) -> list[tuple[str, dict[str, Any]]]:
    calls: list[tuple[str, dict[str, Any]]] = []
    remaining = list(sequence)

    def fake_get(
        url: str,
        *,
        params: dict[str, Any],
        timeout: float,
    ) -> httpx.Response:
        assert timeout > 0
        calls.append((url, dict(params)))
        if not remaining:
            raise AssertionError("Unexpected extra FRED request attempt")
        item = remaining.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    monkeypatch.setattr(fred_module.httpx, "get", fake_get)
    return calls


def _capture_sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    sleeps: list[float] = []

    def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(fred_module.time, "sleep", fake_sleep)
    return sleeps


def test_transient_502_retries_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _install_sequence(
        monkeypatch,
        [
            _response(502),
            _response(200, {"seriess": [{"id": "RPS-TEST"}]}),
        ],
    )
    sleeps = _capture_sleeps(monkeypatch)
    client = FredClient("key", max_attempts=4, backoff_seconds=0.25)

    payload = client._get("series", {"series_id": "RPS-TEST"})

    assert payload["seriess"][0]["id"] == "RPS-TEST"
    assert len(calls) == 2
    assert sleeps == [0.25]


def test_transient_429_uses_same_bounded_retry_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_sequence(
        monkeypatch,
        [
            _response(429),
            _response(200, {"seriess": [{"id": "RPS-TEST"}]}),
        ],
    )
    sleeps = _capture_sleeps(monkeypatch)
    client = FredClient("key", max_attempts=3, backoff_seconds=0.5)

    client._get("series", {"series_id": "RPS-TEST"})

    assert len(calls) == 2
    assert sleeps == [0.5]


def test_transport_error_retries_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    request = httpx.Request("GET", "https://api.stlouisfed.org/fred/series")
    calls = _install_sequence(
        monkeypatch,
        [
            httpx.ConnectError("temporary connection failure", request=request),
            _response(200, {"seriess": [{"id": "RPS-TEST"}]}),
        ],
    )
    sleeps = _capture_sleeps(monkeypatch)
    client = FredClient("key", max_attempts=3, backoff_seconds=0.125)

    client._get("series", {"series_id": "RPS-TEST"})

    assert len(calls) == 2
    assert sleeps == [0.125]


def test_nontransient_400_fails_immediately(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _install_sequence(monkeypatch, [_response(400)])
    sleeps = _capture_sleeps(monkeypatch)
    client = FredClient("key", max_attempts=4, backoff_seconds=0.25)

    with pytest.raises(FredError, match="FRED request failed for series"):
        client._get("series", {"series_id": "RPS-TEST"})

    assert len(calls) == 1
    assert sleeps == []


def test_transient_failure_exhausts_attempts_and_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_sequence(monkeypatch, [_response(502), _response(502), _response(502)])
    sleeps = _capture_sleeps(monkeypatch)
    client = FredClient("key", max_attempts=3, backoff_seconds=0.25)

    with pytest.raises(FredError, match="after 3 attempts"):
        client._get("series", {"series_id": "RPS-TEST"})

    assert len(calls) == 3
    assert sleeps == [0.25, 0.5]


@pytest.mark.parametrize(
    ("factory", "message"),
    [
        (lambda: FredClient("key", timeout_seconds=0), "timeout_seconds must be positive"),
        (lambda: FredClient("key", max_attempts=0), "max_attempts must be positive"),
        (lambda: FredClient("key", backoff_seconds=-1), "backoff_seconds must be nonnegative"),
    ],
)
def test_retry_configuration_is_validated(
    factory: Callable[[], FredClient],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        factory()
