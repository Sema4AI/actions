"""Tree shaking and import detection for dual-tier build system."""

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union


@dataclass
class ImportViolation:
    """Represents a prohibited import detected in code."""
    
    file_path: Union[str, Path]
    line_number: int
    import_statement: str
    prohibited_module: str
    severity: str = "error"  # "error" or "warning"


def scan_imports(file_path: str) -> list[ImportViolation]:
    """Scan a TypeScript/JavaScript file for enterprise imports.
    
    Only flags violations if the file is in a core/ directory.
    Enterprise files are allowed to import from enterprise modules.
    
    Args:
        file_path: Path to file to scan
        
    Returns:
        List of import violations found
    """
    violations = []
    path = Path(file_path)
    
    # Don't flag enterprise files - they're allowed to import from enterprise
    if "/enterprise/" in str(path) or "\\enterprise\\" in str(path):
        return violations
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        for line_num, line in enumerate(lines, start=1):
            # Check for @sema4ai/* imports
            sema4ai_match = re.search(r'["\'](@sema4ai/[^"\']+)["\']', line)
            if sema4ai_match:
                violations.append(
                    ImportViolation(
                        file_path=file_path,
                        line_number=line_num,
                        import_statement=line.strip(),
                        prohibited_module=sema4ai_match.group(1),  # Group 1 excludes quotes
                        severity="error",
                    )
                )
            
            # Check for @/enterprise imports
            enterprise_match = re.search(r'["\'](@/enterprise[^"\']*)["\']', line)
            if enterprise_match:
                violations.append(
                    ImportViolation(
                        file_path=file_path,
                        line_number=line_num,
                        import_statement=line.strip(),
                        prohibited_module=enterprise_match.group(1),  # Group 1 excludes quotes
                        severity="error",
                    )
                )
                
    except Exception as e:
        # If file can't be read, skip it
        pass
    
    return violations


def detect_enterprise_imports(bundle_path: str) -> list[ImportViolation]:
    """Scan a built bundle for enterprise imports.
    
    Args:
        bundle_path: Path to built JavaScript bundle
        
    Returns:
        List of import violations found
    """
    violations = []
    
    try:
        with open(bundle_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Search for @sema4ai packages in bundle
        for match in re.finditer(r'@sema4ai/[\w-]+', content):
            violations.append(
                ImportViolation(
                    file_path=bundle_path,
                    line_number=0,  # Bundle is minified, line numbers not meaningful
                    import_statement=match.group(0),
                    prohibited_module=match.group(0),
                    severity="error",
                )
            )
        
        # Search for @/enterprise references
        for match in re.finditer(r'@/enterprise/[\w/-]+', content):
            violations.append(
                ImportViolation(
                    file_path=bundle_path,
                    line_number=0,
                    import_statement=match.group(0),
                    prohibited_module=match.group(0),
                    severity="error",
                )
            )
            
    except Exception as e:
        pass
    
    return violations


def generate_vite_external_config(tier) -> dict:
    """Generate Vite external configuration for tree-shaking.
    
    Args:
        tier: Build tier (BuildTier object or string "community"/"enterprise")
        
    Returns:
        Dictionary for Vite rollupOptions configuration
    """
    # Handle both BuildTier objects and strings
    tier_name = tier
    if hasattr(tier, 'name'):
        # BuildTier object with TierName enum
        tier_name = tier.name.value if hasattr(tier.name, 'value') else str(tier.name)
    
    if tier_name == "community":
        # Exclude enterprise code from community builds
        return {
            "rollupOptions": {
                "external": [
                    re.compile(r"^@sema4ai/"),
                    re.compile(r"^@/enterprise/"),
                    re.compile(r"\.\./enterprise/"),
                ]
            }
        }
    else:
        # Enterprise builds include everything
        return {}


class TreeShaker:
    """Tree shaker for detecting and enforcing import boundaries."""
    
    def __init__(self, tier, root_dir: Path):
        """Initialize TreeShaker.
        
        Args:
            tier: BuildTier instance (COMMUNITY or ENTERPRISE)
            root_dir: Root directory to scan
        """
        self.tier = tier
        self.root_dir = Path(root_dir)
    
    def scan_directory(self, directory: Path) -> list[ImportViolation]:
        """Scan a directory recursively for import violations.
        
        Args:
            directory: Directory to scan
            
        Returns:
            List of import violations found
        """
        violations = []
        dir_path = Path(directory)
        
        # Scan all TypeScript/JavaScript files
        for pattern in ["**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx"]:
            for file_path in dir_path.glob(pattern):
                if file_path.is_file():
                    file_violations = scan_imports(str(file_path))
                    violations.extend(file_violations)
        
        return violations
    
    def generate_report(self, violations: list[ImportViolation]) -> str:
        """Generate a human-readable report of violations.
        
        Args:
            violations: List of import violations
            
        Returns:
            Formatted report string
        """
        if not violations:
            return "No import violations found."
        
        report_lines = [
            f"Found {len(violations)} import violation(s):",
            ""
        ]
        
        for violation in violations:
            file_path = violation.file_path
            if isinstance(file_path, Path):
                file_path = str(file_path)
            
            report_lines.append(
                f"  {file_path}:{violation.line_number} - "
                f"[{violation.severity.upper()}] "
                f"Prohibited import: {violation.prohibited_module}"
            )
            report_lines.append(f"    {violation.import_statement}")
            report_lines.append("")
        
        return "\n".join(report_lines)
