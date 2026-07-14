"""Tests for recursive Notion document fetching."""

from __future__ import annotations

from typing import Any

from notion_link.fetcher import Fetcher


class PaginatedClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str | None]] = []

    def get_page(self, page_id: str) -> dict[str, Any]:
        return {"id": page_id, "properties": {}}

    def get_block_children(
        self, block_id: str, *, start_cursor: str | None = None, page_size: int = 100
    ) -> dict[str, Any]:
        self.calls.append((block_id, start_cursor))
        if block_id == "page" and start_cursor is None:
            return {
                "results": [{"id": "toggle", "type": "toggle", "has_children": True}],
                "has_more": True,
                "next_cursor": "next",
            }
        if block_id == "toggle":
            return {
                "results": [{"id": "nested", "type": "paragraph", "has_children": False}],
                "has_more": False,
            }
        return {
            "results": [{"id": "tail", "type": "divider", "has_children": False}],
            "has_more": False,
        }


def test_fetch_document_follows_pagination_and_nested_children() -> None:
    client = PaginatedClient()

    page, blocks = Fetcher(client).fetch_document("page")

    assert page["id"] == "page"
    assert [block["id"] for block in blocks] == ["toggle", "tail"]
    assert blocks[0]["children"][0]["id"] == "nested"
    assert client.calls == [("page", None), ("toggle", None), ("page", "next")]
