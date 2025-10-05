# Build System CLI Contract

**Version**: 1.0.0  
**Date**: 2025-10-05  
**Stability**: Draft

## Overview

This contract defines the command-line interface for the dual-tier build system. All commands must support both human-readable and machine-parseable (JSON) output.

---

## Command: build-frontend

**Description**: Build the Action Server frontend for a specific tier

### Signature

```bash
inv build-frontend [OPTIONS]
```

### Options

| Option | Type | Default | Required | Description |
|--------|------|---------|----------|-------------|
| `--tier` | enum | `community` | No | Build tier: `community` or `enterprise` |
| `--source` | enum | `auto` | No | Dependency source: `registry`, `vendored`, `cdn`, or `auto` (try in priority order) |
| `--debug` | flag | `false` | No | Build with debug symbols (no minification) |
| `--install` | flag | `true` | No | Run `npm ci` before build |
| `--json` | flag | `false` | No | Output results as JSON |
| `--output-dir` | path | `./dist` | No | Output directory for built files |

### Exit Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 0 | Success | Build completed successfully |
| 1 | Build Error | Compilation failed (TypeScript errors, Vite errors) |
| 2 | Validation Error | Post-build validation failed (imports, licenses, size) |
| 3 | Configuration Error | Invalid tier, missing package.json, etc. |
| 4 | Dependency Error | Failed to resolve dependencies from any source |

### Output Format (Human-Readable)

```
🔧 Action Server Frontend Build
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tier:              community
Source:            registry (public npm)
Node version:      v20.11.0
NPM version:       10.2.4

📦 Installing dependencies...
   ✓ Copied package.json.community → package.json
   ✓ Running npm ci
   ✓ Installed 42 packages in 8.3s

🏗️  Building frontend...
   ✓ vite build
   ✓ dist/index.html (342 KB)
   ✓ Build completed in 12.5s

✅ Validating artifact...
   ✓ Zero enterprise imports detected
   ✓ All licenses OSI-approved
   ✓ Bundle size: 342 KB (baseline: 320 KB, +6.9%)
   ✓ Determinism check passed

📋 Build Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Artifact:          frontend-dist-community.tar.gz
SHA256:            a3f9b1247c8...
Size:              342 KB
Duration:          21.2s
Status:            ✓ SUCCESS
```

### Output Format (JSON, `--json` flag)

```json
{
  "status": "success",
  "tier": "community",
  "source": "registry",
  "artifact": {
    "path": "/path/to/frontend-dist-community.tar.gz",
    "sha256": "a3f9b1247c8e5d3f2b1a9c4e7f8d2a5b3c6e9f1d4a7b2c5e8f1d4a7b2c5e8f1d",
    "size_bytes": 350208,
    "size_human": "342 KB"
  },
  "validation": {
    "imports_check": {"passed": true, "violations": []},
    "license_check": {"passed": true, "non_osi_packages": []},
    "size_check": {"passed": true, "baseline_bytes": 327680, "growth_percent": 6.9},
    "determinism_check": {"passed": true, "rebuild_hash_matches": true}
  },
  "metadata": {
    "node_version": "v20.11.0",
    "npm_version": "10.2.4",
    "git_commit": "a3f9b12",
    "build_timestamp": "2025-10-05T14:32:15Z",
    "duration_seconds": 21.2
  }
}
```

### Examples

```bash
# Build community tier (default)
inv build-frontend

# Build enterprise tier with explicit source
inv build-frontend --tier=enterprise --source=registry

# Build enterprise tier with vendored fallback
inv build-frontend --tier=enterprise --source=vendored

# Build with JSON output for CI
inv build-frontend --tier=community --json > build-result.json

# Debug build (no minification)
inv build-frontend --debug

# Skip npm install (dependencies already installed)
inv build-frontend --install=false
```

### Error Examples

**Invalid Tier**:
```bash
$ inv build-frontend --tier=premium
ERROR: Invalid tier 'premium'. Must be 'community' or 'enterprise'.
Exit code: 3
```

**Enterprise Import in Community Build**:
```bash
$ inv build-frontend --tier=community
...
❌ Validating artifact...
   ✗ Enterprise imports detected:
     - frontend/src/core/pages/Dashboard.tsx:12
       import { Button } from '@sema4ai/components'
     - frontend/src/core/App.tsx:8
       import { theme } from '@sema4ai/theme'
   ✓ All licenses OSI-approved
   ✓ Bundle size OK

ERROR: Validation failed (2 violations)
Exit code: 2
```

**Dependency Resolution Failure**:
```bash
$ inv build-frontend --tier=enterprise --source=registry
...
📦 Installing dependencies...
   ✓ Copied package.json.enterprise → package.json
   ✗ Failed to connect to private npm registry (timeout)
   ✗ No fallback source available (--source=registry forces single source)

ERROR: Dependency resolution failed
Exit code: 4
```

---

## Command: build-frontend-community (alias)

**Description**: Convenience alias for `inv build-frontend --tier=community`

### Signature

```bash
inv build-frontend-community [OPTIONS]
```

All options same as `build-frontend` except `--tier` (hardcoded to `community`).

---

## Command: build-frontend-enterprise (alias)

