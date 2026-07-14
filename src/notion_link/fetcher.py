"""Fetch a Notion page and its complete nested block tree."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .notion_client import NotionClient


class Fetcher:
    """Fetches a document, following block pagination and nesting."""

    def __init__(self, client: NotionClient) -> None:
        self._client = client

    def fetch_document(self, page_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Return page metadata and all descendant blocks."""
        page = self._client.get_page(page_id)
        return page, self._fetch_children(page_id)

    def _fetch_children(self, block_id: str) -> list[dict[str, Any]]:
        blocks: list[dict[str, Any]] = []
        cursor: str | None = None

        while True:
            result = self._client.get_block_children(block_id, start_cursor=cursor)
            for raw_block in result.get("results", []):
                block = dict(raw_block)
                if block.get("has_children"):
                    block["children"] = self._fetch_children(block["id"])
                blocks.append(block)

            if not result.get("has_more"):
                break
            cursor = result.get("next_cursor")
            if not cursor:
                raise ValueError("Notion returned has_more without next_cursor")

        return blocks
