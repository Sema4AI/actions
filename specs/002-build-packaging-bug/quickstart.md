# Quickstart: Build Action Server Frontend Without Credentials

**Feature**: Remove Private Package Dependencies from Build  
**Date**: October 3, 2025  
**Audience**: External contributors, downstream packagers

## Overview

This quickstart validates that you can build the Action Server frontend from source without requiring authentication to private package registries. This is the primary success criterion for resolving GitHub issue #220.

## Prerequisites

- **Git**: Any recent version
- **Node.js**: LTS 20.x (20.9.0 or later)
- **npm**: 10.x or later (bundled with Node.js)
- **Operating System**: Linux (Ubuntu 22.04+), macOS, or Windows
- **No credentials**: You should NOT have GitHub Packages authentication configured

## Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/joshyorko/actions.git
cd actions

# Switch to the fix branch (or use main after merge)
git checkout 002-build-packaging-bug
```

**Verification**:
```bash
# You should see the vendored directory
ls -la action_server/frontend/vendored/

# Output should show:
# components/
# icons/
# theme/
# manifest.json
```

## Step 2: Verify No Private Registry Access

**Important**: Ensure you don't have GitHub Packages authentication configured. This validates the external contributor experience.

```bash
# Check for .npmrc file (should not contain GitHub registry config)
cat ~/.npmrc 2>/dev/null || echo "No .npmrc file (good!)"

# Verify no authentication environment variables
echo "NPM_TOKEN: ${NPM_TOKEN:-not set (good!)}"
echo "GITHUB_TOKEN: ${GITHUB_TOKEN:-not set (good!)}"
```

**Expected**: You should see "not set" for both tokens. If they are set, temporarily rename your `.npmrc`:

```bash
mv ~/.npmrc ~/.npmrc.backup  # Restore later if needed
```

## Step 3: Install Dependencies

```bash
cd action_server/frontend
npm ci
```

**Expected Output**:
- No errors related to `401 Unauthorized`
- No errors related to `npm.pkg.github.com`
- Dependencies install successfully from vendored local packages
- Process completes in < 30 seconds (depending on machine)

**Troubleshooting**:
- If you see 401 errors, your npm is still configured with private registry access
- Ensure `package.json` references `file:./vendored/...` not version numbers
- Clear npm cache: `npm cache clean --force`

## Step 4: Build the Frontend

```bash
npm run build
```

**Expected Output**:
- Build completes successfully
- Exit code 0
- No errors or warnings
- `dist/` directory is created
- Build time similar to previous builds (if you've built before)

**Verification**:
```bash
# Check that dist directory was created
ls -lh dist/

# Output should show:
# index.html
# assets/ (JavaScript and CSS bundles)
```

## Step 5: Verify Build Output

```bash
# Check that index.html exists and is non-empty
wc -l dist/index.html
# Should show >0 lines

# Check that JavaScript bundles exist
find dist -name "*.js" -type f | wc -l
# Should show >0 files

# Check that CSS files exist
find dist -name "*.css" -type f | wc -l
# Should show >0 files
```

**Expected**: All files exist and are non-empty.

## Step 6: Validate Vendored Integrity (Optional)

If you want to verify the vendored packages haven't been tampered with:

```bash
# Run integrity tests
cd ../../  # Back to repo root
pytest action_server/tests/action_server_tests/test_vendored_integrity.py -v
```

**Expected**: All tests pass with exit code 0.

## Success Criteria

✅ **You have successfully validated the fix if**:

1. `npm ci` completed without 401 authentication errors
2. `npm run build` completed successfully (exit code 0)
3. `dist/index.html` was created
4. No private registry access was required
5. Build time was reasonable (< 2 minutes on modern hardware)

## Benchmark Build Time (Optional)

To measure build performance:

```bash
# Clean build
rm -rf node_modules dist

# Time the full build
time (npm ci && npm run build)
```

**Expected**: Total time should be ≤ previous authenticated build times. Vendored local packages should be equal or faster than registry downloads.

**Baseline Comparison**:
- Authenticated build (pre-fix): ~X seconds (to be measured)
- Unauthenticated build (post-fix): ~Y seconds (should be ≤ X)

## Troubleshooting

### Problem: "Cannot find module '@sema4ai/components'"

**Cause**: package.json still references registry versions instead of `file:` paths.

**Solution**:
```bash
# Verify package.json has file: references
grep "@sema4ai" action_server/frontend/package.json

# Should show:
# "@sema4ai/components": "file:./vendored/components",
# "@sema4ai/icons": "file:./vendored/icons",
# "@sema4ai/theme": "file:./vendored/theme",
```

### Problem: "ENOENT: no such file or directory, open 'vendored/...'"

**Cause**: Vendored packages not present in repository.

**Solution**:
```bash
# Check that vendored directory exists
ls -la action_server/frontend/vendored/

# If missing, ensure you're on the correct branch
git checkout 002-build-packaging-bug
```

### Problem: Checksum mismatch errors in tests

**Cause**: Vendored package files have been modified.

**Solution**:
```bash
# Restore from git
git checkout action_server/frontend/vendored/
```

### Problem: Build is slower than expected

**Cause**: Network or disk I/O issues, or first build (npm cache warming).

**Solution**:
```bash
# Run build again (second build should use cache)
npm run build

# Clear npm cache and retry
npm cache clean --force
rm -rf node_modules
npm ci && npm run build
```

## Next Steps

- **For Contributors**: You can now modify frontend code and rebuild locally
- **For Packagers**: You can package the frontend for distribution
- **For CI/CD**: Configure your pipeline to build without credentials

## Testing Your Changes

After modifying frontend code:

```bash
# Rebuild
npm run build

# Run frontend tests
npm test

# Run linting
npm run test:lint

# Run type checking
npm run test:types
```

## Reporting Issues

If this quickstart doesn't work for you:

1. Verify prerequisites (Node.js version, npm version)
2. Check for any error messages in the output
3. Run with verbose logging: `npm ci --loglevel verbose`
4. Report issue on GitHub with:
   - Your OS and Node.js version
   - Full error output
   - Steps you followed

## Related Documentation

- [Vendored Dependencies README](../action_server/frontend/vendored/README.md) - Details on vendored packages
- [Contributing Guide](../../CONTRIBUTING.md) - General contribution guidelines
- [Build Contract](./contracts/build-contract.md) - Automated tests for this process
