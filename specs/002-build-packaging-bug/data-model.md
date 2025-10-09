# Data Model: Vendored Package Manifest

**Feature**: Remove Private Package Dependencies from Build  
**Date**: October 3, 2025

## Overview

The vendored package system requires a machine-readable manifest to track package versions, checksums, and metadata for Constitutional compliance (V. Vendored Builds).

## Entity: Vendor Manifest

**File**: `action_server/frontend/vendored/manifest.json`

**Purpose**: Track all vendored npm packages with cryptographic integrity, licensing, and provenance information.

### Schema

```typescript
interface VendorManifest {
  version: string;           // Manifest schema version (semver)
  updated: string;           // ISO 8601 timestamp of last update
  updatedBy: string;         // "manual" | "automation" | email/username
  packages: {
    [packageName: string]: VendoredPackage;
  };
}

interface VendoredPackage {
  version: string;           // Package semantic version
  sha256: string;            // SHA256 checksum of package directory contents
  source: string;            // Original registry URL or tarball location
  license: string;           // SPDX license identifier or "SEE LICENSE IN <file>"
  vendoredDate: string;      // ISO 8601 timestamp when vendored
  notes?: string;            // Optional: reason for version, known issues, etc.
}
```

### Example

```json
{
  "version": "1.0.0",
  "updated": "2025-10-03T12:00:00Z",
  "updatedBy": "automation",
  "packages": {
    "@sema4ai/components": {
      "version": "0.1.1",
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "source": "https://npm.pkg.github.com/@sema4ai/components/-/components-0.1.1.tgz",
      "license": "SEE LICENSE IN LICENSE",
      "vendoredDate": "2025-10-03T12:00:00Z",
      "notes": "Initial vendoring for issue #220"
    },
    "@sema4ai/icons": {
      "version": "0.1.2",
      "sha256": "d14a028c2a3a2bc9476102bb288234c415a2b01f828ea62ac5b3e42f",
      "source": "https://npm.pkg.github.com/@sema4ai/icons/-/icons-0.1.2.tgz",
      "license": "SEE LICENSE IN LICENSE",
      "vendoredDate": "2025-10-03T12:00:00Z"
    },
    "@sema4ai/theme": {
      "version": "0.1.1-RC1",
      "sha256": "6dcd4ce23d88e2ee9568ba546c007c63d9131c1b",
      "source": "https://npm.pkg.github.com/@sema4ai/theme/-/theme-0.1.1-RC1.tgz",
      "license": "SEE LICENSE IN LICENSE",
      "vendoredDate": "2025-10-03T12:00:00Z"
    }
  }
}
```

## Validation Rules

1. **Version Format**: Must be valid semantic versioning (x.y.z or x.y.z-prerelease)
2. **SHA256 Format**: Must be 64-character hexadecimal string
3. **Source URL**: Must be HTTPS URL or file path
4. **License**: Must be non-empty string
5. **Timestamps**: Must be valid ISO 8601 format
6. **Package Names**: Must match directory names under `vendored/`
7. **Uniqueness**: Each package name appears exactly once

## State Transitions

```
[Not Vendored] 
    ↓ (manual vendoring script)
[Vendored - Current]
    ↓ (monthly automation detects update)
[Update Available]
    ↓ (automation creates PR)
[PR Under Review]
    ↓ (maintainer approves + merges)
[Vendored - Updated]
```

## Relationships

```
VendorManifest (1) ──contains──> (N) VendoredPackage
VendoredPackage (1) ──references──> (1) PackageDirectory
PackageDirectory (N) ──used by──> (1) package.json (via file: protocol)
```

## Entity: Package Directory

**Location**: `action_server/frontend/vendored/<package-name>/`

**Purpose**: Contains complete npm package structure for local resolution.

### Structure

```
vendored/<package-name>/
├── package.json          # Required: npm package metadata
├── dist/                 # Compiled outputs (JS, CSS, etc.)
│   ├── index.js
│   ├── index.css
│   └── ...
├── LICENSE               # License file (if present in original)
└── README.md             # Optional: original README
```

### Constraints

- Directory name MUST match package name in manifest (without @scope/ prefix)
- package.json MUST be valid and contain at minimum: name, version, main/exports
- All files referenced by package.json (main, exports, types) MUST exist
- No symlinks (for cross-platform compatibility)
- No node_modules subdirectories (dependencies should be hoisted)

## Checksum Calculation

**Algorithm**: SHA256 of concatenated file contents in deterministic order.

**Implementation**:
```python
import hashlib
import os
from pathlib import Path

def calculate_package_checksum(package_dir: Path) -> str:
    """Calculate SHA256 checksum of all files in package directory."""
    hasher = hashlib.sha256()
    
    # Walk directory in sorted order for determinism
    for root, dirs, files in os.walk(package_dir):
        dirs.sort()  # Sort subdirectories
        for filename in sorted(files):
            filepath = Path(root) / filename
            with open(filepath, 'rb') as f:
                hasher.update(f.read())
    
    return hasher.hexdigest()
```

**Verification**: CI job recalculates checksums and compares with manifest.json on every build.

## Usage in Build Process

**Before (with private registry)**:
```json
"dependencies": {
  "@sema4ai/components": "0.1.1",
  "@sema4ai/icons": "0.1.2",
  "@sema4ai/theme": "0.1.1-RC1"
}
```

**After (with vendored packages)**:
```json
"dependencies": {
  "@sema4ai/components": "file:./vendored/components",
  "@sema4ai/icons": "file:./vendored/icons",
  "@sema4ai/theme": "file:./vendored/theme"
}
```

NPM resolves `file:` references by symlinking (Unix) or copying (Windows) during `npm install`, making vendored packages indistinguishable from registry packages during build.

## Maintenance Operations

### Initial Vendoring
1. Authenticate to GitHub Packages
2. Download packages via `npm pack <package>@<version>`
3. Extract tarballs to `vendored/<package-name>/`
4. Calculate checksums
5. Generate manifest.json
6. Commit to repository

### Automated Updates
1. Query GitHub Packages API for latest versions
2. Compare with manifest.json versions
3. If newer version exists:
   - Download new package
   - Extract to temporary directory
   - Calculate new checksum
   - Update manifest.json
   - Create git branch and PR

### Manual Updates
1. Maintainer downloads new package version
2. Runs `python build-binary/vendor-frontend.py --update <package-name>`
3. Script validates, calculates checksum, updates manifest
4. Maintainer reviews diff and commits

## Security Considerations

1. **Checksum Verification**: CI MUST verify checksums on every build to detect tampering
2. **Source Provenance**: manifest.json MUST record original source URL for auditability
3. **License Compliance**: All vendored packages MUST have license declarations
4. **No Secrets**: Vendored packages MUST NOT contain API keys, tokens, or credentials
5. **Version Pinning**: Exact versions MUST be recorded (no ^, ~, or * ranges)

## Documentation References

- Constitution V: Vendored Builds & Reproducible Releases
- Research finding #2: Vendored Asset Structure
- Research finding #3: Checksum & Integrity Verification
