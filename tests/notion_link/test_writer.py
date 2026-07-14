"""Tests for writer module."""

from __future__ import annotations

from datetime import UTC, datetime

from notion_link.models import PageRecord
from notion_link.writer import Writer


class TestWriter:
    """Tests for Writer class."""

    def test_write_markdown(self, sample_config, temp_output_dir):
        """Write should create markdown file with front matter."""
        writer = Writer(sample_config, temp_output_dir)
        record = PageRecord(
            notion_page_id="01234567-89ab-cdef-0123-456789abcdef",
            title="테스트 제목",
            category="meeting",
            content="본문 내용",
            tags=["개발", "일정"],
            format="markdown",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        path, _ = writer.write(record)

        assert path.exists()
        assert path.suffix == ".md"
        content = path.read_text(encoding="utf-8")
        assert "type: meeting" in content
        assert "# 테스트 제목" in content
        assert "본문 내용" in content

    def test_write_json(self, sample_config, temp_output_dir):
        """Write should create JSON file."""
        writer = Writer(sample_config, temp_output_dir)
        record = PageRecord(
            notion_page_id="01234567-89ab-cdef-0123-456789abcdef",
            title="테스트 제목",
            category="meeting",
            content="본문 내용",
            tags=["개발"],
            format="json",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        path, _ = writer.write(record)

        assert path.exists()
        assert path.suffix == ".json"

        import json

        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["type"] == "meeting"
        assert data["title"] == "테스트 제목"

    def test_write_csv(self, sample_config, temp_output_dir):
        """Write should create CSV file with header."""
        writer = Writer(sample_config, temp_output_dir)
        record = PageRecord(
            notion_page_id="01234567-89ab-cdef-0123-456789abcdef",
            title="테스트 제목",
            category="meeting",
            content="본문 내용",
            tags=["개발", "일정"],
            format="csv",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        path, _ = writer.write(record)

        assert path.exists()
        assert path.suffix == ".csv"
        content = path.read_text(encoding="utf-8")
        assert "type,title,content,tags,notion_page_id" in content
        assert "개발|일정" in content

    def test_write_idempotent(self, sample_config, temp_output_dir):
        """Writing same content should not modify file."""
        writer = Writer(sample_config, temp_output_dir)
        record = PageRecord(
            notion_page_id="01234567-89ab-cdef-0123-456789abcdef",
            title="테스트",
            category="meeting",
            content="내용",
            tags=[],
            format="markdown",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        path1, hash1 = writer.write(record)
        mtime1 = path1.stat().st_mtime

        path2, hash2 = writer.write(record)

        assert path1 == path2
        assert hash1 == hash2
        assert path2.stat().st_mtime == mtime1

    def test_write_path_template(self, sample_config, temp_output_dir):
        """Output path should follow template."""
        writer = Writer(sample_config, temp_output_dir)
        record = PageRecord(
            notion_page_id="01234567-89ab-cdef-0123-456789abcdef",
            title="테스트",
            category="Project Notes",
            content="내용",
            tags=[],
            format="markdown",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        path, _ = writer.write(record)

        expected = temp_output_dir / "project-notes" / "01234567-89ab-cdef-0123-456789abcdef.md"
        assert path == expected
