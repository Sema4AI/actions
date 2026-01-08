#!/bin/bash -e

# UV-based Development Environment Setup
# Syncs all workspace packages for development

SCRIPT_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$SCRIPT_PATH/../.."

echo
echo "=== UV-based Development Environment Setup ==="
echo

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv not found."
    echo "Please install uv v0.9.18 or later: https://github.com/astral-sh/uv"
    exit 1
fi

echo "uv version: $(uv --version)"
echo

# Run uv sync --all-packages from repo root to install all workspace packages
echo "Running uv sync --all-packages (installs all workspace packages)..."
cd "$REPO_ROOT"
uv sync --all-packages

echo
echo "Developer env. ready!"
echo
echo "Usage:"
echo "  cd action_server"
echo "  uv run list          # List available commands"
echo "  uv run lint          # Run linting"
echo "  uv run test          # Run tests"
echo "  uv run build-exe     # Build executable"
echo
echo "Workspace packages installed:"
echo "  - sema4ai-action-server"
echo "  - sema4ai-actions"
echo "  - sema4ai-build-common"
echo "  - sema4ai-common"
echo "  - sema4ai-devutils"
echo "  - sema4ai-mcp"
echo "  - sema4ai-http-helper"
echo
