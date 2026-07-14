"""Tests for Notion block-to-document extraction."""

from notion_link.document_extractor import DocumentExtractor

from .test_service import document_blocks, document_page


def test_extracts_title_and_markdown_content(sample_config) -> None:
    record = DocumentExtractor(sample_config).extract(document_page(), document_blocks())

    assert record.title == "프로젝트 문서"
    assert record.category == "notion"
    assert record.content == "## 개요\n\n문서 본문입니다."


def test_extracts_lists_todos_and_code(sample_config) -> None:
    blocks = [
        {
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"plain_text": "항목"}]},
        },
        {
            "type": "to_do",
            "to_do": {"checked": True, "rich_text": [{"plain_text": "완료"}]},
        },
        {
            "type": "code",
            "code": {"language": "python", "rich_text": [{"plain_text": "print(1)"}]},
        },
    ]

    record = DocumentExtractor(sample_config).extract(document_page(), blocks)

    assert "- 항목" in record.content
    assert "- [x] 완료" in record.content
    assert "```python\nprint(1)\n```" in record.content
