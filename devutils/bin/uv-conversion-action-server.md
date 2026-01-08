# UV Migration Guide for Sema4.ai Actions Monorepo

## Overview

This document describes the completed UV migration for the `action_server` project, serving as a template for migrating other projects in the monorepo.

**Goal:** Replace RCC + invoke with uv while keeping the same developer experience and Python logic.

**Key Principle:** Same Python logic, just different entry points (uv scripts instead of invoke).

---

## What Was Changed

### Files Modified/Created

| File | Action |
|------|--------|
| `pyproject.toml` (repo root) | NEW - UV workspace configuration (virtual, no [project]) |
| `uv.lock` (repo root) | NEW - Workspace lock file |
| `.gitignore` (repo root) | Updated - Added `.venv/` |
| `action_server/pyproject.toml` | Updated - Added `[project]`, `[tool.uv]`, `[project.scripts]` |
| `action_server/scripts/__init__.py` | NEW - Package marker |
| `action_server/scripts/uv_tasks.py` | NEW - Project-specific task entry points |
| `action_server/uv.lock` | NEW - Project lock file |
| `action_server/.gitignore` | Updated - Added `.venv/` |
| `action_server/docs/DEVELOP.md` | NEW - UV development documentation |
| `devutils/src/devutils/uv_tasks.py` | NEW - Common task implementations |
| `devutils/pyproject.toml` | Updated - Added `[project]` section |
| `devutils/bin/develop-uv.sh` | NEW - Bootstrap script (Linux/macOS) |
| `devutils/bin/develop-uv.bat` | NEW - Bootstrap script (Windows) |
| `actions/pyproject.toml` | Updated - Added `[project]`, `[tool.uv]` sections |
| `build_common/pyproject.toml` | Updated - Added `[project]`, `[tool.uv]` sections |
| `common/pyproject.toml` | Updated - Added `[project]`, `[tool.uv]` sections |
| `mcp/pyproject.toml` | Updated - Added `[project]`, `[tool.uv]` sections |
| `sema4ai-http-helper/pyproject.toml` | Updated - Added `[project]`, `[tool.uv]` sections |

---

## Architecture

### File Structure

```
repo-root/
├── pyproject.toml              # Workspace config (virtual, no [project])
├── uv.lock                     # Workspace lock file
├── .gitignore                  # Added .venv/
│
├── devutils/
│   ├── pyproject.toml          # [project] + [tool.uv] sections added
│   ├── bin/
│   │   ├── develop-uv.sh       # Bootstrap script (Linux/macOS)
│   │   └── develop-uv.bat      # Bootstrap script (Windows)
│   └── src/devutils/
│       ├── invoke_utils.py     # KEEP - invoke backward compat
│       └── uv_tasks.py         # NEW - common pure Python functions
│
├── action_server/
│   ├── pyproject.toml          # Updated with UV config
│   ├── uv.lock                 # Project lock file
│   ├── scripts/
│   │   ├── __init__.py
│   │   └── uv_tasks.py         # Project-specific task entry points
│   ├── tasks.py                # KEEP - invoke backward compat
│   └── docs/DEVELOP.md         # UV documentation
│
└── [other projects]/
    └── pyproject.toml          # [project] + [tool.uv] sections added
```

### Key Design Decisions

1. **Scripts location:** `action_server/scripts/uv_tasks.py` (not inside src/)
   - Entry points reference: `scripts.uv_tasks:function_name`
   - Keeps task code separate from package code

2. **Common functions:** `devutils/src/devutils/uv_tasks.py`
   - Pure Python implementations (no invoke, no poetry dependencies)
   - Project scripts import and call these functions

3. **TAG_PREFIX derived dynamically:** `PACKAGE_NAME.replace(".", "-")`
   - Same logic as invoke_utils.py
   - Example: `sema4ai.action_server` → `sema4ai-action_server`

4. **Windows subprocess handling:** Use `shell=True` for git glob patterns
   - Required for commands like `git describe --tags --match pattern-[0-9]*`

---

## Root Workspace Configuration

**File:** `pyproject.toml` (repo root)

```toml
# =============================================================================
# UV Workspace Configuration for Sema4.ai Actions Monorepo
# =============================================================================
#
# This file defines a UV workspace that includes all packages in the monorepo.
# Use `uv sync --all-packages` from the repo root to install all packages in
# development mode (similar to the old `inv devinstall`).
#
# From individual project directories, you can use:
#   uv sync                 # Install just that project's dependencies
#   uv sync --all-packages  # Install all workspace packages
#
# =============================================================================

[tool.uv.workspace]
members = [
    "action_server",
    "actions",
    "build_common",
    "common",
    "devutils",
    "mcp",
    "sema4ai-http-helper",
]
```

