"""Pytest fixtures for notion_link tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from notion_link.config import MappingsConfig


@pytest.fixture
def sample_config() -> MappingsConfig:
    """Load the default mappings config."""
    config_path = Path(__file__).parent.parent / "config" / "mappings.yaml"
    import yaml

    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return MappingsConfig.model_validate(data)


@pytest.fixture
def sample_page() -> dict:
    """Sample Notion page response."""
    return {
        "id": "01234567-89ab-cdef-0123-456789abcdef",
        "created_time": "2024-01-15T10:00:00.000Z",
        "last_edited_time": "2024-01-15T12:30:00.000Z",
        "properties": {
            "제목": {
                "type": "title",
                "title": [{"plain_text": "테스트 회의록"}],
            },
            "상태": {
                "type": "status",
                "status": {"name": "변환 요청"},
            },
            "분류": {
                "type": "select",
                "select": {"name": "meeting"},
            },
            "본문": {
                "type": "rich_text",
                "rich_text": [{"plain_text": "회의 내용입니다."}],
            },
            "태그": {
                "type": "multi_select",
                "multi_select": [{"name": "개발"}, {"name": "일정"}],
            },
            "출력 형식": {
                "type": "select",
                "select": {"name": "markdown"},
            },
            "생성일": {
                "type": "created_time",
                "created_time": "2024-01-15T10:00:00.000Z",
            },
            "수정일": {
                "type": "last_edited_time",
                "last_edited_time": "2024-01-15T12:30:00.000Z",
            },
        },
    }


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Create a temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir
