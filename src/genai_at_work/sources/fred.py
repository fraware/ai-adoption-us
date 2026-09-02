"""Official FRED API client for the RPS GenAI tracker.

The client intentionally uses only documented FRED API endpoints. It does not scrape
FRED HTML, consistent with FRED's published Terms of Use. Transient transport,
rate-limit, and server failures are retried with bounded exponential backoff; semantic
client errors and exhausted retries fail closed.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import httpx

TRANSIENT_HTTP_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


class FredError(RuntimeError):
    """Raised when the FRED API returns an invalid or unsuccessful response."""


def _string_keyed_dict(value: object, *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FredError(f"FRED {label} must be a JSON object")
    return {str(key): item for key, item in value.items()}


def _dict_rows(value: object, *, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise FredError(f"FRED {label} must be a JSON array")
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise FredError(f"FRED {label}[{index}] must be a JSON object")
        rows.append({str(key): cell for key, cell in item.items()})
    return rows


@dataclass(frozen=True)
class FredClient:
    """Small, explicit FRED API v1 client.

    Parameters
    ----------
    api_key:
        Registered FRED API key.
    timeout_seconds:
        Network timeout applied to each individual request attempt.
    max_attempts:
        Maximum attempts for transient transport, HTTP 429, and selected HTTP 5xx
        failures. Non-transient HTTP failures are never retried.
    backoff_seconds:
        Initial deterministic backoff before the second attempt. Subsequent retry
        delays double. Set to zero only in deterministic tests.
    """

    api_key: str
    timeout_seconds: float = 30.0
    max_attempts: int = 4
    backoff_seconds: float = 1.0
    base_url: str = "https://api.stlouisfed.org/fred"

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.max_attempts <= 0:
            raise ValueError("max_attempts must be positive")
        if self.backoff_seconds < 0:
            raise ValueError("backoff_seconds must be nonnegative")

    def _sleep_before_retry(self, attempt: int) -> None:
        delay = self.backoff_seconds * (2 ** (attempt - 1))
        if delay > 0:
            time.sleep(delay)

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise FredError("FRED_API_KEY is required; HTML scraping is intentionally unsupported.")

        query = {**params, "api_key": self.api_key, "file_type": "json"}
        url = f"{self.base_url}/{path}"

        for attempt in range(1, self.max_attempts + 1):
            try:
                response = httpx.get(url, params=query, timeout=self.timeout_seconds)
            except httpx.RequestError as exc:
                if attempt >= self.max_attempts:
                    raise FredError(
                        f"FRED request failed for {path} after {attempt} attempts: {exc}"
                    ) from exc
                self._sleep_before_retry(attempt)
                continue

            if response.status_code in TRANSIENT_HTTP_STATUS_CODES:
                if attempt >= self.max_attempts:
                    try:
                        response.raise_for_status()
                    except httpx.HTTPStatusError as exc:
                        raise FredError(
                            f"FRED transient request failed for {path} after {attempt} attempts: {exc}"
                        ) from exc
                self._sleep_before_retry(attempt)
                continue

            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise FredError(f"FRED request failed for {path}: {exc}") from exc

            try:
                raw_payload: object = response.json()
            except ValueError as exc:
                raise FredError(f"FRED response for {path} was not valid JSON") from exc
            payload = _string_keyed_dict(raw_payload, label="response")
            if "error_code" in payload:
                raise FredError(
                    f"FRED API error {payload['error_code']}: {payload.get('error_message')}"
                )
            return payload

        raise AssertionError("unreachable FRED retry loop")

    def iter_release_series(self, release_id: int, page_size: int = 1000) -> Iterator[dict[str, Any]]:
        """Yield every series listed on a FRED release with pagination."""

        offset = 0
        while True:
            payload = self._get(
                "release/series",
                {
                    "release_id": release_id,
                    "limit": page_size,
                    "offset": offset,
                    "order_by": "series_id",
                    "sort_order": "asc",
                },
            )
            rows = _dict_rows(payload.get("seriess", []), label="release series")
            yield from rows
            offset += len(rows)
            if not rows or offset >= int(payload.get("count", offset)):
                break

    def series_metadata(self, series_id: str) -> dict[str, Any]:
        """Return metadata, including series notes, for one FRED series."""

        payload = self._get("series", {"series_id": series_id})
        rows = _dict_rows(payload.get("seriess", []), label="series metadata")
        if len(rows) != 1:
            raise FredError(f"Expected one metadata row for {series_id}, got {len(rows)}")
        return rows[0]

    def series_tags(self, series_id: str) -> list[dict[str, Any]]:
        """Return FRED tags for one series, including copyright-status tags."""

        payload = self._get("series/tags", {"series_id": series_id, "limit": 1000})
        return _dict_rows(payload.get("tags", []), label="series tags")

    def series_observations(self, series_id: str) -> list[dict[str, Any]]:
        """Return all available observations for one series."""

        payload = self._get(
            "series/observations",
            {"series_id": series_id, "sort_order": "asc"},
        )
        return _dict_rows(payload.get("observations", []), label="series observations")
