# Tasks: Remove Private Package Dependencies from Build

**Feature Branch**: `002-build-packaging-bug`  
**Input**: Design documents from `/var/home/kdlocpanda/second_brain/Resources/robocorp-forks/actions/specs/002-build-packaging-bug/`  
**Prerequisites**: plan.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

## Execution Summary

This task list implements vendoring of three private design system packages to enable external contributors to build the Action Server frontend without private registry authentication.

**Tech Stack**:
- Frontend: Node.js 20.x LTS, TypeScript 5.3.3, Vite 6.1.0, React 18.2.0
- Build Automation: Python 3.11.x
- Testing: pytest (Python), Vitest (TypeScript)

**Key Constraints**:
- Test-First Development (TDD) - All tests MUST fail before implementation
- 0% build time increase tolerance
- Constitutional compliance (Vendored Builds)

---

## Phase 3.1: Setup & Infrastructure

### T001 Create vendored directory structure
**Path**: `action_server/frontend/vendored/`  
**Description**: Create the directory structure for vendored packages:
```
action_server/frontend/vendored/
├── components/  (empty initially)
├── icons/       (empty initially)
├── theme/       (empty initially)
└── .gitkeep     (ensure directory is tracked)
```
**Dependencies**: None  
**Parallel**: Can be done independently

---

### T002 Create manifest.json schema file
**Path**: `action_server/frontend/vendored/manifest.json`  
**Description**: Create initial manifest.json with schema structure (no packages yet):
```json
{
  "version": "1.0.0",
  "updated": "2025-10-03T00:00:00Z",
  "updatedBy": "manual",
  "packages": {}
}
```
Refer to data-model.md for complete schema specification.  
**Dependencies**: T001  
**Parallel**: No (same directory as T001)

---

### T003 [P] Create vendoring automation script
**Path**: `action_server/build-binary/vendor-frontend.py`  
**Description**: Create Python script to automate vendoring process:
- Authenticate to GitHub Packages using provided credentials
- Download specified package versions via npm
- Extract tarballs to vendored/ directories
- Calculate SHA256 checksums per data-model.md algorithm
- Update manifest.json with package metadata
- Validate all required files present

Include CLI interface:
```bash
python vendor-frontend.py --package @sema4ai/components --version 0.1.1
python vendor-frontend.py --update-all  # Check and update all packages
```

Refer to research.md decision #2 and #3 for implementation details.  
**Dependencies**: None (can be developed in parallel)  
**Parallel**: Yes

---

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL**: These tests MUST be written and MUST FAIL before ANY implementation in Phase 3.3.

### T004 [P] Contract test: Unauthenticated build succeeds
**Path**: `action_server/tests/action_server_tests/test_frontend_build_unauthenticated.py`  
**Description**: Implement all contract tests from `contracts/build-contract.md`:
- `test_npm_ci_succeeds_without_auth` - Verify npm ci works without credentials
- `test_npm_build_succeeds_without_auth` - Verify npm run build works
- `test_build_output_exists` - Verify dist/ directory and files created
- `test_no_private_registry_access` - Verify no requests to npm.pkg.github.com
- `test_build_time_performance` - Benchmark build time (must be ≤ baseline)

All tests MUST FAIL initially (packages not yet vendored).  
**Dependencies**: None  
**Parallel**: Yes

---

### T005 [P] Contract test: Vendored integrity verification
**Path**: `action_server/tests/action_server_tests/test_vendored_integrity.py`  
**Description**: Implement all contract tests from `contracts/vendor-integrity-contract.md`:
- `test_manifest_exists` - Verify manifest.json exists
- `test_manifest_valid_json` - Verify JSON is parseable
- `test_manifest_schema_compliance` - Verify schema per data-model.md
- `test_all_packages_have_directories` - Verify directories match manifest
- `test_no_orphaned_packages` - Verify no extra directories
- `test_package_checksums_match` - Verify SHA256 checksums match
- `test_package_json_exists_in_each_package` - Verify package.json files
- `test_required_packages_present` - Verify all 3 packages vendored
- `test_checksum_reproducibility` - Verify deterministic checksums

All tests MUST FAIL initially (packages not yet vendored).  
**Dependencies**: None  
**Parallel**: Yes

---

### T006 [P] Integration test: Quickstart validation
**Path**: `action_server/tests/action_server_tests/test_quickstart_validation.py`  
**Description**: Create integration test that validates the quickstart.md workflow:
- Clone simulation (use existing repo)
- Verify vendored/ directory exists and is complete
- Run npm ci without authentication
- Run npm run build
- Verify dist/ output
- Measure build time

This test validates the end-to-end external contributor experience.  
**Dependencies**: None  
**Parallel**: Yes

