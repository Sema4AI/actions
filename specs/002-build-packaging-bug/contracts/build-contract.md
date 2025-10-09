# Build Contract: Unauthenticated Frontend Build

**Feature**: Remove Private Package Dependencies from Build  
**Date**: October 3, 2025  
**Status**: Failing (not yet implemented)

## Contract Description

The frontend build process MUST complete successfully without any authentication to private package registries. This contract validates that external contributors can build the Action Server frontend using only the public repository contents.

## Contract Requirements

### Input Conditions
- Fresh git clone of the repository
- No GitHub Packages authentication credentials
- No `NPM_TOKEN` or `GITHUB_TOKEN` environment variables
- No `.npmrc` file with private registry configuration
- Standard build tools installed: Node.js 20.x LTS, npm 10.x

### Expected Behavior
1. `npm ci` completes with exit code 0
2. `npm run build` completes with exit code 0
3. No HTTP 401 Unauthorized errors logged
4. No network requests to `npm.pkg.github.com` during build
5. Build output directory `dist/` is created
6. Build output contains expected files

### Output Conditions
- `action_server/frontend/dist/index.html` exists
- `action_server/frontend/dist/` contains JavaScript bundles
- `action_server/frontend/dist/` contains CSS assets
- Build time ≤ baseline authenticated build time (0% increase)

## Contract Test

**File**: `action_server/tests/action_server_tests/test_frontend_build_unauthenticated.py`

```python
"""
Contract test: Frontend builds without authentication to private registries.

This test MUST pass for external contributors to build the Action Server.
"""
import os
import subprocess
import tempfile
import shutil
from pathlib import Path
import pytest


class TestUnauthenticatedBuild:
    """Validate frontend builds without private registry credentials."""
    
    @pytest.fixture(scope="class")
    def clean_frontend_dir(self):
        """Provide a clean frontend directory without node_modules or dist."""
        frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        
        # Remove any cached dependencies and build outputs
        if (frontend_dir / "node_modules").exists():
            shutil.rmtree(frontend_dir / "node_modules")
        if (frontend_dir / "dist").exists():
            shutil.rmtree(frontend_dir / "dist")
        
        return frontend_dir
    
    @pytest.fixture(scope="class")
    def unauthenticated_env(self):
        """Environment without any GitHub Packages authentication."""
        env = os.environ.copy()
        
        # Remove any authentication tokens
        env.pop("NPM_TOKEN", None)
        env.pop("GITHUB_TOKEN", None)
        env.pop("NODE_AUTH_TOKEN", None)
        
        # Remove npmrc files that might contain credentials
        npmrc_user = Path.home() / ".npmrc"
        npmrc_backup = None
        if npmrc_user.exists():
            npmrc_backup = npmrc_user.read_text()
            npmrc_user.unlink()
        
        yield env
        
        # Restore npmrc if it existed
        if npmrc_backup:
            npmrc_user.write_text(npmrc_backup)
    
    def test_npm_ci_succeeds_without_auth(
        self, clean_frontend_dir, unauthenticated_env
    ):
        """MUST: npm ci completes successfully without authentication."""
        result = subprocess.run(
            ["npm", "ci"],
            cwd=clean_frontend_dir,
            env=unauthenticated_env,
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0, (
            f"npm ci failed with exit code {result.returncode}\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}"
        )
        
        # Verify no 401 authentication errors
        assert "401" not in result.stderr, (
            "npm ci attempted to access private registry:\n" + result.stderr
        )
        assert "Unauthorized" not in result.stderr
    
    def test_npm_build_succeeds_without_auth(
        self, clean_frontend_dir, unauthenticated_env
    ):
        """MUST: npm run build completes successfully without authentication."""
        # First install dependencies
        subprocess.run(
            ["npm", "ci"],
            cwd=clean_frontend_dir,
            env=unauthenticated_env,
            check=True,
            capture_output=True,
        )
        
        # Then build
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=clean_frontend_dir,
            env=unauthenticated_env,
            capture_output=True,
            text=True,
        )
        
        assert result.returncode == 0, (
            f"npm run build failed with exit code {result.returncode}\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}"
        )
    
    def test_build_output_exists(self, clean_frontend_dir, unauthenticated_env):
        """MUST: Build creates dist/ directory with expected files."""
        # Build (assuming npm ci already ran in previous tests)
        subprocess.run(
            ["npm", "ci"],
            cwd=clean_frontend_dir,
            env=unauthenticated_env,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["npm", "run", "build"],
            cwd=clean_frontend_dir,
            env=unauthenticated_env,
            check=True,
            capture_output=True,
        )
        
        dist_dir = clean_frontend_dir / "dist"
        assert dist_dir.exists(), "dist/ directory not created"
        
        index_html = dist_dir / "index.html"
        assert index_html.exists(), "dist/index.html not created"
        
        # Verify at least one JS bundle exists
        js_files = list(dist_dir.glob("**/*.js"))
        assert len(js_files) > 0, "No JavaScript bundles found in dist/"
        
        # Verify at least one CSS file exists
        css_files = list(dist_dir.glob("**/*.css"))
        assert len(css_files) > 0, "No CSS files found in dist/"
    
    def test_no_private_registry_access(
        self, clean_frontend_dir, unauthenticated_env
    ):
        """MUST: Build does not make network requests to GitHub Packages."""
        # Mock DNS resolution for npm.pkg.github.com to detect access attempts
        # This is a simplified version; a full implementation might use mitmproxy
        
        result = subprocess.run(
            ["npm", "ci", "--verbose"],
            cwd=clean_frontend_dir,
            env=unauthenticated_env,
            capture_output=True,
            text=True,
        )
        
        # Verify no requests to GitHub Packages
        assert "npm.pkg.github.com" not in result.stdout
        assert "npm.pkg.github.com" not in result.stderr
    
    def test_build_time_performance(
        self, clean_frontend_dir, unauthenticated_env, benchmark
    ):
        """MUST: Build time does not increase compared to baseline."""
        # Note: This test requires pytest-benchmark plugin
        # and a baseline measurement stored separately
        
        def build_frontend():
            subprocess.run(
                ["npm", "ci"],
                cwd=clean_frontend_dir,
                env=unauthenticated_env,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["npm", "run", "build"],
                cwd=clean_frontend_dir,
                env=unauthenticated_env,
                check=True,
                capture_output=True,
            )
        
        # Benchmark the build
        result = benchmark(build_frontend)
        
        # TODO: Load baseline from metrics file and assert <= baseline
        # For now, just ensure build completes
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

## Test Execution

**Initial State**: ❌ FAILING (private packages still in package.json)

**Run Command**:
```bash
cd action_server
pytest tests/action_server_tests/test_frontend_build_unauthenticated.py -v
```

**Expected Failures** (before implementation):
- `test_npm_ci_succeeds_without_auth` - Fails with 401 error
- All subsequent tests - Fail due to npm ci failure

**Success Criteria** (after implementation):
- All tests pass with exit code 0
- No 401 errors in logs
- dist/ directory created with valid content
- Build time ≤ baseline

## Contract Maintenance

This contract test MUST:
- Run on every pull request in CI (unauthenticated environment)
- Block merge if failing
- Be updated if frontend build process changes
- Remain passing indefinitely (regression prevention)

## Related Contracts

- [Vendored Integrity Contract](./vendor-integrity-contract.md) - Validates checksums
- [CI Validation Contract](./ci-validation-contract.md) - Validates CI can build
