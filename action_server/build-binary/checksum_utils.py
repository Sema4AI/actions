"""
Checksum calculation utility for vendored packages.

This module provides utilities for calculating SHA256 checksums of package
directories in a deterministic way for integrity verification.
"""

import hashlib
import os
from pathlib import Path


def calculate_package_checksum(package_dir: Path) -> str:
    """
    Calculate SHA256 checksum of all files in package directory.
    
    Files are processed in sorted order for deterministic results.
    Symlinks are skipped for cross-platform compatibility.
    
    Args:
        package_dir: Path to the package directory
        
    Returns:
        Hexadecimal SHA256 checksum string (64 characters)
        
    Example:
        >>> from pathlib import Path
        >>> checksum = calculate_package_checksum(Path("vendored/components"))
        >>> len(checksum)
        64
    """
    hasher = hashlib.sha256()
    
    # Walk directory in sorted order for determinism
    for root, dirs, files in os.walk(package_dir):
        dirs.sort()  # Sort subdirectories in place
        for filename in sorted(files):
            filepath = Path(root) / filename
            # Skip symlinks for cross-platform compatibility
            if filepath.is_symlink():
                continue
            with open(filepath, 'rb') as f:
                hasher.update(f.read())
    
    return hasher.hexdigest()


def verify_package_checksum(package_dir: Path, expected_checksum: str) -> bool:
    """
    Verify that a package directory matches the expected checksum.
    
    Args:
        package_dir: Path to the package directory
        expected_checksum: Expected SHA256 checksum (64-character hex string)
        
    Returns:
        True if checksums match, False otherwise
        
    Example:
        >>> from pathlib import Path
        >>> is_valid = verify_package_checksum(
        ...     Path("vendored/components"),
        ...     "abc123..."
        ... )
    """
    if not package_dir.exists():
        return False
    
    if not package_dir.is_dir():
        return False
    
    calculated = calculate_package_checksum(package_dir)
    return calculated.lower() == expected_checksum.lower()
