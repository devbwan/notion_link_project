"""Tests for the complete document sync service flow."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from notion_link.config import EnvConfig
from notion_link.service import SyncService


class FakeNotionClient:
    """Small in-memory Notion document client used by service tests."""

    def __init__(self, page: dict[str, Any], blocks: list[dict[str, Any]]) -> None:
        self.page = page
        self.blocks = blocks

    def get_page(self, page_id: str) -> dict[str, Any]:
        assert page_id == self.page["id"]
        return self.page

    def get_block_children(
        self, block_id: str, *, start_cursor: str | None = None, page_size: int = 100
    ) -> dict[str, Any]:
        assert block_id == self.page["id"]
        assert start_cursor is None
        assert page_size == 100
        return {"results": self.blocks, "has_more": False, "next_cursor": None}


def document_page() -> dict[str, Any]:
    return {
        "id": "01234567-89ab-cdef-0123-456789abcdef",
        "created_time": "2024-01-15T10:00:00.000Z",
        "last_edited_time": "2024-01-15T12:30:00.000Z",
        "properties": {
            "title": {
                "type": "title",
                "title": [{"plain_text": "프로젝트 문서"}],
            }
        },
    }


def document_blocks() -> list[dict[str, Any]]:
    return [
        {
            "id": "heading",
            "type": "heading_2",
            "has_children": False,
            "heading_2": {"rich_text": [{"plain_text": "개요"}]},
        },
        {
            "id": "paragraph",
            "type": "paragraph",
            "has_children": False,
            "paragraph": {"rich_text": [{"plain_text": "문서 본문입니다."}]},
        },
    ]


def make_service(client: FakeNotionClient, sample_config) -> SyncService:
    env = EnvConfig(
        notion_token="test-token",
        notion_page_id="01234567-89ab-cdef-0123-456789abcdef",
    )
    return SyncService(client, env, sample_config)


class TestSyncService:
    def test_sync_extracts_document_and_records_state(
        self, monkeypatch, tmp_path: Path, sample_config
    ) -> None:
        monkeypatch.chdir(tmp_path)
        client = FakeNotionClient(document_page(), document_blocks())

        results = make_service(client, sample_config).sync()

        assert [result.status for result in results] == ["success"]
        output = tmp_path / "output/notion/01234567-89ab-cdef-0123-456789abcdef.md"
        assert output.is_file()
        text = output.read_text(encoding="utf-8")
        assert "# 프로젝트 문서" in text
        assert "## 개요" in text
        assert "문서 본문입니다." in text
        assert (tmp_path / ".state/notion-link.db").is_file()

    def test_sync_skips_unchanged_document(
        self, monkeypatch, tmp_path: Path, sample_config
    ) -> None:
        monkeypatch.chdir(tmp_path)
        client = FakeNotionClient(document_page(), document_blocks())
        service = make_service(client, sample_config)
        service.sync()
        output = tmp_path / "output/notion/01234567-89ab-cdef-0123-456789abcdef.md"
        first_mtime = output.stat().st_mtime_ns

        second_results = service.sync()

        assert second_results[0].status == "success"
        assert output.stat().st_mtime_ns == first_mtime

    def test_empty_document_title_is_an_isolated_error(
        self, monkeypatch, tmp_path: Path, sample_config
    ) -> None:
        monkeypatch.chdir(tmp_path)
        page = document_page()
        page["properties"]["title"]["title"] = []

        results = make_service(
            FakeNotionClient(page, document_blocks()), sample_config
        ).sync()

        assert results[0].status == "error"
        assert results[0].error_message == "Notion document title is empty"
        assert not list((tmp_path / "output").glob("**/*.md"))

    def test_dry_run_leaves_output_and_state_untouched(
        self, monkeypatch, tmp_path: Path, sample_config
    ) -> None:
        monkeypatch.chdir(tmp_path)
        client = FakeNotionClient(document_page(), document_blocks())

        results = make_service(client, sample_config).sync(dry_run=True)

        assert [result.status for result in results] == ["success"]
        assert not (tmp_path / "output").exists()
        assert not (tmp_path / ".state").exists()
