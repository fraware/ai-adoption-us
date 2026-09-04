from __future__ import annotations

from collections.abc import Callable
from typing import Any

import httpx
import pytest

import genai_at_work.sources.fred as fred_module
from genai_at_work.sources.fred import (
    DEFAULT_MIN_REQUEST_INTERVAL_SECONDS,
    FredClient,
    FredError,
)


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
    client = FredClient(
        "key",
        max_attempts=4,
        backoff_seconds=0.25,
        min_request_interval_seconds=0,
    )

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
    client = FredClient(
        "key",
        max_attempts=3,
        backoff_seconds=0.5,
        min_request_interval_seconds=0,
    )

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
    client = FredClient(
        "key",
        max_attempts=3,
        backoff_seconds=0.125,
        min_request_interval_seconds=0,
    )

    client._get("series", {"series_id": "RPS-TEST"})

    assert len(calls) == 2
    assert sleeps == [0.125]


def test_nontransient_400_fails_immediately(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _install_sequence(monkeypatch, [_response(400)])
    sleeps = _capture_sleeps(monkeypatch)
    client = FredClient(
        "key",
        max_attempts=4,
        backoff_seconds=0.25,
        min_request_interval_seconds=0,
    )

    with pytest.raises(FredError, match="FRED request failed for series"):
        client._get("series", {"series_id": "RPS-TEST"})

    assert len(calls) == 1
    assert sleeps == []


def test_transient_failure_exhausts_attempts_and_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_sequence(monkeypatch, [_response(502), _response(502), _response(502)])
    sleeps = _capture_sleeps(monkeypatch)
    client = FredClient(
        "key",
        max_attempts=3,
        backoff_seconds=0.25,
        min_request_interval_seconds=0,
    )

    with pytest.raises(FredError, match="after 3 attempts"):
        client._get("series", {"series_id": "RPS-TEST"})

    assert len(calls) == 3
    assert sleeps == [0.25, 0.5]


def test_default_request_pacing_is_below_fred_two_per_second_ceiling() -> None:
    assert DEFAULT_MIN_REQUEST_INTERVAL_SECONDS > 0.5


def test_request_starts_are_paced_by_monotonic_clock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_sequence(
        monkeypatch,
        [
            _response(200, {"seriess": [{"id": "FIRST"}]}),
            _response(200, {"seriess": [{"id": "SECOND"}]}),
        ],
    )
    clock = {"now": 100.0}
    sleeps: list[float] = []

    def fake_monotonic() -> float:
        return clock["now"]

    def fake_sleep(delay: float) -> None:
        sleeps.append(delay)
        clock["now"] += delay

    monkeypatch.setattr(fred_module.time, "monotonic", fake_monotonic)
    monkeypatch.setattr(fred_module.time, "sleep", fake_sleep)
    client = FredClient(
        "key",
        max_attempts=1,
        backoff_seconds=0,
        min_request_interval_seconds=0.55,
    )

    client._get("series", {"series_id": "FIRST"})
    client._get("series", {"series_id": "SECOND"})

    assert len(calls) == 2
    assert sleeps == pytest.approx([0.55])
    assert client._last_request_started_at == pytest.approx(100.55)


def test_elapsed_time_reduces_only_the_remaining_pacing_delay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_sequence(
        monkeypatch,
        [
            _response(200, {"seriess": [{"id": "FIRST"}]}),
            _response(200, {"seriess": [{"id": "SECOND"}]}),
        ],
    )
    clock = {"now": 10.0}
    sleeps: list[float] = []

    monkeypatch.setattr(fred_module.time, "monotonic", lambda: clock["now"])

    def fake_sleep(delay: float) -> None:
        sleeps.append(delay)
        clock["now"] += delay

    monkeypatch.setattr(fred_module.time, "sleep", fake_sleep)
    client = FredClient(
        "key",
        max_attempts=1,
        backoff_seconds=0,
        min_request_interval_seconds=0.55,
    )

    client._get("series", {"series_id": "FIRST"})
    clock["now"] += 0.2
    client._get("series", {"series_id": "SECOND"})

    assert len(calls) == 2
    assert sleeps == pytest.approx([0.35])


@pytest.mark.parametrize(
    ("factory", "message"),
    [
        (lambda: FredClient("key", timeout_seconds=0), "timeout_seconds must be positive"),
        (lambda: FredClient("key", max_attempts=0), "max_attempts must be positive"),
        (lambda: FredClient("key", backoff_seconds=-1), "backoff_seconds must be nonnegative"),
        (
            lambda: FredClient("key", min_request_interval_seconds=-0.1),
            "min_request_interval_seconds must be nonnegative",
        ),
    ],
)
def test_retry_configuration_is_validated(
    factory: Callable[[], FredClient],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        factory()
