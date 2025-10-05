# Vendored Design System Packages

This directory contains vendored npm packages for the Action Server frontend design system. These packages are vendored (copied into the repository) to enable external contributors to build the frontend without requiring authentication to private GitHub Packages.

## What is Vendored

The following packages are vendored in this directory:

- **@sema4ai/components** (v0.1.1) - UI component library
- **@sema4ai/icons** (v0.1.2) - Icon library
- **@sema4ai/theme** (v0.1.1-RC1) - Theming system

## Why These Packages are Vendored

These packages are proprietary to Sema4.ai and hosted in a private GitHub Packages registry. To enable:

1. **External Contributors**: Anyone can build the frontend without Sema4.ai credentials
2. **Offline Builds**: Builds work without network access after initial clone
3. **Reproducible Builds**: Exact package versions are locked in the repository
4. **Air-gapped Environments**: Can build in isolated/secure environments

This approach follows the Constitution V (Vendored Builds) requirement for reproducible releases.

## Directory Structure

```
vendored/
├── manifest.json           # Package metadata and checksums
├── components/             # @sema4ai/components package
│   ├── package.json
│   ├── dist/              # Compiled JS/CSS
│   └── LICENSE
├── icons/                  # @sema4ai/icons package
│   ├── package.json
│   ├── dist/
│   └── LICENSE
└── theme/                  # @sema4ai/theme package
    ├── package.json
    ├── dist/
    └── LICENSE
```

## Integrity Verification

Each vendored package has a SHA256 checksum stored in `manifest.json`. These checksums are verified:

- **On every CI build** (via `vendor-integrity-check.yml` workflow)
- **Before releases** (automated verification)
- **Manually** using the checksum utility

### Verify Checksums Manually

```bash
cd action_server
python -m pytest tests/action_server_tests/test_vendored_integrity.py -v
```

Or use the checksum utility directly:

```python
from pathlib import Path
from build-binary.checksum_utils import calculate_package_checksum

checksum = calculate_package_checksum(Path("frontend/vendored/components"))
print(f"Checksum: {checksum}")
```

## How Packages Were Vendored

Packages were vendored using the automated vendoring script:

```bash
# Requires GitHub Packages authentication
cd action_server

# Vendor a single package
python build-binary/vendor-frontend.py \
  --package @sema4ai/components \
  --version 0.1.1

# Or update all packages
python build-binary/vendor-frontend.py --update-all
```

The script:
1. Authenticates to GitHub Packages (requires `GITHUB_TOKEN`)
2. Downloads the specified package version via `npm pack`
3. Extracts the tarball to the vendored directory
4. Calculates SHA256 checksum
5. Updates `manifest.json` with metadata

## How to Update Packages

### Automated Monthly Updates

A GitHub Actions workflow runs monthly to check for updates:

- **Workflow**: `.github/workflows/monthly-vendor-update.yml`
- **Schedule**: First day of each month at midnight UTC
- **Process**:
  1. Checks for newer versions of all vendored packages
  2. Downloads and vendors updated packages
  3. Creates a pull request with the updates
  4. Maintainers review and merge

### Manual Updates (Maintainers Only)

If you have GitHub Packages access and need to update immediately:

1. **Authenticate to GitHub Packages**:
   ```bash
   export GITHUB_TOKEN="your_token_here"
   echo "//npm.pkg.github.com/:_authToken=$GITHUB_TOKEN" > ~/.npmrc
   echo "@sema4ai:registry=https://npm.pkg.github.com" >> ~/.npmrc
   ```

2. **Check for updates**:
   ```bash
   cd action_server
   python build-binary/vendor-frontend.py --update-all
   ```

3. **Update a specific package**:
   ```bash
   python build-binary/vendor-frontend.py \
     --package @sema4ai/components \
     --version 0.1.2
   ```

4. **Verify the update**:
   ```bash
   # Check that checksums pass
   python -m pytest tests/action_server_tests/test_vendored_integrity.py
   
   # Test that build still works
   cd frontend
   npm ci
   npm run build
   ```

5. **Commit and push**:
   ```bash
   git add vendored/
   git commit -m "chore: Update vendored packages"
   git push
   ```

## License Information

All vendored packages are proprietary to Sema4.ai, Inc. and licensed under "SEE LICENSE IN LICENSE". See the LICENSE file in each package directory for details.

## Troubleshooting

### Build fails with "Cannot find module '@sema4ai/components'"

**Cause**: npm didn't properly install the local packages.

**Solution**:
```bash
cd action_server/frontend
rm -rf node_modules package-lock.json
npm install
```

### Checksum mismatch errors

**Cause**: Vendored files have been modified or corrupted.

**Solution**:
```bash
# Restore from git
git checkout action_server/frontend/vendored/

# Or re-vendor the packages (requires credentials)
cd action_server
python build-binary/vendor-frontend.py --package @sema4ai/components --version 0.1.1
```

### Monthly update workflow fails

**Cause**: Usually authentication issues or npm registry problems.

**Solution**:
1. Check that `GITHUB_TOKEN` has `packages:read` permission
2. Verify packages are still available in GitHub Packages
3. Check workflow logs for specific errors
4. Can manually update and create PR instead

## Related Documentation

- [Build Contract](../../specs/002-build-packaging-bug/contracts/build-contract.md) - Requirements for unauthenticated builds
- [Vendor Integrity Contract](../../specs/002-build-packaging-bug/contracts/vendor-integrity-contract.md) - Checksum verification requirements
- [Quickstart Guide](../../specs/002-build-packaging-bug/quickstart.md) - External contributor build validation
- [Repository Size Impact](../../specs/002-build-packaging-bug/REPOSITORY-SIZE.md) - Justification and measurements

## FAQ

**Q: Why not use a private npm registry mirror?**  
A: That would still require authentication and infrastructure. Vendoring is simpler and more portable.

**Q: Why not use Git submodules?**  
A: Submodules would still point to private repositories, requiring authentication. Vendoring makes packages truly public.

**Q: Does this increase repository size significantly?**  
A: Yes, by ~800 KB - 3.5 MB. See [REPOSITORY-SIZE.md](../../specs/002-build-packaging-bug/REPOSITORY-SIZE.md) for justification.

**Q: Are the vendored packages tested?**  
A: Yes, the CI workflows validate checksums and build the frontend on every PR and push.

**Q: Can I use these vendored packages in other projects?**  
A: No, these packages are licensed for use within this repository only. Contact Sema4.ai for licensing.
