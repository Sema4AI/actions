# Action Server Build Instructions

## Quick Build (Community Edition)

This builds the **open-source community edition** with Radix UI + Tailwind CSS (no proprietary components).

### Prerequisites

- Python 3.12+
- Node.js 20.x
- Go 1.23+
- uv (install with: `curl -LsSf https://astral.sh/uv/install.sh | sh`)

### Build Steps (exactly as CI does)

```bash
# 1. Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install devutils requirements
cd action_server
uv run --no-project --python 3.12 python -m pip install --break-system-packages -r ../devutils/requirements.txt

# 3. Install project dependencies (this installs all monorepo packages)
uv run --no-project --python 3.12 inv install

# 4. Build frontend (community tier - default)
uv run --no-project --python 3.12 inv build-frontend
# Output: frontend/dist/index.html (single-file, ~291 KB)

# 5. Build OAuth2 config
uv run --no-project --python 3.12 inv build-oauth2-config

# 6. Build final executable
uv run --no-project --python 3.12 poetry run inv build-executable --go-wrapper
# Output: dist/final/action-server (Linux)
#         dist/final/action-server.exe (Windows)
```

### Test the Binary

```bash
# Check version
./dist/final/action-server version

# Start server (needs a package.yaml with actions)
./dist/final/action-server start --port=8080
```

## Enterprise Build (Internal Only)

For building with proprietary `@sema4ai/*` design system components:

```bash
# Setup npm authentication
npm config set @sema4ai:registry https://npm.pkg.github.com/
npm config set //npm.pkg.github.com/:_authToken "${NPM_TOKEN}"

# Build enterprise frontend
uv run --no-project --python 3.12 inv build-frontend --tier=enterprise

# Rest of build is the same
uv run --no-project --python 3.12 inv build-oauth2-config
uv run --no-project --python 3.12 poetry run inv build-executable --go-wrapper
```

## What Gets Built

### Community Edition
- **Frontend**: `frontend/src/core/` components only
  - UI: Radix UI primitives + Tailwind CSS
  - Features: Action execution, logs, artifacts, run history
  - Dependencies: Public npm packages only
  - Size: ~291 KB (single HTML file)

### Enterprise Edition
- **Frontend**: `frontend/src/core/` + `frontend/src/enterprise/`
  - UI: @sema4ai/components design system
  - Features: Community features + KB, analytics, org management, SSO
  - Dependencies: Public npm + @sema4ai/* private packages
  - Size: ~418 KB (larger due to design system)

### Backend (Same for Both Tiers)
- Python action execution engine
- FastAPI server
- Embedded frontend HTML
- RCC integration (downloaded on first run)
- Go wrapper executable

## Directory Structure

```
dist/
├── action-server/          # PyInstaller output
│   ├── action-server       # Python executable
│   └── _internal/          # Dependencies
└── final/                  # Go wrapper (FINAL OUTPUT)
    └── action-server       # ← THIS IS WHAT YOU DISTRIBUTE
```

## Build Artifacts

After successful build:
- `dist/final/action-server` - Final distributable binary (Linux/macOS)
- `dist/final/action-server.exe` - Final distributable binary (Windows)
- `frontend/dist/index.html` - Standalone frontend (for debugging)
- `src/sema4ai/action_server/_static_contents.py` - Embedded frontend Python module

## Verification

```bash
# 1. Binary exists and is executable
ls -lh dist/final/action-server
# Expected: ~150-200 MB executable

# 2. Version check works
./dist/final/action-server version
# Expected: 2.16.1 (or current version)

# 3. Help command works
./dist/final/action-server --help
# Expected: CLI help output

# 4. Server can start (will fail without actions - that's OK)
./dist/final/action-server start
# Expected: Initializes DB, downloads RCC, fails on missing package.yaml
```

## Common Issues

### Issue: "No module named pytest"
**Solution**: Run `inv install` first - it installs all dependencies

### Issue: "Go executable not found"
**Solution**: Install Go 1.23+ and add to PATH

### Issue: "dist/final/ doesn't exist"
**Solution**: You must use `--go-wrapper` flag for final build

### Issue: "Enterprise imports detected in community build"
**Solution**: Check `frontend/src/core/` doesn't import from `@sema4ai/*` or `../enterprise/`

## CI/CD

The CI workflow (`.github/workflows/action_server_binary_release.yml`) builds:
- **4 platforms**: ubuntu-22.04, windows-2022, macos-13, macos-15
- **Community tier only** (for external contributors)
- **Enterprise tier** (internal PRs only, requires NPM_TOKEN)

Artifacts are uploaded to S3 and GitHub Releases.
