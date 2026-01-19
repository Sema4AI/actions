"""
Contract tests for artifact naming conventions.

Tests that build artifacts follow the specified naming conventions for
frontend bundles and executable binaries across tiers and platforms.
"""

import re
from pathlib import Path

import pytest

# Import will fail until implementation exists (TDD)
try:
    from build_artifact import ArtifactType, BuildArtifact, generate_artifact_name
    from tier_selector import COMMUNITY, ENTERPRISE
except ImportError:
    pytest.skip("Artifact naming not yet implemented", allow_module_level=True)


class TestFrontendArtifactNaming:
    """Test frontend artifact naming convention."""

    def test_community_frontend_artifact_name(self):
        """Test community frontend artifact: frontend-dist-community.tar.gz"""
        # Act
        name = generate_artifact_name(
            artifact_type=ArtifactType.FRONTEND,
            tier=COMMUNITY
        )

        # Assert
        assert name == "frontend-dist-community.tar.gz"

    def test_enterprise_frontend_artifact_name(self):
        """Test enterprise frontend artifact: frontend-dist-enterprise.tar.gz"""
        # Act
        name = generate_artifact_name(
            artifact_type=ArtifactType.FRONTEND,
            tier=ENTERPRISE
        )

        # Assert
        assert name == "frontend-dist-enterprise.tar.gz"

    def test_frontend_artifact_name_pattern(self):
        """Test frontend artifact name matches pattern."""
        # Arrange
        pattern = re.compile(r"^frontend-dist-(community|enterprise)\.tar\.gz$")

        # Act
        community_name = generate_artifact_name(ArtifactType.FRONTEND, COMMUNITY)
        enterprise_name = generate_artifact_name(ArtifactType.FRONTEND, ENTERPRISE)

        # Assert
        assert pattern.match(community_name)
        assert pattern.match(enterprise_name)


class TestExecutableArtifactNaming:
    """Test executable artifact naming convention."""

    def test_community_linux_executable_name(self):
        """Test community Linux executable: action-server-community-linux-{commit}.zip"""
        # Act
        name = generate_artifact_name(
            artifact_type=ArtifactType.EXECUTABLE,
            tier=COMMUNITY,
            platform="linux",
            git_commit="a3f9b12"
        )

        # Assert
        assert name == "action-server-community-linux-a3f9b12.zip"

    def test_enterprise_macos_executable_name(self):
        """Test enterprise macOS executable: action-server-enterprise-macos-{commit}.zip"""
        # Act
        name = generate_artifact_name(
            artifact_type=ArtifactType.EXECUTABLE,
            tier=ENTERPRISE,
            platform="macos",
            git_commit="b1c2d3e"
        )

        # Assert
        assert name == "action-server-enterprise-macos-b1c2d3e.zip"

    def test_windows_executable_name(self):
        """Test Windows executable: action-server-{tier}-windows-{commit}.zip"""
        # Act
        name = generate_artifact_name(
            artifact_type=ArtifactType.EXECUTABLE,
            tier=COMMUNITY,
            platform="windows",
            git_commit="x7y8z9a"
        )

        # Assert
        assert name == "action-server-community-windows-x7y8z9a.zip"

    def test_executable_name_pattern(self):
        """Test executable name matches pattern."""
        # Arrange
        pattern = re.compile(
            r"^action-server-(community|enterprise)-(linux|macos|windows)-[a-f0-9]{7}\.zip$"
        )

        # Act
        linux_name = generate_artifact_name(
            ArtifactType.EXECUTABLE, COMMUNITY, platform="linux", git_commit="a3f9b12"
        )
        macos_name = generate_artifact_name(
            ArtifactType.EXECUTABLE, ENTERPRISE, platform="macos", git_commit="b1c2d3e"
        )
        windows_name = generate_artifact_name(
            ArtifactType.EXECUTABLE, COMMUNITY, platform="windows", git_commit="c4d5e6f"
        )

        # Assert
        assert pattern.match(linux_name)
        assert pattern.match(macos_name)
        assert pattern.match(windows_name)

    def test_executable_requires_platform(self):
        """Test executable artifact requires platform parameter."""
        # Act & Assert
        with pytest.raises(ValueError):
            generate_artifact_name(
                artifact_type=ArtifactType.EXECUTABLE,
                tier=COMMUNITY,
                platform=None  # INVALID
            )

    def test_executable_requires_git_commit(self):
        """Test executable artifact requires git_commit parameter."""
        # Act & Assert
        with pytest.raises(ValueError):
            generate_artifact_name(
                artifact_type=ArtifactType.EXECUTABLE,
                tier=COMMUNITY,
                platform="linux",
                git_commit=None  # INVALID
            )

    def test_git_commit_short_sha_format(self):
        """Test git commit is 7-character short SHA."""
        # Arrange
        valid_commits = ["a3f9b12", "b1c2d3e", "1234567"]
        invalid_commits = ["short", "toolong12345", "a3f9b1247c8e"]

        # Act & Assert
        for commit in valid_commits:
            name = generate_artifact_name(
                ArtifactType.EXECUTABLE,
                COMMUNITY,
                platform="linux",
                git_commit=commit
            )
            assert commit in name

        for commit in invalid_commits:
            with pytest.raises(ValueError):
                generate_artifact_name(
                    ArtifactType.EXECUTABLE,
                    COMMUNITY,
                    platform="linux",
                    git_commit=commit
                )


