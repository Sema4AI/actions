# Phase 0: Research & Technical Decisions

**Feature**: Remove Private Package Dependencies from Build  
**Date**: October 3, 2025

## Research Findings

### 1. Vendoring Strategy for NPM Packages

**Decision**: Use local file references (`file:./vendored/...`) in package.json instead of vendoring at build time.

**Rationale**:
- NPM supports `file:` protocol for local package dependencies
- Vite can resolve local packages as efficiently as registry packages
- No build-time overhead compared to authenticated registry access
- Simpler than creating a local npm registry mirror
- Maintains standard `npm ci && npm run build` workflow

**Alternatives Considered**:
1. **Webpack alias/resolve** - More complex, requires Vite config changes, less standard
2. **Local npm registry (Verdaccio)** - Overkill for 3 packages, adds infrastructure dependency
3. **Git submodules** - Doesn't solve the private registry problem, just moves it
4. **Copy during build** - Adds build-time overhead, violates 0% performance constraint

**Implementation**: Replace private GitHub Packages references in package.json with:
```json
"@sema4ai/components": "file:./vendored/components",
"@sema4ai/icons": "file:./vendored/icons",
"@sema4ai/theme": "file:./vendored/theme"
```

### 2. Vendored Asset Structure

**Decision**: Store complete npm package contents (package.json, dist/, etc.) under `vendored/` subdirectories.

**Rationale**:
- NPM `file:` protocol expects a complete package directory structure
- Preserves original package.json metadata for dependency resolution
- Allows npm to handle transitive dependencies normally
- Simplifies updates (replace entire directory)

**Structure**:
```
frontend/vendored/
├── components/
│   ├── package.json
│   ├── dist/           # Compiled JS/CSS
│   └── ...
├── icons/
│   ├── package.json
│   ├── dist/
│   └── ...
├── theme/
│   ├── package.json
│   ├── dist/
│   └── ...
└── manifest.json       # Our tracking file
```

**Alternatives Considered**:
1. **Flat dist/ files only** - Breaks npm package resolution, requires custom Vite config
2. **Monorepo workspace** - Overly complex for vendored read-only assets
3. **Tarballs (.tgz)** - Requires extraction step, less transparent than directories

### 3. Checksum & Integrity Verification

**Decision**: Generate SHA256 checksums for each package directory and store in `manifest.json`.

**Rationale**:
- Constitutional requirement (V. Vendored Builds)
- Detects tampering or corruption
- Enables CI validation without re-downloading
- Simple to generate (Python hashlib) and verify

**Manifest Format**:
```json
{
  "version": "1.0",
  "updated": "2025-10-03T00:00:00Z",
  "packages": {
    "@sema4ai/components": {
      "version": "0.1.1",
      "sha256": "abc123...",
      "source": "https://npm.pkg.github.com/@sema4ai/components/-/components-0.1.1.tgz",
      "license": "SEE LICENSE IN LICENSE"
    }
  }
}
```

**Alternatives Considered**:
1. **Per-file checksums** - More granular but overkill for read-only packages
2. **Git LFS** - Doesn't provide checksum validation, adds infrastructure dependency
3. **Signed tarballs** - Requires key management, excessive for internal packages

### 4. Automated Update Process

**Decision**: GitHub Actions workflow running monthly via cron schedule.

**Rationale**:
- GitHub Actions already used in project CI
- Cron schedule (first of month) matches clarified requirement
- Can authenticate to private registry using GITHUB_TOKEN
- Automated PR creation via GitHub CLI (`gh pr create`)

**Workflow Steps**:
1. Authenticate to GitHub Packages (GITHUB_TOKEN)
2. Download latest versions of three packages
3. Extract to temporary directory
4. Generate checksums, update manifest.json
5. Compare with current vendored/ content
6. If changes detected: commit to branch, create PR
7. If no changes: exit silently (no noise)

**Alternatives Considered**:
1. **Dependabot** - Doesn't support private registries or custom vendoring logic
2. **Renovate Bot** - Same limitations as Dependabot
3. **Manual process** - Violates clarified requirement for automated updates
4. **Webhook-triggered** - Real-time not needed, monthly cadence sufficient

### 5. CI Validation Strategy

**Decision**: Single unauthenticated CI job; remove or isolate authenticated job.

**Rationale**:
- Clarified requirement: unauthenticated-only testing
- Simpler CI configuration
- Internal Sema4.ai builds will continue to work (vendored assets used by default)
- Reduces credential management complexity

**CI Job Requirements**:
- Fresh checkout (no credentials)
- Run `npm ci && npm run build`
- Assert exit code 0
- Assert `dist/` directory exists and contains expected files
- Verify checksums in manifest.json match vendored/ content

**Alternatives Considered**:
1. **Both authenticated and unauthenticated** - Rejected per clarification (Option B chosen)
2. **Authenticated with fallback** - More complex, not required
3. **No CI changes** - Doesn't validate the fix works

### 6. Build Performance Analysis

**Decision**: Measure and document build time before/after vendoring; must be ≤0% increase.

**Rationale**:
- Clarified constraint: 0% build time increase allowed
- Local file references should be equal or faster than registry downloads
- No network latency for package resolution
- NPM caching behavior unchanged

**Measurement Approach**:
- Baseline: Time authenticated build on clean checkout
- Post-vendoring: Time unauthenticated build with vendored assets
- Run 10 iterations each, report median
- Document in quickstart.md

**Risk Mitigation**:
- If vendoring adds overhead: investigate npm linking instead of copying
- If still problematic: question the constraint with stakeholders (unlikely given local files are faster)

### 7. Documentation Requirements

**Decision**: Update README, CONTRIBUTING.md, and create frontend/vendored/README.md.

**Rationale**:
- External contributors need clear build instructions
- Maintainers need vendoring/update instructions
- Constitutional requirement for documented processes

**Documentation Sections**:
- **README.md**: Add "Building from Source" section mentioning no credentials needed
- **CONTRIBUTING.md**: Add "Vendored Dependencies" section explaining structure
- **frontend/vendored/README.md**: Explain what's vendored, why, and how to update
- **quickstart.md**: Step-by-step external build validation

## Unknowns Resolved

All technical unknowns from the specification have been resolved:
- ✅ Vendoring approach selected and validated (local file: references)
- ✅ Update automation strategy defined (GitHub Actions monthly cron)
- ✅ CI validation approach clarified (unauthenticated-only)
- ✅ Performance constraint strategy defined (measure and document)
- ✅ No remaining blockers for Phase 1

## Next Steps

Proceed to Phase 1: Design & Contracts
- Define data model (manifest.json schema)
- Create contract tests (build validation, checksum verification)
- Generate quickstart.md for external contributor validation
- Create failing test stubs
