#!/bin/bash -e

# UV-based Development Environment Setup
# Just checks for uv, then runs uv sync in action_server

SCRIPT_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ACTION_SERVER_PATH="$SCRIPT_PATH/../../action_server"

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

# Run uv sync in action_server directory
echo "Running uv sync in action_server..."
cd "$ACTION_SERVER_PATH"
uv sync

echo
echo "Developer env. ready!"
echo
echo "Usage:"
echo "  cd action_server"
echo "  uv run list          # List available commands"
echo "  uv run lint          # Run linting"
echo "  uv run test          # Run tests"
echo
