"""Package manifest management for dual-tier build system."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ValidationResult:
    """Result of manifest validation."""
    
    passed: bool
    errors: list[str]
    warnings: list[str]


class PackageManifest:
    """Manages package.json manifests for different tiers."""
    
    def __init__(self, tier: str, file_path: Path):
        """Initialize manifest manager.
        
        Args:
            tier: Build tier ("community" or "enterprise")
            file_path: Path to tier-specific package.json file
        """
        self.tier = tier
        self.file_path = file_path
        self.data = {}
        
    @classmethod
    def load(cls, tier: str, frontend_dir: Path) -> "PackageManifest":
        """Load tier-specific package.json.
        
        Args:
            tier: Build tier ("community" or "enterprise")
            frontend_dir: Path to frontend directory
            
        Returns:
            PackageManifest instance
        """
        file_path = frontend_dir / f"package.json.{tier}"
        
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
        
        # Check for @sema4ai/* imports in community tier
        if self.tier == "community":
            deps = self.data.get("dependencies", {})
            for dep_name in deps:
                if dep_name.startswith("@sema4ai/"):
                    errors.append(
                        f"Community tier cannot include proprietary package: {dep_name}"
                    )
        
        # Check required fields
        required_fields = ["name", "version", "dependencies"]
        for field in required_fields:
            if field not in self.data:
                errors.append(f"Missing required field: {field}")
        
        return ValidationResult(
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )
    
    def copy_to_root(self, frontend_dir: Path) -> None:
        """Copy tier-specific manifest to root package.json.
        
        Args:
            frontend_dir: Path to frontend directory
        """
        target_path = frontend_dir / "package.json"
        
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)
            f.write("\n")  # Add trailing newline
