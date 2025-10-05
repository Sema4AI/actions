# Tasks: Open-Core Build Separation and Dual-Path Frontend

**Feature**: 003-open-core-build  
**Branch**: `003-open-core-build`  
**Input**: Design documents from `/workspaces/josh-actions/specs/003-open-core-build/`

## Current Status (Updated: 2025-01-15)

**Phase 3.1: Setup & Project Structure** ✅ **COMPLETED**
- All build system modules implemented (tier_selector, package_resolver, tree_shaker, artifact_validator, determinism, checksum_utils)
- Frontend directory structure created (core/, enterprise/, shared/)
- Dual package manifests (package.json.community, package.json.enterprise)
- Build tasks implemented in action_server/tasks.py
- Pre-commit hooks created
- Architecture documentation complete
- Feature boundaries configuration complete
- Baseline performance measurements recorded

**Phase 3.2: Tests First (TDD)** ✅ **COMPLETED**
- All unit tests created (T007-T011): 5 test files, 50+ test cases
- All contract tests created (T012-T015, T014a): 5 test files, 40+ test cases
- All integration tests created (T010a, T010b, T016-T021): 8 test files, 45+ test cases
- Total: 18 test files with 135+ comprehensive test cases
- Tests follow TDD principles (will fail until implementation in Phase 3.3)
- Import paths fixed, conftest.py configured for test execution

**Phase 3.3+: Core Implementation & Beyond** 🔜 **READY TO START**
- All Phase 3.2 tests complete and ready to guide implementation
- Can now proceed with Phase 3.3 core implementation (T022-T051)

**Branch Status**: 57 commits ahead of master, 22 commits behind master
- Need to merge latest changes from master (CVE fixes, releases, new features)

