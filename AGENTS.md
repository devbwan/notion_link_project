# Repository Guidelines

## Project Structure & Module Organization

This repository is currently a clean scaffold with no source tree or build system. Keep the root uncluttered as the project grows. Place application code in `src/`, automated tests in `tests/`, static resources in `assets/`, and project documentation in `docs/`. Mirror source paths in the test tree where practical; for example, tests for `src/notion/links.py` should live in `tests/notion/test_links.py`. Keep configuration files at the root only when required by the selected toolchain.

## Build, Test, and Development Commands

No build, test, or package-management commands are configured yet. When introducing a toolchain, add its canonical commands to the README and keep them reproducible from a fresh clone. Prefer a small, discoverable command surface, such as:

- `npm run dev` — start a local development server.
- `npm test` — run the complete automated test suite.
- `npm run lint` — check formatting and static-analysis rules.

These are examples, not currently available commands. Commit the relevant manifest and lockfile together when adding dependencies.

## Coding Style & Naming Conventions

Follow the formatter and linter conventions of the language adopted by the project, and commit their configuration. Use spaces rather than tabs unless the formatter requires otherwise. Choose descriptive names: `snake_case` for Python modules and functions, `camelCase` for JavaScript/TypeScript variables and functions, and `PascalCase` for classes and UI components. Keep modules focused and avoid committing generated output, local caches, or secrets.

## Testing Guidelines

Add tests with every behavior change and regression fix. Use the ecosystem-standard framework chosen with the initial implementation. Name tests after observable behavior, and keep unit tests deterministic and independent of live Notion services. Put credentials and network-dependent cases behind explicit integration-test configuration. Document the test command and any coverage threshold once established.

## Commit & Pull Request Guidelines

There is no existing commit history from which to infer a convention. Use short, imperative subjects, optionally following Conventional Commits (for example, `feat: add Notion URL parser` or `fix: reject malformed page IDs`). Pull requests should explain the problem and solution, list verification performed, link relevant issues, and include screenshots or sample output for user-visible changes. Keep each PR focused and call out configuration changes or breaking behavior clearly.

## Security & Configuration

Never commit Notion tokens, database IDs, or `.env` files. Provide sanitized examples in `.env.example`, use least-privilege integrations, and redact sensitive URLs and identifiers from fixtures and logs.
