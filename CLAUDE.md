# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sema4.ai Actions is a Python monorepo that turns decorated Python functions (`@tool`, `@action`) into MCP tools and REST API endpoints via the Action Server. Users define functions with type hints and docstrings, and the Action Server auto-generates OpenAPI specs and exposes them over MCP (`/mcp`) and HTTP.

## Monorepo Modules

| Module | Package | Purpose |
|--------|---------|---------|
| `action_server/` | `sema4ai-action-server` | Core server: FastAPI/Uvicorn REST API, MCP endpoint, React web UI, SQLite run storage |
| `actions/` | `sema4ai-actions` | `@action` and `@query` decorators, action discovery, secret management |
| `mcp/` | `sema4ai-mcp` | `@tool`, `@resource`, `@prompt` MCP decorators |
| `common/` | `sema4ai-common` | Shared utilities |
| `sema4ai-http-helper/` | `sema4ai-http-helper` | Enterprise HTTP/HTTPS with SSL/proxy support |
| `build_common/` | `sema4ai-build-common` | PyInstaller build, signing, Go wrapper utilities |
| `devutils/` | `sema4ai-devutils` | Invoke tasks, Ruff config, docs generation |

## Build System

**Dependency management:** Poetry  
**Task runner:** Invoke (`inv` / `invoke`)  
**Initial setup:** `pip install -r devutils/requirements.txt`

### Common Commands (run from a module directory)

```bash
inv install              # Install dependencies for this module
inv install -u           # Update and install dependencies
inv devinstall           # Install with all sema4ai deps in develop mode
inv test                 # Run all tests (pytest)
inv test -t path/to/test.py::test_func  # Run a single test
inv lint                 # Lint with Ruff
inv pretty               # Auto-format with Ruff
inv typecheck            # Type-check with mypy
inv docs                 # Regenerate docs
inv check-all            # Run lint + typecheck + docs together
```

### Root-Level Commands

```bash
inv install              # Install all modules' environments
inv lock                 # Lock all modules' Poetry dependencies
inv docs                 # Regenerate docs for all modules
```

### Action Server-Specific Commands

```bash
inv build-frontend       # Build React frontend (Vite) into _static_contents.py
inv dev-frontend         # Run frontend dev server
inv build-executable     # Build signed binary via PyInstaller
inv build-oauth2-config  # Fetch and embed OAuth2 configs
inv test-not-integration # Run non-integration tests in parallel
inv test-binary          # Run integration tests against built binary
inv download-rcc         # Download RCC binary
```

### Frontend (action_server/frontend/)

```bash
npm ci --no-audit --no-fund
npm run build            # Production build
npm run dev              # Dev server
npm run test             # Vitest tests
```

## Code Style

- **Linter/formatter:** Ruff (config at `devutils/ruff.toml`, line-length=88)
- **Type checker:** mypy
- Source uses `src/` layout: e.g., `action_server/src/sema4ai/action_server/`
- Python namespace packages under `sema4ai.*`

## Architecture

### Action Server Request Flow

1. **Discovery:** `_actions_import.py` scans packages for `@action`/`@tool` decorated functions
2. **Schema generation:** Type hints and docstrings are parsed to generate OpenAPI specs
3. **Serving:** FastAPI app (`_app.py`) exposes REST routes (`_api_*.py` modules) and MCP endpoint
4. **Execution:** `_actions_process_pool.py` runs actions in isolated processes
5. **Storage:** SQLite database (`_database.py`) with migrations tracks runs and results
6. **Web UI:** React frontend served as embedded static content (`_static_contents.py`)

### Key Patterns

- `@action` (from `sema4ai.actions`) and `@tool` (from `sema4ai.mcp`) are interchangeable — either decorator makes a function available as both
- Action packages are defined by `package.yaml` which specifies the Python environment (managed by RCC)
- The CLI entry point is `sema4ai.action_server.cli:main`
- The frontend is compiled into a Python file (`_static_contents.py`) containing the HTML as bytes — don't edit this file directly

## Testing

- **Framework:** pytest (Python), Vitest (frontend)
- **Parallel execution:** pytest-xdist (`-n auto`) for non-integration tests
- **Test markers:** `integration_test` marks tests that require the built binary
- Integration tests set `SEMA4AI_INTEGRATION_TEST_ACTION_SERVER_EXECUTABLE` env var
- Test config is in each module's `pyproject.toml` under `[tool.pytest.ini_options]`

## Releasing

1. Run `inv check-all` to verify lint/typecheck/docs pass
2. Bump version with `inv set-version <version>` (updates files + CHANGELOG)
3. Commit and merge to `master`
4. Run `inv make-release` to create and push the release tag
5. GitHub Actions workflow handles PyPI publish and binary builds

CI runs on ubuntu-22.04, windows-2022, macos-15 with Python 3.12.
