
# Implementation Plan: Remove Private Package Dependencies from Build

**Branch**: `002-build-packaging-bug` | **Date**: October 3, 2025 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/var/home/kdlocpanda/second_brain/Resources/robocorp-forks/actions/specs/002-build-packaging-bug/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from file system structure or context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code, or `AGENTS.md` for all other agents).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary

**Primary Requirement**: Enable external contributors to build the Action Server frontend without requiring authentication to private GitHub Packages registry.

**Technical Approach**: Vendor compiled assets from three private design system packages (`@sema4ai/components`, `@sema4ai/icons`, `@sema4ai/theme`) directly into the repository under `action_server/frontend/vendored/`. Implement automated CI process to check for upstream updates monthly and create pull requests when updates are available.

**Key Constraint**: Build time must not increase (0% tolerance) compared to current authenticated builds.

## Technical Context
**Language/Version**: Node.js (LTS 20.x) / TypeScript 5.3.3 for frontend; Python 3.11.x for build automation  
**Primary Dependencies**: Vite 6.1.0, React 18.2.0, design system packages to be vendored  
**Storage**: Local filesystem for vendored assets; GitHub Packages for upstream source  
**Testing**: Vitest 3.1.3 for frontend tests; pytest for Python build automation tests  
**Target Platform**: Linux (Ubuntu 22.04), macOS, Windows - cross-platform frontend builds  
**Project Type**: Web application (frontend under action_server/frontend/)  
**Performance Goals**: Build time must equal or be faster than current authenticated build  
**Constraints**: 0% build time increase; offline builds must work; no private registry access during build  
**Scale/Scope**: Single frontend application; 3 design system packages to vendor; monthly update cadence

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

✅ **Library-First**: This is a build/packaging infrastructure fix, not a feature library. **Exception justified**: The fix enables the existing Action Server library to be built by external contributors. No new library is being created; the work modifies build configuration and package dependencies.

✅ **CLI & HTTP-First**: N/A - This fix does not expose new functionality. The existing Action Server CLI and HTTP interfaces remain unchanged.

✅ **Test-First**: 
- **Contract tests**: Validate that `npm ci && npm run build` completes successfully without authentication credentials
- **Integration tests**: Verify offline builds work with vendored assets
- **Unit tests**: Test vendor update automation scripts
- Failing test placeholders will be created in Phase 1 for all scenarios

✅ **Contract & Integration Tests**:
- Build contract test: Verify external build succeeds (exit code 0, dist/ directory created)
- Vendored asset integrity test: Verify checksums match expected values
- CI validation test: Ensure unauthenticated CI environment can build
- Update automation test: Verify monthly check process creates valid PRs
- **Migration plan**: N/A - This is a bugfix that enables builds, not a breaking change

✅ **Vendored Builds** (REQUIRED for this feature):
- **Justification**: External contributors cannot access private GitHub Packages registry. Vendoring eliminates authentication dependency and enables offline/air-gapped builds per Constitution V.
- **Vendor directory**: `action_server/frontend/vendored/` (new directory)
- **Build artifacts to vendor**:
  - `@sema4ai/components@0.1.1` (compiled CSS/JS)
  - `@sema4ai/icons@0.1.2` (compiled CSS/JS/SVG assets)
  - `@sema4ai/theme@0.1.1-RC1` (compiled CSS/JS)
- **Build command**: Downloaded from authenticated GitHub Packages registry (one-time), then committed
- **Checksum verification**: SHA256 checksums will be stored in `action_server/frontend/vendored/manifest.json`
- **License compliance**: All three packages are Sema4.ai-owned; no third-party license issues. Vendor manifest will document licensing.
- **CI verification**: Post-vendoring, CI will validate checksums match and unauthenticated builds succeed
- **Update process**: Monthly automated CI job checks for new versions, downloads authenticated, creates PR with updated manifest

**Initial Constitution Check**: ✅ PASS (all requirements satisfied or exceptions justified)

---

## Post-Design Constitution Re-Check

After completing Phase 1 design, re-validating Constitutional compliance:

✅ **Library-First**: Still justified as infrastructure fix (no new violations)

✅ **CLI & HTTP-First**: N/A - Still no new functionality exposed

✅ **Test-First**: 
- ✅ Contract tests defined in `contracts/build-contract.md`
- ✅ Integration tests defined in `contracts/vendor-integrity-contract.md`
- ✅ All tests documented as FAILING (not yet implemented) per TDD
- ✅ Tests will drive implementation in Phase 4

✅ **Contract & Integration Tests**:
- ✅ Build contract fully specified with expected failures
- ✅ Integrity contract fully specified with checksum verification
- ✅ Quickstart provides end-to-end validation scenario
- ✅ No breaking changes to existing contracts

