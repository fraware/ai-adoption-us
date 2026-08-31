"""Official FRED API client for the RPS GenAI tracker.

The client intentionally uses only documented FRED API endpoints. It does not scrape
FRED HTML, consistent with FRED's published Terms of Use.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import httpx


class FredError(RuntimeError):
    """Raised when the FRED API returns an invalid or unsuccessful response."""


@dataclass(frozen=True)
class FredClient:
    """Small, explicit FRED API v1 client.

    Parameters
    ----------
    api_key:
        Registered FRED API key.
    timeout_seconds:
        Network timeout applied to each request.
    """

    api_key: str
    timeout_seconds: float = 30.0
    base_url: str = "https://api.stlouisfed.org/fred"

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise FredError("FRED_API_KEY is required; HTML scraping is intentionally unsupported.")

        query = {**params, "api_key": self.api_key, "file_type": "json"}
        try:
            response = httpx.get(
                f"{self.base_url}/{path}", params=query, timeout=self.timeout_seconds
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise FredError(f"FRED request failed for {path}: {exc}") from exc

        payload = response.json()
        if "error_code" in payload:
            raise FredError(f"FRED API error {payload['error_code']}: {payload.get('error_message')}")
        return payload

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
            rows = payload.get("seriess", [])
            yield from rows
            offset += len(rows)
            if not rows or offset >= int(payload.get("count", offset)):
                break

    def series_metadata(self, series_id: str) -> dict[str, Any]:
        """Return metadata, including series notes, for one FRED series."""

        payload = self._get("series", {"series_id": series_id})
        rows = payload.get("seriess", [])
        if len(rows) != 1:
            raise FredError(f"Expected one metadata row for {series_id}, got {len(rows)}")
        return rows[0]

    def series_tags(self, series_id: str) -> list[dict[str, Any]]:
        """Return FRED tags for one series, including copyright-status tags."""

        payload = self._get("series/tags", {"series_id": series_id, "limit": 1000})
        return list(payload.get("tags", []))

    def series_observations(self, series_id: str) -> list[dict[str, Any]]:
        """Return all available observations for one series."""

        payload = self._get(
            "series/observations",
            {"series_id": series_id, "sort_order": "asc"},
        )
        return list(payload.get("observations", []))
