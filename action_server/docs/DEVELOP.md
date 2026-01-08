# Development

This document describes the UV-based development workflow.

## Requirements

- [uv](https://github.com/astral-sh/uv) v0.9.18 or later - [installation](https://docs.astral.sh/uv/getting-started/installation/) | [changelog](https://github.com/astral-sh/uv/blob/main/CHANGELOG.md)
- Python 3.12 or later (uv will use system Python if available, or download a managed version)

## Setup

### First-time setup

Run the bootstrap script from the repository root:

```bash
# Linux/macOS
cd devutils/bin
./develop-uv.sh

# Windows
cd devutils\bin
develop-uv.bat
```

This will:
1. Check that uv is installed (error if not)
2. Run `uv sync --all-packages` from repo root (installs all workspace packages)

uv automatically uses system Python 3.12 if available, or downloads a managed version (isolated, doesn't affect OS Python).

### Workspace structure

This repository uses a UV workspace defined in the root `pyproject.toml`. All packages are installed together:

- `action_server` - Sema4.ai Action Server
- `actions` - Sema4.ai Actions library
- `build_common` - Build utilities
- `common` - Common utilities
- `devutils` - Development utilities
- `mcp` - Model Context Protocol support
- `sema4ai-http-helper` - HTTP helper library

### Alternative setup options

```bash
# From repo root - install all packages (recommended)
uv sync --all-packages

# From action_server/ - install just action_server deps
cd action_server
uv sync

# From action_server/ - install all workspace packages
cd action_server
uv sync --all-packages
```

## Available commands

Run `uv run list` to list all available commands:

```
  list                 List all available tasks
  lint                 Run linting checks (ruff, isort)
  format               Auto-format code (ruff --fix, isort)
  typecheck            Run mypy type checking
  test                 Run all tests with pytest
  test-unit            Run non-integration tests
  test-binary          Run integration tests against built binary
  test-run-in-parallel Run action server 3 times in parallel (lock file testing)
  build                Build wheel distribution
  build-frontend       Build frontend static assets
  build-oauth2-config  Fetch and embed OAuth2 configs
  build-exe            Build PyInstaller executable
  build-go             Build Go wrapper
  dev-frontend         Run frontend dev server (vite)
  download-rcc         Download RCC binary
  clean                Clean build artifacts
  set-rcc-version      Set RCC version in source files
  print-env            Print environment variables
  docs                 Build API documentation
  doctest              Validate code examples in docs
  check-all            Run all checks (lint, typecheck, test, docs)
  make-release         Create a release tag
  set-version          Set project version in files
  check-tag-version    Check if tag matches module version
  publish              Publish to PyPI
```

### Command comparison (invoke vs uv)

| invoke | uv |
|--------|-----|
| `inv -l` | `uv run list` |
| `inv install` | `uv sync` |
| `inv devinstall` | `uv sync --all-packages` |
| `inv lint` | `uv run lint` |
| `inv pretty` | `uv run format` |
| `inv typecheck` | `uv run typecheck` |
| `inv test` | `uv run test` |
| `inv docs` | `uv run docs` |
| `inv build-frontend` | `uv run build-frontend` |
| `inv build-executable` | `uv run build-exe` |
| `inv build-go-wrapper` | `uv run build-go` |
| `inv set-version X.Y.Z` | `uv run set-version X.Y.Z` |
| `inv make-release` | `uv run make-release` |
| `inv check-tag-version` | `uv run check-tag-version` |
| `inv publish` | `uv run publish` |

## Running tests

```bash
# Run all tests
uv run test

# Run unit tests only (no integration tests)
uv run test-unit

# Run a specific test file
uv run pytest tests/action_server_tests/mcp/test_mcp_integration.py -v

# Run a specific test
uv run pytest tests/action_server_tests/mcp/test_mcp_integration.py::test_mcp_integration_with_actions_in_no_conda_mcp -v
```

**Note:** To run tests, you need to set `ACTION_SERVER_TEST_ACCESS_CREDENTIALS` which is an access credential to `ci.robocloud.dev`.

## Building

```bash
# Build wheel distribution
uv run build

# Build frontend assets
uv run build-frontend

# Build PyInstaller executable
uv run build-exe

# Build with signing
uv run build-exe --sign

# Build Go wrapper
uv run build-go
```

## Release process

To release a new version (in the `/action_server` directory):

1. **Check for CVE updates**
   - Review dependabot alerts for fixable items
   - Update direct deps in `pyproject.toml`
   - Run `uv lock --upgrade` to bump transient deps in `uv.lock`

2. **Update CHANGELOG.md**
   - Ensure changes are documented under `## Unreleased` section

3. **Set the version**
   ```bash
   uv run set-version <version>
   ```
   This will update the version and change `## Unreleased` to the specified version/date.

4. **Commit and merge**
   - Open a PR with the version changes
   - Get it reviewed and merged
   - Pull the merged changes locally

5. **Create the release**
   ```bash
   uv run make-release
   ```
   This creates a tag and pushes it to the remote, triggering the release pipeline.

## Beta releases

To create a beta release:

1. Create a tag ending in `-beta`:
   ```bash
   git tag sema4ai-action_server-<version>-beta
   git push origin sema4ai-action_server-<version>-beta
   ```

2. This triggers a release pipeline that builds and uploads binaries to S3.

**Note:** Only one beta version exists at a time. Running the pipeline again overwrites the previous version.

### Beta binary URLs

- **Windows:** `https://cdn.sema4.ai/action-server/beta/windows64/action-server.exe`
- **Linux:** `https://cdn.sema4.ai/action-server/beta/linux64/action-server`
- **macOS:** `https://cdn.sema4.ai/action-server/beta/mac64/action-server`
- **Version:** `https://cdn.sema4.ai/action-server/beta/version.txt`

## Updating dependencies

```bash
# Update all dependencies to latest compatible versions
uv lock --upgrade

# Update a specific package
uv lock --upgrade-package <package-name>

# Sync after updating lock file
uv sync
```

## Adding new task commands

Task commands are defined as entry points in `pyproject.toml` under `[project.scripts]`.

To add a new command:

1. Add the function to `scripts/uv_tasks.py`
2. Add the entry point to `pyproject.toml`:
   ```toml
   [project.scripts]
   my-command = "scripts.uv_tasks:my_command"
   ```
3. Update the `TASKS` dict in `uv_tasks.py` for `uv run list` listing
4. Run `uv sync` to install the new entry point