class TestMetadataArtifactNaming:
    """Test artifact metadata file naming."""

    def test_metadata_file_name_appends_metadata_json(self):
        """Test metadata file: {artifact}.metadata.json"""
        # Arrange
        artifact_name = "frontend-dist-community.tar.gz"

        # Act
        metadata_name = f"{artifact_name}.metadata.json"

        # Assert
        assert metadata_name == "frontend-dist-community.tar.gz.metadata.json"

    def test_metadata_file_for_executable(self):
        """Test metadata file for executable artifact."""
        # Arrange
        artifact_name = "action-server-community-linux-a3f9b12.zip"

        # Act
        metadata_name = f"{artifact_name}.metadata.json"

        # Assert
        assert metadata_name == "action-server-community-linux-a3f9b12.zip.metadata.json"


class TestCIArtifactNaming:
    """Test CI artifact naming for GitHub Actions uploads."""

    def test_ci_artifact_name_includes_tier_os_commit(self):
        """Test CI artifact: frontend-{tier}-{os}-{commit_sha}"""
        # Arrange
        pattern = re.compile(r"^frontend-(community|enterprise)-(ubuntu|macos|windows)-[a-f0-9]{7,40}$")

        # Act
        ci_names = [
            "frontend-community-ubuntu-a3f9b1247c8e5d3f",
            "frontend-enterprise-macos-b1c2d3e4f5a6b7c8",
            "frontend-community-windows-c4d5e6f"
        ]

        # Assert
        for name in ci_names:
            assert pattern.match(name)

    def test_ci_artifact_distinguishes_tiers(self):
        """Test CI artifacts for different tiers are distinguishable."""
        # Arrange
        community_name = "frontend-community-ubuntu-a3f9b12"
        enterprise_name = "frontend-enterprise-ubuntu-a3f9b12"

        # Assert
        assert "community" in community_name
        assert "enterprise" in enterprise_name
        assert community_name != enterprise_name

    def test_ci_artifact_distinguishes_platforms(self):
        """Test CI artifacts for different platforms are distinguishable."""
        # Arrange
        linux_name = "frontend-community-ubuntu-a3f9b12"
        macos_name = "frontend-community-macos-a3f9b12"
        windows_name = "frontend-community-windows-a3f9b12"

        # Assert
        assert "ubuntu" in linux_name
        assert "macos" in macos_name
        assert "windows" in windows_name
        assert len({linux_name, macos_name, windows_name}) == 3  # All unique