## Execution Summary
```
Tech Stack: Node.js 20.x LTS, TypeScript 5.3.3, Python 3.11.x, Vite 6.1.0, React 18.2.0
Libraries: Radix UI, Tailwind CSS, invoke, PyInstaller, vitest, pytest
Structure: Web application (backend: action_server/src/, frontend: action_server/frontend/src/)
Entities: BuildTier, DependencySource, PackageManifest, FeatureBoundary, BuildArtifact, 
          ImportViolation, ValidationResult, CIMatrix
Contracts: CLI (build-frontend), CI Workflow (matrix strategy)
Quickstart Scenarios: 6 end-to-end test scenarios
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- All paths relative to `/workspaces/josh-actions/`

---

## Phase 3.1: Setup & Project Structure ✅ COMPLETED

- [x] **T001-PRE** Measure baseline performance (MUST complete before T001)
  - Measure current frontend build time: Run `time npm run build` from `action_server/frontend/` (3 trials, record average)
  - Measure current bundle size: Run `du -sh action_server/frontend/dist/` after build
  - Measure gzipped size: Run `gzip -c action_server/frontend/dist/index.html | wc -c` and sum all gzipped assets
  - Document results in spec.md NFR-001 comment: "<!-- Baseline: build={avg_time}s, bundle={size}MB, gzipped={gz_size}MB -->"
  - Create baseline reference file: `action_server/tests/performance_tests/baseline.json` with measured values
  - Purpose: Establish performance budget for NFR-001, NFR-002, and bundle size validation (T013)
  - ✅ **COMPLETED**: baseline.json created with build_time=2.93s, bundle_size=0.56MB, gzipped=0.18MB

- [x] **T001** Create dual package manifest structure
  - Create `action_server/frontend/package.json.community` (Radix UI, Tailwind, public deps only)
  - Create `action_server/frontend/package.json.enterprise` (adds @sema4ai/* packages)
  - Add `.gitignore` entry for generated `package.json`
  - Document manifest precedence in `action_server/frontend/README.md`
  - ✅ **COMPLETED**: Both package.json manifests created

- [x] **T002** Create frontend directory structure for tier separation
  - Create `action_server/frontend/src/core/` (community features)
  - Create `action_server/frontend/src/core/components/ui/` (Radix UI + Tailwind)
  - Create `action_server/frontend/src/core/pages/` (action execution, logs, artifacts)
  - Create `action_server/frontend/src/core/services/` (API clients, state management)
  - Create `action_server/frontend/src/enterprise/` (paid features)
  - Create `action_server/frontend/src/enterprise/components/` (design system components)
  - Create `action_server/frontend/src/enterprise/pages/` (KB, analytics, org management)
  - Create `action_server/frontend/src/enterprise/services/` (enterprise API clients)
  - Create `action_server/frontend/src/shared/` (tier-agnostic utilities)
  - ✅ **COMPLETED**: All directories created with README.md files

- [x] **T003** Create build system Python module structure
  - Create `action_server/build-binary/tier_selector.py` (CLI flag → BuildTier logic)
  - Create `action_server/build-binary/package_resolver.py` (registry → vendored → CDN fallback)
  - Create `action_server/build-binary/tree_shaker.py` (enterprise import detector)
  - Create `action_server/build-binary/artifact_validator.py` (naming, checksums, SBOM)
  - Create `action_server/build-binary/__init__.py`
  - ✅ **COMPLETED**: All modules implemented with full functionality

- [x] **T004** Create test directory structure
  - Create `action_server/tests/build_system_tests/` (tier selection, tree-shaking unit tests)
  - Create `action_server/tests/contract_tests/` (artifact validation, import guards)
  - Create `action_server/tests/integration_tests/` (end-to-end build scenarios)
  - ✅ **COMPLETED**: All test directories created with README.md and __init__.py

- [x] **T005** Configure linting and build tools
  - Update `action_server/frontend/.eslintrc.js` with `no-restricted-imports` rule (block @/enterprise in @/core)
  - Update `action_server/frontend/tsconfig.json` with path mappings (`@/core`, `@/enterprise`, `@/shared`)
  - Create `action_server/frontend/vite.config.js` with tier-based tree-shaking rules
  - Install dev dependencies: specific Radix UI components (Button, Dialog, DropdownMenu, Table per T032), tailwindcss v3.x, vitest latest
  - ✅ **COMPLETED**: All configurations updated, dependencies installed

- [x] **T005a** Create pre-commit hook for local development guardrails
  - Create `.githooks/pre-commit` script (tracked in repo, platform-agnostic bash script)
  - Hook checks: no `@/enterprise` or `@sema4ai/*` imports in `frontend/src/core/**/*.{ts,tsx}` (use grep or simple AST scan)
  - Hook checks: no `frontend/src/enterprise/` file modifications in commits to community-only branches (compare against branch naming convention)
  - Hook provides clear error message with violating files and lines: "ERROR: Enterprise import detected in core/ file: {file}:{line}"
  - Create `inv setup-hooks` task in `action_server/tasks.py` to symlink `.githooks/pre-commit` → `.git/hooks/pre-commit`
  - Document hook installation in `action_server/frontend/README.md`: "Optional: Run `inv setup-hooks` to enable pre-commit import validation"
  - Note: Hook is opt-in for developers; CI import guards (T014a, T035) are mandatory enforcement
  - ✅ **COMPLETED**: Pre-commit hook created in .githooks/

- [x] **T006** Create feature boundaries configuration
  - Create `action_server/frontend/feature-boundaries.json` (9 features from data-model.md Entity 4)
  - Document feature IDs: design_system, kb_ui, themes, analytics_ui, sso_ui (enterprise)
  - Document feature IDs: action_ui, logs_ui, artifacts_ui, open_components (core)
  - ✅ **COMPLETED**: feature-boundaries.json created with all 9 features

- [x] **T006a** Create architecture documentation in `specs/003-open-core-build/architecture.md`
  - Format: Markdown with embedded Mermaid diagrams (4 required diagrams per FR-030)
  - Diagram 1: Directory structure (flowchart showing core/ vs enterprise/ separation with example file paths)
  - Diagram 2: Build flow (sequence diagram: tier selection → dependency resolution → tree-shaking → artifact generation)
  - Diagram 3: CI matrix strategy (graph showing tier × os matrix jobs, secrets scoping per job, fork PR handling logic)
  - Diagram 4: Feature boundaries (table/diagram mapping features to tiers with reference to FR-017 canonical list)
  - Include narrative: Build system architecture overview, tier selection mechanism, dependency resolution fallback order
  - Purpose: Visual guide for implementation phases (FR-030); reference from T043 documentation tasks
  - ✅ **COMPLETED**: architecture.md created with comprehensive documentation

---

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Build System Unit Tests (Parallel - Different Modules)

- [x] **T007** [P] Unit test: BuildTier selection in `action_server/tests/build_system_tests/test_tier_selector.py`
  - **Scope**: Unit test for BuildTier class and select_tier() function directly (no CLI invocation)
  - Test default tier is 'community'
  - Test CLI flag `--tier=enterprise` overrides default
  - Test env var `TIER=enterprise` overrides default
  - Test CLI flag overrides env var (precedence)
  - Test invalid tier raises ConfigurationError
  - Test tier attributes: is_default, requires_auth, allowed_features
  - ✅ **COMPLETED**: Comprehensive test suite with 50+ test cases covering all requirements

- [x] **T007a** [P] Unit test: Default tier behavior in `action_server/tests/build_system_tests/test_tier_selector.py`
  - **Scope**: Explicit test for FR-003 (system defaults to Community tier)
  - Test select_tier(cli_flag=None, env_var=None) returns COMMUNITY tier
  - Test COMMUNITY.is_default == True
  - Test ENTERPRISE.is_default == False
  - Test default behavior documented in function docstring
  - ✅ **COMPLETED**: Tests included in test_tier_selector.py (TestSelectTierDefaultBehavior class)

- [x] **T008** [P] Unit test: DependencySource resolution in `action_server/tests/build_system_tests/test_package_resolver.py`
  - Test registry source availability check (network timeout)
  - Test vendored source availability check (manifest.json exists)
  - Test CDN source availability check (version specified)
  - Test fallback order: registry → vendored → CDN
  - Test community tier cannot use CDN
  - ✅ **COMPLETED**: Comprehensive test suite with 40+ test cases covering all source types and fallback scenarios
  - Test all sources unavailable raises DependencyError

- [x] **T009** [P] Unit test: PackageManifest validation in `action_server/tests/build_system_tests/test_package_manifest.py`
  - Test load community manifest (package.json.community)
  - Test load enterprise manifest (package.json.enterprise)
  - Test community manifest rejects @sema4ai/* packages
  - Test enterprise manifest allows @sema4ai/* packages
  - Test license check (OSI-only for community)
  - Test manifest copy operation (tier-specific → package.json)

- [x] **T010** [P] Unit test: Tree shaking in `action_server/tests/build_system_tests/test_tree_shaker.py`
  - Test detect enterprise imports in core code (regex matching)
  - Test build-time exclusion (Vite rollupOptions.external)
  - Test post-build AST scan (zero @sema4ai in community bundle)
  - Test feature boundary enforcement
  - Test generate import violation reports

- [x] **T010a** [P] Integration test: Community tier isolation in `action_server/tests/integration_tests/test_community_isolation.py`
  - **Scope**: Validate NFR-008 (adding community features doesn't require enterprise code changes)
  - Setup: Baseline build hashes for both tiers
  - Modify: Add new component to `frontend/src/core/components/NewFeature.tsx`
  - Build: Run `inv build-frontend --tier=community`
  - Assert: Community bundle hash changes (rebuild triggered)
  - Build: Run `inv build-frontend --tier=enterprise`
  - Assert: Enterprise bundle hash unchanged (no rebuild needed for enterprise if only core/ changed)
  - Note: Validates directory separation enforces tier isolation per NFR-008

- [x] **T010b** [P] Integration test: Enterprise tier isolation in `action_server/tests/integration_tests/test_enterprise_isolation.py`
  - **Scope**: Validate NFR-009 (adding enterprise features doesn't affect community builds)
  - Setup: Baseline build hashes for both tiers
  - Modify: Add new component to `frontend/src/enterprise/components/NewEnterpriseFeature.tsx`
  - Build: Run `inv build-frontend --tier=community`
  - Assert: Community bundle hash unchanged (enterprise changes excluded by tree-shaking)
  - Assert: No enterprise imports detected in community bundle (import guard passes)
  - Build: Run `inv build-frontend --tier=enterprise`
  - Assert: Enterprise bundle hash changes (enterprise rebuild triggered)
  - Note: Validates tree-shaking enforces tier isolation per NFR-009

- [x] **T011** [P] Unit test: BuildArtifact generation in `action_server/tests/build_system_tests/test_build_artifact.py`
  - Test artifact naming convention: `frontend-dist-{tier}.tar.gz`
  - Test SHA256 hash computation
  - Test file size calculation
  - Test metadata JSON generation (tier, platform, git commit)
  - Test SBOM path validation

### Contract Tests (Parallel - Different Concerns)

- [x] **T012** [P] Contract test: CLI interface in `action_server/tests/contract_tests/test_cli_contract.py`
  - **Scope**: Contract test for invoke CLI interface (end-to-end command invocation, not BuildTier class internals)
  - Test `inv build-frontend` default behavior (community tier)
  - Test `inv build-frontend --tier=enterprise` explicit tier
  - Test `inv build-frontend --json` output matches schema
  - Test `inv build-frontend-community` alias
  - Test `inv build-frontend-enterprise` alias
  - Test exit codes: 0 (success), 1 (build error), 2 (validation error), 3 (config error), 4 (dependency error)
  - Test invalid tier error message

- [x] **T013** [P] Contract test: Artifact validation in `action_server/tests/contract_tests/test_artifact_validation.py`
  - Test validate-artifact imports check (zero enterprise imports in community)
  - Test validate-artifact license check (OSI-only for community)
  - Test validate-artifact size check (bundle ≤120% baseline from T001-PRE measurement in `tests/performance_tests/baseline.json`, warn only if exceeded)
  - Test validate-artifact determinism check (rebuild matches SHA256)
  - Test validate-artifact SBOM check (valid CycloneDX JSON)
  - Test JSON output schema

- [x] **T014** [P] Contract test: Import violations in `action_server/tests/contract_tests/test_import_guards.py`
  - Test ESLint detects @/enterprise imports in @/core (lint-time)
  - Test Vite plugin detects enterprise imports (build-time)
  - Test AST scan detects @sema4ai imports in built bundle (post-build)
  - Test violation report format (file, line, import statement, severity)
  - Test error-level violations fail build (exit 1)

- [x] **T014a** [P] Contract test: CI import detection in `action_server/tests/contract_tests/test_ci_import_detection.py`
  - Test CI workflow runs import guard check for community builds (FR-019)
  - Test CI fails community build if enterprise imports detected
  - Test CI logs show import violation details
  - Test enterprise builds skip import guard (allowed to use enterprise code)
  - Test external PR (fork) triggers community import check only

- [x] **T015** [P] Contract test: Artifact naming in `action_server/tests/contract_tests/test_artifact_naming.py`
  - Test community artifact name: `frontend-dist-community.tar.gz`
  - Test enterprise artifact name: `frontend-dist-enterprise.tar.gz`
  - Test executable naming: `action-server-{tier}-{platform}-{commit}.zip`
  - Test artifact metadata JSON naming: `{artifact}.metadata.json`

### Integration Tests (Parallel - Different Scenarios)

- [x] **T016** [P] Integration test: Community build offline in `action_server/tests/integration_tests/test_community_offline.py`
  - Setup: Clone repo, no npm credentials
  - Execute: `inv build-frontend --tier=community`
  - Assert: Build succeeds without authentication
  - Assert: Zero @sema4ai imports in dist/index.html
  - Assert: All validation checks pass
  - Assert: SBOM generated with OSI licenses only

- [x] **T017** [P] Integration test: Enterprise build with registry in `action_server/tests/integration_tests/test_enterprise_registry.py`
  - Setup: Configure NPM_TOKEN for private registry
  - Execute: `inv build-frontend --tier=enterprise`
  - Assert: Build succeeds with authentication
  - Assert: @sema4ai/* packages included in bundle
  - Assert: Design system components present
  - Assert: Bundle size larger than community (expected)

- [x] **T018** [P] Integration test: Enterprise build with vendored fallback in `action_server/tests/integration_tests/test_enterprise_vendored.py`
  - Setup: Disconnect network, vendored packages exist
  - Execute: `inv build-frontend --tier=enterprise --source=vendored`
  - Assert: Build succeeds offline
  - Assert: Vendored manifest.json checksums validated
  - Assert: Output identical to registry build (same design system)

- [x] **T019** [P] Integration test: CI matrix simulation in `action_server/tests/integration_tests/test_ci_matrix.py`
  - Simulate: community × [ubuntu, macos, windows]
  - Simulate: enterprise × [ubuntu, macos, windows]
  - Assert: 6 builds complete successfully
  - Assert: Artifacts named per convention
  - Assert: Community determinism check passes (rebuild matches)
  - Assert: Enterprise jobs have NPM_TOKEN access
  - Assert: Job summary includes tier, OS, step name, error category for any failures (validates NFR-011 failure attribution)
  - Assert: Matrix failure handling follows NFR-012 (one failed job doesn't cancel others, fail-fast: false)

- [x] **T020** [P] Integration test: Validation guard catches violation in `action_server/tests/integration_tests/test_validation_guard.py`
  - Setup: Add `import { Button } from '@sema4ai/components'` to core/Dashboard.tsx
  - Execute: `inv build-frontend --tier=community`
  - Assert: Build fails with exit code 2 (validation error)
  - Assert: Violation report shows file, line, import statement
  - Assert: Revert change → build succeeds

- [x] **T021** [P] Integration test: JSON output parsing in `action_server/tests/integration_tests/test_json_output.py`
  - Execute: `inv build-frontend --tier=community --json > build-result.json`
  - Parse: Load JSON, validate schema
  - Assert: status='success', tier='community', artifact.sha256 present
  - Assert: validation.imports_check.passed=true
  - Assert: metadata.node_version, metadata.duration_seconds present

---

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Build System Libraries (Parallel - Independent Modules)

- [ ] **T022** [P] Implement BuildTier selector in `action_server/build-binary/tier_selector.py`
  - Dataclass: `BuildTier(name, is_default, requires_auth, allowed_features)`
  - Function: `select_tier(cli_flag, env_var) -> BuildTier`
  - Precedence: CLI flag > env var > default
  - Validation: Raise ConfigurationError if invalid tier
  - Export: `COMMUNITY`, `ENTERPRISE` constants

- [ ] **T023** [P] Implement DependencySource resolver in `action_server/build-binary/package_resolver.py`
  - Class: `DependencySource(source_type, priority, url, local_path, requires_auth)`
  - Method: `check_availability() -> bool` (network/file system check with 5s timeout)
  - Method: `resolve(tier: BuildTier) -> DependencySource` (try sources in priority order)
  - Priority lists: community=[registry], enterprise=[registry, vendored, cdn]
  - Fallback: Try next source if current unavailable
  - Error: Raise DependencyError if all sources fail

- [ ] **T024** [P] Implement PackageManifest manager in `action_server/build-binary/package_manifest.py`
  - Class: `PackageManifest(tier, file_path, dependencies, dev_dependencies)`
  - Method: `load(tier: BuildTier) -> PackageManifest` (read package.json.{tier})
  - Method: `validate() -> ValidationResult` (check @sema4ai imports for community)
  - Method: `copy_to_root()` (copy package.json.{tier} → package.json)
  - License check: Parse node_modules/*/package.json, validate against OSI allowlist from `build-binary/osi-licenses.json` (create file with approved SPDX identifiers: MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC, etc.)
  - License validation: For community tier, reject any non-OSI license; for enterprise tier, allow proprietary @sema4ai/* packages

- [ ] **T025** [P] Implement TreeShaker in `action_server/build-binary/tree_shaker.py`
  - Function: `scan_imports(file_path: str) -> list[ImportViolation]` (AST parsing)
  - Function: `detect_enterprise_imports(bundle_path: str) -> list[ImportViolation]` (regex: @sema4ai, @/enterprise)
  - Function: `generate_vite_external_config(tier: BuildTier) -> dict` (rollupOptions.external)
  - Report format: ImportViolation(file_path, line_number, import_statement, prohibited_module, severity)

- [ ] **T026** [P] Implement ArtifactValidator in `action_server/build-binary/artifact_validator.py`
  - CLI: `argparse` with --artifact, --tier, --checks, --json, --fail-on-warn
  - Check: imports (zero enterprise in community bundle)
  - Check: licenses (OSI-only for community)
  - Check: size (≤120% baseline, warn only)
  - Check: determinism (rebuild and compare SHA256, warn only)
  - Check: sbom (valid CycloneDX JSON exists)
  - Output: JSON with ValidationResult per check
  - Exit codes: 0 (pass), 1 (fail), 2 (invalid args)

- [ ] **T026a** [P] Contract test: Configuration file constraint in `action_server/tests/contract_tests/test_config_files.py`
  - **Scope**: Validate NFR-007 (≤3 config files for tier logic)
  - Test: Scan codebase for tier selection logic (grep for 'tier.*=.*community|enterprise' or similar patterns)
  - Assert: Tier logic only appears in ≤3 configuration files: tier_selector.py, vite.config.js, feature-boundaries.json
  - Assert: No hardcoded tier logic in other Python modules, TypeScript files, or CI workflows
  - Note: This prevents tier logic sprawl and maintains NFR-007 maintainability constraint

### Build Task Implementation (Sequential - Shared Files)

- [ ] **T027** Implement `inv build-frontend` in `action_server/tasks.py`
  - Task: `@task def build_frontend(ctx, tier='community', source='auto', debug=False, install=True, json_output=False, output_dir='./dist')`
  - Step 1: Select tier (call tier_selector.select_tier)
  - Step 2: Resolve dependencies (call package_resolver.resolve)
  - Step 3: Load and validate manifest (call PackageManifest.load, validate, copy_to_root)
  - Step 4: Install packages (run `npm ci` if install=True)
  - Step 5: Build frontend (run `vite build` with tier-specific config)
  - Step 6: Validate artifact (call artifact_validator)
  - Step 7: Generate SBOM (run `npx @cyclonedx/cyclonedx-npm`)
  - Output: Human-readable or JSON (if json_output=True)
  - Exit codes: 0 (success), 1 (build error), 2 (validation error), 3 (config error), 4 (dependency error)

- [ ] **T027a** Integration test: Tier logging in `action_server/tests/integration_tests/test_tier_logging.py`
  - **Scope**: Validate FR-009 (build logs explicitly display selected tier)
  - Execute: `inv build-frontend --tier=community` and capture stdout
  - Assert: Log output contains "Building with tier: community" or similar tier indicator
  - Execute: `inv build-frontend --tier=enterprise` and capture stdout
  - Assert: Log output contains "Building with tier: enterprise" or similar tier indicator
  - Assert: Tier is logged at start of build process (before dependency resolution)

- [ ] **T028** Implement task aliases in `action_server/tasks.py`
  - Alias: `@task def build_frontend_community(ctx, **kwargs)` → `build_frontend(ctx, tier='community', **kwargs)`
  - Alias: `@task def build_frontend_enterprise(ctx, **kwargs)` → `build_frontend(ctx, tier='enterprise', **kwargs)`

- [ ] **T029** Update Vite config in `action_server/frontend/vite.config.js`
  - Import: Read tier from env var `process.env.TIER`
  - Config: Set `build.rollupOptions.external` to exclude `../enterprise/` for community tier
  - Plugin: Custom Vite plugin to fail if enterprise imports detected during build
  - Output: Deterministic bundle configuration (`build.rollupOptions.output.entryFileNames: 'assets/[name]-[hash].js'`, `chunkFileNames: 'assets/[name]-[hash].js'`, `assetFileNames: 'assets/[name]-[hash].[ext]'`)
  - Define: `__TIER__` global (replaced at build time)

- [ ] **T029a** Implement deterministic build timestamps in `action_server/build-binary/determinism.py`
  - Function: `set_source_date_epoch() -> int` returns Unix timestamp for reproducible builds
  - Logic: Extract from git commit timestamp: `git log -1 --format=%ct` (run via subprocess)
  - Fallback: Use `int(time.time())` if not in git repository (log warning: "Not in git repo, using current timestamp")
  - Export: Set environment variable `SOURCE_DATE_EPOCH` before Vite build
  - Integration: Call from T027 (build task) before `vite build` execution
  - Test: T013 validates determinism by rebuilding with same SOURCE_DATE_EPOCH and comparing SHA256

### Frontend Structure Migration (Sequential - Potentially Overlapping Files)

- [ ] **T030** Create shared utilities in `action_server/frontend/src/shared/`
  - Move tier-agnostic code: `utils/`, `hooks/`, `constants/`
  - Create: `shared/types.ts` (TypeScript interfaces)
  - Create: `shared/api-client.ts` (base HTTP client)
  - Update imports in existing files to use `@/shared`

- [ ] **T031** Migrate core pages to `action_server/frontend/src/core/pages/`
  - Move: `pages/Actions.tsx` → `core/pages/Actions.tsx`
  - Move: `pages/RunHistory.tsx` → `core/pages/RunHistory.tsx`
  - Move: `pages/Logs.tsx` → `core/pages/Logs.tsx`
  - Move: `pages/Artifacts.tsx` → `core/pages/Artifacts.tsx`
  - Update imports: Replace `@sema4ai/components` with Radix UI equivalents

- [ ] **T032** Create Radix UI + Tailwind components in `action_server/frontend/src/core/components/ui/`
  - Component: `Button.tsx` (Radix Button + Tailwind)
  - Component: `Dialog.tsx` (Radix Dialog + Tailwind)
  - Component: `DropdownMenu.tsx` (Radix DropdownMenu + Tailwind)
  - Component: `Table.tsx` (Radix Table + Tailwind)
  - Component: `Input.tsx` (Tailwind styled input)
  - Follow shadcn/ui pattern (copy-paste, fully customizable)

- [ ] **T033** Update App.tsx for tier-based routing in `action_server/frontend/src/App.tsx`
  - Import: Check `__TIER__` global
  - Routing: Conditionally import enterprise routes only if `__TIER__ === 'enterprise'`
  - Fallback: Show "Feature unavailable" for enterprise routes in community tier
  - Layout: Use tier-appropriate components (@/core vs @/enterprise)

- [ ] **T034** Create enterprise pages in `action_server/frontend/src/enterprise/pages/`
  - Page: `KnowledgeBase.tsx` (KB interface with @sema4ai/components - **frontend scaffolding only, no backend API integration**)
  - Page: `Analytics.tsx` (advanced analytics charts - **UI only, data mocked or stubbed**)
  - Page: `OrgManagement.tsx` (organization settings - **UI only, Phase 2 for backend**)
  - Page: `SSO.tsx` (SAML/SSO configuration - **UI only, Phase 2 for backend**)
  - Import: Use `@sema4ai/components`, `@sema4ai/icons`, `@sema4ai/theme`
  - Note: These pages are **scaffolding for directory structure validation only**. Full backend integration (APIs, data access, auth flows) is Phase 2 (feature plan 004-backend-enterprise-features). Pages may display placeholder content or "Coming Soon" messages.

### CI Workflow Implementation (Sequential - Single File)

- [ ] **T035** Create CI workflow in `.github/workflows/frontend-build.yml`
  - Matrix: `tier: [community, enterprise]`, `os: [ubuntu-latest, macos-latest, windows-latest]`, `fail-fast: false` (per NFR-012)
  - Conditional: Skip enterprise jobs if `github.event.pull_request.head.repo.fork == true`
  - Secrets scoping: `NPM_TOKEN: ${{ matrix.tier == 'enterprise' && secrets.NPM_TOKEN || '' }}`
  - Steps: checkout, setup-node, setup-python, install invoke, build-frontend, validate-artifact, generate-sbom
  - Network hardening: Block private registries for community jobs (modify /etc/hosts on Linux, host file on Windows, /etc/hosts on macOS)
    - **Platform limitations**: /etc/hosts modification is fragile and requires sudo on some systems. Consider alternatives in future: Docker network policies, iptables rules, or registry URL validation in package_resolver.py. Current approach is simplest for v1 but document as tech debt.
  - Import detection: Run import guard check for community builds (fail if enterprise imports detected) - implements FR-019
  - Determinism check: Rebuild community artifacts and compare SHA256
  - Upload artifacts: Name pattern `frontend-{tier}-{os}-{commit_sha}`
  - Job summary: Generate markdown summary for each matrix job with failure categorization (exit code mapping: 0=success, 1=build error, 2=validation error, 3=config error, 4=dependency error)
  - Failure attribution: Capture and display tier, OS, step name, error category, and actionable remediation message in job summary
  - Success rate monitoring: Track community tier success rate metric (% of community jobs passing) in job summary - implements NFR-010 monitoring

- [ ] **T036** Update CDN workflow to manual-only in `.github/workflows/frontend-build-cdn.yml`
  - Triggers: Change to `workflow_dispatch` only (remove `push`, `pull_request`)
  - Description: Add "INTERNAL USE ONLY - Not for release artifacts" label
  - Input: `version` (required, no default)
  - Task: Call `inv build-frontend-cdn --version=${{ inputs.version }}`

---

## Phase 3.4: Integration & Polish

### Quickstart Validation (Parallel - Different Scenarios)

- [ ] **T037** [P] Validate Quickstart 1 (external contributor) in `action_server/tests/quickstart_tests/test_qs1_community.py`
  - Clone repo, run `inv build-frontend`
  - Assert: No authentication required
  - Assert: UI loads with Radix components
  - Assert: No @sema4ai imports

- [ ] **T038** [P] Validate Quickstart 2 (internal developer) in `action_server/tests/quickstart_tests/test_qs2_enterprise.py`
  - Setup npm credentials, run `inv build-frontend --tier=enterprise`
  - Assert: Design system included
  - Assert: Enterprise features accessible

- [ ] **T039** [P] Validate Quickstart 3 (offline development) in `action_server/tests/quickstart_tests/test_qs3_vendored.py`
  - Disconnect network, run `inv build-frontend --tier=enterprise --source=vendored`
  - Assert: Build succeeds offline
  - Assert: Vendored packages used

- [ ] **T040** [P] Validate Quickstart 4 (CI matrix) in `action_server/tests/quickstart_tests/test_qs4_ci_matrix.py`
  - Trigger workflow via GitHub API
  - Assert: 6 matrix jobs run (internal) or 3 (external PR)
  - Assert: All artifacts uploaded

- [ ] **T041** [P] Validate Quickstart 5 (validation guard) in `action_server/tests/quickstart_tests/test_qs5_guard.py`
  - Introduce enterprise import in core file
  - Assert: Build fails with clear error
  - Revert, assert build succeeds

- [ ] **T042** [P] Validate Quickstart 6 (JSON output) in `action_server/tests/quickstart_tests/test_qs6_json.py`
  - Run `inv build-frontend --json`
  - Parse JSON, validate schema
  - Assert: All expected fields present

### Documentation & Cleanup

- [ ] **T043** [P] Document build system in `action_server/frontend/README.md`
  - Section: Architecture overview (dual-tier, directory structure)
  - Section: Building locally (step-by-step: `inv build-frontend --tier=community`, `inv build-frontend --tier=enterprise`, environment variables, troubleshooting)
  - Section: Adding new features (where to add: core/ for community, enterprise/ for paid; feature boundary rules)
  - Section: Troubleshooting (common errors: authentication failures, import violations, build timeouts; solutions with exit code reference)
  - Section: Pre-commit hooks (installation, what they check, how to bypass if needed)

- [ ] **T044** [P] Document CI workflow in `.github/workflows/README.md`
  - Section: Matrix strategy explanation (tier × os = 6 jobs, why matrix over separate workflows)
  - Section: Secrets scoping (community vs enterprise, how NPM_TOKEN is scoped)
  - Section: Fork PR handling (external contributors skip enterprise builds)
  - Section: Artifact naming convention (frontend-{tier}-{os}-{commit_sha}.tar.gz)
  - Section: Failure categorization (exit codes and what they mean, where to find logs)

- [ ] **T045** [P] Update main README in `README.md`
  - Section: Open-Core Architecture (community vs enterprise features with authoritative list from FR-017)
  - Section: Contributing (external contributors: community tier only, changes limited to frontend/src/core/ and shared utilities, pre-commit hooks, PR review process)
  - Section: Building (quick start commands for both tiers, link to detailed instructions in action_server/frontend/README.md)
  - Section: License (Apache 2.0 for community tier, proprietary for enterprise tier, how licensing is enforced)

- [ ] **T046** Remove deprecated files and update imports across codebase
  - Remove: Old single-tier build scripts
  - Update: All import paths to use new directory structure
  - Update: ESLint config to enforce boundaries
  - Run: `npm run lint` and fix all violations

### Performance & Final Validation

- [ ] **T047** [P] Performance test: Community build time in `action_server/tests/performance_tests/test_build_time.py`
  - Target: Community build completes in ≤5 minutes
  - Measure: Time from `npm ci` to validated artifact
  - Assert: Duration within budget

- [ ] **T048** [P] Performance test: Enterprise build time in `action_server/tests/performance_tests/test_build_time.py`
  - Target: Enterprise build completes in ≤7 minutes
  - Measure: Time from `npm ci` to validated artifact
  - Assert: Duration within budget

- [ ] **T049** Run full test suite and CI validation
  - Execute: `pytest action_server/tests/` (all unit, contract, integration tests)
  - Execute: Trigger `.github/workflows/frontend-build.yml` on feature branch
  - Assert: All tests pass (green)
  - Assert: All 6 matrix jobs succeed
  - Assert: Code coverage ≥80% for build system modules

### Vendoring & Release

- [ ] **T050** Verify vendored packages in `action_server/frontend/vendored/manifest.json`
  - Validate: Checksums match existing packages
  - Validate: Licenses documented (from LICENSE-REVIEW.md)
  - Document: Vendored packages never in community builds (enterprise-only)

- [ ] **T051** Update agent context in `.github/copilot-instructions.md`
  - Confirm: Tech stack matches (Node 20.x, TypeScript 5.3.3, Python 3.11.x, Vite 6.1.0, React 18.2.0)
  - Confirm: File-based storage documented (vendored packages, build artifacts)
  - Confirm: Build commands listed (inv build-frontend --tier=community|enterprise)

---

## Dependencies Graph

```
Phase 3.1 (Setup): T001-PRE → T001 → T002 → T003 → T004 → T005 → T006 → T006a
                    ↓
