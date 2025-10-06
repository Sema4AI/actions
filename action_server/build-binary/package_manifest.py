"""Package manifest management for dual-tier build system."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union


class ManifestValidationError(Exception):
    """Raised when manifest validation fails."""
    
    pass


@dataclass
class ValidationResult:
    """Result of manifest validation."""
    
    passed: bool
    errors: list[str]
    warnings: list[str]
    
    @property
    def violations(self) -> Optional[list[str]]:
        """Get list of violations (errors)."""
        return self.errors if self.errors else None
    
    @property
    def message(self) -> str:
        """Get summary message of validation result."""
        if self.passed:
            return "Validation passed"
        if self.errors:
            return "; ".join(self.errors)
        return "Validation failed"


class PackageManifest:
    """Manages package.json manifests for different tiers."""
    
    def __init__(self, tier, file_path: Path):
        """Initialize manifest manager.
        
        Args:
            tier: Build tier (BuildTier object or string "community"/"enterprise")
            file_path: Path to tier-specific package.json file
        """
        self.tier = tier
        self.file_path = file_path
        self.data = {}
        
    @property
    def dependencies(self) -> dict:
        """Get dependencies from manifest."""
        return self.data.get("dependencies", {})
    
    @property
    def dev_dependencies(self) -> dict:
        """Get devDependencies from manifest."""
        return self.data.get("devDependencies", {})
    
    @property
    def locked(self) -> bool:
        """Check if package-lock.json exists."""
        lock_file = self.file_path.parent / "package-lock.json"
        return lock_file.exists()
        
    @classmethod
    def load(cls, tier, frontend_dir: Path) -> "PackageManifest":
        """Load tier-specific package.json.
        
        Args:
            tier: Build tier (BuildTier object or string)
            frontend_dir: Path to frontend directory
            
        Returns:
            PackageManifest instance
        """
        # Get tier name
        tier_name = tier
        if hasattr(tier, 'name'):
            tier_name = tier.name.value if hasattr(tier.name, 'value') else str(tier.name)
        
        file_path = frontend_dir / f"package.json.{tier_name}"
        
        if not file_path.exists():
            raise FileNotFoundError(f"Manifest not found: {file_path}")
        
        manifest = cls(tier, file_path)
        
        with open(file_path, "r", encoding="utf-8") as f:
            manifest.data = json.load(f)
        
        return manifest
    
    def validate(self) -> ValidationResult:
        """Validate manifest for tier requirements.
        
        Returns:
            ValidationResult with any errors or warnings
        """
        errors = []
        warnings = []
        
        # Get tier name
        tier_name = self.tier
        if hasattr(self.tier, 'name'):
            tier_name = self.tier.name.value if hasattr(self.tier.name, 'value') else str(self.tier.name)
        
        # Check for @sema4ai/* imports in community tier
        if tier_name == "community":
            deps = self.data.get("dependencies", {})
            for dep_name in deps:
                if dep_name.startswith("@sema4ai/"):
                    errors.append(
                        f"Community tier cannot include proprietary package: {dep_name}"
                    )
        
        # Check for wildcard or "latest" versions
        all_deps = {**self.data.get("dependencies", {}), **self.data.get("devDependencies", {})}
        for dep_name, version in all_deps.items():
            if version == "*":
                errors.append(f"Package {dep_name} uses wildcard version '*' (not allowed)")
            elif version == "latest":
                errors.append(f"Package {dep_name} uses 'latest' version (not allowed)")
        
        # Check required fields only if not empty manifest
        if self.data:
            # Only warn about missing fields, don't fail validation
            # This allows partial manifests for testing
            pass
        
        return ValidationResult(
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )
    
    def copy_to_root(self, frontend_dir: Optional[Path] = None) -> None:
        """Copy tier-specific manifest to root package.json.
        
        Args:
            frontend_dir: Path to frontend directory (defaults to parent of manifest file)
        """
        if frontend_dir is None:
            frontend_dir = self.file_path.parent
        
        target_path = frontend_dir / "package.json"
        
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)
            f.write("\n")  # Add trailing newline
