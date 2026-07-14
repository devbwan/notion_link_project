"""Tests for transformer module."""

from __future__ import annotations

from notion_link.transformer import Transformer


class TestTransformer:
    """Tests for Transformer class."""

    def test_transform_basic(self, sample_config, sample_page):
        """Transform should produce correct PageRecord."""
        transformer = Transformer(sample_config)
        record = transformer.transform(sample_page)

        assert record.notion_page_id == "01234567-89ab-cdef-0123-456789abcdef"
        assert record.title == "테스트 회의록"
        assert record.category == "meeting"
        assert record.content == "회의 내용입니다."
        assert record.tags == ["개발", "일정"]
        assert record.format == "markdown"

    def test_transform_normalizes_category(self, sample_config, sample_page):
        """Category should be lowercased."""
        sample_page["properties"]["분류"]["select"]["name"] = "MEETING"
        transformer = Transformer(sample_config)
        record = transformer.transform(sample_page)

        assert record.category == "meeting"

    def test_transform_whitespace_in_title(self, sample_config, sample_page):
        """Title whitespace should be collapsed."""
        sample_page["properties"]["제목"]["title"] = [{"plain_text": "  여러   공백   테스트  "}]
        transformer = Transformer(sample_config)
        record = transformer.transform(sample_page)

        assert record.title == "여러 공백 테스트"

    def test_transform_deduplicates_tags(self, sample_config, sample_page):
        """Duplicate tags should be removed."""
        sample_page["properties"]["태그"]["multi_select"] = [
            {"name": "개발"},
            {"name": "일정"},
            {"name": "개발"},
        ]
        transformer = Transformer(sample_config)
        record = transformer.transform(sample_page)

        assert record.tags == ["개발", "일정"]

    def test_transform_default_format(self, sample_config, sample_page):
        """Missing format should use default."""
        sample_page["properties"]["출력 형식"]["select"] = None
        transformer = Transformer(sample_config)
        record = transformer.transform(sample_page)

        assert record.format == "markdown"
