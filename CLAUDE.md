# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is a **monorepo** containing multiple Python packages that make up the Sema4.ai Actions ecosystem:

### Core Packages
- **`actions/`** - Core library for creating Python actions with `@action` decorator (sema4ai-actions)
- **`action_server/`** - HTTP server that exposes actions as APIs (sema4ai-action-server)
- **`common/`** - Shared utilities across packages (sema4ai-common)
- **`mcp/`** - Model Context Protocol integration (sema4ai-mcp)

### Supporting Packages
- **`build_common/`** - Build utilities for executables
- **`devutils/`** - Development utilities and common tasks
- **`sema4ai-http-helper/`** - HTTP utilities
- **`templates/`** - Project templates (basic, advanced, data-access, minimal)

### Key Concepts
- **Actions**: Python functions decorated with `@action` that become AI-callable tools
- **Action Server**: HTTP server that automatically exposes actions via OpenAPI
- **Package Structure**: Actions are organized in packages with `package.yaml` for environment management
- **RCC Integration**: Uses RCC (Robocorp Control Center) for Python environment management

## Common Development Commands

### Root Level Commands (using invoke)
```bash
# Install dependencies for all packages
invoke install

# Install with local development dependencies
invoke devinstall

# Update all package dependencies
invoke install --update

# Generate documentation for all packages
invoke docs
```

### Individual Package Commands (using invoke in package directories)
```bash
# Install package dependencies
invoke install

# Run tests
invoke test

# Run specific test
invoke test -t test_name

# Lint and format code
invoke lint
invoke pretty

# Type checking
invoke typecheck

# Build package
invoke build
```

### Action Server Specific Commands
```bash
# Build frontend assets (in action_server/)
invoke build-frontend

# Build executable binary
invoke build-executable

# Test non-integration tests
invoke test-not-integration

# Test with built binary
invoke test-binary
```

### Package Management
Each package has its own:
- `pyproject.toml` - Poetry configuration and dependencies
- `tasks.py` - Invoke task definitions (extends devutils.invoke_utils.build_common_tasks)
- Package.yaml files are used for action packages, not the Python packages themselves

## Testing Structure

### Test Organization
- Each package has a `tests/` directory
- Action Server: `tests/action_server_tests/`
- Actions: `tests/actions_tests/` and `tests/actions_core_tests/`
- Tests use pytest with fixtures defined in `conftest.py`

### Test Commands
- `invoke test` - Run all tests for a package
- `invoke test -t specific_test` - Run specific test
- Tests support parallel execution with `-n auto` flag

## Development Workflow

### Code Quality Tools
- **Ruff**: Fast linting and formatting (configured in root `ruff.toml`)
- **Black**: Code formatting (via Ruff)
- **isort**: Import sorting
- **mypy**: Type checking
- **pytest**: Testing framework

### Key Files to Know
- `devutils/src/devutils/invoke_utils.py` - Common task definitions used across packages
- `ruff.toml` - Ruff configuration at repository root
- Each package's `pyproject.toml` - Package-specific configuration

### Environment Management
- Uses Poetry for dependency management
- Optional Conda support via `RC_USE_CONDA` environment variable
- RCC manages Python environments for action packages (not for development)

## Action Server Architecture

### Frontend
- React/TypeScript frontend in `action_server/frontend/`
- Built with Vite, uses npm for dependencies
- Static assets embedded in Python via `_static_contents.py`

### Backend Components
- FastAPI-based HTTP server
- WebSocket support for real-time communication
- SQLite database for storing runs and metadata
- OAuth2 integration for authentication
- Package management and environment isolation

### Key Modules
- `_api_*.py` - API route handlers
- `_actions_*.py` - Action execution and management
- `_server.py` - Main server implementation
- `package/` - Package building and metadata handling

## Template Structure

Templates in `templates/` directory provide starting points:
- `basic/` - Simple action example
- `advanced/` - Complex multi-file actions
- `minimal/` - Bare minimum setup
- `data-access-*/` - Database interaction examples

Each template includes:
- `package.yaml` - Environment definition
- Action implementation files
- `devdata/` - Test input data
- Tests and documentation