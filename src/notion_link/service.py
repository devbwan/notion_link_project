"""Main sync service orchestrating the processing flow."""

from __future__ import annotations

import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from .document_extractor import DocumentExtractor
from .fetcher import Fetcher
from .models import ProcessingResult
from .state_store import StateStore
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
        self._fetcher = Fetcher(client)
        self._extractor = DocumentExtractor(config)
        self._writer = Writer(config)
        # State storage is initialized lazily so constructing the service, and in
        # particular running a dry-run, does not create a local database.
        self._state: StateStore | None = None

    def _get_state(self) -> StateStore:
        """Return the state store, creating it only for a mutating sync."""
        if self._state is None:
            self._state = StateStore()
        return self._state

    def sync(self, *, dry_run: bool = False) -> list[ProcessingResult]:
        """Run the sync process.

        Returns list of processing results.
        Exit codes: 0 = all success, 2 = partial failure, 3 = lock conflict
        """
        if dry_run:
            return self._run_sync(dry_run=True)

        lock_path = Path(self._config.output.root) / ".sync.lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)

        with open(lock_path, "wb") as lock_file:
            try:
                _lock_file(lock_file)
            except OSError:
                logger.error("Another sync process is running")
                raise SystemExit(3) from None

            try:
                return self._run_sync(dry_run=dry_run)
            finally:
                _unlock_file(lock_file)

    def _run_sync(self, *, dry_run: bool) -> list[ProcessingResult]:
        """Execute the sync logic."""
        page_id = self._env.notion_page_id
        logger.info(f"Reading Notion document: ...{page_id[-8:]}")
        page, blocks = self._fetcher.fetch_document(page_id)
        result = self._process_document(page, blocks, dry_run=dry_run)
        results = [result]

        if not dry_run:
            self._get_state().mark_seen([r.notion_page_id for r in results])

        success_count = sum(1 for r in results if r.status == "success")
        error_count = sum(1 for r in results if r.status == "error")
        logger.info(f"Processed: {success_count} success, {error_count} error")

        return results

    def _process_document(
        self, page: dict, blocks: list[dict], *, dry_run: bool
    ) -> ProcessingResult:
        """Extract and write a single Notion document."""
        page_id = page["id"]
        last_edited = page.get("last_edited_time", "")
        now = datetime.now(UTC)

        logger.debug(f"Processing page {page_id[-8:]}")

        try:
            record = self._extractor.extract(page, blocks)

            if dry_run:
                logger.info(f"[DRY-RUN] Would write: {record.notion_page_id}")
                return ProcessingResult(
                    notion_page_id=page_id,
                    status="success",
                    processed_at=now,
                )

            state = self._get_state()
            if state.is_unchanged(page_id, last_edited):
                logger.debug(f"Page {page_id[-8:]} unchanged, skipping")
                return ProcessingResult(
                    notion_page_id=page_id,
                    status="success",
                    processed_at=now,
                )

            path, content_hash = self._writer.write(record)

            state.save_success(
                page_id,
                last_edited,
                content_hash,
                str(path),
            )

            logger.info(f"Wrote {path}")

            return ProcessingResult(
                notion_page_id=page_id,
                status="success",
                output_path=str(path),
                content_hash=content_hash,
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
        self._get_state().save_error(page_id, last_edited, message)
