# Fresh Community Edition Build - Start to Finish

## Prerequisites Check

```bash
# Verify prerequisites are installed
node --version    # Should be v20.x or v22.x
go version       # Should be go1.23+
uv --version     # Should be 0.9.x+
```

## Step 1: Install Python Dependencies

```bash
cd /workspaces/actions/action_server

# Install devutils requirements
uv run --no-project --python 3.12 python -m pip install --break-system-packages -r ../devutils/requirements.txt

# Install all monorepo packages
uv run --no-project --python 3.12 inv install
```

## Step 2: Build Community Frontend

```bash
cd /workspaces/actions/action_server

# Build frontend with community tier (default)
# This will:
# - Copy package.json.community → package.json
# - Install npm dependencies (Radix UI, Tailwind CSS, etc.)
# - Build with Vite
# - Generate single-file HTML (~291 KB)
# - Embed into _static_contents.py
uv run --no-project --python 3.12 inv build-frontend --tier=community
```

**Expected Output:**
```
🔨 Building with tier: community
⏰ Using SOURCE_DATE_EPOCH: 1760281226
✓ Using community package manifest
📦 Installing dependencies...
npm ci --no-audit --no-fund
added 500 packages in 4s
🏗️  Building frontend...
npm run build
dist/index.html  291.42 kB │ gzip: 92.44 kB
✓ built in 930ms
📝 Writing static contents to: _static_contents.py
✅ Frontend built successfully (community tier)
```

## Step 3: Build OAuth2 Config (Optional)

```bash
# Only needed if you have GH_TOKEN for oauth2 configs
uv run --no-project --python 3.12 inv build-oauth2-config
# Skip if you get auth errors - not required for basic build
```

## Step 4: Build Final Binary with Go Wrapper

```bash
cd /workspaces/actions/action_server

# Make sure Go is in PATH
export PATH=$PATH:/usr/local/go/bin

# Build the complete binary
# This will:
# - Build Python executable with PyInstaller
# - Zip the Python app as assets
# - Build Go wrapper around it
# - Create dist/final/action-server (the final distributable)
uv run --no-project --python 3.12 poetry run inv build-executable --go-wrapper
```

**Expected Output:**
```
... PyInstaller building ...
Finished building executable with pyinstaller: dist/action-server/action-server
Creating symlink: libpython3.12.so -> libpython3.12.so.1.0
Zipping assets from dist/action-server to go-wrapper/assets/assets.zip
Building Go wrapper...
Copying Go wrapper executable to dist directory...
Final executable available at: dist/final/action-server
```

## Step 5: Test the Binary

```bash
# Check version
./dist/final/action-server version
# Expected: 2.16.1

# Test with a template
cd /tmp
mkdir test-action && cd test-action
cp -r /workspaces/actions/templates/minimal/* .

# Start the server
/workspaces/actions/action_server/dist/final/action-server start --port=8080
```

**Expected:**
- Server starts
- Downloads RCC on first run (~30s)
- Bootstraps Python environment (~1-2 min first time)
- Imports actions from package.yaml
- Web UI available at http://localhost:8080
- Shows "community tier" in header
- Enterprise features show as "Locked"

## Verification Checklist

- [ ] Binary exists: `ls -lh dist/final/action-server`
- [ ] Binary is ~150-200 MB
- [ ] Version command works: `./dist/final/action-server version`
- [ ] Server starts without errors
- [ ] Web UI loads at http://localhost:8080
- [ ] UI shows "community tier" indicator
- [ ] Enterprise features are locked/hidden
- [ ] Actions page works
- [ ] Can execute the `greet` action from minimal template
- [ ] Run history shows execution results

## Build Artifacts

After successful build, you should have:

```
action_server/
├── dist/
│   ├── action-server/           # PyInstaller output
│   │   ├── action-server        # Python executable
│   │   └── _internal/           # Python dependencies
│   └── final/
│       └── action-server        # ← FINAL DISTRIBUTABLE BINARY
├── frontend/
│   ├── dist/
│   │   └── index.html          # Standalone frontend for debugging
│   └── node_modules/           # npm dependencies
├── go-wrapper/
│   └── assets/
│       ├── assets.zip          # Zipped Python app
│       ├── app_hash            # Hash for integrity check
│       └── version.txt         # Version info
└── src/sema4ai/action_server/
    └── _static_contents.py     # Embedded frontend module
```

## Common Issues & Solutions

### Issue: "Go executable not found"
```bash
# Install Go 1.23
cd /tmp
curl -LO https://go.dev/dl/go1.23.0.linux-amd64.tar.gz
sudo rm -rf /usr/local/go
sudo tar -C /usr/local -xzf go1.23.0.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bin
go version
```

### Issue: "ModuleNotFoundError: No module named 'sema4ai'"
**Solution:** Run `uv run --no-project --python 3.12 inv install` first

### Issue: UI styling looks broken
**Solution:** Tailwind CSS and PostCSS configs were missing. Now added:
- `frontend/src/index.css` - Tailwind directives
- `frontend/tailwind.config.js` - Tailwind configuration  
- `frontend/postcss.config.js` - PostCSS with Tailwind plugin

### Issue: Want to clean and rebuild
```bash
cd /workspaces/actions/action_server
rm -rf dist/ build/ frontend/dist/ frontend/node_modules/
rm -rf go-wrapper/assets/*.zip go-wrapper/assets/app_hash go-wrapper/assets/version.txt
# Then start from Step 1
```

## What Makes This "Community Edition"?

### Frontend (Community Tier)
- ✅ Uses `package.json.community` (public npm packages only)
- ✅ UI components: Radix UI + Tailwind CSS (open-source)
- ✅ Features: Actions, Run History, Logs, Artifacts
- ✅ No `@sema4ai/*` proprietary packages
- ✅ Build artifact: ~291 KB single HTML file
- ✅ Shows "community tier" indicator in UI
- ✅ Enterprise features locked/hidden

### Backend (Tier-Agnostic)
- Python action execution engine (same for both tiers)
- FastAPI server
- RCC integration
- Local database (SQLite)
- No license validation (community is always allowed)

### Binary Distribution
- Single executable: `action-server` (Linux/macOS) or `action-server.exe` (Windows)
- Self-contained: No external dependencies needed
- Downloads RCC automatically on first run
- Creates isolated Python environments via RCC
- ~150-200 MB compressed

## Enterprise Edition (For Reference)

To build enterprise edition (internal only):
```bash
# Setup npm authentication
export NPM_TOKEN="your_github_pat_with_read:packages"
npm config set @sema4ai:registry https://npm.pkg.github.com/
npm config set //npm.pkg.github.com/:_authToken "${NPM_TOKEN}"

# Build with enterprise tier
uv run --no-project --python 3.12 inv build-frontend --tier=enterprise

# Rest is the same
uv run --no-project --python 3.12 inv build-oauth2-config
uv run --no-project --python 3.12 poetry run inv build-executable --go-wrapper
```

Enterprise adds:
- `@sema4ai/components` design system
- Knowledge Base UI
- Advanced Analytics
- Org Management
- SSO/SAML configuration
- Larger bundle: ~418 KB