---

### T007 [P] Unit test: Checksum calculation
**Path**: `action_server/tests/action_server_tests/test_checksum_utils.py`  
**Description**: Create unit tests for checksum calculation utility:
- Test deterministic file ordering
- Test empty directory handling
- Test symlink handling (should fail or skip)
- Test binary vs text file handling
- Test reproducibility across runs

This can be written before the utility exists (TDD).  
**Dependencies**: None  
**Parallel**: Yes

---

## Phase 3.3: Core Implementation (ONLY after tests are failing)

**GATE**: Do NOT proceed until T004-T007 are committed and verified FAILING.

### T008 Implement checksum calculation utility
**Path**: `action_server/build-binary/checksum_utils.py`  
**Description**: Implement SHA256 checksum calculation for package directories:
- Implement `calculate_package_checksum(package_dir: Path) -> str`
- Ensure deterministic file traversal (sorted order)
- Handle edge cases per T007 unit tests
- Make T007 tests pass

Refer to data-model.md for algorithm specification.  
**Dependencies**: T007 (test must exist and fail)  
**Parallel**: No (makes T007 pass)

---

### T009 Download and vendor @sema4ai/components
**Path**: `action_server/frontend/vendored/components/`  
**Description**: Use vendoring script (T003) or manual process:
1. Authenticate to GitHub Packages (requires GITHUB_TOKEN)
2. Download `@sema4ai/components@0.1.1`
3. Extract to `vendored/components/`
4. Verify package.json, dist/, and required files exist
5. Calculate checksum
6. Update manifest.json

**Manual fallback** if script not ready:
```bash
npm pack @sema4ai/components@0.1.1 --registry=https://npm.pkg.github.com
tar -xzf sema4ai-components-0.1.1.tgz
mv package vendored/components/
```

**Dependencies**: T003 (script), T008 (checksum), T002 (manifest)  
**Parallel**: No (modifies manifest.json)

---

### T010 Download and vendor @sema4ai/icons
**Path**: `action_server/frontend/vendored/icons/`  
**Description**: Same process as T009 for `@sema4ai/icons@0.1.2`:
1. Download from authenticated GitHub Packages
2. Extract to `vendored/icons/`
3. Calculate checksum
4. Update manifest.json

**Dependencies**: T009 (sequential manifest updates)  
**Parallel**: No

---

### T011 Download and vendor @sema4ai/theme
**Path**: `action_server/frontend/vendored/theme/`  
**Description**: Same process as T009 for `@sema4ai/theme@0.1.1-RC1`:
1. Download from authenticated GitHub Packages
2. Extract to `vendored/theme/`
3. Calculate checksum
4. Update manifest.json

**Dependencies**: T010 (sequential manifest updates)  
**Parallel**: No

---

### T012 Update package.json to use vendored packages
**Path**: `action_server/frontend/package.json`  
**Description**: Modify dependencies to use local `file:` references:

**Before**:
```json
"dependencies": {
  "@sema4ai/components": "0.1.1",
  "@sema4ai/icons": "0.1.2",
  "@sema4ai/theme": "0.1.1-RC1"
}
```

**After**:
```json
"dependencies": {
  "@sema4ai/components": "file:./vendored/components",
  "@sema4ai/icons": "file:./vendored/icons",
  "@sema4ai/theme": "file:./vendored/theme"
}
```

Refer to research.md decision #1 for rationale.  
**Dependencies**: T009, T010, T011 (packages must be vendored first)  
**Parallel**: No

---

### T013 Verify contract tests pass
**Path**: `action_server/tests/action_server_tests/`  
**Description**: Run all contract tests and verify they now PASS:
```bash
pytest action_server/tests/action_server_tests/test_frontend_build_unauthenticated.py -v
pytest action_server/tests/action_server_tests/test_vendored_integrity.py -v
```

If any tests fail, debug and fix before proceeding.  
**Dependencies**: T004, T005, T012 (implementation complete)  
**Parallel**: No (validation step)

---

## Phase 3.4: CI/CD Integration

### T014 Create CI workflow for unauthenticated builds
**Path**: `.github/workflows/frontend-build-unauthenticated.yml`  
**Description**: Create GitHub Actions workflow that validates external contributor builds:
```yaml
name: Frontend Build (Unauthenticated)

on: [pull_request, push]

jobs:
  build-external:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      - name: Verify no credentials
        run: |
          test -z "$NPM_TOKEN" || exit 1
          test -z "$GITHUB_TOKEN" || exit 1
      - name: Install dependencies
        working-directory: action_server/frontend
        run: npm ci
      - name: Build
        working-directory: action_server/frontend
        run: npm run build
      - name: Verify output
        run: test -d action_server/frontend/dist/index.html
```

