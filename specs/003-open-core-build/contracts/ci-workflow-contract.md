# CI Workflow Contract

**Version**: 1.0.0  
**Date**: 2025-10-05  
**Stability**: Draft

## Overview

This contract defines the GitHub Actions CI workflow for building and validating both community and enterprise tiers across multiple platforms. The workflow uses a matrix strategy to ensure all tier × platform combinations are validated.

---

## Workflow: frontend-build.yml

**File**: `.github/workflows/frontend-build.yml`  
**Triggers**: `push`, `pull_request`, `workflow_dispatch`

### Matrix Strategy

```yaml
strategy:
  fail-fast: false  # Continue other jobs if one fails
  matrix:
    tier: [community, enterprise]
    os: [ubuntu-latest, macos-latest, windows-latest]
```

**Total Jobs**: 2 tiers × 3 operating systems = 6 parallel jobs

---

## Job: build-{tier}-{os}

### Inputs

| Input | Type | Source | Description |
|-------|------|--------|-------------|
| `matrix.tier` | string | Matrix strategy | Build tier (`community` or `enterprise`) |
| `matrix.os` | string | Matrix strategy | GitHub runner OS |
| `github.event.pull_request.head.repo.fork` | bool | GitHub context | True if PR is from external fork |

### Environment Variables

| Variable | Value | Condition | Description |
|----------|-------|-----------|-------------|
| `TIER` | `${{ matrix.tier }}` | Always | Build tier for env var precedence |
| `NPM_TOKEN` | `${{ secrets.NPM_TOKEN }}` | `matrix.tier == 'enterprise'` | Private npm registry auth |
| `NODE_VERSION` | `20.x` | Always | Node.js LTS version |
| `PYTHON_VERSION` | `3.11.x` | Always | Python version for build scripts |

### Secrets Scoping

```yaml
env:
  # Only enterprise jobs can access NPM_TOKEN
  NPM_TOKEN: ${{ matrix.tier == 'enterprise' && secrets.NPM_TOKEN || '' }}
  
  # Community jobs must have empty NPM_TOKEN (security requirement)
  # This ensures accidental use of private registry fails loudly
```

### Steps

#### 1. Checkout Code

```yaml
- name: Checkout repository
  uses: actions/checkout@v4
  with:
    fetch-depth: 0  # Full history for git commit hash
```

**Success Criteria**: Repository checked out at correct commit SHA

---

#### 2. Setup Node.js

```yaml
- name: Setup Node.js
  uses: actions/setup-node@v4
  with:
    node-version: '20.x'
    cache: 'npm'
    cache-dependency-path: action_server/frontend/package-lock.json
```

**Success Criteria**: Node v20.x installed, npm cache restored

---

#### 3. Setup Python

```yaml
- name: Setup Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.11.x'
    cache: 'pip'
```

**Success Criteria**: Python 3.11.x installed, pip cache restored

---

#### 4. Install Python Dependencies

```yaml
- name: Install build dependencies
  run: |
    pip install invoke
```

**Success Criteria**: `invoke` command available

---

#### 5. Network Hardening (Community Tier Only)

```yaml
- name: Block private registries (community tier)
  if: matrix.tier == 'community'
  run: |
    # Add hosts entries to block private npm registries
    echo "127.0.0.1 npm.pkg.github.com" | sudo tee -a /etc/hosts
    echo "127.0.0.1 registry.sema4ai.com" | sudo tee -a /etc/hosts
```

**Success Criteria**: Private registry domains resolve to localhost (unreachable)

**Rationale**: Ensures community builds cannot accidentally access private packages even if credentials leak

---

#### 6. Build Frontend

```yaml
- name: Build frontend (${{ matrix.tier }})
  run: |
    inv build-frontend --tier=${{ matrix.tier }} --json > build-result.json
  working-directory: action_server
```

**Success Criteria**: 
- Exit code 0
- `build-result.json` contains valid JSON
- Artifact file exists at reported path

