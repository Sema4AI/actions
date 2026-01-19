"""
Unit tests for BuildArtifact generation.

Tests artifact naming, hashing, metadata generation, and SBOM validation.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Import will fail until implementation exists (TDD)
try:
    from build_artifact import (
        ArtifactType,
        BuildArtifact,
        compute_sha256,
        generate_artifact_name,
        generate_metadata,
    )
    from tier_selector import COMMUNITY, ENTERPRISE
except ImportError:
    # Expected to fail initially (TDD)
    pytest.skip("BuildArtifact not yet implemented", allow_module_level=True)


class TestArtifactNaming:
    """Test artifact naming conventions."""

    def test_frontend_community_artifact_name(self):
        """Test community frontend artifact follows naming convention."""
        # Act
        name = generate_artifact_name(
            artifact_type=ArtifactType.FRONTEND,
            tier=COMMUNITY,
            platform=None
        )

        # Assert
        assert name == "frontend-dist-community.tar.gz"

    def test_frontend_enterprise_artifact_name(self):
        """Test enterprise frontend artifact follows naming convention."""
        # Act
        name = generate_artifact_name(
            artifact_type=ArtifactType.FRONTEND,
            tier=ENTERPRISE,
            platform=None
        )

        # Assert
        assert name == "frontend-dist-enterprise.tar.gz"

    def test_executable_community_linux_artifact_name(self):
        """Test community executable artifact name includes platform and commit."""
        # Act
        name = generate_artifact_name(
            artifact_type=ArtifactType.EXECUTABLE,
            tier=COMMUNITY,
            platform="linux",
            git_commit="a3f9b12"
        )

        # Assert
        assert name == "action-server-community-linux-a3f9b12.zip"

    def test_executable_enterprise_macos_artifact_name(self):
        """Test enterprise executable artifact name."""
        # Act
        name = generate_artifact_name(
            artifact_type=ArtifactType.EXECUTABLE,
            tier=ENTERPRISE,
            platform="macos",
            git_commit="b1c2d3e"
        )

        # Assert
        assert name == "action-server-enterprise-macos-b1c2d3e.zip"

    def test_executable_windows_artifact_name(self):
        """Test Windows executable artifact name."""
        # Act
        name = generate_artifact_name(
            artifact_type=ArtifactType.EXECUTABLE,
            tier=COMMUNITY,
            platform="windows",
            git_commit="x7y8z9a"
        )

        # Assert
        assert name == "action-server-community-windows-x7y8z9a.zip"


class TestSHA256Computation:
    """Test SHA256 hash computation for artifacts."""

    def test_compute_sha256_for_file(self, tmp_path):
        """Test computing SHA256 hash for a file."""
        # Arrange
        test_file = tmp_path / "artifact.tar.gz"
        test_content = b"test artifact content"
        test_file.write_bytes(test_content)

        expected_hash = hashlib.sha256(test_content).hexdigest()

        # Act
        computed_hash = compute_sha256(test_file)

        # Assert
        assert computed_hash == expected_hash
        assert len(computed_hash) == 64  # SHA256 is 64 hex chars

    def test_compute_sha256_for_large_file(self, tmp_path):
        """Test SHA256 computation handles large files (chunked reading)."""
        # Arrange
        test_file = tmp_path / "large_artifact.tar.gz"
        # Create 10MB file
        large_content = b"x" * (10 * 1024 * 1024)
        test_file.write_bytes(large_content)

        expected_hash = hashlib.sha256(large_content).hexdigest()

        # Act
        computed_hash = compute_sha256(test_file)

        # Assert
        assert computed_hash == expected_hash

    def test_sha256_deterministic(self, tmp_path):
        """Test SHA256 is deterministic (same input → same hash)."""
        # Arrange
        test_file = tmp_path / "artifact.tar.gz"
        test_file.write_bytes(b"deterministic content")

        # Act
        hash1 = compute_sha256(test_file)
        hash2 = compute_sha256(test_file)

        # Assert
        assert hash1 == hash2


class TestBuildArtifactCreation:
    """Test BuildArtifact creation and attributes."""

    def test_create_frontend_artifact(self, tmp_path):
        """Test creating BuildArtifact for frontend."""
        # Arrange
        artifact_file = tmp_path / "frontend-dist-community.tar.gz"
        artifact_file.write_bytes(b"frontend bundle")

        # Act
        artifact = BuildArtifact.create(
            artifact_type=ArtifactType.FRONTEND,
            tier=COMMUNITY,
            file_path=artifact_file,
            platform=None
        )

        # Assert
        assert artifact.artifact_type == ArtifactType.FRONTEND
        assert artifact.tier == COMMUNITY
        assert artifact.file_path == artifact_file
        assert artifact.platform is None
        assert artifact.sha256_hash is not None
        assert len(artifact.sha256_hash) == 64
        assert artifact.file_size_bytes == len(b"frontend bundle")

    def test_create_executable_artifact(self, tmp_path):
        """Test creating BuildArtifact for executable."""
        # Arrange
        artifact_file = tmp_path / "action-server-enterprise-linux-a3f9b12.zip"
        artifact_file.write_bytes(b"executable binary")

        # Act
        artifact = BuildArtifact.create(
            artifact_type=ArtifactType.EXECUTABLE,
            tier=ENTERPRISE,
            file_path=artifact_file,
            platform="linux",
            git_commit="a3f9b12"
        )

        # Assert
        assert artifact.artifact_type == ArtifactType.EXECUTABLE
        assert artifact.tier == ENTERPRISE
        assert artifact.platform == "linux"
        assert artifact.git_commit == "a3f9b12"

    def test_artifact_has_build_timestamp(self, tmp_path):
        """Test artifact includes build timestamp."""
        # Arrange
        artifact_file = tmp_path / "frontend-dist-community.tar.gz"
        artifact_file.write_bytes(b"content")

        # Act
        before = datetime.utcnow()
        artifact = BuildArtifact.create(
            artifact_type=ArtifactType.FRONTEND,
            tier=COMMUNITY,
            file_path=artifact_file
        )
        after = datetime.utcnow()

        # Assert
        assert artifact.build_timestamp is not None
        assert before <= artifact.build_timestamp <= after

    @patch("subprocess.run")
    def test_artifact_includes_git_commit(self, mock_subprocess, tmp_path):
        """Test artifact captures git commit SHA."""
        # Arrange
        mock_subprocess.return_value = Mock(
            stdout="a3f9b1247c8e5d3f\n",
            returncode=0
        )

        artifact_file = tmp_path / "frontend-dist-community.tar.gz"
        artifact_file.write_bytes(b"content")

        # Act
        artifact = BuildArtifact.create(
            artifact_type=ArtifactType.FRONTEND,
            tier=COMMUNITY,
            file_path=artifact_file
        )

        # Assert
        assert artifact.git_commit == "a3f9b12"  # First 7 chars


class TestMetadataGeneration:
    """Test artifact metadata JSON generation."""

    def test_generate_metadata_json(self, tmp_path):
        """Test generating metadata JSON file."""
        # Arrange
        artifact_file = tmp_path / "frontend-dist-community.tar.gz"
        artifact_file.write_bytes(b"test content")

        artifact = BuildArtifact.create(
            artifact_type=ArtifactType.FRONTEND,
            tier=COMMUNITY,
            file_path=artifact_file
        )

        # Act
        metadata = generate_metadata(artifact)

        # Assert
        assert metadata["tier"] == "community"
        assert metadata["artifact_type"] == "frontend"
        assert metadata["sha256"] == artifact.sha256_hash
        assert metadata["size_bytes"] == artifact.file_size_bytes
        assert "build_timestamp" in metadata
        assert "git_commit" in metadata

    def test_write_metadata_to_file(self, tmp_path):
        """Test writing metadata to .metadata.json file."""
        # Arrange
        artifact_file = tmp_path / "frontend-dist-community.tar.gz"
        artifact_file.write_bytes(b"test content")

        artifact = BuildArtifact.create(
            artifact_type=ArtifactType.FRONTEND,
            tier=COMMUNITY,
            file_path=artifact_file
        )

        # Act
        metadata_file = artifact.write_metadata()

        # Assert
        assert metadata_file.exists()
        assert metadata_file.name == "frontend-dist-community.tar.gz.metadata.json"
        
        metadata = json.loads(metadata_file.read_text())
        assert metadata["sha256"] == artifact.sha256_hash


class TestSBOMValidation:
    """Test SBOM path validation."""

    def test_artifact_has_sbom_path(self, tmp_path):
        """Test artifact includes SBOM path."""
        # Arrange
        artifact_file = tmp_path / "frontend-dist-community.tar.gz"
        artifact_file.write_bytes(b"content")

        sbom_file = tmp_path / "sbom.json"
        sbom_file.write_text(json.dumps({
            "bomFormat": "CycloneDX",
            "components": []
        }))

        # Act
        artifact = BuildArtifact.create(
            artifact_type=ArtifactType.FRONTEND,
            tier=COMMUNITY,
            file_path=artifact_file,
            sbom_path=sbom_file
        )

        # Assert
        assert artifact.sbom_path == sbom_file

    def test_sbom_path_validated(self, tmp_path):
        """Test SBOM path validation checks file exists."""
        # Arrange
        artifact_file = tmp_path / "frontend-dist-community.tar.gz"
        artifact_file.write_bytes(b"content")

        nonexistent_sbom = tmp_path / "nonexistent-sbom.json"

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            BuildArtifact.create(
                artifact_type=ArtifactType.FRONTEND,
                tier=COMMUNITY,
                file_path=artifact_file,
                sbom_path=nonexistent_sbom
            )


class TestFileSizeCalculation:
    """Test file size calculation."""

    def test_file_size_in_bytes(self, tmp_path):
        """Test file size is computed in bytes."""
        # Arrange
        artifact_file = tmp_path / "test.tar.gz"
        content = b"x" * 1024  # 1 KB
        artifact_file.write_bytes(content)

        # Act
        artifact = BuildArtifact.create(
            artifact_type=ArtifactType.FRONTEND,
            tier=COMMUNITY,
            file_path=artifact_file
        )

        # Assert
        assert artifact.file_size_bytes == 1024

    def test_file_size_human_readable(self, tmp_path):
        """Test file size has human-readable format."""
        # Arrange
        artifact_file = tmp_path / "test.tar.gz"
        artifact_file.write_bytes(b"x" * (5 * 1024 * 1024))  # 5 MB

        # Act
        artifact = BuildArtifact.create(
            artifact_type=ArtifactType.FRONTEND,
            tier=COMMUNITY,
            file_path=artifact_file
        )

        # Assert
        assert artifact.file_size_human == "5.00 MB"


class TestProvenanceURL:
    """Test GitHub Actions provenance URL generation."""

    @patch.dict("os.environ", {
        "GITHUB_REPOSITORY": "sema4ai/actions",
        "GITHUB_RUN_ID": "123456789"
    })
    def test_provenance_url_from_ci(self, tmp_path):
        """Test provenance URL is generated from CI environment."""
        # Arrange
        artifact_file = tmp_path / "test.tar.gz"
        artifact_file.write_bytes(b"content")

        # Act
        artifact = BuildArtifact.create(
            artifact_type=ArtifactType.FRONTEND,
            tier=COMMUNITY,
            file_path=artifact_file
        )

        # Assert
        assert artifact.provenance_url is not None
        assert "github.com/sema4ai/actions/actions/runs/123456789" in artifact.provenance_url

    def test_provenance_url_none_for_local_build(self, tmp_path):
        """Test provenance URL is None for local builds."""
        # Arrange
        artifact_file = tmp_path / "test.tar.gz"
        artifact_file.write_bytes(b"content")

        # Act
        with patch.dict("os.environ", {}, clear=True):
            artifact = BuildArtifact.create(
                artifact_type=ArtifactType.FRONTEND,
                tier=COMMUNITY,
                file_path=artifact_file
            )

        # Assert
        assert artifact.provenance_url is None
