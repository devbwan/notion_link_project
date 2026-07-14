"""Fetch a Notion page and its complete nested block tree."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .notion_client import NotionClient

logger = logging.getLogger(__name__)

MAX_DEPTH = 10


class Fetcher:
    """Fetches a document, following block pagination and nesting."""

    def __init__(self, client: NotionClient) -> None:
        self._client = client

    def fetch_document(self, page_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Return page metadata and all descendant blocks."""
        page = self._client.get_page(page_id)
        return page, self._fetch_children(page_id)

    def fetch_all_pages(
        self, root_page_id: str
    ) -> list[tuple[dict[str, Any], list[dict[str, Any]]]]:
        """Fetch root page and all child pages recursively.

        Returns list of (page, blocks) tuples for each discovered page.
        """
        visited: set[str] = set()
        results: list[tuple[dict[str, Any], list[dict[str, Any]]]] = []
        self._fetch_page_recursive(root_page_id, visited, results, depth=0)
        return results

    def _fetch_page_recursive(
        self,
        page_id: str,
        visited: set[str],
        results: list[tuple[dict[str, Any], list[dict[str, Any]]]],
        depth: int,
    ) -> None:
        """Recursively fetch a page and its child pages."""
        if page_id in visited:
            return
        if depth > MAX_DEPTH:
            logger.warning(f"Max depth {MAX_DEPTH} exceeded for page {page_id[-8:]}")
            return

        visited.add(page_id)

        try:
            page, blocks = self.fetch_document(page_id)
            results.append((page, blocks))

            child_page_ids = self._collect_child_page_ids(blocks)
            for child_id in child_page_ids:
                self._fetch_page_recursive(child_id, visited, results, depth + 1)

        except Exception as e:
            logger.warning(f"Failed to fetch page {page_id[-8:]}: {e}")

    def _collect_child_page_ids(self, blocks: list[dict[str, Any]]) -> list[str]:
        """Collect all child_page block IDs from a block tree."""
        ids: list[str] = []
        for block in blocks:
            if block.get("type") == "child_page":
                ids.append(block["id"])
            children = block.get("children", [])
            if children:
                ids.extend(self._collect_child_page_ids(children))
        return ids

    def _fetch_children(self, block_id: str) -> list[dict[str, Any]]:
        blocks: list[dict[str, Any]] = []
        cursor: str | None = None

        while True:
            result = self._client.get_block_children(block_id, start_cursor=cursor)
            for raw_block in result.get("results", []):
                block = dict(raw_block)
                if block.get("has_children") and block.get("type") != "child_page":
                    block["children"] = self._fetch_children(block["id"])
                blocks.append(block)

            if not result.get("has_more"):
                break
            cursor = result.get("next_cursor")
            if not cursor:
                raise ValueError("Notion returned has_more without next_cursor")

        return blocks
