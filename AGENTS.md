# Repository Guidelines

## Project Structure & Module Organization
This repository is a monorepo of Poetry-managed Python packages. `action_server/` contains the CLI, FastAPI service, and web UI assets; `actions/` and `mcp/` provide reusable agent-side toolkits; `common/`, `build_common/`, and `devutils/` host shared runtime and build utilities. Test suites live in each package’s `tests/` directory, and templates for new action packages reside in `templates/`. Use the top-level `tasks.py` to run cross-project automation with Invoke when you need to touch multiple packages.

## Build, Test, and Development Commands
- `poetry install` (run inside a package directory) sets up the virtual environment; `invoke install` from the repo root installs every package in one go.
- `poetry run action-server start --auto-reload` boots the local server with hot reload; add `--log-level debug` when troubleshooting agent tooling.
- `poetry run pytest` executes the package’s unit tests; `invoke docs` rebuilds documentation bundles across projects.

## Coding Style & Naming Conventions
Target Python 3.12 with type hints and docstrings that describe tool contracts. Format code with Black (4-space indents) and import order with Isort; both run automatically through Poetry scripts. Keep module and function names in `snake_case`, classes in `PascalCase`, and tests in `test_<feature>.py`. Prefer explicit dataclasses or Pydantic models for payloads exposed to agents so that generated schemas stay stable.

## Testing Guidelines
Pytest drives all suites (`tests/action_server_tests`, `tests/actions_tests`, etc.). Name fixtures descriptively and place golden files under `tests/resources/` where applicable. Add regression coverage when touching protocols, serializers, or CLI entry points, and ensure new agent commands include happy-path and failure-path assertions. Run `poetry run pytest -k <scope>` while iterating, and finish with a full `poetry run pytest` before submitting.

## Commit & Pull Request Guidelines
Follow the observed Conventional Commit style (`feat:`, `fix:`, `chore:`, …) so changelog generation stays accurate. Keep commits focused and include context on affected packages in the body (e.g., “action_server: tighten OAuth flow”). Pull requests should link to an issue, summarize user-facing impact, note breaking changes, and paste the relevant test output or screenshots of the web UI. Request review from the package owner when modifying shared `common/` components.

## Security & Configuration Tips
Store secrets outside the repo—load them via environment variables or the local agent vault—and never commit generated binaries in `action_server/dist/`. When updating `package.yaml` templates, double-check dependency pins to avoid widening attack surfaces, and review OAuth configuration changes alongside another maintainer.
