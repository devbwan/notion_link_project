"""Command-line interface."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .config import load_env, load_mappings
from .notion_client import NotionClient
from .service import SyncService


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for console and file output."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_format = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_format)

    file_handler = logging.FileHandler(log_dir / "notion-link.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    file_handler.setFormatter(file_format)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


def cmd_sync(args: argparse.Namespace) -> int:
    """Execute sync command."""
    config_path = Path(args.config) if args.config else None
    config = load_mappings(config_path)
    env = load_env()

    with NotionClient(env.notion_token) as client:
        service = SyncService(client, env, config)
        results = service.sync(dry_run=args.dry_run)

    errors = [r for r in results if r.status == "error"]
    return 2 if errors else 0


def cmd_validate_config(args: argparse.Namespace) -> int:
    """Execute validate-config command."""
    logger = logging.getLogger(__name__)

    try:
        config_path = Path(args.config) if args.config else None
        load_mappings(config_path)
        logger.info("Configuration is valid")

        env = load_env()
        logger.info(f"Page ID: ...{env.notion_page_id[-8:]}")

        return 0

    except Exception as e:
        logger.error(f"Configuration error: {e}")
        return 1


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="notion-link",
        description="Notion database to local file converter",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug output")

    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser("sync", help="Sync Notion pages to local files")
    sync_parser.add_argument("--dry-run", action="store_true", help="Preview without changes")
    sync_parser.add_argument("--config", help="Path to mappings config file")

    validate_parser = subparsers.add_parser("validate-config", help="Validate configuration")
    validate_parser.add_argument("--config", help="Path to mappings config file")

    args = parser.parse_args()

    setup_logging(args.verbose)

    if args.command == "sync":
        sys.exit(cmd_sync(args))
    elif args.command == "validate-config":
        sys.exit(cmd_validate_config(args))


if __name__ == "__main__":
    main()