**Dependencies**: T013 (tests passing)  
**Parallel**: Can be done after T012

---

### T015 Create CI workflow for vendored integrity check
**Path**: `.github/workflows/vendor-integrity-check.yml`  
**Description**: Create GitHub Actions workflow that validates checksums on every build:
```yaml
name: Vendor Integrity Check

on: [pull_request, push]

jobs:
  check-integrity:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Run integrity tests
        run: |
          cd action_server
          pytest tests/action_server_tests/test_vendored_integrity.py -v
```

**Dependencies**: T005 (integrity tests exist)  
**Parallel**: Can be parallel with T014

---

### T016 [P] Create monthly update automation workflow
**Path**: `.github/workflows/monthly-vendor-update.yml`  
**Description**: Create scheduled GitHub Actions workflow for automated updates:
```yaml
name: Monthly Vendor Update Check

on:
  schedule:
    - cron: '0 0 1 * *'  # First of every month
  workflow_dispatch:  # Manual trigger

jobs:
  check-updates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Authenticate to GitHub Packages
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: echo "//npm.pkg.github.com/:_authToken=$GITHUB_TOKEN" > ~/.npmrc
      - name: Check for updates
        run: |
          # Query GitHub Packages API for latest versions
          # Compare with manifest.json
          # If updates available, run vendor script
      - name: Create PR if updates found
        uses: peter-evans/create-pull-request@v5
        with:
          title: "chore: Update vendored design system packages"
          body: "Automated update of vendored packages"
          branch: "vendor-update-${{ github.run_number }}"
```

Refer to research.md decision #4 for complete requirements.  
**Dependencies**: T003 (vendor script)  
**Parallel**: Yes

---

## Phase 3.5: Documentation & Polish

### T017 [P] Create vendored packages README
**Path**: `action_server/frontend/vendored/README.md`  
**Description**: Document the vendored packages:
- What is vendored and why
- How packages were vendored (reference to vendor script)
- How to update packages (manual and automated process)
- License information
- Checksum verification instructions

Reference Constitution V requirements.  
**Dependencies**: None  
**Parallel**: Yes

---

### T018 [P] Update root README with build instructions
**Path**: `README.md`  
**Description**: Add "Building from Source" section:
- Mention no credentials required
- Link to quickstart.md for detailed steps
- Note that vendored dependencies are included
- Add badge or note about open-source buildability

**Dependencies**: None  
**Parallel**: Yes

---

### T019 [P] Update CONTRIBUTING.md with vendoring info
**Path**: `CONTRIBUTING.md`  
**Description**: Add "Vendored Dependencies" section:
- Explain what's vendored and why
- Document update process for maintainers
- Reference vendoring script and automation
- Constitutional compliance notes

**Dependencies**: None  
**Parallel**: Yes

---

### T020 Execute and validate quickstart.md
**Path**: N/A (validation task)  
**Description**: Manually follow every step in quickstart.md to ensure accuracy:
1. Clone fresh repository
2. Remove any .npmrc authentication
3. Follow all 6 steps in quickstart
4. Verify all success criteria met
5. Measure build time and document
6. Update quickstart.md with actual measurements

This validates the external contributor experience end-to-end.  
**Dependencies**: T013 (tests passing), T014 (CI working)  
**Parallel**: No (validation must be last)

---

### T021 [P] Measure and document build time baseline
**Path**: `specs/002-build-packaging-bug/build-performance.md`  
**Description**: Create performance documentation:
- Baseline authenticated build time (pre-fix)
- Post-vendoring build time (with local files)
- Comparison table showing 0% increase achieved
- Methodology for measurement
- Hardware specs used

This documents compliance with NFR-001.  
**Dependencies**: T020 (after validation)  
**Parallel**: Yes

---

### T022 Run full test suite
**Path**: N/A (validation task)  
**Description**: Execute complete test suite to ensure no regressions:
```bash
# Python tests
cd action_server
pytest -v

# Frontend tests
cd frontend
npm test
npm run test:lint
npm run test:types
```

All tests must pass before merging.  
**Dependencies**: T020 (after validation)  
**Parallel**: No

---

## Phase 3.6: Vendoring & Release (Constitutional Compliance)

### T023 Create vendor manifest for release
**Path**: `action_server/frontend/vendored/manifest.json`  
**Description**: Ensure manifest.json is complete and ready for release:
- All 3 packages documented
- All checksums calculated and verified
- Source URLs documented
- License information complete
- Updated timestamp reflects final vendor date

This is already created in T002 and updated in T009-T011, but verify completeness.  
**Dependencies**: T011 (all packages vendored)  
**Parallel**: No

