"""
Unit tests for PackageManifest validation.

Tests the PackageManifest class for loading, validating, and copying
tier-specific package.json files.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

# Import will fail until implementation exists (TDD)
try:
    from action_server.build_binary.package_manifest import (
        PackageManifest,
        ValidationResult,
        ManifestValidationError,
    )
    from action_server.build_binary.tier_selector import BuildTier, COMMUNITY, ENTERPRISE
except ImportError:
    # Expected to fail initially (TDD)
    pytest.skip("PackageManifest not yet implemented", allow_module_level=True)


class TestPackageManifestLoad:
    """Test PackageManifest.load() method."""

    def test_load_community_manifest(self, tmp_path):
        """Test loading community manifest (package.json.community)."""
        # Arrange
        community_manifest = tmp_path / "package.json.community"
        community_manifest.write_text(json.dumps({
            "name": "action-server-frontend",
            "dependencies": {
                "@radix-ui/react-button": "^1.0.0",
                "tailwindcss": "^3.3.0"
            },
            "devDependencies": {
                "vite": "^6.1.0"
            }
        }))

        # Act
        manifest = PackageManifest.load(COMMUNITY, tmp_path)

        # Assert
        assert manifest.tier == COMMUNITY
        assert manifest.file_path == community_manifest
        assert "@radix-ui/react-button" in manifest.dependencies
        assert "tailwindcss" in manifest.dependencies
        assert "vite" in manifest.dev_dependencies

    def test_load_enterprise_manifest(self, tmp_path):
        """Test loading enterprise manifest (package.json.enterprise)."""
        # Arrange
        enterprise_manifest = tmp_path / "package.json.enterprise"
        enterprise_manifest.write_text(json.dumps({
            "name": "action-server-frontend",
            "dependencies": {
                "@radix-ui/react-button": "^1.0.0",
                "@sema4ai/components": "^1.2.0",
                "@sema4ai/icons": "^1.1.0"
            }
        }))

        # Act
        manifest = PackageManifest.load(ENTERPRISE, tmp_path)

        # Assert
        assert manifest.tier == ENTERPRISE
        assert manifest.file_path == enterprise_manifest
        assert "@sema4ai/components" in manifest.dependencies
        assert "@sema4ai/icons" in manifest.dependencies

    def test_load_nonexistent_manifest_raises_error(self, tmp_path):
        """Test loading fails if manifest file doesn't exist."""
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            PackageManifest.load(COMMUNITY, tmp_path)

    def test_load_invalid_json_raises_error(self, tmp_path):
        """Test loading fails if manifest is not valid JSON."""
        # Arrange
        community_manifest = tmp_path / "package.json.community"
        community_manifest.write_text("{ invalid json")

        # Act & Assert
        with pytest.raises(json.JSONDecodeError):
            PackageManifest.load(COMMUNITY, tmp_path)


class TestPackageManifestValidation:
    """Test PackageManifest.validate() method."""

    def test_community_manifest_rejects_sema4ai_packages(self, tmp_path):
        """Test community manifest validation fails if @sema4ai/* packages present."""
        # Arrange
        community_manifest = tmp_path / "package.json.community"
        community_manifest.write_text(json.dumps({
            "dependencies": {
                "@radix-ui/react-button": "^1.0.0",
                "@sema4ai/components": "^1.2.0"  # INVALID
            }
        }))

        manifest = PackageManifest.load(COMMUNITY, tmp_path)

        # Act
        result = manifest.validate()

        # Assert
        assert result.passed is False
        assert "@sema4ai/components" in result.message
        assert result.violations is not None
        assert len(result.violations) == 1

    def test_community_manifest_allows_public_packages(self, tmp_path):
        """Test community manifest validation passes for public packages."""
        # Arrange
        community_manifest = tmp_path / "package.json.community"
        community_manifest.write_text(json.dumps({
            "dependencies": {
                "@radix-ui/react-button": "^1.0.0",
                "tailwindcss": "^3.3.0",
                "react": "^18.2.0"
            }
        }))

        manifest = PackageManifest.load(COMMUNITY, tmp_path)

        # Act
        result = manifest.validate()

        # Assert
        assert result.passed is True
        assert result.violations is None or len(result.violations) == 0

    def test_enterprise_manifest_allows_sema4ai_packages(self, tmp_path):
        """Test enterprise manifest validation allows @sema4ai/* packages."""
        # Arrange
        enterprise_manifest = tmp_path / "package.json.enterprise"
        enterprise_manifest.write_text(json.dumps({
            "dependencies": {
                "@radix-ui/react-button": "^1.0.0",
                "@sema4ai/components": "^1.2.0",
                "@sema4ai/icons": "^1.1.0",
                "@sema4ai/theme": "^2.0.0"
            }
        }))

        manifest = PackageManifest.load(ENTERPRISE, tmp_path)

        # Act
        result = manifest.validate()

        # Assert
        assert result.passed is True

    def test_validate_rejects_wildcard_versions(self, tmp_path):
        """Test validation fails if package uses wildcard version."""
        # Arrange
        community_manifest = tmp_path / "package.json.community"
        community_manifest.write_text(json.dumps({
            "dependencies": {
                "react": "*"  # INVALID
            }
        }))

        manifest = PackageManifest.load(COMMUNITY, tmp_path)

        # Act
        result = manifest.validate()

        # Assert
        assert result.passed is False
        assert "wildcard" in result.message.lower() or "*" in result.message

    def test_validate_rejects_latest_version(self, tmp_path):
        """Test validation fails if package uses 'latest' version."""
        # Arrange
        community_manifest = tmp_path / "package.json.community"
        community_manifest.write_text(json.dumps({
            "dependencies": {
                "react": "latest"  # INVALID
            }
        }))

        manifest = PackageManifest.load(COMMUNITY, tmp_path)

        # Act
        result = manifest.validate()

        # Assert
        assert result.passed is False
        assert "latest" in result.message.lower()


