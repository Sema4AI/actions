"""Artifact validation for dual-tier build system."""

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from . import tree_shaker


@dataclass
class ValidationCheck:
    """Result of a single validation check."""
    
    name: str
    passed: bool
    message: str
    severity: str = "error"  # "error" or "warning"


@dataclass
class BuildArtifact:
    """Represents a build artifact with metadata."""
    
    tier: str
    platform: str
    file_path: Path
    sha256: Optional[str] = None
    size_bytes: Optional[int] = None
    git_commit: Optional[str] = None
    
    def compute_hash(self) -> str:
        """Compute SHA256 hash of artifact."""
        sha256_hash = hashlib.sha256()
        
        with open(self.file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        self.sha256 = sha256_hash.hexdigest()
        return self.sha256
    
    def compute_size(self) -> int:
        """Compute size of artifact in bytes."""
        self.size_bytes = self.file_path.stat().st_size
        return self.size_bytes
    
    def to_metadata_json(self) -> str:
        """Generate metadata JSON for artifact."""
        metadata = {
            "tier": self.tier,
            "platform": self.platform,
            "sha256": self.sha256 or self.compute_hash(),
            "size_bytes": self.size_bytes or self.compute_size(),
            "git_commit": self.git_commit,
        }
        return json.dumps(metadata, indent=2)


def validate_imports(artifact_path: Path, tier: str) -> ValidationCheck:
    """Validate that community artifacts have no enterprise imports."""
    if tier != "community":
        return ValidationCheck(
            name="imports",
            passed=True,
            message="Enterprise tier allows enterprise imports",
            severity="info",
        )
    
    violations = tree_shaker.detect_enterprise_imports(str(artifact_path))
    
    if violations:
        messages = [
            f"{v.prohibited_module} at line {v.line_number}" for v in violations
        ]
        return ValidationCheck(
            name="imports",
            passed=False,
            message=f"Enterprise imports detected: {', '.join(messages)}",
            severity="error",
        )
    
    return ValidationCheck(
        name="imports",
        passed=True,
        message="No enterprise imports detected",
        severity="info",
    )


def validate_size(artifact_path: Path, baseline_path: Optional[Path]) -> ValidationCheck:
    """Validate artifact size against baseline (warn if >120%)."""
    size_mb = artifact_path.stat().st_size / (1024 * 1024)
    
    if not baseline_path or not baseline_path.exists():
        return ValidationCheck(
            name="size",
            passed=True,
            message=f"Artifact size: {size_mb:.2f}MB (no baseline to compare)",
            severity="warning",
        )
    
    with open(baseline_path, "r") as f:
        baseline = json.load(f)
    
    baseline_size = baseline.get("bundle_size_mb", 0)
    if baseline_size == 0:
        return ValidationCheck(
            name="size",
            passed=True,
            message=f"Artifact size: {size_mb:.2f}MB (baseline not set)",
            severity="warning",
        )
    
    threshold = baseline_size * 1.2
    if size_mb > threshold:
        return ValidationCheck(
            name="size",
            passed=False,
            message=f"Artifact size {size_mb:.2f}MB exceeds 120% of baseline ({baseline_size:.2f}MB)",
            severity="warning",
        )
    
    return ValidationCheck(
        name="size",
        passed=True,
        message=f"Artifact size {size_mb:.2f}MB within budget (baseline: {baseline_size:.2f}MB)",
        severity="info",
    )


def validate_artifact(
    artifact_path: Path,
    tier: str,
    baseline_path: Optional[Path] = None,
    json_output: bool = False,
) -> tuple[bool, list[ValidationCheck]]:
    """Validate build artifact.
    
    Args:
        artifact_path: Path to artifact to validate
        tier: Build tier
        baseline_path: Optional path to baseline.json
        json_output: Output results as JSON
        
    Returns:
        Tuple of (all_passed, checks)
    """
    checks = []
    
    # Run validation checks
    checks.append(validate_imports(artifact_path, tier))
    checks.append(validate_size(artifact_path, baseline_path))
    
    # Determine overall result
    all_passed = all(
        check.passed or check.severity == "warning" for check in checks
    )
    
    return all_passed, checks


def main():
    """CLI entry point for artifact validation."""
    parser = argparse.ArgumentParser(description="Validate build artifacts")
    parser.add_argument("--artifact", required=True, help="Path to artifact")
    parser.add_argument("--tier", required=True, choices=["community", "enterprise"])
    parser.add_argument("--baseline", help="Path to baseline.json")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    artifact_path = Path(args.artifact)
    if not artifact_path.exists():
        print(f"Error: Artifact not found: {artifact_path}", file=sys.stderr)
        sys.exit(2)
    
    baseline_path = Path(args.baseline) if args.baseline else None
    
    all_passed, checks = validate_artifact(
        artifact_path, args.tier, baseline_path, args.json
    )
    
    if args.json:
        result = {
            "passed": all_passed,
            "checks": [
                {
                    "name": check.name,
                    "passed": check.passed,
                    "message": check.message,
                    "severity": check.severity,
                }
                for check in checks
            ],
        }
        print(json.dumps(result, indent=2))
    else:
        for check in checks:
            status = "[OK]" if check.passed else "[FAIL]"
            print(f"{status} {check.name}: {check.message}")
    
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
