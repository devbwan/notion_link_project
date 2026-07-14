"""Configuration loading and validation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator


class DocumentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str = "notion"
    format: Literal["markdown", "json", "csv"] = "markdown"


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


class MappingsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int
    document: DocumentConfig = Field(default_factory=DocumentConfig)
    output: OutputConfig

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: int) -> int:
        if v != 1:
            raise ValueError("Only version 1 is supported")
        return v


class EnvConfig(BaseModel):
    notion_token: str
    notion_page_id: str

    @field_validator("notion_page_id")
    @classmethod
    def normalize_page_id(cls, v: str) -> str:
        """Convert 32-char hex to UUID format (8-4-4-4-12)."""
        v = v.replace("-", "")
        if len(v) != 32:
            raise ValueError("Page ID must be 32 hex characters")
        return f"{v[:8]}-{v[8:12]}-{v[12:16]}-{v[16:20]}-{v[20:]}"


def load_env() -> EnvConfig:
    """Load environment variables."""
    from dotenv import load_dotenv

    load_dotenv()

    return EnvConfig(
        notion_token=os.environ["NOTION_TOKEN"],
        notion_page_id=os.environ["NOTION_PAGE_ID"],
    )


def load_mappings(path: Path | None = None) -> MappingsConfig:
    """Load and validate mappings configuration."""
    if path is None:
        path = Path("config/mappings.yaml")

    with open(path, encoding="utf-8") as f:
        data: Any = yaml.safe_load(f)

    return MappingsConfig.model_validate(data)
