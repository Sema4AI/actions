# Building Action Server with CDN Frontend

This document describes how to build the action server using pre-built frontend assets from the CDN, bypassing the need for private npm packages.

## Problem

The action server frontend depends on private npm packages that require authentication:
- `@sema4ai/components`
- `@sema4ai/icons`
- `@sema4ai/theme`
- `@robocorp/prettier-config-robocorp`
- `@sema4ai/eslint-config-frontend`

These packages are hosted on GitHub Package Registry and require a `NODE_AUTH_TOKEN` to access.

## Solution

We've created an alternative build approach that downloads the pre-built frontend from the CDN instead of building from source.

### Method 1: Using the CDN Build Task

We've added a new invoke task `build-frontend-cdn` that downloads and extracts the frontend:

```bashuv
cd action_server
uv run --no-project --python 3.12 poetry run inv build-frontend-cdn
```

You can specify a specific version:

```bash
uv run --no-project --python 3.12 poetry run inv build-frontend-cdn --version=2.13.1
```

### Method 2: Modifying GitHub Actions

To use this in GitHub Actions, you can either:

1. **Use the custom workflow** (action_server_binary_release_cdn.yml)
2. **Modify the existing workflow** by replacing the build-frontend step:

```yaml
- name: Build frontend
  run: uv run --no-project --python ${{ matrix.python }} inv build-frontend-cdn
  # No need for NODE_AUTH_TOKEN
```

### Method 3: Environment Variable

Set `ACTION_SERVER_USE_CDN_FRONTEND=true` when running the regular build:

```bash
export ACTION_SERVER_USE_CDN_FRONTEND=true
uv run --no-project --python 3.12 poetry run inv build-frontend
```

## How It Works

1. Downloads the pre-built action-server binary from CDN
2. Runs it temporarily with a minimal package structure
3. Fetches the frontend HTML from http://localhost:8080/
4. Extracts and saves it to `_static_contents.py`
5. Cleans up temporary files

## Benefits

- No need for npm authentication tokens
- Faster builds (no npm install required)
- Guaranteed compatibility with released versions
- Works for open source contributors

## Caveats

- Requires internet access to download from CDN
- Frontend will match the CDN version, not local changes
- Only works for building releases, not for frontend development