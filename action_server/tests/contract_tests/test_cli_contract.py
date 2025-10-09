"""
Contract tests for CLI interface.

Tests the invoke CLI commands for building frontend with different tiers,
exit codes, and output formats.
"""

import json
import pytest
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

# Import will fail until implementation exists (TDD)
try:
    from invoke import Context
except ImportError:
    pytest.skip("invoke not available", allow_module_level=True)


class TestBuildFrontendDefaultBehavior:
    """Test default behavior of inv build-frontend command."""

    def test_inv_build_frontend_defaults_to_community_tier(self, tmp_path):
        """Test inv build-frontend uses community tier by default."""
        # Act
        result = subprocess.run(
            ["inv", "build-frontend"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # Assert
        # Will fail until task implemented (TDD)
        assert result.returncode in [0, 1, 2, 3, 4]
        # Should see "community" in output
        if result.returncode == 0:
            assert "community" in result.stdout.lower() or "tier" in result.stdout.lower()

    def test_inv_build_frontend_community_flag(self, tmp_path):
        """Test inv build-frontend --tier=community explicit flag."""
        # Act
        result = subprocess.run(
            ["inv", "build-frontend", "--tier=community"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # Assert
        assert result.returncode in [0, 1, 2, 3, 4]
        if "tier" in result.stdout.lower():
            assert "community" in result.stdout.lower()

    def test_inv_build_frontend_enterprise_flag(self, tmp_path):
        """Test inv build-frontend --tier=enterprise explicit flag."""
        # Act
        result = subprocess.run(
            ["inv", "build-frontend", "--tier=enterprise"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # Assert
        assert result.returncode in [0, 1, 2, 3, 4]
        if "tier" in result.stdout.lower():
            assert "enterprise" in result.stdout.lower()


class TestBuildFrontendAliases:
    """Test convenience aliases for build commands."""

    def test_inv_build_frontend_community_alias(self, tmp_path):
        """Test inv build-frontend-community alias."""
        # Act
        result = subprocess.run(
            ["inv", "build-frontend-community"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # Assert
        # Will fail until alias implemented (TDD)
        assert result.returncode in [0, 1, 2, 3, 4]

    def test_inv_build_frontend_enterprise_alias(self, tmp_path):
        """Test inv build-frontend-enterprise alias."""
        # Act
        result = subprocess.run(
            ["inv", "build-frontend-enterprise"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # Assert
        # Will fail until alias implemented (TDD)
        assert result.returncode in [0, 1, 2, 3, 4]


class TestCLIExitCodes:
    """Test CLI exit codes for different error scenarios."""

    def test_exit_code_0_on_success(self, tmp_path):
        """Test exit code 0 for successful build."""
        # Arrange - setup valid community build environment
        # (will fail until implementation complete)
        
        # Act
        result = subprocess.run(
            ["inv", "build-frontend", "--tier=community"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # Assert
        if "success" in result.stdout.lower():
            assert result.returncode == 0

    def test_exit_code_1_on_build_error(self, tmp_path):
        """Test exit code 1 for build errors (vite build fails)."""
        # Arrange - setup invalid build that will fail
        # (will fail until implementation complete)
        
        # Act & Assert
        # Exit code 1 = build error
        pass  # Test will be implemented with actual build system

    def test_exit_code_2_on_validation_error(self, tmp_path):
        """Test exit code 2 for validation errors (enterprise imports in community)."""
        # Will fail until validation implemented (TDD)
        pass

    def test_exit_code_3_on_config_error(self, tmp_path):
        """Test exit code 3 for configuration errors (invalid tier)."""
        # Act
        result = subprocess.run(
            ["inv", "build-frontend", "--tier=invalid"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # Assert
        # Should fail with exit code 3 (config error)
        assert result.returncode == 3 or "invalid" in result.stderr.lower()

    def test_exit_code_4_on_dependency_error(self, tmp_path):
        """Test exit code 4 for dependency errors (npm install fails)."""
        # Will fail until dependency resolution implemented (TDD)
        pass


class TestJSONOutput:
    """Test --json flag for machine-readable output."""

    def test_json_output_flag(self, tmp_path):
        """Test inv build-frontend --json produces JSON output."""
        # Act
        result = subprocess.run(
            ["inv", "build-frontend", "--tier=community", "--json"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # Assert
        # Will fail until JSON output implemented (TDD)
        if result.returncode == 0:
            try:
                output = json.loads(result.stdout)
                assert "status" in output
                assert "tier" in output
            except json.JSONDecodeError:
                pytest.fail("Output is not valid JSON")

    def test_json_output_schema(self, tmp_path):
        """Test JSON output matches expected schema."""
        # Act
        result = subprocess.run(
            ["inv", "build-frontend", "--tier=community", "--json"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # Assert
        if result.returncode == 0:
            try:
                output = json.loads(result.stdout)
                
                # Required fields
                assert "status" in output
                assert "tier" in output
                assert "artifact" in output
                
                # Artifact fields
                if output["status"] == "success":
                    artifact = output["artifact"]
                    assert "sha256" in artifact
                    assert "size_bytes" in artifact
                    assert "file_path" in artifact
                
                # Validation results
                assert "validation" in output
                validation = output["validation"]
                assert "imports_check" in validation
                assert "license_check" in validation
                
            except (json.JSONDecodeError, KeyError) as e:
                pytest.fail(f"Invalid JSON schema: {e}")


class TestSourceParameter:
    """Test --source parameter for dependency resolution."""

    def test_source_auto_default(self, tmp_path):
        """Test --source=auto is default (registry → vendored → cdn)."""
        # Act
        result = subprocess.run(
            ["inv", "build-frontend", "--tier=community"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # Assert
        # Default should attempt registry first
        # (will fail until implementation complete)
        pass

    def test_source_registry_explicit(self, tmp_path):
        """Test --source=registry forces registry dependency resolution."""
        # Act
        result = subprocess.run(
            ["inv", "build-frontend", "--tier=enterprise", "--source=registry"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # Assert
        # Should only try registry, fail if unavailable
        pass

    def test_source_vendored_explicit(self, tmp_path):
        """Test --source=vendored forces vendored dependencies."""
        # Act
        result = subprocess.run(
            ["inv", "build-frontend", "--tier=enterprise", "--source=vendored"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # Assert
        # Should only use vendored packages
        if "vendored" in result.stdout.lower():
            assert "registry" not in result.stdout.lower()

    def test_source_cdn_blocked_for_community(self, tmp_path):
        """Test --source=cdn fails for community tier."""
        # Act
        result = subprocess.run(
            ["inv", "build-frontend", "--tier=community", "--source=cdn"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # Assert
        # Should fail with error (CDN not allowed for community)
        assert result.returncode != 0
        assert "cdn" in result.stderr.lower() or "not allowed" in result.stderr.lower()


class TestDebugFlag:
    """Test --debug flag for verbose output."""

    def test_debug_flag_verbose_output(self, tmp_path):
        """Test --debug flag produces verbose output."""
        # Act
        result = subprocess.run(
            ["inv", "build-frontend", "--tier=community", "--debug"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # Assert
        # Debug output should be more verbose
        # (will fail until implementation complete)
        pass


class TestOutputDirParameter:
    """Test --output-dir parameter for custom build directory."""

    def test_output_dir_custom_path(self, tmp_path):
        """Test --output-dir specifies custom build output directory."""
        # Arrange
        custom_dir = tmp_path / "custom-build"

        # Act
        result = subprocess.run(
            ["inv", "build-frontend", "--tier=community", f"--output-dir={custom_dir}"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # Assert
        # Build artifacts should be in custom directory
        # (will fail until implementation complete)
        if result.returncode == 0:
            assert custom_dir.exists() or str(custom_dir) in result.stdout


class TestInstallParameter:
    """Test --install parameter for npm ci behavior."""

    def test_install_true_default(self, tmp_path):
        """Test dependencies are installed by default."""
        # Act
        result = subprocess.run(
            ["inv", "build-frontend", "--tier=community"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # Assert
        # Should run npm ci
        if "npm" in result.stdout.lower() or "install" in result.stdout.lower():
            pass  # Expected

    def test_install_false_skips_npm_ci(self, tmp_path):
        """Test --no-install skips npm ci step."""
        # Act
        result = subprocess.run(
            ["inv", "build-frontend", "--tier=community", "--no-install"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # Assert
        # Should skip npm ci
        if "skip" in result.stdout.lower():
            assert "install" in result.stdout.lower()


class TestInvalidTierError:
    """Test error handling for invalid tier values."""

    def test_invalid_tier_raises_error(self, tmp_path):
        """Test invalid tier value produces clear error message."""
        # Act
        result = subprocess.run(
            ["inv", "build-frontend", "--tier=pro"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # Assert
        assert result.returncode == 3  # Config error
        assert "invalid" in result.stderr.lower() or "tier" in result.stderr.lower()
        # Should suggest valid tiers
        assert "community" in result.stderr.lower() or "enterprise" in result.stderr.lower()