**Description**: Convenience alias for `inv build-frontend --tier=enterprise`

### Signature

```bash
inv build-frontend-enterprise [OPTIONS]
```

All options same as `build-frontend` except `--tier` (hardcoded to `enterprise`).

---

## Command: build-frontend-cdn

**Description**: Download prebuilt frontend from CDN (internal convenience, not for external use)

### Signature

```bash
inv build-frontend-cdn --version=VERSION [OPTIONS]
```

### Options

| Option | Type | Default | Required | Description |
|--------|------|---------|----------|-------------|
| `--version` | string | - | Yes | Exact CDN version to download (no "latest") |
| `--output-dir` | path | `./dist` | No | Output directory for downloaded files |
| `--json` | flag | `false` | No | Output results as JSON |

### Notes

- This command is **not** part of the community tier workflow
- Used only for internal quick builds (workflow_dispatch in CI)
- Requires valid CDN credentials
- Never used in release builds (matrix workflow only)

---

## Command: validate-artifact

**Description**: Run build guardrails against a built artifact (post-build validation)

### Signature

```bash
python action_server/build-binary/artifact_validator.py --artifact=PATH [OPTIONS]
```

### Options

| Option | Type | Default | Required | Description |
|--------|------|---------|----------|-------------|
| `--artifact` | path | - | Yes | Path to built artifact (tar.gz or directory) |
| `--tier` | enum | - | Yes | Expected tier (`community` or `enterprise`) |
| `--checks` | list | `all` | No | Comma-separated checks: `imports,licenses,size,determinism,sbom` or `all` |
| `--json` | flag | `false` | No | Output results as JSON |
| `--fail-on-warn` | flag | `false` | No | Treat warnings as errors (exit 1) |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All checks passed |
| 1 | One or more checks failed |
| 2 | Invalid arguments |

### Output Format (JSON)

```json
{
  "artifact": "/path/to/frontend-dist-community.tar.gz",
  "tier": "community",
  "checks": [
    {
      "type": "imports",
      "passed": true,
      "severity": "error",
      "message": "Zero enterprise imports detected",
      "details": {"scanned_files": 42, "violations": []}
    },
    {
      "type": "licenses",
      "passed": true,
      "severity": "error",
      "message": "All dependencies OSI-approved",
      "details": {"total_packages": 42, "non_osi": []}
    },
    {
      "type": "size",
      "passed": true,
      "severity": "warning",
      "message": "Bundle size within budget (+6.9%)",
      "details": {"size_bytes": 350208, "baseline_bytes": 327680, "growth_percent": 6.9}
    },
    {
      "type": "determinism",
      "passed": true,
      "severity": "warning",
      "message": "Rebuild produces identical hash",
      "details": {"original_hash": "a3f9b12...", "rebuild_hash": "a3f9b12...", "matches": true}
    },
    {
      "type": "sbom",
      "passed": true,
      "severity": "error",
      "message": "Valid CycloneDX SBOM found",
      "details": {"sbom_path": "/path/to/sbom.json", "format": "CycloneDX", "spec_version": "1.5"}
    }
  ],
  "summary": {
    "total_checks": 5,
    "passed": 5,
    "failed": 0,
    "warnings": 2
  }
}
```

---

## Environment Variables

| Variable | Description | Default | Used By |
|----------|-------------|---------|---------|
| `TIER` | Default build tier | `community` | `build-frontend` |
| `NPM_TOKEN` | Authentication token for private npm registry | - | `npm ci` (enterprise only) |
| `NODE_OPTIONS` | Node.js runtime options | - | All Node.js commands |
| `CI` | Signals running in CI environment | `false` | All commands (affects output formatting) |

### Precedence

CLI flag `--tier` > Environment variable `TIER` > Default (`community`)

---

## Backward Compatibility

### Deprecated Commands (to be removed in v2.0)

| Old Command | Replacement | Deprecation Date |
|-------------|-------------|------------------|
| `inv build-frontend` (no tier flag support) | `inv build-frontend --tier=community` | 2025-10-05 |

### Migration Path

Existing invocations of `inv build-frontend` without `--tier` flag will continue to work (defaults to `community`). A deprecation warning will be logged:

```
⚠️  WARNING: No --tier specified. Defaulting to 'community'.
   This behavior will become required in v2.0. Please specify --tier explicitly.
```

---

## Contract Tests

The following contract tests must pass:

1. ✅ `test_build_frontend_default_tier()` - Verify default tier is 'community'
2. ✅ `test_build_frontend_json_output()` - Verify JSON output matches schema
3. ✅ `test_build_frontend_exit_codes()` - Verify correct exit codes for each failure type
4. ✅ `test_build_frontend_artifact_naming()` - Verify artifact names match convention
5. ✅ `test_build_frontend_env_var_precedence()` - Verify TIER env var overrides default
6. ✅ `test_build_frontend_cli_flag_precedence()` - Verify --tier flag overrides TIER env var
7. ✅ `test_validate_artifact_all_checks()` - Verify all validation checks run
8. ✅ `test_validate_artifact_json_schema()` - Verify JSON output matches schema

---

**Status**: ✅ READY FOR IMPLEMENTATION - Contract defined, test placeholders created
