#!/usr/bin/env python3
"""
Vendoring automation script for frontend design system packages.

This script automates the process of downloading, extracting, and checksumming
npm packages from GitHub Packages registry for vendoring into the repository.
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Import checksum utility
from checksum_utils import calculate_package_checksum


def download_package(package_name: str, version: str, output_dir: Path) -> Path:
    """
    Download an npm package using npm pack.
    
    Args:
        package_name: Full package name (e.g., '@sema4ai/components')
        version: Package version (e.g., '0.1.1')
        output_dir: Directory to download the package to
        
    Returns:
        Path to the downloaded tarball
        
    Raises:
        RuntimeError: If npm pack fails
    """
    package_spec = f"{package_name}@{version}"
    print(f"Downloading {package_spec}...")
    
    try:
        result = subprocess.run(
            ["npm", "pack", package_spec],
            cwd=output_dir,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Extract tarball filename from output
        tarball_name = result.stdout.strip().split('\n')[-1]
        tarball_path = output_dir / tarball_name
        
        if not tarball_path.exists():
            raise RuntimeError(f"Expected tarball not found: {tarball_path}")
            
        print(f"Downloaded to {tarball_path}")
        return tarball_path
        
    except subprocess.CalledProcessError as e:
        print(f"Error downloading package: {e.stderr}")
        raise RuntimeError(f"Failed to download {package_spec}") from e


def extract_package(tarball_path: Path, extract_dir: Path) -> Path:
    """
    Extract npm package tarball.
    
    npm pack creates tarballs with a 'package/' directory at the root.
    
    Args:
        tarball_path: Path to the tarball file
        extract_dir: Directory to extract to
        
    Returns:
        Path to the extracted package directory
    """
    print(f"Extracting {tarball_path}...")
    
    subprocess.run(
        ["tar", "-xzf", str(tarball_path)],
        cwd=extract_dir,
        check=True
    )
    
    package_dir = extract_dir / "package"
    if not package_dir.exists():
        raise RuntimeError(f"Expected 'package/' directory not found after extraction")
    
    print(f"Extracted to {package_dir}")
    return package_dir


def vendor_package(
    package_name: str,
    version: str,
    vendored_root: Path,
    manifest_path: Path,
    updated_by: str = "manual"
) -> None:
    """
    Vendor a single npm package.
    
    Args:
        package_name: Full package name (e.g., '@sema4ai/components')
        version: Package version
        vendored_root: Root directory for vendored packages
        manifest_path: Path to manifest.json
        updated_by: Who/what is performing the update
    """
    # Determine target directory name (remove @scope/ prefix)
    dir_name = package_name.split('/')[-1]
    target_dir = vendored_root / dir_name
    
    # Create temporary directory for download/extract
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Download package
        tarball_path = download_package(package_name, version, temp_path)
        
        # Extract package
        package_dir = extract_package(tarball_path, temp_path)
        
        # Calculate checksum before moving
        print(f"Calculating checksum for {package_name}...")
        checksum = calculate_package_checksum(package_dir)
        print(f"Checksum: {checksum}")
        
        # Remove existing vendored directory if present
        if target_dir.exists():
            print(f"Removing existing {target_dir}...")
            shutil.rmtree(target_dir)
        
        # Move package to vendored directory
        print(f"Moving to {target_dir}...")
        shutil.move(str(package_dir), str(target_dir))
        
        # Update manifest
        update_manifest(
            manifest_path,
            package_name,
            version,
            checksum,
            updated_by
        )
        
        print(f"✓ Successfully vendored {package_name}@{version}")


def update_manifest(
    manifest_path: Path,
    package_name: str,
    version: str,
    checksum: str,
    updated_by: str
) -> None:
    """
    Update the vendor manifest with package information.
    
    Args:
        manifest_path: Path to manifest.json
        package_name: Package name
        version: Package version
        checksum: SHA256 checksum
        updated_by: Who/what is performing the update
    """
    # Load existing manifest
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    # Update package entry
    manifest["packages"][package_name] = {
        "version": version,
        "sha256": checksum,
        "source": f"https://npm.pkg.github.com/{package_name}/-/{package_name.split('/')[-1]}-{version}.tgz",
        "license": "SEE LICENSE IN LICENSE",
        "vendoredDate": datetime.now(timezone.utc).isoformat()
    }
    
    # Update manifest metadata
    manifest["updated"] = datetime.now(timezone.utc).isoformat()
    manifest["updatedBy"] = updated_by
    
    # Write updated manifest
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
        f.write('\n')  # Add trailing newline
    
    print(f"Updated manifest: {manifest_path}")


def update_all_packages(vendored_root: Path, manifest_path: Path) -> None:
    """
    Check for updates to all vendored packages.
    
    Args:
        vendored_root: Root directory for vendored packages
        manifest_path: Path to manifest.json
    """
    # Load manifest
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    if not manifest.get("packages"):
        print("No packages in manifest to update")
        return
    
    print("Checking for package updates...")
    
    for package_name, package_info in manifest["packages"].items():
        current_version = package_info["version"]
        print(f"\nChecking {package_name} (current: {current_version})")
        
        # Query npm for latest version
        try:
            result = subprocess.run(
                ["npm", "view", package_name, "version"],
                capture_output=True,
                text=True,
                check=True
            )
            latest_version = result.stdout.strip()
            
            if latest_version != current_version:
                print(f"  → Update available: {latest_version}")
                print(f"  → Run: python vendor-frontend.py --package {package_name} --version {latest_version}")
            else:
                print(f"  → Up to date")
                
        except subprocess.CalledProcessError as e:
            print(f"  → Error checking version: {e.stderr}")


def main():
    """Main entry point for the vendoring script."""
    parser = argparse.ArgumentParser(
        description="Vendor npm packages for the Action Server frontend"
    )
    parser.add_argument(
        "--package",
        help="Package name to vendor (e.g., '@sema4ai/components')"
    )
    parser.add_argument(
        "--version",
        help="Package version to vendor (e.g., '0.1.1')"
    )
    parser.add_argument(
        "--update-all",
        action="store_true",
        help="Check all vendored packages for updates"
    )
    parser.add_argument(
        "--updated-by",
        default="manual",
        help="Who/what is performing the update (default: manual)"
    )
    
    args = parser.parse_args()
    
    # Determine paths
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    vendored_root = repo_root / "frontend" / "vendored"
    manifest_path = vendored_root / "manifest.json"
    
    # Validate paths
    if not vendored_root.exists():
        print(f"Error: Vendored directory not found: {vendored_root}")
        sys.exit(1)
    
    if not manifest_path.exists():
        print(f"Error: Manifest not found: {manifest_path}")
        sys.exit(1)
    
    # Execute command
    if args.update_all:
        update_all_packages(vendored_root, manifest_path)
    elif args.package and args.version:
        vendor_package(
            args.package,
            args.version,
            vendored_root,
            manifest_path,
            args.updated_by
        )
    else:
        parser.print_help()
        print("\nError: Either --package and --version, or --update-all must be specified")
        sys.exit(1)


if __name__ == "__main__":
    main()
