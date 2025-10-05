"""Tree shaking and import detection for dual-tier build system."""

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ImportViolation:
    """Represents a prohibited import detected in code."""
    
    file_path: str
    line_number: int
    import_statement: str
    prohibited_module: str
    severity: str = "error"  # "error" or "warning"


def scan_imports(file_path: str) -> list[ImportViolation]:
    """Scan a TypeScript/JavaScript file for enterprise imports.
    
    Args:
        file_path: Path to file to scan
        
    Returns:
        List of import violations found
    """
    violations = []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        for line_num, line in enumerate(lines, start=1):
            # Check for @sema4ai/* imports
            sema4ai_match = re.search(r'["\']@sema4ai/[^"\']+["\']', line)
            if sema4ai_match:
                violations.append(
                    ImportViolation(
                        file_path=file_path,
                        line_number=line_num,
                        import_statement=line.strip(),
                        prohibited_module=sema4ai_match.group(0),
                        severity="error",
                    )
                )
            
            # Check for @/enterprise imports
            enterprise_match = re.search(r'["\']@/enterprise[^"\']*["\']', line)
            if enterprise_match:
                violations.append(
                    ImportViolation(
                        file_path=file_path,
                        line_number=line_num,
                        import_statement=line.strip(),
                        prohibited_module=enterprise_match.group(0),
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


def generate_vite_external_config(tier_name: str) -> dict:
    """Generate Vite external configuration for tree-shaking.
    
    Args:
        tier_name: Build tier ("community" or "enterprise")
        
    Returns:
        Dictionary for Vite rollupOptions.external
    """
    if tier_name == "community":
        # Exclude enterprise code from community builds
        return {
            "external": [
                re.compile(r"^@sema4ai/"),
                re.compile(r"^@/enterprise/"),
                re.compile(r"\.\./enterprise/"),
            ]
        }
    else:
        # Enterprise builds include everything
        return {}
