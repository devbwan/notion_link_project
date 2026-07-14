"""Notion API client."""

from __future__ import annotations

from typing import Any

import httpx

NOTION_API_VERSION = "2026-03-11"
NOTION_BASE_URL = "https://api.notion.com/v1"


class NotionClient:
    """HTTP client for Notion API."""

    def __init__(self, token: str) -> None:
        self._client = httpx.Client(
            base_url=NOTION_BASE_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Notion-Version": NOTION_API_VERSION,
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(connect=10.0, read=30.0, write=30.0, pool=10.0),
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> NotionClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def get_database(self, database_id: str) -> dict[str, Any]:
        """Retrieve database metadata including data sources."""
        response = self._client.get(f"/databases/{database_id}")
        response.raise_for_status()
        return response.json()

    def get_data_source(self, data_source_id: str) -> dict[str, Any]:
        """Retrieve data source schema."""
        response = self._client.get(f"/data_sources/{data_source_id}")
        response.raise_for_status()
        return response.json()

    def query_data_source(
        self,
        data_source_id: str,
        *,
        filter_: dict[str, Any] | None = None,
        start_cursor: str | None = None,
        page_size: int = 100,
    ) -> dict[str, Any]:
        """Query pages from a data source."""
        payload: dict[str, Any] = {"page_size": page_size}
        if filter_:
            payload["filter"] = filter_
        if start_cursor:
            payload["start_cursor"] = start_cursor

        response = self._client.post(f"/data_sources/{data_source_id}/query", json=payload)
        response.raise_for_status()
        return response.json()

    def update_page(self, page_id: str, properties: dict[str, Any]) -> dict[str, Any]:
        """Update page properties."""
        response = self._client.patch(f"/pages/{page_id}", json={"properties": properties})
        response.raise_for_status()
        return response.json()