---

### T024 [P] License review documentation
**Path**: `specs/002-build-packaging-bug/LICENSE-REVIEW.md`  
**Description**: Document license compliance:
- All three packages are Sema4.ai-owned (SEE LICENSE IN LICENSE)
- No third-party dependencies with incompatible licenses
- Vendoring approved per Constitution V
- Sign-off from appropriate authority (if required)

**Dependencies**: None (documentation task)  
**Parallel**: Yes

---

### T025 Verify CI validates vendored checksums
**Path**: N/A (validation task)  
**Description**: Confirm CI workflow (T015) correctly validates checksums:
- Create test PR that modifies a vendored file
- Verify CI fails with checksum mismatch
- Revert change
- Verify CI passes

This validates Constitutional requirement for checksum verification.  
**Dependencies**: T015 (integrity CI exists)  
**Parallel**: No

---

### T026 Final validation against specification
**Path**: N/A (validation task)  
**Description**: Validate all functional requirements from spec.md are met:
- FR-001: Build succeeds without private registry auth ✓
- FR-002: Build is reproducible ✓
- FR-003: No private package dependencies ✓
- FR-004: Assets publicly accessible or vendored ✓
- FR-005: Build instructions work without Sema4.ai access ✓
- FR-006: Visual consistency maintained ✓
- FR-007: Documentation doesn't reference private resources ✓
- FR-008-014: All build & release requirements ✓
- NFR-001-004: All non-functional requirements ✓

Create checklist and verify each item.  
**Dependencies**: T022 (all tests passing)  
**Parallel**: No

---

## Dependencies Graph

```
Setup Phase:
T001 → T002 → [T009, T010, T011] → T012 → T013
       └─→ T003 (parallel)

Test Phase (parallel):
T004, T005, T006, T007 (all parallel, must complete before T013)

Implementation:
T007 → T008 → T009 → T010 → T011 → T012 → T013

CI Integration:
T013 → T014, T015 (parallel)
T003 → T016 (parallel after script ready)

Documentation (parallel after T013):
T017, T018, T019 (all parallel)

Validation (sequential):
T013 → T020 → T021, T022 (parallel) → T023 → T025 → T026

Release (parallel docs):
T024 (parallel anytime)
```

---

## Parallel Execution Examples

### Example 1: Launch all contract tests together (Phase 3.2)
```bash
# Terminal 1
pytest action_server/tests/action_server_tests/test_frontend_build_unauthenticated.py

# Terminal 2
pytest action_server/tests/action_server_tests/test_vendored_integrity.py

# Terminal 3
pytest action_server/tests/action_server_tests/test_quickstart_validation.py

# Terminal 4
pytest action_server/tests/action_server_tests/test_checksum_utils.py
```

### Example 2: Launch documentation tasks together (Phase 3.5)
```bash
# Task Agent 1
Task: "Create vendored packages README at action_server/frontend/vendored/README.md"

# Task Agent 2
Task: "Update root README with build instructions at README.md"

# Task Agent 3
Task: "Update CONTRIBUTING.md with vendoring info at CONTRIBUTING.md"
```

### Example 3: CI workflows in parallel
```bash
# Task Agent 1
Task: "Create CI workflow for unauthenticated builds at .github/workflows/frontend-build-unauthenticated.yml"

# Task Agent 2
Task: "Create CI workflow for vendored integrity check at .github/workflows/vendor-integrity-check.yml"
```

---

## Validation Checklist
*GATE: Verify before marking complete*

- [x] All contracts have corresponding tests (T004, T005)
- [x] All entities have model tasks (manifest.json schema - T002)
- [x] All tests come before implementation (Phase 3.2 before 3.3)
- [x] Parallel tasks truly independent (T004-T007, T014-T016, T017-T019, etc.)
- [x] Each task specifies exact file path ✓
- [x] No task modifies same file as another [P] task ✓
- [x] Vendoring tasks included per Constitution V (T023-T025)
- [x] Test-First Development enforced (explicit gate before T008)

---

## Notes

- **Authentication Required**: T009-T011 require GitHub Packages authentication to download packages (one-time)
- **Test-First Critical**: Do NOT skip Phase 3.2 or implement before tests fail
- **Commit Frequency**: Commit after each task completion
- **0% Performance**: T021 validates the critical constraint
- **Constitutional Compliance**: T023-T025 ensure release readiness

**Total Tasks**: 26  
**Parallelizable**: 11 tasks marked [P]  
**Critical Path**: T001 → T002 → T009 → T010 → T011 → T012 → T013 → T020 → T026  
**Estimated Completion**: ~3-5 days (depending on review cycles)
