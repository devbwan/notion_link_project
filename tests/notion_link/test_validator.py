"""Tests for validator module."""

from __future__ import annotations

import pytest

from notion_link.validator import ValidationError, Validator


class TestValidator:
    """Tests for Validator class."""

    def test_validate_valid_page(self, sample_config, sample_page):
        """Valid page should pass validation."""
        validator = Validator(sample_config)
        validator.validate(sample_page)

    def test_validate_missing_title(self, sample_config, sample_page):
        """Missing title should raise ValidationError."""
        validator = Validator(sample_config)
        del sample_page["properties"]["제목"]

        with pytest.raises(ValidationError) as exc_info:
            validator.validate(sample_page)

        assert "제목" in str(exc_info.value)

    def test_validate_empty_title(self, sample_config, sample_page):
        """Empty title should raise ValidationError."""
        validator = Validator(sample_config)
        sample_page["properties"]["제목"]["title"] = [{"plain_text": "  "}]

        with pytest.raises(ValidationError) as exc_info:
            validator.validate(sample_page)

        assert "empty" in str(exc_info.value).lower()

    def test_validate_missing_content(self, sample_config, sample_page):
        """Missing content should raise ValidationError."""
        validator = Validator(sample_config)
        del sample_page["properties"]["본문"]

        with pytest.raises(ValidationError) as exc_info:
            validator.validate(sample_page)

        assert "본문" in str(exc_info.value)

    def test_validate_optional_tags_missing(self, sample_config, sample_page):
        """Missing optional tags should pass validation."""
        validator = Validator(sample_config)
        del sample_page["properties"]["태그"]

        validator.validate(sample_page)
