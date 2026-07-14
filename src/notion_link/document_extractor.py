"""Extract normalized document data from Notion page and block objects."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .config import MappingsConfig
from .models import PageRecord


class DocumentExtractor:
    """Convert a Notion document block tree into a Markdown-oriented record."""

    def __init__(self, config: MappingsConfig) -> None:
        self._config = config

    def extract(self, page: dict[str, Any], blocks: list[dict[str, Any]]) -> PageRecord:
        title = self._extract_title(page)
        if not title.strip():
            raise ValueError("Notion document title is empty")

        return PageRecord(
            notion_page_id=page["id"],
            title=title.strip(),
            category=self._config.document.category,
            content="\n".join(self._render_blocks(blocks)).strip(),
            tags=[],
            format=self._config.document.format,
            created_at=self._parse_datetime(page.get("created_time")),
            updated_at=self._parse_datetime(page.get("last_edited_time")),
        )

    def _extract_title(self, page: dict[str, Any]) -> str:
        for prop in page.get("properties", {}).values():
            if prop.get("type") == "title":
                return self._plain_text(prop.get("title", []))
        return ""

    def _render_blocks(self, blocks: list[dict[str, Any]], depth: int = 0) -> list[str]:
        lines: list[str] = []
        for block in blocks:
            rendered = self._render_block(block, depth)
            if rendered:
                lines.extend(rendered)
            children = block.get("children", [])
            if children:
                lines.extend(self._render_blocks(children, depth + 1))
        return lines

    def _render_block(self, block: dict[str, Any], depth: int) -> list[str]:
        block_type = block.get("type", "unsupported")
        data = block.get(block_type, {})
        text = self._plain_text(data.get("rich_text", []))
        indent = "  " * depth

        if block_type.startswith("heading_"):
            level = block_type.removeprefix("heading_")
            return [f"{'#' * int(level)} {text}", ""]
        if block_type == "paragraph":
            return [f"{indent}{text}", ""] if text else [""]
        if block_type == "bulleted_list_item":
            return [f"{indent}- {text}"]
        if block_type == "numbered_list_item":
            return [f"{indent}1. {text}"]
        if block_type == "to_do":
            marker = "x" if data.get("checked") else " "
            return [f"{indent}- [{marker}] {text}"]
        if block_type == "quote":
            return [f"{indent}> {text}", ""]
        if block_type == "callout":
            return [f"{indent}> {text}", ""]
        if block_type == "code":
            language = data.get("language", "")
            return [f"```{language}", text, "```", ""]
        if block_type == "divider":
            return ["---", ""]
        if block_type == "equation":
            return [f"$${data.get('expression', '')}$$", ""]
        if block_type in {"bookmark", "embed", "link_preview"}:
            url = data.get("url", "")
            return [f"<{url}>", ""] if url else []
        if block_type == "child_page":
            title = data.get("title", "")
            page_id = block.get("id", "")
            if title and page_id:
                return [f"{indent}- [{title}](./{page_id}.md)", ""]
            return [f"{indent}- {title}"] if title else []
        if block_type == "child_database":
            title = data.get("title", "")
            return [f"{indent}- {title}"] if title else []
        return [f"{indent}{text}", ""] if text else []

    @staticmethod
    def _plain_text(rich_text: list[dict[str, Any]]) -> str:
        return "".join(item.get("plain_text", "") for item in rich_text)

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime:
        if not value:
            return datetime.now(UTC)
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
