# Development

This document describes the UV-based development workflow.

## Requirements

- [uv](https://github.com/astral-sh/uv)
  - Exact version specified in [root pyproject.toml](../../pyproject.toml) 
  - [installation](https://docs.astral.sh/uv/getting-started/installation/)
  - [changelog](https://github.com/astral-sh/uv/blob/main/CHANGELOG.md)
- Python 3.12 or later (uv will use system Python if available, or download a managed version)

## Setup

### First-time setup

From the repository root, run:

```bash
uv sync --all-packages
```

This installs all workspace packages in development mode. UV automatically uses system Python 3.12 if available, or downloads a managed version (isolated, doesn't affect OS Python).

### Workspace structure

This repository uses a UV workspace defined in the root `pyproject.toml`. All packages are installed together:

- `action_server` - Sema4.ai Action Server
- `actions` - Sema4.ai Actions library
- `build_common` - Build utilities
- `common` - Common utilities
- `devutils` - Development utilities
- `mcp` - Model Context Protocol support
- `sema4ai-http-helper` - HTTP helper library

### Pre-project tooling

Run `uv run list` to list all available commands.

The project-specific scripts are in /action-server/scripts/uv-tasks.py
The repo common ones are at: /devutils/src/uv-tasks.py
Commands are defined in `pyproject.toml > [project.scripts]`


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

# Build PyInstaller executable (output: dist/action-server/)
uv run build-exe

# Build with Go wrapper (output: dist/final/)
uv run build-exe --go-wrapper

# Build with signing
uv run build-exe --sign

# Build Go wrapper only (output: go-wrapper/action-server-unsigned.exe)
uv run build-go
```

### Build output locations

| Command | Output location |
|---------|-----------------|
| `uv run build-exe` | `dist/action-server/action-server.exe` |
| `uv run build-exe --go-wrapper` | `dist/final/action-server.exe` |
| `uv run build-go` | `go-wrapper/action-server-unsigned.exe` |

**Note:** The `test-binary` and `test-run-in-parallel` commands expect the executable at `dist/final/action-server.exe`, which requires building with `--go-wrapper`.

## Dependency management

### Updating dependencies

**For direct dependencies:**
1. Edit version constraints in `pyproject.toml`
2. Regenerate the lock file: `uv lock`
3. Install updates: `uv sync`

**For transitive dependencies:**
```bash
uv lock --upgrade                        # Update all transitive dependencies
uv lock --upgrade-package <package-name>  # Update specific package only
uv sync                                  # Install updates
```

**Testing after updates:**
```bash
uv run test-unit  # Run unit tests
uv run test       # Run all tests
```

## Release process

To release a new version (in the `/action_server` directory):

1. **Check for dependency updates**
   - Review Dependabot alerts for CVEs
   - Update direct dependencies in `pyproject.toml` if needed
   - Run `uv lock --upgrade` to update transitive dependencies
   - Run `uv sync` and test changes

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