**Failure Modes**:
- Exit code 1: TypeScript/Vite compilation error
- Exit code 2: Validation error (imports, licenses)
- Exit code 3: Configuration error
- Exit code 4: Dependency resolution error

---

#### 7. Validate Artifact

```yaml
- name: Validate build artifact
  run: |
    python build-binary/artifact_validator.py \
      --artifact=frontend/dist \
      --tier=${{ matrix.tier }} \
      --checks=all \
      --json > validation-result.json
  working-directory: action_server
```

**Success Criteria**:
- Exit code 0
- All checks passed (imports, licenses, size, sbom)
- `validation-result.json` contains zero failures

**Failure Modes**:
- Exit code 1: One or more validation checks failed
- Exit code 2: Invalid arguments

---

#### 8. Generate SBOM

```yaml
- name: Generate Software Bill of Materials
  run: |
    npx @cyclonedx/cyclonedx-npm --output-file sbom.json
  working-directory: action_server/frontend
```

**Success Criteria**:
- `sbom.json` exists
- Valid CycloneDX format
- Contains all installed npm packages

---

#### 9. Determinism Check (Community Tier Only)

```yaml
- name: Determinism check (rebuild and compare)
  if: matrix.tier == 'community'
  run: |
    # Save original hash
    ORIGINAL_HASH=$(sha256sum frontend/dist/index.html | cut -d' ' -f1)
    
    # Clean and rebuild
    rm -rf frontend/dist frontend/node_modules
    inv build-frontend --tier=community
    
    # Compare hashes
    REBUILD_HASH=$(sha256sum frontend/dist/index.html | cut -d' ' -f1)
    
    if [ "$ORIGINAL_HASH" != "$REBUILD_HASH" ]; then
      echo "ERROR: Non-deterministic build detected"
      echo "Original: $ORIGINAL_HASH"
      echo "Rebuild:  $REBUILD_HASH"
      exit 1
    fi
    
    echo "✓ Determinism check passed"
  working-directory: action_server
```

**Success Criteria**: Original and rebuild produce identical SHA256 hash

**Rationale**: Community builds must be reproducible for security auditing

---

#### 10. Upload Artifact

```yaml
- name: Upload build artifact
  uses: actions/upload-artifact@v4
  with:
    name: frontend-${{ matrix.tier }}-${{ matrix.os }}-${{ github.sha }}
    path: |
      action_server/frontend/dist/
      action_server/frontend/sbom.json
      build-result.json
      validation-result.json
    retention-days: 30
```

**Success Criteria**: Artifact uploaded to GitHub Actions with correct name

**Artifact Contents**:
- `dist/` - Built frontend files
- `sbom.json` - Software Bill of Materials
- `build-result.json` - Build metadata
- `validation-result.json` - Validation results

---

#### 11. Generate Job Summary

```yaml
- name: Generate job summary
  if: always()
  run: |
    echo "## Build Summary: ${{ matrix.tier }} / ${{ matrix.os }}" >> $GITHUB_STEP_SUMMARY
    echo "" >> $GITHUB_STEP_SUMMARY
    echo "**Tier**: ${{ matrix.tier }}" >> $GITHUB_STEP_SUMMARY
    echo "**OS**: ${{ matrix.os }}" >> $GITHUB_STEP_SUMMARY
    echo "**Status**: ${{ job.status }}" >> $GITHUB_STEP_SUMMARY
    echo "" >> $GITHUB_STEP_SUMMARY
    
    if [ -f build-result.json ]; then
      echo "### Build Result" >> $GITHUB_STEP_SUMMARY
      jq -r '.artifact.sha256, .artifact.size_human' build-result.json >> $GITHUB_STEP_SUMMARY
    fi
    
    if [ -f validation-result.json ]; then
      echo "### Validation Results" >> $GITHUB_STEP_SUMMARY
      jq -r '.summary | "Passed: \(.passed)/\(.total_checks)"' validation-result.json >> $GITHUB_STEP_SUMMARY
    fi
```

**Success Criteria**: Job summary visible in GitHub Actions UI

---

## Fork PR Handling

### External Contributor PRs

