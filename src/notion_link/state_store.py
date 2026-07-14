"""State storage for tracking processed pages."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


class StateStore:
    """SQLite-based state storage for processed pages."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or Path(".state/notion-link.db")
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS processed_pages (
                    notion_page_id TEXT PRIMARY KEY,
                    last_edited_time TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    output_path TEXT NOT NULL,
                    processed_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    last_seen_at TEXT,
                    orphaned_at TEXT
                )
            """)
            conn.commit()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """Create a database connection."""
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def get(self, page_id: str) -> dict | None:
        """Get processing record for a page."""
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT * FROM processed_pages WHERE notion_page_id = ?",
                (page_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def is_unchanged(self, page_id: str, last_edited_time: str) -> bool:
        """Check if page hasn't changed since last processing."""
        record = self.get(page_id)
        if not record:
            return False
        return record["last_edited_time"] == last_edited_time

    def save_success(
        self,
        page_id: str,
        last_edited_time: str,
        content_hash: str,
        output_path: str,
    ) -> None:
        """Record successful processing."""
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO processed_pages
                (notion_page_id, last_edited_time, content_hash, output_path,
                 processed_at, status, error_message, last_seen_at, orphaned_at)
                VALUES (?, ?, ?, ?, ?, 'success', NULL, ?, NULL)
                """,
                (page_id, last_edited_time, content_hash, output_path, now, now),
            )
            conn.commit()

    def save_error(self, page_id: str, last_edited_time: str, error_message: str) -> None:
        """Record failed processing."""
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO processed_pages
                (notion_page_id, last_edited_time, content_hash, output_path,
                 processed_at, status, error_message, last_seen_at, orphaned_at)
                VALUES (?, ?, '', '', ?, 'error', ?, ?, NULL)
                """,
                (page_id, last_edited_time, now, error_message, now),
            )
            conn.commit()

    def mark_seen(self, page_ids: list[str]) -> None:
        """Update last_seen_at for pages still in Notion."""
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.executemany(
                "UPDATE processed_pages SET last_seen_at = ? WHERE notion_page_id = ?",
                [(now, pid) for pid in page_ids],
            )
            conn.commit()
