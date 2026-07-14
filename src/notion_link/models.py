"""Input and output data models."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class NotionPage(BaseModel):
    """Raw page data from Notion API."""

    id: str
    created_time: datetime
    last_edited_time: datetime
    properties: dict


class PageRecord(BaseModel):
    """Normalized internal representation of a page."""

    notion_page_id: str
    title: str
    category: str
    content: str
    tags: list[str] = []
    format: Literal["markdown", "json", "csv"] = "markdown"
    created_at: datetime
    updated_at: datetime


class ProcessingResult(BaseModel):
    """Result of processing a single page."""

    notion_page_id: str
    status: Literal["success", "error"]
    output_path: str | None = None
    content_hash: str | None = None
    error_message: str | None = None
    processed_at: datetime