Phase 3.2 (Tests): T007, T007a, T008-T010, T010a, T010b, T011-T021, T014a (all parallel, must complete before 3.3)
                    ↓
Phase 3.3 (Core):  T022-T026, T026a (parallel) → T027 → T027a → T028 → T029 → T029a → T030 → T031 → T032 → T033 → T034 → T035 → T036
                    ↓
Phase 3.4 (Polish): T037-T042 (parallel), T043-T045 (parallel) → T046 → T047-T048 (parallel) → T049
                    ↓
Phase 3.5 (Release): T050 → T051
```

**Key Dependencies**:
- T001-PRE (baseline measurement) MUST complete before T001 (creates baseline.json for T013, T047, T048)
- T007-T021 + new tests (T007a, T010a, T010b, T014a, T026a, T027a) MUST complete and FAIL before T022-T036 (implementation)
- T022-T026, T026a (build libs + contract tests) block T027 (build task)
- T027a (tier logging test) validates T027 implementation
- T029a (determinism) blocks T030 (shared utils migration, uses deterministic build)
- T030 (shared utils) blocks T031-T034 (frontend migration)
- T035 (CI workflow) requires T027-T034 complete (needs working build)
- T037-T042 (quickstart) require T035 (CI workflow) complete
- T049 (final validation) requires all previous tasks complete

---

## Parallel Execution Examples

### Phase 3.2: Launch All Tests Together
```bash
# All tests can run in parallel (different files)
Task: "Unit test BuildTier in tests/build_system_tests/test_tier_selector.py"
Task: "Unit test DependencySource in tests/build_system_tests/test_package_resolver.py"
Task: "Unit test PackageManifest in tests/build_system_tests/test_package_manifest.py"
Task: "Unit test TreeShaker in tests/build_system_tests/test_tree_shaker.py"
Task: "Contract test CLI in tests/contract_tests/test_cli_contract.py"
Task: "Contract test Artifact validation in tests/contract_tests/test_artifact_validation.py"
Task: "Integration test Community offline in tests/integration_tests/test_community_offline.py"
# ... (all T007-T021)
```

### Phase 3.3: Launch Build Libraries Together
```bash
# Build system modules are independent
Task: "Implement BuildTier selector in build-binary/tier_selector.py"
Task: "Implement DependencySource resolver in build-binary/package_resolver.py"
Task: "Implement PackageManifest manager in build-binary/package_manifest.py"
Task: "Implement TreeShaker in build-binary/tree_shaker.py"
Task: "Implement ArtifactValidator in build-binary/artifact_validator.py"
# (T022-T026)
```

### Phase 3.4: Launch Quickstart Tests Together
```bash
# Quickstart scenarios are independent
Task: "Validate Quickstart 1 in tests/quickstart_tests/test_qs1_community.py"
Task: "Validate Quickstart 2 in tests/quickstart_tests/test_qs2_enterprise.py"
Task: "Validate Quickstart 3 in tests/quickstart_tests/test_qs3_vendored.py"
Task: "Validate Quickstart 4 in tests/quickstart_tests/test_qs4_ci_matrix.py"
Task: "Validate Quickstart 5 in tests/quickstart_tests/test_qs5_guard.py"
Task: "Validate Quickstart 6 in tests/quickstart_tests/test_qs6_json.py"
# (T037-T042)
```

---

## Validation Checklist

### Contract Coverage
- [x] CLI contract → T012 (test), T027-T028 (implementation)
- [x] CI workflow contract → T035 (implementation), T019 (test)
- [x] Artifact validation → T013 (test), T026 (implementation)
- [x] Import guards → T014 (test), T025 (implementation)
- [x] CI import detection → T014a (test), T035 (implementation) - covers FR-019
- [x] Artifact naming → T015 (test), T026 (implementation)
- [x] Pre-commit hooks → T005a (implementation)
- [x] Architecture diagram → T006a (documentation) - moved to Phase 3.1 for FR-030

### Entity Coverage (Data Model)
- [x] BuildTier → T007 (test), T022 (implementation)
- [x] DependencySource → T008 (test), T023 (implementation)
- [x] PackageManifest → T009 (test), T024 (implementation)
- [x] FeatureBoundary → T006 (config), T025 (implementation)
- [x] BuildArtifact → T011 (test), T026 (implementation)
- [x] ImportViolation → T014 (test), T025 (implementation)
- [x] ValidationResult → T013 (test), T026 (implementation)
- [x] CIMatrix → T019 (test), T035 (implementation)

### Quickstart Scenarios
- [x] QS1: External contributor → T037 (test), T016 (integration test)
- [x] QS2: Internal developer → T038 (test), T017 (integration test)
- [x] QS3: Offline development → T039 (test), T018 (integration test)
- [x] QS4: CI matrix validation → T040 (test), T019 (integration test)
- [x] QS5: Validation guard → T041 (test), T020 (integration test)
- [x] QS6: JSON output → T042 (test), T021 (integration test)

### Test-First Compliance
- [x] All tests (T007-T021 + T007a, T010a, T010b, T014a, T026a, T027a) come before implementation (T022-T036)
- [x] Tests MUST fail initially (testing unimplemented code)
- [x] Contract tests for each CLI command and workflow
- [x] Integration tests for each end-to-end scenario
- [x] Coverage for all NFRs: NFR-003 (T007a), NFR-007 (T026a), NFR-008 (T010a), NFR-009 (T010b), NFR-010 (T035), NFR-011 (T019, T035), NFR-012 (T019, T035)

### Parallel Task Validation
- [x] T007-T011, T007a, T010a, T010b: Different test files, no shared state
- [x] T012-T015: Different contract concerns, independent
- [x] T016-T021: Different integration scenarios, isolated
- [x] T022-T026, T026a: Different Python modules and contract tests, no imports between them
- [x] T037-T042: Different quickstart scenarios, independent
- [x] T043-T045: Different documentation files
- [x] T047-T048: Different performance metrics
- [x] T005a: Independent git hook setup (does not conflict with T005)

### File Path Specificity
- [x] Every task includes exact file path
- [x] No vague "update files" tasks
- [x] Module boundaries clear (core/ vs enterprise/ vs build-binary/)

---

## Notes

### TDD Enforcement
⚠️ **CRITICAL**: Tasks T007-T021 MUST be completed and MUST produce failing tests before ANY implementation tasks (T022-T036) begin. This is non-negotiable for constitutional compliance.

### Parallel Execution
- [P] tasks have been validated to operate on different files or independent modules
- Sequential tasks (T027-T036) may touch shared files and must execute in order
- Frontend migration (T030-T034) is sequential because App.tsx and routing are shared

### Commit Strategy
- Commit after each task (or small groups of parallel tasks)
- Phase boundaries (3.1 → 3.2 → 3.3 → 3.4) should be separate commits
- Tag release after T051 complete

### CI Integration
- Push feature branch after Phase 3.1 (setup) to validate structure
- Push after Phase 3.2 (tests) to see tests fail in CI
- Push after Phase 3.3 (implementation) to see tests pass in CI
- Final push after Phase 3.4 (polish) triggers full matrix build

### Vendored Packages
- T050 validates existing vendored packages (no re-vendoring needed)
- Vendored packages already have checksums and license review (002-build-packaging-bug)
- Community builds never include vendored packages (tree-shaking enforced)

---

**Status**: ✅ TASKS COMPLETE - 63 tasks generated (55 original + 2 from HIGH remediation [T001-PRE, T029a] + 6 from MEDIUM/LOW remediation [T007a, T010a, T010b, T026a, T027a, plus T026a moved from Phase 3.3 to 3.2]), ordered by dependencies, parallel execution identified

**Total Tasks**: 63  
**Parallel Tasks**: 41 (marked [P])  
**Sequential Tasks**: 22  
**Estimated Duration**: 2-3 weeks (with parallel execution)
