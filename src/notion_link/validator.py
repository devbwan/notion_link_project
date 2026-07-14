"""Input validation for Notion page data."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .config import MappingsConfig


class ValidationError(Exception):
    """Raised when page validation fails."""

    def __init__(self, page_id: str, message: str) -> None:
        self.page_id = page_id
        self.message = message
        super().__init__(f"Page {page_id}: {message}")


class Validator:
    """Validates Notion page properties against configuration."""

    def __init__(self, config: MappingsConfig) -> None:
        self._config = config

    def validate(self, page: dict[str, Any]) -> None:
        """Validate a page's properties.

        Raises ValidationError if validation fails.
        """
        page_id = page.get("id", "unknown")
        properties = page.get("properties", {})

        for _field_name, field_config in self._config.fields.items():
            if not field_config.required:
                continue

            source = field_config.source
            notion_prop_name = getattr(self._config.notion.properties, source)
            prop = properties.get(notion_prop_name)

            if prop is None:
                raise ValidationError(page_id, f"Missing required property: {notion_prop_name}")

            value = self._extract_value(prop)
            if value is None or (isinstance(value, str) and not value.strip()):
                raise ValidationError(
                    page_id, f"Required property is empty: {notion_prop_name}"
                )

    def _extract_value(self, prop: dict[str, Any]) -> Any:
        """Extract value from a Notion property based on its type."""
        prop_type = prop.get("type")

        if prop_type == "title":
            texts = prop.get("title", [])
            return "".join(t.get("plain_text", "") for t in texts)

        if prop_type == "rich_text":
            texts = prop.get("rich_text", [])
            return "".join(t.get("plain_text", "") for t in texts)

        if prop_type == "select":
            select = prop.get("select")
            return select.get("name") if select else None

        if prop_type == "multi_select":
            return [item.get("name") for item in prop.get("multi_select", [])]

        if prop_type == "status":
            status = prop.get("status")
            return status.get("name") if status else None

        if prop_type in ("created_time", "last_edited_time"):
            return prop.get(prop_type)

        return None
