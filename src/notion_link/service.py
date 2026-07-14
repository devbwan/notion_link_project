"""Main sync service orchestrating the processing flow."""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from .fetcher import Fetcher
from .models import ProcessingResult
from .state_store import StateStore
from .transformer import Transformer
from .validator import ValidationError, Validator
from .writer import Writer

if TYPE_CHECKING:
    from typing import BinaryIO

    from .config import EnvConfig, MappingsConfig
    from .notion_client import NotionClient

logger = logging.getLogger(__name__)


def _lock_file(f: BinaryIO) -> None:
    """Acquire exclusive non-blocking lock on file."""
    if sys.platform == "win32":
        import msvcrt

        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl

        fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock_file(f: BinaryIO) -> None:
    """Release file lock."""
    if sys.platform == "win32":
        import msvcrt

        f.seek(0)
        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl

        fcntl.flock(f.fileno(), fcntl.LOCK_UN)


class SyncService:
    """Orchestrates the sync process from Notion to local files."""

    def __init__(
        self,
        client: NotionClient,
        env: EnvConfig,
        config: MappingsConfig,
    ) -> None:
        self._client = client
        self._env = env
        self._config = config
        self._fetcher = Fetcher(client, config)
        self._validator = Validator(config)
        self._transformer = Transformer(config)
        self._writer = Writer(config)
        self._state = StateStore()

    def sync(self, *, dry_run: bool = False) -> list[ProcessingResult]:
        """Run the sync process.

        Returns list of processing results.
        Exit codes: 0 = all success, 2 = partial failure, 3 = lock conflict
        """
        lock_path = Path("output/.sync.lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)

        with open(lock_path, "wb") as lock_file:
            try:
                _lock_file(lock_file)
            except OSError:
                logger.error("Another sync process is running")
                raise SystemExit(3)

            try:
                return self._run_sync(dry_run=dry_run)
            finally:
                _unlock_file(lock_file)

    def _run_sync(self, *, dry_run: bool) -> list[ProcessingResult]:
        """Execute the sync logic."""
        data_source_id = self._fetcher.resolve_data_source_id(
            self._env.notion_database_id,
            self._env.notion_data_source_id,
        )

        logger.info(f"Using data source: {data_source_id[-8:]}")

        pages = self._fetcher.fetch_request_pages(data_source_id)
        logger.info(f"Found {len(pages)} pages to process")

        results: list[ProcessingResult] = []

        for page in pages:
            result = self._process_page(page, dry_run=dry_run)
            results.append(result)

        self._state.mark_seen([r.notion_page_id for r in results])

        success_count = sum(1 for r in results if r.status == "success")
        error_count = sum(1 for r in results if r.status == "error")
        logger.info(f"Processed: {success_count} success, {error_count} error")

        return results

    def _process_page(self, page: dict, *, dry_run: bool) -> ProcessingResult:
        """Process a single page."""
        page_id = page["id"]
        last_edited = page.get("last_edited_time", "")
        now = datetime.now(timezone.utc)

        logger.debug(f"Processing page {page_id[-8:]}")

        try:
            self._validator.validate(page)
            record = self._transformer.transform(page)

            if dry_run:
                logger.info(f"[DRY-RUN] Would write: {record.notion_page_id}")
                return ProcessingResult(
                    notion_page_id=page_id,
                    status="success",
                    processed_at=now,
                )

            if self._state.is_unchanged(page_id, last_edited):
                logger.debug(f"Page {page_id[-8:]} unchanged, skipping")
                return ProcessingResult(
                    notion_page_id=page_id,
                    status="success",
                    processed_at=now,
                )

            path, content_hash = self._writer.write(record)

            self._state.save_success(
                page_id,
                last_edited,
                content_hash,
                str(path),
            )

            if self._config.notion.write_status:
                self._update_notion_status(page_id, "success")

            logger.info(f"Wrote {path}")

            return ProcessingResult(
                notion_page_id=page_id,
                status="success",
                output_path=str(path),
                content_hash=content_hash,
                processed_at=now,
            )

        except ValidationError as e:
            logger.warning(f"Validation failed for {page_id[-8:]}: {e.message}")
            self._handle_error(page_id, last_edited, e.message, dry_run=dry_run)
            return ProcessingResult(
                notion_page_id=page_id,
                status="error",
                error_message=e.message,
                processed_at=now,
            )

        except Exception as e:
            msg = str(e)[:200]
            logger.exception(f"Error processing {page_id[-8:]}")
            self._handle_error(page_id, last_edited, msg, dry_run=dry_run)
            return ProcessingResult(
                notion_page_id=page_id,
                status="error",
                error_message=msg,
                processed_at=now,
            )

    def _handle_error(
        self, page_id: str, last_edited: str, message: str, *, dry_run: bool
    ) -> None:
        """Handle processing error."""
        if dry_run:
            return
        self._state.save_error(page_id, last_edited, message)
        if self._config.notion.write_status:
            self._update_notion_status(page_id, "error", message)

    def _update_notion_status(
        self, page_id: str, status: str, error_message: str | None = None
    ) -> None:
        """Update page status in Notion."""
        props = self._config.notion.properties
        statuses = self._config.notion.statuses

        status_value = getattr(statuses, status)
        properties = {
            props.status: {"status": {"name": status_value}},
        }

        if error_message and props.error_message:
            properties[props.error_message] = {
                "rich_text": [{"text": {"content": error_message[:200]}}]
            }

        try:
            self._client.update_page(page_id, properties)
        except Exception:
            logger.exception(f"Failed to update Notion status for {page_id[-8:]}")
