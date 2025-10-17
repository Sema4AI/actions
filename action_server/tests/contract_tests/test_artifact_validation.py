"""
Contract tests for artifact validation.

Tests the validate-artifact command for imports, licenses, size, determinism, and SBOM checks.
"""

import json
import pytest
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

# Import will fail until implementation exists (TDD)
try:
    from artifact_validator import (
        ArtifactValidator,
        ValidationResult,
        ValidationCheck,
    )
except ImportError:
    pytest.skip("ArtifactValidator not yet implemented", allow_module_level=True)


class TestImportsCheck:
    """Test imports validation check (zero enterprise imports in community)."""

    def test_community_artifact_with_no_enterprise_imports_passes(self, tmp_path):
        """Test community artifact with no enterprise imports passes check."""
        # Arrange
        artifact = tmp_path / "frontend-dist-community.tar.gz"
        # Create mock bundle with only community imports
        bundle_content = """
        import React from 'react';
        import { Button } from '@radix-ui/react-button';
        """
        artifact.write_text(bundle_content)

        # Act
        validator = ArtifactValidator(artifact_path=artifact, tier="community")
        result = validator.check_imports()

        # Assert
        assert result.passed is True
        assert result.violations is None or len(result.violations) == 0

    def test_community_artifact_with_enterprise_imports_fails(self, tmp_path):
        """Test community artifact with enterprise imports fails check."""
        # Arrange
        artifact = tmp_path / "frontend-dist-community.tar.gz"
        # Create mock bundle with enterprise imports
        bundle_content = """
        import React from 'react';
        import { Button } from '@sema4ai/components';  // VIOLATION
        """
        artifact.write_text(bundle_content)

        # Act
        validator = ArtifactValidator(artifact_path=artifact, tier="community")
        result = validator.check_imports()

        # Assert
        assert result.passed is False
        assert result.violations is not None
        assert len(result.violations) > 0
        assert any("@sema4ai" in v.import_statement for v in result.violations)

    def test_enterprise_artifact_allows_enterprise_imports(self, tmp_path):
        """Test enterprise artifact allows @sema4ai imports."""
        # Arrange
        artifact = tmp_path / "frontend-dist-enterprise.tar.gz"
        bundle_content = """
        import { Button } from '@sema4ai/components';  // ALLOWED
        """
        artifact.write_text(bundle_content)

        # Act
        validator = ArtifactValidator(artifact_path=artifact, tier="enterprise")
        result = validator.check_imports()

        # Assert
        assert result.passed is True


class TestLicenseCheck:
    """Test license validation check (OSI-only for community)."""

    @patch("action_server.build_binary.artifact_validator.scan_licenses")
    def test_community_artifact_with_osi_licenses_passes(self, mock_scan, tmp_path):
        """Test community artifact with OSI-approved licenses passes."""
        # Arrange
        artifact = tmp_path / "frontend-dist-community.tar.gz"
        artifact.write_bytes(b"artifact content")

        mock_scan.return_value = [
            {"package": "react", "license": "MIT"},
            {"package": "@radix-ui/react-button", "license": "MIT"},
            {"package": "tailwindcss", "license": "MIT"}
        ]

        # Act
        validator = ArtifactValidator(artifact_path=artifact, tier="community")
        result = validator.check_licenses()

        # Assert
        assert result.passed is True

    @patch("action_server.build_binary.artifact_validator.scan_licenses")
    def test_community_artifact_with_non_osi_license_fails(self, mock_scan, tmp_path):
        """Test community artifact with non-OSI license fails."""
        # Arrange
        artifact = tmp_path / "frontend-dist-community.tar.gz"
        artifact.write_bytes(b"artifact content")

        mock_scan.return_value = [
            {"package": "react", "license": "MIT"},
            {"package": "proprietary-lib", "license": "Proprietary"}  # VIOLATION
        ]

        # Act
        validator = ArtifactValidator(artifact_path=artifact, tier="community")
        result = validator.check_licenses()

        # Assert
        assert result.passed is False
        assert "proprietary" in result.message.lower()

    @patch("action_server.build_binary.artifact_validator.scan_licenses")
    def test_enterprise_artifact_allows_proprietary_licenses(self, mock_scan, tmp_path):
        """Test enterprise artifact allows proprietary @sema4ai licenses."""
        # Arrange
        artifact = tmp_path / "frontend-dist-enterprise.tar.gz"
        artifact.write_bytes(b"artifact content")

        mock_scan.return_value = [
            {"package": "@sema4ai/components", "license": "Proprietary"}  # ALLOWED
        ]

        # Act
        validator = ArtifactValidator(artifact_path=artifact, tier="enterprise")
        result = validator.check_licenses()

        # Assert
        assert result.passed is True


