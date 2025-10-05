
# Implementation Plan: Open-Core Build Separation and Dual-Path Frontend

**Branch**: `003-open-core-build` | **Date**: 2025-10-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `./spec.md`

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
Establish a maintainable, open-core architecture for Action Server where external contributors can build and customize without private credentials, while internal developers retain seamless access to proprietary design system and CDN workflows. Primary approach: dual-tier build system (Community/Enterprise) with directory-based feature separation, build-time tree-shaking, and matrix CI validation.

## Technical Context
**Language/Version**: Node.js 20.x LTS / TypeScript 5.3.3 (frontend), Python 3.11.x (backend/build automation)  
**Primary Dependencies**: Vite 6.1.0, React 18.2.0, Radix UI + Tailwind CSS (community), @sema4ai/* design system (enterprise), invoke (build tasks), PyInstaller (backend packaging)  
**Storage**: File-based (vendored packages in `action_server/frontend/vendored/`, build artifacts)  
**Testing**: vitest (frontend unit), pytest (backend), contract tests (OpenAPI validation), integration tests (CLI + HTTP endpoints)  
**Target Platform**: Linux, macOS, Windows (cross-platform executables via PyInstaller)
**Project Type**: Web application (backend Python + frontend TypeScript/React)  
**Performance Goals**: Community builds complete in ≤5 minutes, enterprise builds ≤7 minutes, deterministic outputs (byte-identical for same inputs)  
**Constraints**: Community builds air-gapped (no private registry access), bundle size budget (warn if +20% vs baseline), OSI-only licenses for community tier  
**Scale/Scope**: 2 build tiers × 3 OS platforms, ~15-20 CI matrix jobs, directory-based feature separation (core vs enterprise)

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Library-First**: ✅ PASS - Build system components (tier selector, package manager adapter, tree-shaking rules) will be modular Python libraries under `action_server/build-binary/` with standalone unit tests. Frontend components follow React component library pattern (core/ and enterprise/ as separate modules).

**CLI & HTTP-First**: ✅ PASS - CLI surface via invoke tasks: `inv build-frontend --tier=community|enterprise [--source=registry|vendored|cdn]` with JSON output for CI (`--json` flag returns build metadata: tier, source, artifact paths, checksums). HTTP surface unchanged (Action Server API unaffected by build tier selection).

**Test-First**: ✅ PASS - Phase 1 will generate failing tests:
- Unit: `test_tier_selection.py`, `test_tree_shaking.py`, `test_package_resolver.py`
- Contract: `test_community_no_enterprise_imports.py`, `test_osi_licenses_only.py`, `test_artifact_naming.py`
- Integration: `test_community_build_offline.py`, `test_enterprise_build_with_fallback.py`, `test_ci_matrix.py`

**Contract & Integration Tests**: ✅ PASS - Contract tests will validate:
1. Build artifacts follow naming convention: `action-server-{tier}-{os}-{hash}.zip`
2. Community bundles contain zero `@sema4ai/*` imports (AST scan)
3. SBOM generation for all artifacts
4. Deterministic build verification (rebuild produces identical hash)
No breaking changes to Action Server HTTP API - build tier is packaging-only concern.

**Vendoring Decision**
**Community Tier:** No vendored packages - uses only public npm registry packages (e.g., Radix UI, Tailwind)

**Enterprise Tier:** Vendored packages retained as fallback when:
- Private registry is unavailable (offline development, network issues)
- Automated updates applied monthly via existing process (see `action_server/frontend/vendored/`)
- Justification: Enables reliable builds for internal developers without constant network dependency

**New Vendored Package Approval Process** (for reference - not in feature scope):
- **License Review**: MUST have OSI-approved license (for community) or explicit proprietary license approval (for enterprise)
- **Security Scan**: MUST pass `npm audit` and internal security scanning tools
- **Size Justification**: MUST provide rationale for vendoring (size impact, dependency tree analysis)
- **Maintainer Approval**: MUST be approved by at least two maintainers (platform team + security reviewer)
- **Documentation**: MUST update vendored/manifest.json with checksums, licenses, versions, origin URLs
- **CI Validation**: MUST pass checksum verification and license scanning in CI before merge

**Gate Status**: All constitutional requirements satisfied. No complexity violations to document.

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
│   ├── src/
│   │   ├── core/              # Community (open) features
│   │   │   ├── components/    # Radix UI + Tailwind components
│   │   │   ├── pages/         # Action execution, run history, logs
│   │   │   └── services/      # API clients, state management
│   │   ├── enterprise/        # Enterprise (paid) features
│   │   │   ├── components/    # Design system components
│   │   │   ├── pages/         # KB, analytics, org management
│   │   │   └── services/      # Enterprise API clients
│   │   ├── shared/            # Common utilities (tier-agnostic)
│   │   └── App.tsx            # Root with tier-based routing
│   ├── package.json           # Generated from tier-specific manifest
│   ├── package.json.community # Open-source dependencies only
│   ├── package.json.enterprise# Includes @sema4ai/* packages
│   ├── vite.config.js         # Tree-shaking rules per tier
│   └── vendored/              # Enterprise fallback packages
│       ├── components/
│       ├── icons/
│       ├── theme/
│       └── manifest.json      # Checksums, versions, licenses
├── build-binary/
│   ├── tier_selector.py       # CLI flag → env var logic
│   ├── package_resolver.py    # Registry → vendored → CDN fallback
│   ├── tree_shaker.py         # Enterprise import detector
│   └── artifact_validator.py  # Naming, checksums, SBOM
├── src/sema4ai/action_server/ # Backend (tier-agnostic)
└── tests/
    ├── build_system_tests/    # NEW: tier selection, tree-shaking
    ├── contract_tests/        # NEW: artifact validation, import guards
    └── integration_tests/     # NEW: end-to-end build scenarios

.github/workflows/
├── frontend-build.yml         # Matrix: tier × os (replaces old workflows)
└── frontend-build-cdn.yml     # Manual-only internal convenience
```

**Structure Decision**: Web application structure (Option 2) with frontend/backend separation. Frontend adds tier-based directory organization (`src/core/` vs `src/enterprise/`) and dual package manifests. Build system tooling lives in `build-binary/` as standalone Python modules. CI matrix workflow consolidates tier validation.

## Phase 0: Outline & Research

**Status**: ✅ COMPLETE

**Approach**:
1. Extracted technical context from feature spec (all clarifications already resolved via /clarify session)
2. Documented 9 key technology decisions with rationale and alternatives
3. Researched industry standards for:
   - Tier selection mechanisms (CLI flags vs env vars vs config files)
   - Feature separation strategies (directories vs runtime flags vs separate repos)
   - Open-source UI libraries (Radix UI vs MUI vs Chakra vs headless)
   - CI matrix patterns for multi-tier builds
   - Build guardrail best practices (lint-time, build-time, post-build)

**Key Decisions**:
- Tier selection: CLI flag (`--tier`) with env var fallback (`TIER`)
- Feature separation: Directory structure + build-time tree-shaking
- Community UI: Radix UI + Tailwind CSS (shadcn/ui pattern)
- CI workflow: Single matrix (tier × os) with secrets scoping
- Dependency management: Dual `package.json` files with build-time copy
- Vendored packages: Retained as enterprise fallback (existing infrastructure)
- Build guardrails: Multi-layered (ESLint, Vite plugin, AST scan, CI checks)
- Backend handling: Tier-agnostic (no build-time changes)

**Output**: ✅ `research.md` - 9 decisions documented with rationale and alternatives

## Phase 1: Design & Contracts

**Status**: ✅ COMPLETE

**Approach**:
1. **Data Model** - Extracted 8 key entities from functional requirements:
   - BuildTier, DependencySource, PackageManifest, FeatureBoundary, BuildArtifact, ImportViolation, ValidationResult, CIMatrix
   - Defined attributes, relationships, validation rules, and state transitions for each
   - Documented artifact naming conventions and file formats

2. **CLI Contract** - Defined command-line interface:
   - `inv build-frontend` with `--tier`, `--source`, `--debug`, `--json` options
   - Convenience aliases: `build-frontend-community`, `build-frontend-enterprise`
   - `validate-artifact` for post-build guardrails
   - Exit codes, output formats (human-readable + JSON), error examples
   - Environment variable precedence rules

3. **CI Workflow Contract** - Defined GitHub Actions matrix strategy:
   - Single workflow: `frontend-build.yml` with 2×3 matrix (tier × os = 6 jobs)
   - Secrets scoping: NPM_TOKEN only for enterprise matrix jobs
   - Network hardening: Block private registries for community jobs
   - Fork PR handling: External PRs skip enterprise builds
   - Artifact naming: `frontend-{tier}-{os}-{commit_sha}`
   - Determinism check: Rebuild and compare SHA256 (community only)
   - CDN workflow retained as manual-only (`workflow_dispatch`)

4. **Quickstart Scenarios** - Generated 6 end-to-end test scenarios:
   - QS1: External contributor builds community tier (no credentials)
   - QS2: Internal developer builds enterprise tier (with private registry)
   - QS3: Offline development (vendored packages fallback)
   - QS4: CI matrix validation (all tier × os combinations)
   - QS5: Validation guard (detect enterprise imports in community)
   - QS6: JSON output for CI integration
   
   **Backend Scope Note**: Quickstart scenarios test frontend build system and artifact validation only. Backend testing uses **existing Action Server** (no backend implementation in this feature). Backend enterprise feature implementation (APIs, data access, auth flows) is Phase 2 (feature plan 004-backend-enterprise-features).

5. **Agent Context Update** - Updated `.github/copilot-instructions.md`:
   - Added Node.js 20.x LTS / TypeScript 5.3.3, Python 3.11.x to active technologies
   - Added Vite 6.1.0, React 18.2.0, Radix UI + Tailwind, @sema4ai/* design system
   - Added file-based storage (vendored packages, build artifacts)
   - Preserved manual additions between markers

**Output**: 
- ✅ `data-model.md` - 8 entities with full specifications
- ✅ `contracts/cli-contract.md` - CLI interface specification
- ✅ `contracts/ci-workflow-contract.md` - GitHub Actions workflow specification  
- ✅ `quickstart.md` - 6 end-to-end scenarios with validation checklists
- ✅ `.github/copilot-instructions.md` - Updated with 003-open-core-build tech
- [ ] `architecture.md` - 4 Mermaid diagrams showing build system architecture (created in T006a)

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate from Phase 1 outputs:
  - Build system entities (data-model.md) → Python module tasks
  - Frontend contracts (contracts/) → component + test tasks
  - CI workflow contracts → GitHub Actions YAML tasks
  - Quickstart scenarios → integration test tasks
- Grouping: [P] for parallelizable (independent modules/components)

**Ordering Strategy**:
1. TDD order: Tests before implementation (contract tests → unit tests → implementation)
2. Dependency order: 
   - Phase A: Build system libraries (tier_selector, package_resolver)
   - Phase B: Frontend structure (package.json split, vite config)
   - Phase C: Directory reorganization (core/ vs enterprise/)
   - Phase D: CI matrix workflow
   - Phase E: Integration tests + quickstart validation
3. Parallel execution: Mark build system modules [P], frontend components [P]

**Estimated Output**: 50-60 numbered, ordered tasks in tasks.md (larger scope due to dual-tier build system + CI matrix + comprehensive test-first coverage per constitutional requirement)

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

**Status**: ✅ No constitutional violations detected. All gates passed in Constitution Check section above.


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS (all 5 principles satisfied)
- [x] Post-Design Constitution Check: PASS (no new violations)
- [x] All NEEDS CLARIFICATION resolved (via /clarify session 2025-10-05)
- [x] Complexity deviations documented (none - Complexity Tracking section empty)

**Artifacts Generated**:
- [x] `plan.md` - Implementation plan (this file)
- [x] `research.md` - Technology decisions and rationale
- [x] `data-model.md` - 8 entities with full specifications
- [x] `contracts/cli-contract.md` - CLI interface contract
- [x] `contracts/ci-workflow-contract.md` - CI workflow contract
- [x] `quickstart.md` - 6 end-to-end scenarios
- [x] `.github/copilot-instructions.md` - Updated agent context
- [ ] `tasks.md` - Ordered task list (created by /tasks command)

**Next Command**: `/tasks` - Generate ordered task list from Phase 1 design outputs

---
*Based on Constitution v2.2.0 - See `.specify/memory/constitution.md`*
