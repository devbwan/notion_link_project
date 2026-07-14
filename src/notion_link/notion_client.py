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

    def get_page(self, page_id: str) -> dict[str, Any]:
        """Retrieve page metadata and properties."""
        response = self._client.get(f"/pages/{page_id}")
        response.raise_for_status()
        return response.json()

    def get_block_children(
        self,
        block_id: str,
        *,
        start_cursor: str | None = None,
        page_size: int = 100,
    ) -> dict[str, Any]:
        """Retrieve one page of child blocks for a page or block."""
        params: dict[str, Any] = {"page_size": page_size}
        if start_cursor:
            params["start_cursor"] = start_cursor

        response = self._client.get(f"/blocks/{block_id}/children", params=params)
        response.raise_for_status()
        return response.json()