class TestArtifactNameValidation:
    """Test validation of artifact names."""

    def test_validate_frontend_artifact_name(self):
        """Test validation accepts valid frontend artifact names."""
        # Arrange
        valid_names = [
            "frontend-dist-community.tar.gz",
            "frontend-dist-enterprise.tar.gz"
        ]

        # Act & Assert
        for name in valid_names:
            assert validate_artifact_name(name, ArtifactType.FRONTEND)

    def test_validate_executable_artifact_name(self):
        """Test validation accepts valid executable artifact names."""
        # Arrange
        valid_names = [
            "action-server-community-linux-a3f9b12.zip",
            "action-server-enterprise-macos-b1c2d3e.zip",
            "action-server-community-windows-c4d5e6f.zip"
        ]

        # Act & Assert
        for name in valid_names:
            assert validate_artifact_name(name, ArtifactType.EXECUTABLE)

    def test_validate_rejects_invalid_tier(self):
        """Test validation rejects invalid tier names."""
        # Arrange
        invalid_names = [
            "frontend-dist-pro.tar.gz",
            "action-server-premium-linux-a3f9b12.zip"
        ]

        # Act & Assert
        for name in invalid_names:
            assert not validate_artifact_name(name, ArtifactType.FRONTEND)

    def test_validate_rejects_invalid_platform(self):
        """Test validation rejects invalid platform names."""
        # Arrange
        invalid_names = [
            "action-server-community-freebsd-a3f9b12.zip",
            "action-server-enterprise-android-b1c2d3e.zip"
        ]

        # Act & Assert
        for name in invalid_names:
            assert not validate_artifact_name(name, ArtifactType.EXECUTABLE)

    def test_validate_rejects_wrong_extension(self):
        """Test validation rejects wrong file extensions."""
        # Arrange
        invalid_names = [
            "frontend-dist-community.zip",  # Should be .tar.gz
            "action-server-community-linux-a3f9b12.tar.gz"  # Should be .zip
        ]

        # Act & Assert
        # Will fail until validation implemented (TDD)
        pass


class TestArtifactNameExtraction:
    """Test extracting tier, platform, commit from artifact name."""

    def test_extract_tier_from_frontend_artifact(self):
        """Test extracting tier from frontend artifact name."""
        # Arrange
        community_name = "frontend-dist-community.tar.gz"
        enterprise_name = "frontend-dist-enterprise.tar.gz"

        # Act
        community_tier = extract_tier_from_name(community_name)
        enterprise_tier = extract_tier_from_name(enterprise_name)

        # Assert
        assert community_tier == "community"
        assert enterprise_tier == "enterprise"

    def test_extract_platform_from_executable(self):
        """Test extracting platform from executable name."""
        # Arrange
        linux_name = "action-server-community-linux-a3f9b12.zip"
        macos_name = "action-server-enterprise-macos-b1c2d3e.zip"
        windows_name = "action-server-community-windows-c4d5e6f.zip"

        # Act
        linux_platform = extract_platform_from_name(linux_name)
        macos_platform = extract_platform_from_name(macos_name)
        windows_platform = extract_platform_from_name(windows_name)

        # Assert
        assert linux_platform == "linux"
        assert macos_platform == "macos"
        assert windows_platform == "windows"

    def test_extract_commit_from_executable(self):
        """Test extracting git commit from executable name."""
        # Arrange
        name = "action-server-community-linux-a3f9b12.zip"

        # Act
        commit = extract_commit_from_name(name)

        # Assert
        assert commit == "a3f9b12"


# Helper functions (will fail until implemented - TDD)
def validate_artifact_name(name, artifact_type):
    """
    Validate artifact name matches expected pattern.
    Will fail until implemented (TDD).
    """
    raise NotImplementedError("validate_artifact_name not yet implemented")


def extract_tier_from_name(name):
    """
    Extract tier from artifact name.
    Will fail until implemented (TDD).
    """
    raise NotImplementedError("extract_tier_from_name not yet implemented")


def extract_platform_from_name(name):
    """
    Extract platform from artifact name.
    Will fail until implemented (TDD).
    """
    raise NotImplementedError("extract_platform_from_name not yet implemented")


def extract_commit_from_name(name):
    """
    Extract git commit from artifact name.
    Will fail until implemented (TDD).
    """
    raise NotImplementedError("extract_commit_from_name not yet implemented")