**Note:** This is a "virtual" workspace - no `[project]` or `[build-system]` sections. UV uses this only for workspace coordination.

---

## Project pyproject.toml Changes

Each project needs these sections added:

### 1. [project] Section (PEP 621)

```toml
[project]
name = "sema4ai-action-server"
version = "3.0.0"
description = "Sema4AI Action Server"
readme = "README.md"
license = "Apache-2.0"
requires-python = ">=3.12,<3.14"
authors = [
    { name = "Sema4.ai, Inc.", email = "dev@sema4.ai" },
]
dependencies = [
    # ... runtime dependencies ...
]

[project.urls]
Homepage = "https://github.com/sema4ai/actions/"
Repository = "https://github.com/sema4ai/actions/"
```

### 2. [project.scripts] Section (Entry Points)

```toml
[project.scripts]
# Main CLI entry point
action-server = "sema4ai.action_server.cli:main"

# UV task commands (uv run <command>)
list = "scripts.uv_tasks:list_tasks"
lint = "scripts.uv_tasks:lint"
format = "scripts.uv_tasks:format"
typecheck = "scripts.uv_tasks:typecheck"
test = "scripts.uv_tasks:test"
test-unit = "scripts.uv_tasks:test_unit"
test-binary = "scripts.uv_tasks:test_binary"
test-run-in-parallel = "scripts.uv_tasks:test_run_in_parallel"
build = "scripts.uv_tasks:build"
build-frontend = "scripts.uv_tasks:build_frontend"
build-oauth2-config = "scripts.uv_tasks:build_oauth2_config"
build-exe = "scripts.uv_tasks:build_executable"
build-go = "scripts.uv_tasks:build_go_wrapper"
dev-frontend = "scripts.uv_tasks:dev_frontend"
download-rcc = "scripts.uv_tasks:download_rcc"
clean = "scripts.uv_tasks:clean"

# Project-specific tasks
set-rcc-version = "scripts.uv_tasks:set_rcc_version"
print-env = "scripts.uv_tasks:print_env"

# Common tasks (from devutils)
docs = "scripts.uv_tasks:docs"
doctest = "scripts.uv_tasks:doctest"
check-all = "scripts.uv_tasks:check_all"
make-release = "scripts.uv_tasks:make_release"
set-version = "scripts.uv_tasks:set_version"
check-tag-version = "scripts.uv_tasks:check_tag_version"
publish = "scripts.uv_tasks:publish"
```

### 3. [tool.uv] Section

```toml
[tool.uv]
dev-dependencies = [
    "types-requests>=2",
    "types-PyYAML>=6",
    # ... other dev dependencies ...
    "sema4ai-devutils",      # For common task functions
    "sema4ai-build-common",  # For build workflows
]

[tool.uv.sources]
# Map workspace packages
sema4ai-actions = { workspace = true }
sema4ai-common = { workspace = true }
sema4ai-devutils = { workspace = true }
sema4ai-build-common = { workspace = true }
sema4ai-mcp = { workspace = true }
sema4ai-http-helper = { workspace = true }
```

### 4. Keep [tool.poetry] Section

Keep the existing `[tool.poetry]` section for backward compatibility with developers still using invoke.

---

## Scripts Structure

### Project Scripts: `action_server/scripts/uv_tasks.py`

```python
"""
UV task entry points for action_server.
"""

import os
import subprocess
import sys
from pathlib import Path

# Project paths
_SCRIPTS_DIR = Path(__file__).parent.resolve()
ROOT = _SCRIPTS_DIR.parent  # action_server project root
REPO_ROOT = ROOT.parent     # actions repo root

# Constants
PACKAGE_NAME = "sema4ai.action_server"
TAG_PREFIX = PACKAGE_NAME.replace(".", "-")  # Same logic as invoke_utils.py

# Task registry for `uv run list`
TASKS = {
    "list": "List all available tasks",
    "lint": "Run linting checks (ruff, isort)",
    # ... etc
}

def list_tasks():
    """List all available tasks."""
    for name, desc in TASKS.items():
        print(f"  {name:20} {desc}")

def lint():
    """Run linting."""
    # Implementation...

# Common tasks delegate to devutils.uv_tasks
def docs():
    """Build API documentation."""
    from devutils.uv_tasks import run_docs
    run_docs(root=ROOT, package_name=PACKAGE_NAME, output_path=ROOT / "docs" / "api")

def check_tag_version():
    """Check if tag matches module version."""
    from sema4ai.action_server import __version__
    from devutils.uv_tasks import run_check_tag_version
    run_check_tag_version(TAG_PREFIX, __version__)
```

