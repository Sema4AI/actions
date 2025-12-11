# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Sema4.ai Actions is a Python framework for extending AI agent capabilities through MCP Tools and Actions. It enables developers to create Python functions that can be called by AI agents via protocols like MCP (Model Context Protocol), OpenAI GPTs, and LangChain.

The key abstraction is the `@tool` or `@action` decorator that turns Python functions into AI-callable endpoints. Type hints and docstrings are used to describe parameters to AI agents.

## Repository Structure

This is a monorepo with several Python packages:

- `action_server/` - The main Action Server that hosts and exposes actions via HTTP/MCP
- `actions/` - Core `sema4ai-actions` library with `@action` decorator
- `mcp/` - MCP protocol implementation with `@tool`, `@resource`, `@prompt` decorators
- `common/` - Shared utilities across packages
- `build_common/` - Shared build utilities
- `sema4ai-http-helper/` - HTTP helper utilities
- `templates/` - Project templates for `action-server new`

## Development Commands

### Prerequisites
- Python 3.11+
- Node.js 20.x LTS
- Poetry and Invoke: `pip install -r devutils/requirements.txt`

### Per-Package Development
Navigate to a package directory (e.g., `action_server/`, `actions/`, `mcp/`) and run:

```bash
inv install      # Install dependencies and create virtual environment
inv test         # Run tests with pytest
inv test -t path/to/test.py::test_name  # Run specific test
inv lint         # Run linter (ruff)
inv pretty       # Auto-format code
inv typecheck    # Run type checking
inv check-all    # Run lint, typecheck, and tests
inv docs         # Generate documentation
```

### Root-Level Tasks
From repository root:

```bash
inv install              # Install all packages
inv install --skip=devutils  # Skip specific packages
inv docs                 # Regenerate docs for all packages
inv lock                 # Update poetry.lock for all packages
```

### Frontend Build (Action Server)
```bash
cd action_server/frontend
npm ci && npm run build      # Production build

# Or via invoke:
cd action_server
inv build-frontend --tier=community   # Community tier (default)
inv build-frontend --tier=enterprise  # Enterprise tier (requires NPM_TOKEN)
inv build-frontend --debug            # Debug build (not minified)
```

### Frontend Development
```bash
cd action_server/frontend
npm run dev          # Start dev server with hot reload
npm test             # Run tests
npm run test:lint    # Run linter
npm run test:types   # TypeScript type checking
```

### Building Executable
```bash
cd action_server
inv build-frontend           # Build frontend first
inv build-executable         # Build PyInstaller binary
inv build-executable --sign  # Build and sign
inv test-binary              # Test the built binary
```

## Architecture Notes

### Action/Tool Pattern
Functions become AI-callable through decorators:

```python
from sema4ai.mcp import tool

@tool
def greeting(name: str) -> str:
    """
    Greets the user

    Args:
        name: The user name

    Returns:
        Final user greeting
    """
    return f"Hello {name}!"
```

### Environment Management
Python environments are defined via `package.yaml` files (not requirements.txt). The RCC tool manages reproducible environments.

### Frontend Tiers
The Action Server has two frontend tiers:
- **Community**: Open-source, uses vendored packages from `action_server/frontend/vendored/`
- **Enterprise**: Uses private `@sema4ai/*` design system packages (requires NPM_TOKEN)

Vendored packages allow building without private registry access.

### Testing Structure
- Unit tests: `inv test`
- Integration tests: `inv test-binary` (uses built executable)
- Tests use pytest with markers like `@pytest.mark.integration_test`
