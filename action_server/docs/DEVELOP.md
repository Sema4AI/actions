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
2. Run `uv sync` in action_server directory (installs dependencies, creates `.venv`)

uv automatically uses system Python 3.12 if available, or downloads a managed version (isolated, doesn't affect OS Python).

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
  build-frontend       Build frontend static assets
  build-oauth2-config  Fetch and embed OAuth2 configs
  build-exe            Build PyInstaller executable
  build-go             Build Go wrapper
  dev-frontend         Run frontend dev server (vite)
  download-rcc         Download RCC binary
  clean                Clean build artifacts
```

### Command comparison (invoke vs uv)

| invoke | uv |
|--------|-----|
| `inv -l` | `uv run list` |
| `inv install` | `uv sync` |
| `inv lint` | `uv run lint` |
| `inv pretty` | `uv run format` |
| `inv typecheck` | `uv run typecheck` |
| `inv test` | `uv run test` |
| `inv build-frontend` | `uv run build-frontend` |
| `inv build-executable` | `uv run build-exe` |
| `inv build-go-wrapper` | `uv run build-go` |

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
uv build

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
   # This is still done via invoke (or manually edit files)
   # TODO: Add uv run set-version command
   inv set-version <version>
   ```
   This will update the version and change `## Unreleased` to the specified version/date.

4. **Commit and merge**
   - Open a PR with the version changes
   - Get it reviewed and merged
   - Pull the merged changes locally

5. **Create the release**
   ```bash
   # This is still done via invoke (or manually create git tag)
   # TODO: Add uv run make-release command
   inv make-release
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

1. Add the function to `src/sema4ai/action_server/_scripts/tasks.py`
2. Add the entry point to `pyproject.toml`:
   ```toml
   [project.scripts]
   my-command = "sema4ai.action_server._scripts.tasks:my_command"
   ```
3. Update the `TASKS` dict in `tasks.py` for `uv run tasks` listing
4. Run `uv sync` to install the new entry point
