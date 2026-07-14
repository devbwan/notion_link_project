"""Write output files in various formats."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from .models import PageRecord

if TYPE_CHECKING:
    from .config import MappingsConfig


class Writer:
    """Writes PageRecord to local files."""

    def __init__(self, config: MappingsConfig, root: Path | None = None) -> None:
        self._config = config
        self._root = root or Path(config.output.root)

    def write(self, record: PageRecord) -> tuple[Path, str]:
        """Write record to file and return (path, content_hash).

        Uses atomic write with temp file + rename.
        """
        content = self._serialize(record)
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

        path = self._resolve_path(record)

        if path.exists():
            existing_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            if existing_hash == content_hash:
                return path, content_hash

        path.parent.mkdir(parents=True, exist_ok=True)

        fd, temp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
        try:
            with open(fd, "w", encoding="utf-8") as f:
                f.write(content)
            Path(temp_path).replace(path)
        except Exception:
            Path(temp_path).unlink(missing_ok=True)
            raise

        return path, content_hash

    def _resolve_path(self, record: PageRecord) -> Path:
        """Resolve output path from template."""
        ext_map = {"markdown": "md", "json": "json", "csv": "csv"}
        extension = ext_map.get(record.format, "md")

        category_slug = self._to_slug(record.category)

        path_str = self._config.output.path_template.format(
            category=category_slug,
            page_id=record.notion_page_id,
            extension=extension,
        )

        return self._root / path_str

    def _to_slug(self, value: str) -> str:
        """Convert to filesystem-safe slug."""
        import re

        value = value.lower().strip()
        value = re.sub(r"[^\w\s-]", "", value)
        value = re.sub(r"[\s_-]+", "-", value)
        return value.strip("-") or "uncategorized"

    def _serialize(self, record: PageRecord) -> str:
        """Serialize record to string based on format."""
        if record.format == "json":
            return self._to_json(record)
        if record.format == "csv":
            return self._to_csv(record)
        return self._to_markdown(record)

    def _to_markdown(self, record: PageRecord) -> str:
        """Convert record to Markdown with YAML front matter."""
        lines = ["---"]
        lines.append(f"type: {record.category}")

        if record.tags or self._config.output.empty_values == "null":
            if record.tags:
                lines.append("tags:")
                for tag in record.tags:
                    lines.append(f"  - {tag}")
            elif self._config.output.empty_values == "null":
                lines.append("tags: null")

        lines.append(f"notion_page_id: {record.notion_page_id}")
        lines.append("---")
        lines.append("")
        lines.append(f"# {record.title}")
        lines.append("")
        lines.append(record.content)
        lines.append("")

        return "\n".join(lines)

    def _to_json(self, record: PageRecord) -> str:
        """Convert record to JSON."""
        data: dict = {
            "type": record.category,
            "title": record.title,
            "content": record.content,
        }

        if record.tags or self._config.output.empty_values == "null":
            data["tags"] = record.tags if record.tags else None

        data["source"] = {
            "provider": "notion",
            "page_id": record.notion_page_id,
        }

        return json.dumps(data, ensure_ascii=False, indent=2) + "\n"

    def _to_csv(self, record: PageRecord) -> str:
        """Convert record to CSV row."""
        csv_config = self._config.output.csv
        sep = csv_config.multi_value_separator

        row = {
            "type": record.category,
            "title": record.title,
            "content": record.content,
            "tags": sep.join(record.tags),
            "notion_page_id": record.notion_page_id,
        }

        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=csv_config.columns,
            extrasaction="ignore",
        )

        if csv_config.include_header:
            writer.writeheader()
        writer.writerow(row)

        return output.getvalue()
