"""Build artifact generation and management.

This module handles artifact naming, hashing, metadata generation, and SBOM validation.
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Union


class ArtifactType(str, Enum):
    """Types of build artifacts."""
    
    FRONTEND = "frontend"
    FRONTEND_BUNDLE = "frontend-bundle"
    EXECUTABLE = "executable"
    METADATA = "metadata"


@dataclass
class BuildArtifact:
    """Represents a build artifact with its properties."""
    
    artifact_type: ArtifactType
    tier: Union[str, object]
    platform: Optional[str]
    file_path: Path
    sha256: Optional[str] = None
    file_size: Optional[int] = None
    metadata: Optional[dict] = None
    build_timestamp: Optional[datetime] = None
    git_commit: Optional[str] = None
    sbom_path: Optional[Path] = None
    provenance_url: Optional[str] = None
    
    # Aliases for backwards compatibility
    @property
    def sha256_hash(self) -> Optional[str]:
        """Alias for sha256."""
        return self.sha256
    
    @property
    def file_size_bytes(self) -> Optional[int]:
        """Alias for file_size."""
        return self.file_size
    
    @property
    def file_size_human(self) -> str:
        """Get human-readable file size."""
        return self.human_readable_size()
    
    @classmethod
    def create(
        cls,
        artifact_type: ArtifactType,
        tier,
        file_path: Path,
        platform: Optional[str] = None,
        build_timestamp: Optional[datetime] = None,
        git_commit: Optional[str] = None,
        sbom_path: Optional[Path] = None,
        provenance_url: Optional[str] = None,
    ) -> "BuildArtifact":
        """Create a BuildArtifact with computed properties.
        
        Args:
            artifact_type: Type of artifact
            tier: Build tier (BuildTier object or string)
            file_path: Path to artifact file
            platform: Platform name for executables
            build_timestamp: Timestamp of build (defaults to now)
            git_commit: Git commit SHA (auto-detected if None)
            sbom_path: Path to SBOM file
            provenance_url: URL to build provenance (auto-detected from CI env)
            
        Returns:
            BuildArtifact instance
        """
        # Compute SHA256 if file exists
        sha256 = None
        file_size = None
        if file_path.exists():
            sha256 = compute_sha256(file_path)
            file_size = file_path.stat().st_size
        
        # Use current timestamp if not provided
        if build_timestamp is None:
            build_timestamp = datetime.now()
        
        # Auto-detect git commit if not provided
        if git_commit is None:
            try:
                import subprocess
                result = subprocess.run(
                    ["git", "rev-parse", "--short", "HEAD"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    # Use first 7 characters of commit SHA
                    git_commit = result.stdout.strip()[:7]
            except Exception:
                pass
        
        # Auto-detect provenance URL from CI environment
        if provenance_url is None:
            import os
            # GitHub Actions
            if os.getenv("GITHUB_ACTIONS") == "true":
                server_url = os.getenv("GITHUB_SERVER_URL", "https://github.com")
                repository = os.getenv("GITHUB_REPOSITORY", "")
                run_id = os.getenv("GITHUB_RUN_ID", "")
                if repository and run_id:
                    provenance_url = f"{server_url}/{repository}/actions/runs/{run_id}"
        
        # Validate SBOM if provided
        if sbom_path and not sbom_path.exists():
            raise FileNotFoundError(f"SBOM file not found: {sbom_path}")
        
        return cls(
            artifact_type=artifact_type,
            tier=tier,
            platform=platform,
            file_path=file_path,
            sha256=sha256,
            file_size=file_size,
            build_timestamp=build_timestamp,
            git_commit=git_commit,
            sbom_path=sbom_path,
            provenance_url=provenance_url,
        )
    
    def to_metadata_json(self) -> dict:
        """Convert artifact to metadata JSON.
        
        Returns:
            Metadata dictionary
        """
        # Get tier name
        tier_name = self.tier
        if hasattr(self.tier, 'name'):
            tier_name = self.tier.name.value if hasattr(self.tier.name, 'value') else str(self.tier.name)
        
        metadata = {
            "artifact_type": self.artifact_type.value,
            "tier": tier_name,
            "file_path": str(self.file_path),
            "sha256": self.sha256,
            "size_bytes": self.file_size,  # Use "size_bytes" for API compatibility
        }
        
        # Convert datetime to ISO string if present
        if self.build_timestamp:
            if isinstance(self.build_timestamp, datetime):
                metadata["build_timestamp"] = self.build_timestamp.isoformat()
            else:
                metadata["build_timestamp"] = self.build_timestamp
        
        if self.platform:
            metadata["platform"] = self.platform
        if self.git_commit:
            metadata["git_commit"] = self.git_commit
        if self.sbom_path:
            metadata["sbom_path"] = str(self.sbom_path)
        if self.provenance_url:
            metadata["provenance_url"] = self.provenance_url
            
        return metadata
    
    def write_metadata(self, output_path: Optional[Path] = None) -> Path:
        """Write metadata JSON to file.
        
        Args:
            output_path: Path to write metadata JSON (defaults to {file_path}.metadata.json)
            
        Returns:
            Path to written metadata file
        """
        import json
        
        if output_path is None:
            output_path = self.file_path.with_suffix(self.file_path.suffix + ".metadata.json")
        
        with open(output_path, 'w') as f:
            json.dump(self.to_metadata_json(), f, indent=2)
        
        return output_path
    
    def human_readable_size(self) -> str:
        """Get human-readable file size.
        
        Returns:
            File size string (e.g., "1.5 MB")
        """
        if self.file_size is None:
            return "unknown"
        
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"


def generate_artifact_name(
    artifact_type: ArtifactType,
    tier,
    platform: Optional[str] = None,
    commit: Optional[str] = None,
    git_commit: Optional[str] = None,  # Accept both names for compatibility
) -> str:
    """Generate artifact name following naming conventions.
    
    Args:
        artifact_type: Type of artifact to name
        tier: Build tier (BuildTier object or string "community"/"enterprise")
        platform: Platform name for executables (ubuntu, macos, windows)
        commit: Git commit SHA for executables (deprecated, use git_commit)
        git_commit: Git commit SHA for executables
        
    Returns:
        Artifact name string
    """
    # Get tier name
    tier_name = tier
    if hasattr(tier, 'name'):
        tier_name = tier.name.value if hasattr(tier.name, 'value') else str(tier.name)
    
    # Use git_commit or commit (for backwards compatibility)
    commit_sha = git_commit or commit
    
    if artifact_type in (ArtifactType.FRONTEND, ArtifactType.FRONTEND_BUNDLE):
        return f"frontend-dist-{tier_name}.tar.gz"
    elif artifact_type == ArtifactType.EXECUTABLE:
        if not platform or not commit_sha:
            raise ValueError("Executable artifacts require platform and git_commit")
        return f"action-server-{tier_name}-{platform}-{commit_sha}.zip"
    elif artifact_type == ArtifactType.METADATA:
        return f"artifact-metadata-{tier_name}.json"
    else:
        raise ValueError(f"Unknown artifact type: {artifact_type}")


def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of a file.
    
    Args:
        file_path: Path to file to hash
        
    Returns:
        SHA256 hash as hex string
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read file in chunks for memory efficiency
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def generate_metadata(
    artifact: BuildArtifact,
    build_info: Optional[dict] = None,
) -> dict:
    """Generate metadata JSON for an artifact.
    
    Args:
        artifact: BuildArtifact instance
        build_info: Additional build information (optional)
        
    Returns:
        Metadata dictionary
    """
    metadata = artifact.to_metadata_json()
    if build_info:
        metadata.update(build_info)
    return metadata
