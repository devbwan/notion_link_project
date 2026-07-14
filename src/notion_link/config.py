"""Configuration loading and validation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator


class NotionPropertiesConfig(BaseModel):
    title: str
    status: str
    category: str
    content: str
    tags: str
    format: str
    created_at: str
    updated_at: str
    error_message: str


class NotionStatusesConfig(BaseModel):
    draft: str
    request: str
    success: str
    error: str


class NotionConfig(BaseModel):
    properties: NotionPropertiesConfig
    statuses: NotionStatusesConfig
    write_status: bool = True


class FieldConfig(BaseModel):
    source: str
    required: bool
    normalize: list[str] = Field(default_factory=list)


class CsvConfig(BaseModel):
    columns: list[str]
    multi_value_separator: str = "|"
    encoding: str = "utf-8"
    include_header: bool = True


class OutputConfig(BaseModel):
    default_format: str = "markdown"
    allowed_formats: list[str] = Field(default_factory=lambda: ["markdown", "json", "csv"])
    root: str = "output"
    path_template: str = "{category}/{page_id}.{extension}"
    empty_values: str = "omit"
    csv: CsvConfig

    @field_validator("default_format")
    @classmethod
    def validate_default_format(cls, v: str) -> str:
        allowed = {"markdown", "json", "csv"}
        if v not in allowed:
            raise ValueError(f"default_format must be one of {allowed}")
        return v


class DatetimeConfig(BaseModel):
    input_timezone: str = "Asia/Seoul"
    output_timezone: str = "UTC"
    format: str = "iso8601"


class MappingsConfig(BaseModel):
    version: int
    notion: NotionConfig
    fields: dict[str, FieldConfig]
    output: OutputConfig
    datetime: DatetimeConfig

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: int) -> int:
        if v != 1:
            raise ValueError("Only version 1 is supported")
        return v


class EnvConfig(BaseModel):
    notion_token: str
    notion_database_id: str
    notion_data_source_id: str | None = None


def load_env() -> EnvConfig:
    """Load environment variables."""
    from dotenv import load_dotenv

    load_dotenv()

    return EnvConfig(
        notion_token=os.environ["NOTION_TOKEN"],
        notion_database_id=os.environ["NOTION_DATABASE_ID"],
        notion_data_source_id=os.environ.get("NOTION_DATA_SOURCE_ID"),
    )


def load_mappings(path: Path | None = None) -> MappingsConfig:
    """Load and validate mappings configuration."""
    if path is None:
        path = Path("config/mappings.yaml")

    with open(path, encoding="utf-8") as f:
        data: Any = yaml.safe_load(f)

    return MappingsConfig.model_validate(data)