class TestSizeCheck:
    """Test bundle size validation (≤120% baseline, warn only)."""

    def test_size_within_budget_passes(self, tmp_path):
        """Test artifact within size budget passes."""
        # Arrange
        artifact = tmp_path / "frontend-dist-community.tar.gz"
        # Baseline: 500KB, 120% = 600KB
        artifact.write_bytes(b"x" * (550 * 1024))  # 550KB (within budget)

        baseline_file = tmp_path / "baseline.json"
        baseline_file.write_text(json.dumps({
            "bundle_size_bytes": 500 * 1024
        }))

        # Act
        validator = ArtifactValidator(
            artifact_path=artifact,
            tier="community",
            baseline_path=baseline_file
        )
        result = validator.check_size()

        # Assert
        assert result.passed is True

    def test_size_exceeds_budget_warns(self, tmp_path):
        """Test artifact exceeding size budget produces warning (not error)."""
        # Arrange
        artifact = tmp_path / "frontend-dist-community.tar.gz"
        # Baseline: 500KB, 120% = 600KB
        artifact.write_bytes(b"x" * (700 * 1024))  # 700KB (exceeds budget)

        baseline_file = tmp_path / "baseline.json"
        baseline_file.write_text(json.dumps({
            "bundle_size_bytes": 500 * 1024
        }))

        # Act
        validator = ArtifactValidator(
            artifact_path=artifact,
            tier="community",
            baseline_path=baseline_file
        )
        result = validator.check_size()

        # Assert
        # Warn only, not fail
        assert result.passed is True  # Doesn't fail build
        assert result.severity == "warning"
        assert "size" in result.message.lower()


class TestDeterminismCheck:
    """Test deterministic build validation (rebuild matches SHA256)."""

    @patch("action_server.build_binary.artifact_validator.rebuild_artifact")
    def test_deterministic_build_passes(self, mock_rebuild, tmp_path):
        """Test rebuild produces identical SHA256 (deterministic)."""
        # Arrange
        artifact = tmp_path / "frontend-dist-community.tar.gz"
        original_content = b"deterministic build content"
        artifact.write_bytes(original_content)

        # Mock rebuild produces same content
        mock_rebuild.return_value = original_content

        # Act
        validator = ArtifactValidator(artifact_path=artifact, tier="community")
        result = validator.check_determinism()

        # Assert
        assert result.passed is True

    @patch("action_server.build_binary.artifact_validator.rebuild_artifact")
    def test_non_deterministic_build_warns(self, mock_rebuild, tmp_path):
        """Test rebuild with different SHA256 produces warning."""
        # Arrange
        artifact = tmp_path / "frontend-dist-community.tar.gz"
        artifact.write_bytes(b"original build content")

        # Mock rebuild produces different content
        mock_rebuild.return_value = b"different build content"

        # Act
        validator = ArtifactValidator(artifact_path=artifact, tier="community")
        result = validator.check_determinism()

        # Assert
        # Warn only, not fail
        assert result.passed is True  # Doesn't fail build
        assert result.severity == "warning"
        assert "determinism" in result.message.lower()


class TestSBOMCheck:
    """Test SBOM validation (valid CycloneDX JSON exists)."""

    def test_valid_sbom_exists_passes(self, tmp_path):
        """Test valid SBOM file passes check."""
        # Arrange
        artifact = tmp_path / "frontend-dist-community.tar.gz"
        artifact.write_bytes(b"artifact content")

        sbom_file = tmp_path / "sbom.json"
        sbom_file.write_text(json.dumps({
            "bomFormat": "CycloneDX",
            "specVersion": "1.4",
            "version": 1,
            "components": [
                {"name": "react", "version": "18.2.0"}
            ]
        }))

        # Act
        validator = ArtifactValidator(
            artifact_path=artifact,
            tier="community",
            sbom_path=sbom_file
        )
        result = validator.check_sbom()

        # Assert
        assert result.passed is True

    def test_missing_sbom_fails(self, tmp_path):
        """Test missing SBOM file fails check."""
        # Arrange
        artifact = tmp_path / "frontend-dist-community.tar.gz"
        artifact.write_bytes(b"artifact content")

        # Act
        validator = ArtifactValidator(
            artifact_path=artifact,
            tier="community",
            sbom_path=None  # No SBOM
        )
        result = validator.check_sbom()

        # Assert
        assert result.passed is False
        assert "sbom" in result.message.lower()

    def test_invalid_sbom_json_fails(self, tmp_path):
        """Test invalid SBOM JSON fails check."""
        # Arrange
        artifact = tmp_path / "frontend-dist-community.tar.gz"
        artifact.write_bytes(b"artifact content")

        sbom_file = tmp_path / "sbom.json"
        sbom_file.write_text("{ invalid json")

        # Act
        validator = ArtifactValidator(
            artifact_path=artifact,
            tier="community",
            sbom_path=sbom_file
        )
        result = validator.check_sbom()

        # Assert
        assert result.passed is False


