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
def temp_output_dir(tmp_path: Path) -> Path:
    """Create a temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir
