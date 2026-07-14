# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Notion link integration project. Currently scaffolded with no source code or build system yet.

## Build/Test/Lint Commands

No commands configured yet. When toolchain is established, expect:
- `npm run dev` or `python -m src.main` — start local development
- `npm test` or `pytest` — run test suite
- `npm run lint` or `ruff check` — run linter

## Project Structure

```
src/           — application code
tests/         — automated tests (mirror src paths, e.g., tests/notion/test_links.py)
assets/        — static resources
docs/          — documentation
```

Configuration files stay at root only when required by toolchain.

## Coding Style

- Python: `snake_case` for modules/functions
- JavaScript/TypeScript: `camelCase` for variables/functions
- Classes: `PascalCase`
- Follow project's formatter/linter configuration

## Testing

- Add tests with every behavior change
- Unit tests must be deterministic, no live Notion services
- Put Notion API calls behind explicit integration-test configuration
- Name tests after observable behavior

## Security

Never commit Notion tokens, database IDs, or `.env` files. Use `.env.example` for templates. Redact sensitive URLs and identifiers from fixtures and logs.

## Behavioral Guidelines

### Think Before Coding
- State assumptions explicitly; if uncertain, ask
- If multiple interpretations exist, present them
- If a simpler approach exists, say so
- If something is unclear, stop and ask

### Simplicity First
- No features beyond what was asked
- No abstractions for single-use code
- No "flexibility" that wasn't requested
- If 200 lines could be 50, rewrite it

### Surgical Changes
- Don't "improve" adjacent code, comments, or formatting
- Don't refactor things that aren't broken
- Match existing style
- Remove only imports/variables YOUR changes made unused

### Goal-Driven Execution
Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
