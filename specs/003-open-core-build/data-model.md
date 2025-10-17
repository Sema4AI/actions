# Data Model: Open-Core Build System

**Feature**: 003-open-core-build  
**Date**: 2025-10-05  
**Status**: Design Phase

## Overview

This document defines the key entities, their attributes, relationships, and validation rules for the dual-tier build system. These entities are primarily configuration and metadata objects rather than persistent data models.

---

## Entity 1: BuildTier

**Description**: Represents the selected build configuration tier (Community or Enterprise)

**Attributes**:
| Attribute | Type | Required | Default | Validation |
|-----------|------|----------|---------|------------|
| name | enum('community', 'enterprise') | Yes | 'community' | Must be exact string match |
| is_default | bool | No | Computed | True only for 'community' |
| requires_auth | bool | No | Computed | True only for 'enterprise' |
| allowed_features | list[str] | No | Computed | Feature IDs from FeatureBoundary |

**Relationships**:
- One-to-many with DependencySource (each tier has priority list)
- One-to-many with FeatureBoundary (defines included features)
- One-to-one with BuildArtifact (each artifact tied to one tier)

**State Transitions**:
```
[Unset] --select_tier()--> [Community|Enterprise]
    ↓
[Community] --validate()--> [Valid] or [Invalid]
[Enterprise] --validate()--> [Valid] or [Invalid] + auth check
```

**Validation Rules**:
1. Tier name must be lowercase ('community' or 'enterprise', not 'Community')
2. Environment variable `TIER` overrides default but CLI flag `--tier` overrides both
3. Community tier must never have `requires_auth=True`
4. Enterprise tier validation includes npm credentials check

**Implementation Notes**:
- Python dataclass: `@dataclass class BuildTier`
- CLI parsing: `argparse` with `choices=['community', 'enterprise']`
- Default in invoke task: `@task def build_frontend(ctx, tier='community')`

---

## Entity 2: DependencySource

**Description**: Represents a source for frontend npm packages (private registry, vendored files, or CDN)

**Attributes**:
| Attribute | Type | Required | Default | Validation |
|-----------|------|----------|---------|------------|
| source_type | enum('registry', 'vendored', 'cdn') | Yes | - | Must be valid enum value |
| priority | int | Yes | - | 1 (highest) to 3 (lowest) |
| url | str | Conditional | - | Required for 'registry' and 'cdn' types |
| local_path | Path | Conditional | - | Required for 'vendored', must exist |
| requires_auth | bool | No | False | True only for 'registry' |
| available | bool | No | Computed | Runtime check (network, files) |

**Relationships**:
- Many-to-one with BuildTier (tier determines source priority list)
- One-to-many with PackageManifest (each source produces manifest)

**Priority Order** (by tier):
- **Community**: 
  1. registry (public npm only) - priority 1
  
- **Enterprise**:
  1. registry (private npm) - priority 1
  2. vendored (local files) - priority 2
  3. cdn (prebuilt download) - priority 3

**State Transitions**:
```
[Pending] --check_availability()--> [Available|Unavailable]
    ↓
[Available] --fetch_packages()--> [Success|Failure]
    ↓
[Failure] --fallback_to_next()--> [Try next priority source]
```