### Common Functions: `devutils/src/devutils/uv_tasks.py`

```python
"""
Common UV task implementations.
Pure Python - no invoke or poetry dependencies.
"""

import subprocess
import sys
from pathlib import Path

def _run_cmd(cmd, cwd=None, check=True):
    """Run a command with optional directory."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    if check and result.returncode != 0:
        sys.exit(result.returncode)
    return result

def get_tag(tag_prefix: str) -> str:
    """Get the last tagged version for a given prefix."""
    cmd = f"git describe --tags --abbrev=0 --match {tag_prefix}-[0-9]*"
    # Use shell=True on Windows to match invoke's behavior (handles glob patterns)
    proc = subprocess.run(
        shlex.split(cmd) if sys.platform != "win32" else cmd,
        capture_output=True,
        text=True,
        shell=sys.platform == "win32",
    )
    return proc.stdout.strip()

def run_check_tag_version(tag_prefix: str, module_version: str) -> None:
    """Check if the current tag matches the module version."""
    tag = get_tag(tag_prefix)
    version = tag[tag.rfind("-") + 1:]

    if module_version == version:
        sys.stderr.write(f"Version matches ({version}) (exit(0))\n")
        sys.exit(0)
    else:
        sys.stderr.write(f"Version does not match ({tag_prefix}: {module_version} != repo tag: {version}).\n")
        sys.exit(1)

# ... other common functions ...
```

---

## Command Comparison

| invoke | uv |
|--------|-----|
| `inv -l` | `uv run list` |
| `inv install` | `uv sync` |
| `inv devinstall` | `uv sync --all-packages` |
| `inv lint` | `uv run lint` |
| `inv pretty` | `uv run format` |
| `inv typecheck` | `uv run typecheck` |
| `inv test` | `uv run test` |
| `inv test-not-integration` | `uv run test-unit` |
| `inv test-binary` | `uv run test-binary` |
| `inv docs` | `uv run docs` |
| `inv doctest` | `uv run doctest` |
| `inv build-frontend` | `uv run build-frontend` |
| `inv build-executable` | `uv run build-exe` |
| `inv build-executable --go-wrapper` | `uv run build-exe --go-wrapper` |
| `inv build-go-wrapper` | `uv run build-go` |
| `inv set-version X.Y.Z` | `uv run set-version X.Y.Z` |
| `inv make-release` | `uv run make-release` |
| `inv check-tag-version` | `uv run check-tag-version` |
| `inv publish` | `uv run publish` |
| `inv set-rcc-version X` | `uv run set-rcc-version X` |
| `inv print-env` | `uv run print-env` |

---

## Build Output Locations

| Command | Output location |
|---------|-----------------|
| `uv run build-exe` | `dist/action-server/action-server.exe` |
| `uv run build-exe --go-wrapper` | `dist/final/action-server.exe` |
| `uv run build-go` | `go-wrapper/action-server-unsigned.exe` |

**Note:** `test-binary` and `test-run-in-parallel` expect `dist/final/action-server.exe`, which requires `--go-wrapper`.

---

## Setup Instructions

### First-time Setup

```bash
# Linux/macOS
cd devutils/bin
./develop-uv.sh

# Windows
cd devutils\bin
develop-uv.bat
```

This runs `uv sync --all-packages` from repo root.

### Alternative Setup

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

---

## Verification

After migrating a project, verify with:

```bash
# 1. Sync workspace
cd repo-root
uv sync --all-packages

# 2. Basic commands
cd action_server
uv run list
uv run lint
uv run typecheck

# 3. Version/release commands
uv run check-tag-version

# 4. Build commands
uv run build-frontend
uv run build-exe --go-wrapper
uv run test-run-in-parallel
```

---

## Migrating Other Projects

To migrate another project (e.g., `actions`):

1. **Add `[project]` section** to `project/pyproject.toml`
   - Copy structure from action_server, adjust name/version/dependencies

2. **Add `[tool.uv]` section** with dev-dependencies and sources

3. **Create `project/scripts/` directory** with `__init__.py` and `uv_tasks.py`

4. **Add `[project.scripts]` entry points** for each task

5. **Update `.gitignore`** to include `.venv/`

6. **Run `uv sync --all-packages`** to verify

7. **Test all commands** with `uv run list` and verify each task works
