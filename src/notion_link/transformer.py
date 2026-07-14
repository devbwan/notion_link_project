"""Transform Notion pages to internal model."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from zoneinfo import ZoneInfo

from .models import PageRecord

if TYPE_CHECKING:
    from .config import MappingsConfig


class Transformer:
    """Transforms raw Notion pages to normalized PageRecord."""

    def __init__(self, config: MappingsConfig) -> None:
        self._config = config
        self._input_tz = ZoneInfo(config.datetime.input_timezone)
        self._output_tz = ZoneInfo(config.datetime.output_timezone)

    def transform(self, page: dict[str, Any]) -> PageRecord:
        """Transform a Notion page to PageRecord."""
        page_id = page["id"]
        properties = page.get("properties", {})

        props = self._config.notion.properties
        fields = self._config.fields

        title = self._normalize_field(
            self._extract_text(properties.get(props.title, {})),
            fields.get("title"),
        )

        category = self._normalize_field(
            self._extract_select(properties.get(props.category, {})),
            fields.get("type"),
        )

        content = self._normalize_field(
            self._extract_text(properties.get(props.content, {})),
            fields.get("content"),
        )

        tags = self._normalize_field(
            self._extract_multi_select(properties.get(props.tags, {})),
            fields.get("tags"),
        )

        format_value = self._extract_select(properties.get(props.format, {}))
        if format_value not in self._config.output.allowed_formats:
            format_value = self._config.output.default_format

        created_at = self._parse_datetime(
            properties.get(props.created_at, {}).get("created_time")
        )
        updated_at = self._parse_datetime(
            properties.get(props.updated_at, {}).get("last_edited_time")
        )

        return PageRecord(
            notion_page_id=page_id,
            title=title,
            category=category,
            content=content,
            tags=tags,
            format=format_value,
            created_at=created_at,
            updated_at=updated_at,
        )

    def _extract_text(self, prop: dict[str, Any]) -> str:
        """Extract plain text from title or rich_text property."""
        prop_type = prop.get("type")
        if prop_type == "title":
            texts = prop.get("title", [])
        elif prop_type == "rich_text":
            texts = prop.get("rich_text", [])
        else:
            return ""
        return "".join(t.get("plain_text", "") for t in texts)

    def _extract_select(self, prop: dict[str, Any]) -> str:
        """Extract value from select property."""
        select = prop.get("select")
        return select.get("name", "") if select else ""

    def _extract_multi_select(self, prop: dict[str, Any]) -> list[str]:
        """Extract values from multi_select property."""
        return [item.get("name", "") for item in prop.get("multi_select", [])]

    def _normalize_field(self, value: Any, field_config: Any) -> Any:
        """Apply normalization rules to a field value."""
        if field_config is None:
            return value

        for func_name in field_config.normalize:
            value = self._apply_normalizer(value, func_name)

        return value

    def _apply_normalizer(self, value: Any, func_name: str) -> Any:
        """Apply a single normalization function."""
        if func_name == "trim" and isinstance(value, str):
            return value.strip()
        if func_name == "collapse_whitespace" and isinstance(value, str):
            return re.sub(r"\s+", " ", value)
        if func_name == "lowercase" and isinstance(value, str):
            return value.lower()
        if func_name == "slug" and isinstance(value, str):
            return self._to_slug(value)
        if func_name == "deduplicate" and isinstance(value, list):
            seen = set()
            return [x for x in value if not (x in seen or seen.add(x))]
        return value

    def _to_slug(self, value: str) -> str:
        """Convert string to URL-safe slug."""
        value = value.lower().strip()
        value = re.sub(r"[^\w\s-]", "", value)
        value = re.sub(r"[\s_-]+", "-", value)
        return value.strip("-") or "uncategorized"

    def _parse_datetime(self, value: str | None) -> datetime:
        """Parse ISO 8601 datetime and convert to output timezone."""
        if not value:
            return datetime.now(self._output_tz)

        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=self._input_tz)
        return dt.astimezone(self._output_tz)
