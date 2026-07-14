# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Notion database to local file converter. Syncs pages from a Notion database to local Markdown, JSON, or CSV files.

## Build/Test/Lint Commands

```powershell
# Install dependencies
python -m pip install -e ".[dev]"

# Run tests
pytest

# Run single test
pytest tests/notion_link/test_validator.py::TestValidator::test_validate_valid_page

# Lint
ruff check .

# Validate config
python -m notion_link validate-config

# Sync (dry run)
python -m notion_link sync --dry-run

# Sync
python -m notion_link sync
```

## Project Structure

```
src/notion_link/       — main package
  config.py            — configuration loading/validation (Pydantic models)
  models.py            — data models (NotionPage, PageRecord, ProcessingResult)
  notion_client.py     — Notion API HTTP client (httpx)
  fetcher.py           — query pages with 'request' status
  validator.py         — validate required properties
  transformer.py       — convert Notion page to PageRecord
  writer.py            — serialize and write to files
  state_store.py       — SQLite state tracking
  service.py           — orchestrates sync flow
  cli.py               — CLI entry point
tests/notion_link/     — unit tests (pytest)
config/mappings.yaml   — field mapping configuration
```

## Key Patterns

- **Notion API version**: `2026-03-11` (constant in notion_client.py)
- **HTTP client**: httpx with 10s connect / 30s read timeout
- **State storage**: SQLite in `.state/notion-link.db`
- **Atomic writes**: temp file + rename pattern in writer.py
- **File locking**: fcntl for sync lock (`output/.sync.lock`)

## Configuration

- `config/mappings.yaml` — field mapping, status values, output format
- `.env` — `NOTION_TOKEN`, `NOTION_DATABASE_ID`, optional `NOTION_DATA_SOURCE_ID`

## Testing

- Use `pytest-httpx` for mocking Notion API calls
- Tests must not call live Notion services
- Fixtures in `tests/conftest.py`

## Security

Never commit tokens or real database IDs. Use `.env.example` as template.

---

## Behavioral Guidelines

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 0. Language Rule (언어 규칙)

* **Always respond in Korean (한국어).** All explanations, discussions, and clarification questions must be written in Korean, regardless of the language used in the prompt. Code snippets, variable names, and technical terms should remain in English as standard practice.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:

* State your assumptions explicitly. If uncertain, ask.
* If multiple interpretations exist, present them - don't pick silently.
* If a simpler approach exists, say so. Push back when warranted.
* If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

* No features beyond what was asked.
* No abstractions for single-use code.
* No "flexibility" or "configurability" that wasn't requested.
* No error handling for impossible scenarios.
* If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:

* Don't "improve" adjacent code, comments, or formatting.
* Don't refactor things that aren't broken.
* Match existing style, even if you'd do it differently.
* If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:

* Remove imports/variables/functions that YOUR changes made unused.
* Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:

* "Add validation" → "Write tests for invalid inputs, then make them pass"
* "Fix the bug" → "Write a test that reproduces it, then make it pass"
* "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]

```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.