**Validation Rules**:
1. Registry source must have valid URL (https://)
2. Vendored source must have existing directory with manifest.json
3. CDN source must have version specified (no "latest")
4. Community tier cannot use CDN source
5. At least one source must be available or build fails

**Implementation Notes**:
- Python class: `class DependencySource` with `check_availability()` method
- Fallback logic: Try sources in priority order until success
- Timeout: Network checks timeout after 5 seconds

---

## Entity 3: PackageManifest

**Description**: Declarative list of npm dependencies for a specific tier

**Attributes**:
| Attribute | Type | Required | Default | Validation |
|-----------|------|----------|---------|------------|
| tier | BuildTier | Yes | - | Must be valid tier |
| file_path | Path | Yes | - | package.json.{tier} must exist |
| dependencies | dict[str, str] | Yes | {} | Package name → version |
| dev_dependencies | dict[str, str] | No | {} | Package name → version |
| locked | bool | No | False | True if package-lock.json exists |
| license_approved | bool | No | Computed | OSI-only for community tier |

**Relationships**:
- Many-to-one with BuildTier (each tier has one manifest)
- One-to-one with LockFile (manifest → lock file)
- One-to-many with InstalledPackage (manifest defines packages to install)

**Manifest File Paths**:
- Community: `action_server/frontend/package.json.community`
- Enterprise: `action_server/frontend/package.json.enterprise`
- Generated: `action_server/frontend/package.json` (copied from tier-specific)

**Validation Rules**:
1. Community manifest must NOT contain `@sema4ai/*` packages
2. Enterprise manifest must contain valid versions (no `*` or `latest`)
3. All packages must declare licenses in package.json metadata
4. Community tier requires `license_approved=True` before build proceeds
5. Manifest file must be valid JSON

**Implementation Notes**:
- Load with `json.load()`
- Validation: Regex check for `@sema4ai` in community manifest → fail
- License check: Parse `node_modules/*/package.json` for `license` field
- Copy operation: `shutil.copy(f'package.json.{tier}', 'package.json')`

---

## Entity 4: FeatureBoundary

**Description**: Defines which code paths/features are included in each tier

**Attributes**:
| Attribute | Type | Required | Default | Validation |
|-----------|------|----------|---------|------------|
| feature_id | str | Yes | - | Unique identifier (e.g., 'kb_ui') |
| tier | BuildTier | Yes | - | Tier this feature belongs to |
| module_path | Path | Yes | - | Relative path to feature module |
| import_pattern | str | Yes | - | Regex for detecting imports |
| is_frontend | bool | Yes | - | True for UI features |
| is_backend | bool | Yes | - | True for API features |

**Relationships**:
- Many-to-one with BuildTier (tier contains multiple features)
- One-to-many with ImportViolation (feature → detected violations)

**Feature Mapping** (from spec FR-017):

| Feature ID | Tier | Module Path | Description |
|------------|------|-------------|-------------|
| design_system | enterprise | frontend/src/enterprise/components/ds | @sema4ai design system |
| kb_ui | enterprise | frontend/src/enterprise/pages/knowledge-base | KB interface |
| themes | enterprise | frontend/src/enterprise/components/themes | Branding pack |
| analytics_ui | enterprise | frontend/src/enterprise/pages/analytics | Advanced analytics |
| sso_ui | enterprise | frontend/src/enterprise/pages/sso | SSO/SAML UI |
| action_ui | core | frontend/src/core/pages/actions | Action execution UI |
| logs_ui | core | frontend/src/core/pages/logs | Run history/logs |
| artifacts_ui | core | frontend/src/core/pages/artifacts | Artifacts view |
| open_components | core | frontend/src/core/components/ui | Radix + Tailwind |

**Validation Rules**:
1. Enterprise features must have `module_path` starting with `frontend/src/enterprise/`
2. Core features must have `module_path` starting with `frontend/src/core/`
3. Import patterns must be valid regex
4. Feature IDs must be unique across all tiers
5. At least one feature must exist for core tier (sanity check)

**Implementation Notes**:
- Configuration file: `action_server/frontend/feature-boundaries.json`
- AST scanning: Use regex to find imports in built JS bundle
- Vite config: Generate `build.rollupOptions.external` from enterprise module paths

---

## Entity 5: BuildArtifact

**Description**: Compiled output of frontend or backend build process

**Attributes**:
| Attribute | Type | Required | Default | Validation |
|-----------|------|----------|---------|------------|
| artifact_type | enum('frontend', 'executable') | Yes | - | Must be valid type |
| tier | BuildTier | Yes | - | Tier used for build |
| platform | enum('linux', 'macos', 'windows') | Yes | - | Target OS |
| file_path | Path | Yes | - | Absolute path to artifact |
| sha256_hash | str | No | Computed | 64-char hex string |
| file_size_bytes | int | No | Computed | Positive integer |
| build_timestamp | datetime | No | Computed | ISO 8601 format |
| git_commit | str | No | Computed | 7-char short SHA |
| sbom_path | Path | No | Computed | Path to CycloneDX SBOM |
| provenance_url | str | No | Computed | GitHub Actions attestation URL |

**Relationships**:
- Many-to-one with BuildTier (tier → multiple artifacts across platforms)
- One-to-one with SBOM (artifact → software bill of materials)
- One-to-many with ValidationResult (artifact → validation checks)

**Naming Convention**:
```
Frontend: frontend-dist-{tier}.tar.gz
Executable: action-server-{tier}-{platform}-{git_commit}.zip

Examples:
- frontend-dist-community.tar.gz
- action-server-community-linux-a3f9b12.zip
- action-server-enterprise-macos-a3f9b12.zip
```

**Validation Rules**:
1. Artifact file must exist at `file_path`
2. SHA256 hash must match recomputed hash (determinism check)
3. File size for community frontend must be <5MB (sanity check)
4. SBOM must exist for all artifacts
5. Git commit must match current `git rev-parse HEAD`

**Implementation Notes**:
- Hash computation: `hashlib.sha256(file_content).hexdigest()`
- Metadata file: `{artifact_name}.metadata.json` alongside artifact
- Upload to CI: GitHub Actions artifact with retention policy

---

## Entity 6: ImportViolation

**Description**: Detected unauthorized import of enterprise code in community tier

**Attributes**:
| Attribute | Type | Required | Default | Validation |
|-----------|------|----------|---------|------------|
| violation_id | str | Yes | Computed | UUID |
| file_path | Path | Yes | - | Relative path to violating file |
| line_number | int | Yes | - | Line where import occurs |
| import_statement | str | Yes | - | Exact import text |
| prohibited_module | str | Yes | - | Enterprise module being imported |
| severity | enum('error', 'warning') | Yes | 'error' | Must be valid level |

**Relationships**:
- Many-to-one with BuildArtifact (artifact may have multiple violations)
- Many-to-one with FeatureBoundary (violation references prohibited feature)

**Detection Methods**:
1. **Lint-time**: ESLint `no-restricted-imports` rule
2. **Build-time**: Vite plugin scanning import graph
3. **Post-build**: AST parsing of built JS bundle

**Validation Rules**:
1. Error-level violations must fail build (exit code 1)
2. Warning-level violations logged but don't fail (for future restrictions)
3. Violation must reference existing FeatureBoundary
4. File path must be relative to project root

**Implementation Notes**:
- Report format: JSON array of violations
- ESLint config: `.eslintrc.js` with `no-restricted-imports` rule
- CI failure: `if violations: sys.exit(1)`

---

## Entity 7: ValidationResult

**Description**: Result of running build guardrails against an artifact

**Attributes**:
| Attribute | Type | Required | Default | Validation |
|-----------|------|----------|---------|------------|
| check_type | enum('imports', 'licenses', 'size', 'determinism', 'sbom') | Yes | - | Valid check type |
| artifact | BuildArtifact | Yes | - | Artifact being validated |
| passed | bool | Yes | - | True if check passed |
| message | str | No | '' | Human-readable result |
| details | dict | No | {} | Check-specific data |
| timestamp | datetime | No | Computed | When check ran |

**Relationships**:
- Many-to-one with BuildArtifact (artifact → multiple validation results)

**Check Types**:

| Check Type | Pass Criteria | Failure Action |
|------------|---------------|----------------|
| imports | Zero enterprise imports in community bundle | Fail build (exit 1) |
| licenses | All deps OSI-approved for community tier | Fail build (exit 1) |
| size | Bundle size ≤120% of baseline | Warn (log, don't fail) |
| determinism | Rebuild produces identical SHA256 hash | Warn (log, don't fail) |
| sbom | SBOM file exists and valid CycloneDX JSON | Fail build (exit 1) |

**Validation Rules**:
1. All error-level checks must pass before artifact upload
2. Warning-level failures must be logged to CI summary
3. Timestamp must be UTC timezone
4. Details dict must be JSON-serializable

**Implementation Notes**:
- Runner: `action_server/build-binary/artifact_validator.py`
- CLI: `python artifact_validator.py --artifact=path --checks=imports,licenses,size`
- Output: JSON report written to `{artifact}.validation.json`

---

## Entity 8: CIMatrix

**Description**: GitHub Actions matrix configuration for multi-tier, multi-platform builds

**Attributes**:
| Attribute | Type | Required | Default | Validation |
|-----------|------|----------|---------|------------|
| tier | list[BuildTier] | Yes | - | At least one tier |
| os | list[str] | Yes | - | Valid GitHub runner names |
| include_external_prs | bool | No | True | Community only for forks |
| secrets_scope | dict | Yes | - | Tier → secret names mapping |

**Relationships**:
- One-to-many with BuildArtifact (matrix → artifacts for each combo)
- One-to-one with WorkflowRun (matrix config → CI execution)

**Matrix Definition**:
```yaml
strategy:
  matrix:
    tier: [community, enterprise]
    os: [ubuntu-latest, macos-latest, windows-latest]
```

**Secrets Scoping**:
```yaml
env:
  NPM_TOKEN: ${{ matrix.tier == 'enterprise' && secrets.NPM_TOKEN || '' }}
```

**Validation Rules**:
1. External PRs (forks) must only trigger community tier builds
2. Enterprise jobs must have NPM_TOKEN available
3. Community jobs must NOT have access to any secrets
4. At least one OS must be in matrix
5. Matrix must produce deterministic job names

**Implementation Notes**:
- Workflow file: `.github/workflows/frontend-build.yml`
- Job name: `build-${{ matrix.tier }}-${{ matrix.os }}`
- Artifact upload: One artifact per matrix combination

---

## Relationships Diagram

```
BuildTier (1) ----< (N) DependencySource
    |                       |
    |                       v
    |               PackageManifest (1) --- (1) LockFile
    |
    +------< (N) FeatureBoundary
    |                       |
    |                       v
    |               ImportViolation
    |
    +------< (N) BuildArtifact
                    |
                    +------< (N) ValidationResult
                    |
                    +------ (1) SBOM
                    
CIMatrix ----< (N) BuildArtifact
```

---

## State Machine: Build Process

```
[Start] 
  → select_tier() 
  → [Tier Selected: Community|Enterprise]

[Tier Selected]
  → load_manifest()
  → [Manifest Loaded]

[Manifest Loaded]
  → resolve_dependencies()
  → [Dependencies Resolved: Registry|Vendored|CDN]

[Dependencies Resolved]
  → install_packages()
  → [Packages Installed]

[Packages Installed]
  → build_frontend()
  → [Frontend Built]

[Frontend Built]
  → validate_artifact()
  → [Validation: Pass|Fail]

[Validation Pass]
  → generate_sbom()
  → [SBOM Generated]

[SBOM Generated]
  → upload_artifact()
  → [Complete]

[Validation Fail]
  → log_violations()
  → [Build Failed]

[Dependencies Unavailable]
  → try_fallback_source()
  → [Dependencies Resolved] or [Build Failed]
```

---

## Next Steps

1. Generate contracts from these entities (OpenAPI/JSON schemas)
2. Create failing unit tests for entity validation rules
3. Create failing contract tests for artifact naming, SBOM generation
4. Generate quickstart scenarios exercising full build process

---

**Status**: ✅ COMPLETE - Data model defined, ready for contract generation
