# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**All instructions for Claude Code must live in this file (committed to the repo), not in external memory or user-level config.**

## Development Tooling Rules

- **Always use `uv` to invoke Python** for dev tooling (scripts, generators, one-off commands). Never use bare `python` or `python3`. Example: `uv run --python 3.12 --with pyyaml script.py`.

## Project Overview

Monorepo for the Sema4.ai Actions framework. Provides a system for extending AI agents with custom actions and MCP (Model Context Protocol) tools using Python. The Action Server hosts Python `@action`/`@tool` functions as REST APIs and MCP endpoints.

## Modules

- **action_server/** — Core Action Server: discovers/loads action packages, serves REST API + MCP endpoint + web UI
- **actions/** — `sema4ai-actions` library: `@action`, `@query` decorators and core action runtime
- **mcp/** — `sema4ai-mcp` library: `@tool`, `@resource`, `@prompt` MCP protocol decorators
- **common/** — `sema4ai-common` library: shared utilities
- **sema4ai-http-helper/** — HTTP library for enterprise networks (MITM proxy support)
- **build_common/** — Shared build utilities for creating signed executables
- **devutils/** — Development utilities, invoke task builder, test fixtures, linting config
- **templates/** — Action package templates for bootstrapping new projects

**Dependency flow:** `action_server` → `actions`, `mcp`, `common`, `http-helper`. `mcp` → `actions`. Each module is independently versioned and released.

## Build & Development Commands

**Prerequisites:** Install dev tools with `pip install -r devutils/requirements.txt` (installs Poetry + Invoke).

All module-level commands are run from within the module directory (e.g., `cd action_server`):

| Command | Description |
|---|---|
| `inv install` | Install project dependencies (creates .venv or uses active env) |
| `inv test` | Run all pytest tests |
| `inv test -t path/to/test.py::test_func` | Run a specific test |
| `inv lint` | Run ruff + isort + pylint |
| `inv pretty` | Auto-format code (ruff format + isort) |
| `inv typecheck` | Run mypy |
| `inv docs` | Generate API documentation |
| `inv check-all` | Run all checks (lint, typecheck, docs, tests) |
| `inv set-version <version>` | Bump version across relevant files |
| `inv make-release` | Create and push release git tag |

**Root-level tasks** (from repo root):
- `inv install` — Install all modules' dependencies sequentially
- `inv docs` — Generate docs for all modules
- `inv unreleased` — Compare local versions to PyPI

## Testing

- Framework: pytest. Tests live in `tests/` within each module.
- Run all: `inv test` from the module directory.
- Run one: `inv test -t tests/test_file.py::test_name`
- Tests run in parallel by default unless configured otherwise.

## Code Style

- **Formatter/Linter:** Ruff (line-length 88), isort (Black profile), pylint
- **Type checking:** mypy
- **Convention:** Private modules prefixed with underscore (`_private_module.py`). Public API exported from `__init__.py`.
- **Source layout:** `<module>/src/sema4ai/<package_name>/` for source, `<module>/tests/` for tests.

## CI/CD

GitHub Actions workflows in `.github/workflows/` are **auto-generated** by `_gen_workflows.py`. Do not edit `.yml` workflow files directly — edit the generator script and re-run it.

## Release Process

1. `inv set-version <version>` to bump version
2. `inv check-all` to validate
3. Commit to `master`
4. `inv make-release` to tag and push (triggers CI release workflow)

## Key Architectural Notes

- Action Server CLI entry point: `action_server/src/sema4ai/action_server/cli.py` (only public API of the module)
- Actions run in isolated Python subprocesses via a process pool
- `@action` (from `sema4ai.actions`) and `@tool` (from `sema4ai.mcp`) are interchangeable — both are discovered by Action Server
- Action metadata (type hints + docstrings) drives the generated OpenAPI spec and AI agent understanding
- `package.yaml` defines the reproducible Python environment for action packages (managed by RCC)
- Frontend is Vue.js + Vite in `action_server/frontend/`; built output is committed as `_static_contents.py`
- The `_static_contents.py` and `_oauth2_config.py` files in action_server are excluded from ruff formatting