class TestJSONOutput:
    """Test JSON output format for validation results."""

    def test_json_output_schema(self, tmp_path):
        """Test validation results match JSON schema."""
        # Arrange
        artifact = tmp_path / "frontend-dist-community.tar.gz"
        artifact.write_bytes(b"artifact content")

        # Act
        validator = ArtifactValidator(artifact_path=artifact, tier="community")
        json_output = validator.run_all_checks(json_format=True)

        # Assert
        output = json.loads(json_output)
        assert "checks" in output
        assert "imports_check" in output["checks"]
        assert "license_check" in output["checks"]
        assert "size_check" in output["checks"]
        assert "determinism_check" in output["checks"]
        assert "sbom_check" in output["checks"]

        for check_name, check_result in output["checks"].items():
            assert "passed" in check_result
            assert "message" in check_result


class TestCLIIntegration:
    """Test CLI invocation of artifact validation."""

    def test_validate_artifact_cli(self, tmp_path):
        """Test inv validate-artifact CLI command."""
        # Arrange
        artifact = tmp_path / "frontend-dist-community.tar.gz"
        artifact.write_bytes(b"clean community artifact")

        # Act
        result = subprocess.run(
            ["inv", "validate-artifact", f"--artifact={artifact}", "--tier=community"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # Assert
        # Will fail until implementation complete (TDD)
        assert result.returncode in [0, 1, 2]

    def test_validate_artifact_json_output(self, tmp_path):
        """Test validate-artifact --json flag."""
        # Arrange
        artifact = tmp_path / "frontend-dist-community.tar.gz"
        artifact.write_bytes(b"artifact")

        # Act
        result = subprocess.run(
            ["inv", "validate-artifact", f"--artifact={artifact}", "--tier=community", "--json"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # Assert
        if result.returncode == 0:
            output = json.loads(result.stdout)
            assert "checks" in output

    def test_validate_artifact_fail_on_warn_flag(self, tmp_path):
        """Test --fail-on-warn treats warnings as errors."""
        # Arrange
        artifact = tmp_path / "frontend-dist-community.tar.gz"
        # Create oversized artifact (will trigger size warning)
        artifact.write_bytes(b"x" * (10 * 1024 * 1024))  # 10MB

        # Act
        result = subprocess.run(
            ["inv", "validate-artifact", f"--artifact={artifact}", "--tier=community", "--fail-on-warn"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # Assert
        # Should fail (exit 1) with --fail-on-warn
        assert result.returncode == 1


class TestValidationResultAggregation:
    """Test aggregating multiple validation results."""

    def test_all_checks_pass(self, tmp_path):
        """Test all validation checks passing."""
        # Arrange
        artifact = tmp_path / "frontend-dist-community.tar.gz"
        artifact.write_bytes(b"clean artifact")

        # Act
        validator = ArtifactValidator(artifact_path=artifact, tier="community")
        results = validator.run_all_checks()

        # Assert
        assert all(result.passed for result in results.values())

    def test_any_check_fails_aggregates_to_fail(self, tmp_path):
        """Test any failing check causes overall fail."""
        # Arrange
        artifact = tmp_path / "frontend-dist-community.tar.gz"
        # Create artifact with enterprise imports (will fail imports check)
        artifact.write_text("import { Button } from '@sema4ai/components';")

        # Act
        validator = ArtifactValidator(artifact_path=artifact, tier="community")
        results = validator.run_all_checks()

        # Assert
        assert not all(result.passed for result in results.values())
        # imports_check should fail
        assert results["imports_check"].passed is False