✅ **Vendored Builds**:
- ✅ Manifest schema defined in `data-model.md`
- ✅ Checksum calculation algorithm specified
- ✅ Vendor directory structure documented
- ✅ Update process fully designed (monthly GitHub Actions)
- ✅ CI validation strategy defined (unauthenticated builds)
- ✅ License compliance plan: all packages are Sema4.ai-owned

**Post-Design Constitution Check**: ✅ PASS (no new violations, all artifacts created)

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
action_server/
├── frontend/
│   ├── src/                    # Existing TypeScript/React source
│   ├── vendored/               # NEW: Vendored design system assets
│   │   ├── components/         # @sema4ai/components compiled outputs
│   │   ├── icons/              # @sema4ai/icons compiled outputs
│   │   ├── theme/              # @sema4ai/theme compiled outputs
│   │   └── manifest.json       # NEW: Checksums, versions, licenses
│   ├── package.json            # MODIFIED: Remove private dependencies
│   ├── vite.config.js          # MODIFIED: Point to vendored assets
│   └── dist/                   # Build output (unchanged)
├── build-binary/               # Existing directory for vendored binaries
│   └── vendor-frontend.py      # NEW: Script to vendor design assets
├── tests/
│   └── action_server_tests/
│       ├── test_frontend_build_unauthenticated.py  # NEW: Contract test
│       └── test_vendored_integrity.py              # NEW: Checksum validation
└── .github/
    └── workflows/
        ├── frontend-build-check.yml       # MODIFIED: Add unauthenticated test
        └── monthly-vendor-update.yml      # NEW: Automated update job
```

**Structure Decision**: This is a Web application (frontend) with Python backend. The fix targets the frontend build process only. We use the existing `action_server/frontend/` structure and add a new `vendored/` subdirectory following Constitution V (Vendored Builds). The `build-binary/` directory is reused for vendoring automation scripts.

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh copilot`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:

The /tasks command will generate implementation tasks based on the completed Phase 1 artifacts. Tasks will be organized to follow Test-Driven Development (TDD) and Constitutional principles.

**Task Categories**:

1. **Vendoring Infrastructure** (Priority: High, Parallel: Some)
   - Create `action_server/frontend/vendored/` directory structure
   - Create manifest.json schema validation
   - Develop vendoring automation script (`build-binary/vendor-frontend.py`)
   - Download and vendor the three packages (authenticated, one-time)
   - Generate initial manifest.json with checksums

2. **Build Configuration** (Priority: High, Depends on: Vendoring)
   - Modify `package.json` to use `file:` references
   - Update `.gitignore` if needed (vendored/ should be committed)
   - Verify Vite configuration handles local packages

3. **Contract Tests** (Priority: High, Parallel: Yes)
   - Implement `test_frontend_build_unauthenticated.py` (from build-contract.md)
   - Implement `test_vendored_integrity.py` (from vendor-integrity-contract.md)
   - These tests will FAIL initially, driving implementation

4. **CI/CD Integration** (Priority: Medium, Depends on: Build Configuration)
   - Create/modify GitHub Actions workflow for unauthenticated build validation
   - Remove or isolate authenticated build jobs
   - Add checksum verification step to CI

5. **Automated Updates** (Priority: Medium, Can be parallel after infrastructure)
   - Create GitHub Actions workflow for monthly update checks
   - Implement update detection logic (query GitHub Packages API)
   - Implement automated PR creation for updates
   - Add update documentation

6. **Documentation** (Priority: Low, Can be parallel)
   - Create `frontend/vendored/README.md` explaining vendoring
   - Update root `README.md` with build instructions
   - Update `CONTRIBUTING.md` with vendored dependencies section
   - Validate quickstart.md accuracy by following it

7. **Validation** (Priority: High, Must be last)
   - Run all contract tests and ensure they pass
   - Execute quickstart.md end-to-end
   - Measure and document build time (must be ≤ baseline)
   - Verify offline builds work (disconnect network, rebuild)

**Ordering Strategy**:
- TDD order: Contract tests → Infrastructure → Implementation → Validation
- Critical path: Vendoring infrastructure → Build config → Tests pass
- Parallel opportunities: Contract test implementation can happen before vendoring
- Documentation can be written in parallel with implementation

**Estimated Task Count**: 18-22 discrete tasks

**Dependencies Graph**:
```
[Contract Tests] → [Tests Pass] (endpoint)
     ↓ (inform)
[Vendoring Infra] → [Build Config] → [CI Integration] → [Validation]
     ↓ (parallel)
[Update Automation]
     ↓ (parallel)
[Documentation]
```

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [x] Phase 3: Tasks generated (/tasks command) - 26 tasks created
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS (re-validated after Phase 1)
- [x] All NEEDS CLARIFICATION resolved (via /clarify session)
- [ ] Complexity deviations documented (N/A - no violations)

---
*Based on Constitution v2.2.0 - See `.specify/memory/constitution.md`*
