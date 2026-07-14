"""Fetch and filter pages from Notion."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import MappingsConfig
    from .notion_client import NotionClient


class Fetcher:
    """Fetches pages with 'request' status from Notion."""

    def __init__(self, client: NotionClient, config: MappingsConfig) -> None:
        self._client = client
        self._config = config

    def resolve_data_source_id(
        self, database_id: str, explicit_id: str | None = None
    ) -> str:
        """Resolve the data source ID for a database.

        If explicit_id is provided, validates it belongs to the database.
        Otherwise, auto-selects if exactly one data source exists.
        """
        db = self._client.get_database(database_id)
        data_sources = db.get("data_sources", [])

        if not data_sources:
            raise ValueError(f"No data sources found for database {database_id}")

        if explicit_id:
            ids = [ds["id"] for ds in data_sources]
            if explicit_id not in ids:
                raise ValueError(f"Data source {explicit_id} not found in database {database_id}")
            return explicit_id

        if len(data_sources) == 1:
            return data_sources[0]["id"]

        raise ValueError(
            f"Multiple data sources found ({len(data_sources)}). "
            "Set NOTION_DATA_SOURCE_ID explicitly."
        )

    def fetch_request_pages(self, data_source_id: str) -> list[dict]:
        """Fetch all pages with 'request' status."""
        status_prop = self._config.notion.properties.status
        request_value = self._config.notion.statuses.request

        filter_ = {
            "property": status_prop,
            "status": {"equals": request_value},
        }

        pages: list[dict] = []
        cursor: str | None = None

        while True:
            result = self._client.query_data_source(
                data_source_id,
                filter_=filter_,
                start_cursor=cursor,
            )
            pages.extend(result.get("results", []))

            if not result.get("has_more"):
                break
            cursor = result.get("next_cursor")

        return pages