**Condition**: `github.event.pull_request.head.repo.fork == true`

**Behavior**:
- Only `matrix.tier == 'community'` jobs run
- Enterprise jobs skipped (no access to `NPM_TOKEN` secret)
- Network hardening enforced
- Artifact upload succeeds (community artifacts safe to share)

**Implementation**:
```yaml
jobs:
  build:
    # Skip enterprise builds for external PRs
    if: |
      matrix.tier == 'community' || 
      github.event.pull_request.head.repo.fork == false
```

### Internal PRs

**Condition**: `github.event.pull_request.head.repo.fork == false`

**Behavior**:
- All matrix jobs run (both tiers)
- Enterprise jobs have access to `NPM_TOKEN`
- No network hardening (private registry accessible)
- All artifacts uploaded

---

## Workflow: frontend-build-cdn.yml (Manual Only)

**File**: `.github/workflows/frontend-build-cdn.yml`  
**Triggers**: `workflow_dispatch` (manual only)

### Purpose

Internal convenience for quick non-customized builds. **NOT** used for release artifacts.

### Inputs

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | string | Yes | Exact CDN version to download (no "latest") |

### Job: download-cdn

```yaml
jobs:
  download-cdn:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Download from CDN
        run: |
          inv build-frontend-cdn --version=${{ inputs.version }}
        working-directory: action_server
        env:
          CDN_TOKEN: ${{ secrets.CDN_TOKEN }}
      
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: frontend-cdn-${{ inputs.version }}
          path: action_server/frontend/dist/
```

**Important**: This workflow is clearly marked "INTERNAL USE ONLY" in description and README.

---

## Exit Codes

| Code | Meaning | Next Steps |
|------|---------|------------|
| 0 | All jobs passed | Proceed to release |
| 1 | Build or validation failed | Review logs, fix issues |
| Skipped | Job conditionally skipped (e.g., enterprise on fork PR) | Expected behavior |

---

## Artifact Naming Convention

**Pattern**: `frontend-{tier}-{os}-{commit_sha}`

**Examples**:
- `frontend-community-ubuntu-latest-a3f9b12`
- `frontend-enterprise-macos-latest-a3f9b12`
- `frontend-community-windows-latest-a3f9b12`

**Contents**:
- `dist/index.html` - Built frontend (single-file)
- `sbom.json` - Software Bill of Materials
- `build-result.json` - Build metadata
- `validation-result.json` - Validation results

---

## Contract Tests

The following contract tests must pass:

1. ✅ `test_ci_matrix_generates_6_jobs()` - Verify 2×3 matrix
2. ✅ `test_ci_community_no_secrets()` - Verify NPM_TOKEN empty for community
3. ✅ `test_ci_enterprise_has_secrets()` - Verify NPM_TOKEN set for enterprise
4. ✅ `test_ci_fork_pr_community_only()` - Verify external PRs skip enterprise
5. ✅ `test_ci_artifact_naming()` - Verify artifacts follow naming convention
6. ✅ `test_ci_determinism_check_runs()` - Verify rebuild step runs for community
7. ✅ `test_ci_sbom_generated()` - Verify SBOM exists in artifact
8. ✅ `test_ci_network_hardening()` - Verify /etc/hosts modified for community
9. ✅ `test_ci_cdn_workflow_manual_only()` - Verify CDN workflow has no auto triggers

---

## Security Requirements

### Community Tier (External Contributor Safe)

1. ✅ No access to `NPM_TOKEN` secret
2. ✅ Network hardening blocks private registries
3. ✅ Artifacts safe to upload (no proprietary code)
4. ✅ Validation checks enforce OSI-only licenses
5. ✅ Determinism check ensures reproducibility

### Enterprise Tier (Internal Only)

1. ✅ `NPM_TOKEN` secret scoped to enterprise jobs only
2. ✅ Jobs fail if secret not available
3. ✅ Artifacts uploaded to internal storage (not public)
4. ✅ No network hardening (needs private registry access)

---

**Status**: ✅ READY FOR IMPLEMENTATION - Contract defined, test placeholders created