class TestPackageManifestLicenseCheck:
    """Test license validation for community tier."""

    @patch("action_server.build_binary.package_manifest.check_licenses")
    def test_community_requires_osi_licenses_only(self, mock_check_licenses, tmp_path):
        """Test community manifest requires OSI-approved licenses."""
        # Arrange
        community_manifest = tmp_path / "package.json.community"
        community_manifest.write_text(json.dumps({
            "dependencies": {"react": "^18.2.0"}
        }))

        manifest = PackageManifest.load(COMMUNITY, tmp_path)

        # Mock license check to return non-OSI license
        mock_check_licenses.return_value = ValidationResult(
            passed=False,
            message="Non-OSI license found: Proprietary",
            violations=[{"package": "react", "license": "Proprietary"}]
        )

        # Act
        result = manifest.validate_licenses()

        # Assert
        assert result.passed is False
        assert "osi" in result.message.lower() or "proprietary" in result.message.lower()

    @patch("action_server.build_binary.package_manifest.check_licenses")
    def test_enterprise_allows_proprietary_licenses(self, mock_check_licenses, tmp_path):
        """Test enterprise manifest allows proprietary @sema4ai packages."""
        # Arrange
        enterprise_manifest = tmp_path / "package.json.enterprise"
        enterprise_manifest.write_text(json.dumps({
            "dependencies": {
                "@sema4ai/components": "^1.2.0"
            }
        }))

        manifest = PackageManifest.load(ENTERPRISE, tmp_path)

        # Mock license check to return proprietary license (allowed for enterprise)
        mock_check_licenses.return_value = ValidationResult(
            passed=True,
            message="Proprietary license allowed for enterprise tier"
        )

        # Act
        result = manifest.validate_licenses()

        # Assert
        assert result.passed is True


class TestPackageManifestCopy:
    """Test PackageManifest.copy_to_root() method."""

    def test_copy_to_root_creates_package_json(self, tmp_path):
        """Test copy_to_root() creates package.json from tier-specific manifest."""
        # Arrange
        community_manifest = tmp_path / "package.json.community"
        manifest_content = {"dependencies": {"react": "^18.2.0"}}
        community_manifest.write_text(json.dumps(manifest_content))

        manifest = PackageManifest.load(COMMUNITY, tmp_path)

        # Act
        manifest.copy_to_root()

        # Assert
        package_json = tmp_path / "package.json"
        assert package_json.exists()
        assert json.loads(package_json.read_text()) == manifest_content

    def test_copy_to_root_overwrites_existing_package_json(self, tmp_path):
        """Test copy_to_root() overwrites existing package.json."""
        # Arrange
        community_manifest = tmp_path / "package.json.community"
        manifest_content = {"dependencies": {"react": "^18.2.0"}}
        community_manifest.write_text(json.dumps(manifest_content))

        package_json = tmp_path / "package.json"
        package_json.write_text(json.dumps({"old": "content"}))

        manifest = PackageManifest.load(COMMUNITY, tmp_path)

        # Act
        manifest.copy_to_root()

        # Assert
        assert json.loads(package_json.read_text()) == manifest_content


class TestPackageManifestLocked:
    """Test package-lock.json detection."""

    def test_locked_true_if_package_lock_exists(self, tmp_path):
        """Test manifest.locked is True if package-lock.json exists."""
        # Arrange
        community_manifest = tmp_path / "package.json.community"
        community_manifest.write_text(json.dumps({"dependencies": {}}))
        
        package_lock = tmp_path / "package-lock.json"
        package_lock.write_text(json.dumps({"lockfileVersion": 2}))

        # Act
        manifest = PackageManifest.load(COMMUNITY, tmp_path)

        # Assert
        assert manifest.locked is True

    def test_locked_false_if_no_package_lock(self, tmp_path):
        """Test manifest.locked is False if package-lock.json doesn't exist."""
        # Arrange
        community_manifest = tmp_path / "package.json.community"
        community_manifest.write_text(json.dumps({"dependencies": {}}))

        # Act
        manifest = PackageManifest.load(COMMUNITY, tmp_path)

        # Assert
        assert manifest.locked is False


# Fixtures
@pytest.fixture
def sample_community_manifest(tmp_path):
    """Create a sample community manifest for testing."""
    manifest_file = tmp_path / "package.json.community"
    manifest_file.write_text(json.dumps({
        "name": "action-server-frontend",
        "version": "1.0.0",
        "dependencies": {
            "@radix-ui/react-button": "^1.0.0",
            "@radix-ui/react-dialog": "^1.0.0",
            "tailwindcss": "^3.3.0",
            "react": "^18.2.0"
        },
        "devDependencies": {
            "vite": "^6.1.0",
            "typescript": "^5.3.3"
        }
    }))
    return manifest_file


@pytest.fixture
def sample_enterprise_manifest(tmp_path):
    """Create a sample enterprise manifest for testing."""
    manifest_file = tmp_path / "package.json.enterprise"
    manifest_file.write_text(json.dumps({
        "name": "action-server-frontend",
        "version": "1.0.0",
        "dependencies": {
            "@radix-ui/react-button": "^1.0.0",
            "@sema4ai/components": "^1.2.0",
            "@sema4ai/icons": "^1.1.0",
            "@sema4ai/theme": "^2.0.0",
            "react": "^18.2.0"
        },
        "devDependencies": {
            "vite": "^6.1.0",
            "typescript": "^5.3.3"
        }
    }))
    return manifest_file
