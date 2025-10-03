"""
Contract test: Vendored packages maintain cryptographic integrity.

This test validates the Constitutional requirement (V. Vendored Builds)
for checksum verification of all vendored build artifacts.
"""
import hashlib
import json
from pathlib import Path
import pytest


class TestVendoredIntegrity:
    """Validate vendored package checksums and completeness."""
    
    @pytest.fixture(scope="class")
    def vendored_dir(self):
        """Path to vendored packages directory."""
        return Path(__file__).parent.parent.parent / "frontend" / "vendored"
    
    @pytest.fixture(scope="class")
    def manifest_data(self, vendored_dir):
        """Load and parse manifest.json."""
        manifest_path = vendored_dir / "manifest.json"
        assert manifest_path.exists(), (
            "manifest.json not found in vendored directory"
        )
        
        with open(manifest_path, "r") as f:
            data = json.load(f)
        
        return data
    
    def calculate_package_checksum(self, package_dir: Path) -> str:
        """
        Calculate SHA256 checksum of all files in package directory.
        
        Files are processed in sorted order for deterministic results.
        """
        hasher = hashlib.sha256()
        
        # Walk directory in sorted order for determinism
        for root, dirs, files in package_dir.walk():
            # Sort subdirectories for deterministic traversal
            dirs.sort()
            for filename in sorted(files):
                filepath = root / filename
                # Skip symlinks for cross-platform compatibility
                if filepath.is_symlink():
                    continue
                with open(filepath, "rb") as f:
                    hasher.update(f.read())
        
        return hasher.hexdigest()
    
    def test_manifest_exists(self, vendored_dir):
        """MUST: manifest.json exists in vendored directory."""
        manifest_path = vendored_dir / "manifest.json"
        assert manifest_path.exists(), (
            f"manifest.json not found at {manifest_path}"
        )
    
    def test_manifest_valid_json(self, manifest_data):
        """MUST: manifest.json is valid JSON."""
        assert isinstance(manifest_data, dict)
        assert "version" in manifest_data
        assert "packages" in manifest_data
        assert isinstance(manifest_data["packages"], dict)
    
    def test_manifest_schema_compliance(self, manifest_data):
        """MUST: manifest.json follows the defined schema."""
        assert "version" in manifest_data
        assert "updated" in manifest_data
        assert "updatedBy" in manifest_data
        assert "packages" in manifest_data
        
        # Validate each package entry
        for package_name, package_info in manifest_data["packages"].items():
            assert "version" in package_info, (
                f"Package {package_name} missing 'version'"
            )
            assert "sha256" in package_info, (
                f"Package {package_name} missing 'sha256'"
            )
            assert "source" in package_info, (
                f"Package {package_name} missing 'source'"
            )
            assert "license" in package_info, (
                f"Package {package_name} missing 'license'"
            )
            assert "vendoredDate" in package_info, (
                f"Package {package_name} missing 'vendoredDate'"
            )
            
            # Validate SHA256 format (64 hex characters)
            sha256 = package_info["sha256"]
            assert len(sha256) == 64, (
                f"Package {package_name} SHA256 is {len(sha256)} chars, "
                f"expected 64"
            )
            assert all(c in "0123456789abcdef" for c in sha256.lower()), (
                f"Package {package_name} SHA256 contains invalid characters"
            )
    
    def test_all_packages_have_directories(self, vendored_dir, manifest_data):
        """MUST: Each package in manifest has a corresponding directory."""
        for package_name in manifest_data["packages"].keys():
            # Extract directory name (remove @scope/ prefix)
            dir_name = package_name.split("/")[-1]
            package_dir = vendored_dir / dir_name
            
            assert package_dir.exists(), (
                f"Package directory not found: {package_dir}"
            )
            assert package_dir.is_dir(), (
                f"Package path is not a directory: {package_dir}"
            )
    
    def test_no_orphaned_packages(self, vendored_dir, manifest_data):
        """MUST: No extra package directories exist beyond manifest entries."""
        # Get expected directory names from manifest
        expected_dirs = set()
        for package_name in manifest_data["packages"].keys():
            dir_name = package_name.split("/")[-1]
            expected_dirs.add(dir_name)
        
        # Get actual directories (excluding files like manifest.json)
        actual_dirs = set()
        for item in vendored_dir.iterdir():
            if item.is_dir():
                actual_dirs.add(item.name)
        
        orphaned = actual_dirs - expected_dirs
        assert len(orphaned) == 0, (
            f"Orphaned package directories found (not in manifest): {orphaned}"
        )
    
    def test_package_checksums_match(self, vendored_dir, manifest_data):
        """MUST: Calculated checksums match manifest checksums."""
        mismatches = []
        
        for package_name, package_info in manifest_data["packages"].items():
            dir_name = package_name.split("/")[-1]
            package_dir = vendored_dir / dir_name
            
            expected_checksum = package_info["sha256"]
            calculated_checksum = self.calculate_package_checksum(package_dir)
            
            if expected_checksum != calculated_checksum:
                mismatches.append({
                    "package": package_name,
                    "expected": expected_checksum,
                    "calculated": calculated_checksum,
                })
        
        assert len(mismatches) == 0, (
            f"Checksum mismatches detected:\n" +
            "\n".join(
                f"  {m['package']}: expected {m['expected']}, "
                f"got {m['calculated']}"
                for m in mismatches
            )
        )
    
    def test_package_json_exists_in_each_package(
        self, vendored_dir, manifest_data
    ):
        """MUST: Each vendored package has a package.json file."""
        for package_name in manifest_data["packages"].keys():
            dir_name = package_name.split("/")[-1]
            package_json = vendored_dir / dir_name / "package.json"
            
            assert package_json.exists(), (
                f"package.json not found in {package_name}"
            )
            
            # Validate it's valid JSON
            with open(package_json, "r") as f:
                pkg_data = json.load(f)
            
            assert "name" in pkg_data
            assert "version" in pkg_data
    
    def test_required_packages_present(self, manifest_data):
        """MUST: All required design system packages are vendored."""
        required_packages = [
            "@sema4ai/components",
            "@sema4ai/icons",
            "@sema4ai/theme",
        ]
        
        for required in required_packages:
            assert required in manifest_data["packages"], (
                f"Required package {required} not found in manifest"
            )
    
    @pytest.mark.slow
    def test_checksum_reproducibility(self, vendored_dir, manifest_data):
        """SHOULD: Checksum calculation is deterministic."""
        # Calculate checksums twice and ensure they match
        for package_name in manifest_data["packages"].keys():
            dir_name = package_name.split("/")[-1]
            package_dir = vendored_dir / dir_name
            
            checksum1 = self.calculate_package_checksum(package_dir)
            checksum2 = self.calculate_package_checksum(package_dir)
            
            assert checksum1 == checksum2, (
                f"Checksum calculation for {package_name} is non-deterministic"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
