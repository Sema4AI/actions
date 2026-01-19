"""
Integration test: Validates the quickstart.md workflow.

This test validates the end-to-end external contributor experience
by simulating a fresh clone and build without credentials.
"""
import os
import shutil
import subprocess
from pathlib import Path

import pytest


class TestQuickstartValidation:
    """Validate quickstart.md end-to-end workflow."""

    @pytest.fixture(scope="class")
    def frontend_dir(self):
        """Path to frontend directory."""
        return Path(__file__).parent.parent.parent / "frontend"

    @pytest.fixture(scope="class")
    def vendored_dir(self, frontend_dir):
        """Path to vendored directory."""
        return frontend_dir / "vendored"

    @pytest.fixture(scope="class")
    def clean_env(self):
        """Clean environment without credentials."""
        env = os.environ.copy()
        env.pop("NPM_TOKEN", None)
        env.pop("GITHUB_TOKEN", None)
        env.pop("NODE_AUTH_TOKEN", None)
        return env

    def test_vendored_directory_exists(self, vendored_dir):
        """Step 1: Verify vendored/ directory exists and is complete."""
        assert vendored_dir.exists(), "vendored/ directory not found"

        # Check for expected subdirectories
        expected_packages = ["components", "icons", "theme"]
        for package in expected_packages:
            package_dir = vendored_dir / package
            assert package_dir.exists(), f"vendored/{package}/ not found"
            assert package_dir.is_dir(), f"vendored/{package} is not a directory"

    def test_manifest_json_exists(self, vendored_dir):
        """Step 1: Verify manifest.json exists."""
        manifest_path = vendored_dir / "manifest.json"
        assert manifest_path.exists(), "manifest.json not found"

    def test_npm_ci_without_authentication(self, frontend_dir, clean_env):
        """Step 3: Run npm ci without authentication."""
        # Clean first
        if (frontend_dir / "node_modules").exists():
            shutil.rmtree(frontend_dir / "node_modules")

        result = subprocess.run(
            ["npm", "ci"],
            cwd=frontend_dir,
            env=clean_env,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"npm ci failed:\n{result.stderr}"

    def test_npm_build_succeeds(self, frontend_dir, clean_env):
        """Step 4: Run npm run build."""
        # Ensure dependencies are installed
        subprocess.run(
            ["npm", "ci"],
            cwd=frontend_dir,
            env=clean_env,
            check=True,
            capture_output=True,
        )

        # Clean dist
        dist_dir = frontend_dir / "dist"
        if dist_dir.exists():
            shutil.rmtree(dist_dir)

        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=frontend_dir,
            env=clean_env,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"npm run build failed:\n{result.stderr}"

    def test_dist_output_valid(self, frontend_dir, clean_env):
        """Step 5: Verify dist/ output."""
        # Ensure build
        subprocess.run(
            ["npm", "ci"],
            cwd=frontend_dir,
            env=clean_env,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["npm", "run", "build"],
            cwd=frontend_dir,
            env=clean_env,
            check=True,
            capture_output=True,
        )

        dist_dir = frontend_dir / "dist"
        assert dist_dir.exists(), "dist/ directory not created"

        index_html = dist_dir / "index.html"
        assert index_html.exists(), "dist/index.html not created"
        assert index_html.stat().st_size > 0, "dist/index.html is empty"

    def test_build_time_reasonable(self, frontend_dir, clean_env):
        """Step 6: Measure build time (should be < 2 minutes)."""
        import time

        # Clean
        if (frontend_dir / "node_modules").exists():
            shutil.rmtree(frontend_dir / "node_modules")
        if (frontend_dir / "dist").exists():
            shutil.rmtree(frontend_dir / "dist")

        # Time the build
        start_time = time.time()

        subprocess.run(
            ["npm", "ci"],
            cwd=frontend_dir,
            env=clean_env,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["npm", "run", "build"],
            cwd=frontend_dir,
            env=clean_env,
            check=True,
            capture_output=True,
        )

        end_time = time.time()
        build_time = end_time - start_time

        # Should complete in reasonable time (< 2 minutes)
        assert build_time < 120, f"Build took {build_time:.1f}s, expected < 120s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
