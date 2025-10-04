
# Implementation Plan: Build Open-Source Design System Replacement

**Branch**: `003-build-open-source` | **Date**: 2025-10-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/var/home/kdlocpanda/second_brain/Resources/robocorp-forks/actions/specs/003-build-open-source/spec.md`

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
Replace three private npm packages (@sema4ai/components, @sema4ai/icons, @sema4ai/theme) with clean-room open-source implementations to enable external contributors to build the Action Server frontend without GitHub Packages authentication. The replacement must maintain complete API compatibility, visual/functional parity (validated via manual QA), and bundle size within ±5% tolerance. All three packages will be replaced simultaneously in a single PR, implementing only the features/props actually used in the frontend codebase.

## Technical Context
**Language/Version**: TypeScript 5.3.3, Node.js 20.x (LTS), React 18.2.0  
**Primary Dependencies**: Vite 6.1.0 (build tool), React 18.2.0, React Router 6.21.3, TanStack Query 5.28.0  
**Design System Foundation**: To be determined via research (likely Material-UI, Radix UI, or Chakra UI for components; suitable icon library for icons; Emotion or styled-components for theming)  
**Storage**: N/A (frontend-only, no persistent storage)  
**Testing**: Vitest 3.1.3 (unit tests), manual QA for visual/functional parity  
**Target Platform**: Modern browsers (ES2020+), bundled as single-file build via vite-plugin-singlefile  
**Project Type**: Web frontend (single-page application)  
**Performance Goals**: Bundle size within ±5% of current implementation (~TBD KB baseline to be measured), build time <30 seconds  
**Constraints**: 
  - Zero breaking changes to frontend code (no import path changes beyond package name)
  - Only MIT, ISC, or Apache 2.0 licensed dependencies
  - Implement only features/props actually used in codebase (per clarification)
  - Big-bang replacement (all three packages simultaneously)
  - Manual QA validation by maintainers (side-by-side comparison)
**Scale/Scope**: 
  - Components: 22 unique components + 4 utilities (Badge, Box, Button, Code, Column, Dialog, Drawer, EditorView, Grid, Header, Input, Link, Progress, Scroll, SideNavigation, Table, Tabs, Tooltip, Typography; utilities: componentWithRef, useClipboard, usePopover, useSystemTheme)
  - Icons: 18 icons (IconBolt, IconCheck2, IconCopy, IconFileText, IconGlobe, IconLink, IconLoading, IconLogIn, IconLogOut, IconMenu, IconPlay, IconShare, IconStop, IconSun, IconType, IconUnorderedList, IconWifiNoConnection, plus IconSema4 from /logos)
  - Theme: 4 exports (ThemeProvider, ThemeOverrides, styled, Color)

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The plan MUST explicitly document how it satisfies the Constitution. At minimum the plan MUST include checks for:

- **Library-First**: ✅ PASS - The three replacement packages (@sema4ai/components, @sema4ai/icons, @sema4ai/theme) are designed as standalone, independently testable npm libraries within the repository. Each package has clear exports, type definitions, and can be tested in isolation. They follow standard npm workspace conventions.

- **CLI & HTTP-First**: ✅ **EXEMPTION APPLIES** - This feature provides UI component libraries, not CLI or HTTP services. Per Constitution v2.3.0 Section II (Frontend-Only UI Package Exemption), frontend design system packages are exempt from CLI & HTTP requirements when they provide comprehensive contract tests for TypeScript interfaces and component APIs. This feature satisfies the exemption criteria:
  1. Packages are pure UI components (React) with no business logic
  2. Contract tests (T011-T013) validate all exports, types, and API compatibility
  3. TypeScript compilation tests (T071) ensure type correctness
  4. Integration tests (T072-T074) validate usage in target application
  5. Packages are vendored within repository, not exposed as external APIs

- **Test-First**: ✅ PASS - Phase 1 will create failing contract tests that validate:
  1. Each component renders without errors
  2. All required props are accepted
  3. TypeScript type definitions match usage
  4. Theme system provides expected tokens
  5. Icons render with correct props
  These tests will fail initially and guide implementation.

- **Contract & Integration Tests**: ✅ PASS - The feature includes:
  1. **Contract Tests**: Component API contracts validating props, exports, and TypeScript types match existing usage
  2. **Integration Tests**: Full frontend build test validating zero code changes required
  3. **Visual/Functional Parity Tests**: Manual QA validation via side-by-side comparison (per clarification)
  4. **Bundle Size Tests**: Automated validation that bundle stays within ±5% tolerance
  Migration plan: Big-bang replacement in single PR (per clarification), no gradual migration needed.

- **Vendored Builds**: ✅ APPLICABLE - This feature creates vendored open-source packages:
  - **Justification**: Enable external contributors to build without private GitHub Packages authentication (Constitution V compliance)
  - **Location**: `/action_server/frontend/vendored/` (existing structure, replacing current vendored private packages)
  - **Structure**: Three npm packages with package.json, dist/, and LICENSE in each
  - **Reproducibility**: Built from source within repository using npm workspaces; no external download required
  - **Checksums**: Will maintain existing manifest.json structure with SHA256 checksums per package
  - **License Compliance**: All foundation libraries must be MIT/ISC/Apache 2.0 (per spec FR-004); license audit required in Phase 0
  - **CI Verification**: Existing vendor integrity tests will validate checksums remain consistent
  - **Note on Source-Vendored Approach**: This feature uses "source-vendored" packages (built from source code within repository) rather than "binary-vendored" (downloading external artifacts). Therefore, traditional "origin URL" and "producing CI run link" requirements do not apply. The packages are built reproducibly from repository source via documented build commands (tsup), satisfying the spirit of the Vendored Builds principle while adapting to the source-based approach.
  
  This approach differs from typical vendoring (downloading external artifacts) - we're building packages from source code within the repository itself, making them "source-vendored" rather than "binary-vendored". The packages will be referenced via npm workspaces file: protocol.

## Project Structure

### Documentation (this feature)
```
specs/003-build-open-source/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
action_server/frontend/
├── vendored/                          # Replacement packages location
│   ├── manifest.json                  # Package metadata & checksums
│   ├── components/                    # @sema4ai/components replacement
│   │   ├── package.json              # Package definition
│   │   ├── src/                      # Component source code
│   │   │   ├── index.ts              # Main export
│   │   │   ├── Badge/
│   │   │   ├── Box/
│   │   │   ├── Button/
│   │   │   ├── Code/
│   │   │   ├── Dialog/
│   │   │   ├── Drawer/
│   │   │   ├── Grid/
│   │   │   ├── Header/
│   │   │   ├── Input/
│   │   │   ├── Link/
│   │   │   ├── Progress/
│   │   │   ├── Scroll/
│   │   │   ├── SideNavigation/
│   │   │   ├── Table/
│   │   │   ├── Tabs/
│   │   │   ├── Tooltip/
│   │   │   ├── Typography/
│   │   │   └── utils/                # Utilities: componentWithRef, useClipboard, etc.
│   │   ├── dist/                     # Built output (generated)
│   │   ├── tsconfig.json
│   │   └── LICENSE
│   ├── icons/                         # @sema4ai/icons replacement
│   │   ├── package.json
│   │   ├── src/
│   │   │   ├── index.ts              # Icon exports
│   │   │   ├── logos/                # Logo subfolder (IconSema4)
│   │   │   └── icons/                # 18 icon components
│   │   ├── dist/
│   │   ├── tsconfig.json
│   │   └── LICENSE
│   └── theme/                         # @sema4ai/theme replacement
│       ├── package.json
│       ├── src/
│       │   ├── index.ts              # Main theme exports
│       │   ├── ThemeProvider.tsx
│       │   ├── tokens.ts             # Design tokens
│       │   └── styled.ts             # Styled API
│       ├── dist/
│       ├── tsconfig.json
│       └── LICENSE
├── src/                               # Frontend application (no changes)
│   └── ...                           # Existing code unchanged
├── package.json                       # Updated to use file: references
└── vite.config.js                    # May need adjustments for workspace

tests/                                 # Contract & integration tests
└── action_server_tests/
    └── frontend_tests/
        ├── test_component_contracts.py      # Component API validation
        ├── test_icon_contracts.py           # Icon availability validation
        ├── test_theme_contracts.py          # Theme exports validation
        ├── test_build_integration.py        # Full build succeeds
        ├── test_bundle_size.py              # Bundle size ±5% validation
        └── test_vendored_integrity.py       # Checksum validation (existing)
```

**Structure Decision**: Web application (frontend-only). The vendored packages follow npm workspace conventions with separate package.json files and standard src/dist structure. Each package is self-contained and independently buildable. The frontend package.json references these via `file:./vendored/{package}` protocol. Tests are located in the repository's standard Python test directory for consistency with existing test infrastructure.

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
The /tasks command will generate a comprehensive task list following TDD principles and dependency ordering.

**Source Documents for Task Generation**:
1. **research.md**: Foundation library decisions (Emotion, Lucide React, build tooling)
2. **data-model.md**: Complete inventory of components, icons, utilities, types
3. **contracts/**: API contracts for all three packages (theme, icons, components)
4. **quickstart.md**: Validation scenarios and acceptance criteria

**Task Categories**:

1. **Package Setup Tasks** (foundational):
   - Create package.json for each of the three packages
   - Configure TypeScript (tsconfig.json) for each package
   - Configure build tooling (tsup configuration)
   - Set up LICENSE files
   - Create initial directory structures

2. **Contract Test Tasks** [P] (test-first, parallel per package):
   - Theme contract tests: Validate ThemeProvider, styled, tokens exports
   - Icons contract tests: Validate all 18 icon exports, IconProps type
   - Components contract tests: Validate all 22 component exports, utility exports, types

3. **Theme Package Tasks** (sequential, foundational):
   - Implement design tokens (tokens.ts)
   - Create Theme type and module augmentation
   - Implement ThemeProvider wrapper
   - Export styled from Emotion
   - Implement Color and ThemeOverrides types
   - Build theme package

4. **Icons Package Tasks** [P] (parallel after theme, since icons are independent):
   - Implement IconProps interface
   - Create 17 standard icon wrappers (Lucide)
   - Create custom IconSema4 SVG component
   - Set up /logos subpath export
   - Build icons package

5. **Components Package Tasks** (sequential, depends on theme):
   - **Phase 5a - Simple Components** [P]:
     - Badge, Box, Grid, Scroll (layout/basic)
     - Header, Typography (typography)
     - Code (code display)
   - **Phase 5b - Form Components** [P]:
     - Button, Input (form controls)
   - **Phase 5c - Navigation** [P]:
     - Link, Tabs
   - **Phase 5d - Complex Components**:
     - SideNavigation (depends on Link)
     - Table (depends on Box, Typography)
   - **Phase 5e - Overlays**:
     - Tooltip (foundation for Dialog/Drawer)
     - Dialog, Drawer (complex overlays)
   - **Phase 5f - Specialized**:
     - EditorView (CodeMirror integration)
     - Progress (animated component)
   - **Phase 5g - Utilities** [P]:
     - componentWithRef, useClipboard, usePopover, useSystemTheme
   - Build components package

6. **Integration Tasks** (after all packages built):
   - Update frontend package.json dependencies (verify file: references)
   - Verify frontend TypeScript compilation
   - Run frontend build
   - Measure and validate bundle size (±5% tolerance)

7. **Testing Tasks**:
   - Create Python contract test suite (pytest)
   - Create build integration test
   - Create bundle size validation test
   - Update vendor integrity test for new checksums
   - Run full test suite

8. **Documentation Tasks**:
   - Update vendored/README.md with new package information
   - Update vendored/manifest.json with checksums
   - Document license attribution for Lucide React
   - Update CLAUDE.md with feature completion notes

9. **Validation Tasks** (manual QA per clarification):
   - Side-by-side visual comparison checklist
   - Functional behavior validation
   - Accessibility audit
   - External contributor build test (clean clone)

**Ordering Strategy**:

**Sequential Dependencies**:
```
Setup → Theme (foundation) → Components (depends on theme)
                          → Icons (parallel with components)
```

**Parallel Opportunities** [P]:
- All three contract test files (different packages)
- Icons package (independent of components)
- Simple components within same phase (Badge, Box, Grid, etc.)
- Utilities (all independent of each other)

**Test-First Ordering**:
- Contract tests BEFORE package implementation
- Component tests BEFORE component implementation
- Integration tests AFTER all packages built

**Task Numbering Convention**:
- 1-10: Setup and configuration
- 11-20: Contract tests (failing tests first)
- 21-30: Theme package implementation
- 31-40: Icons package implementation
- 41-70: Components package implementation (grouped by category)
- 71-80: Integration and build
- 81-90: Testing and validation
- 91-99: Documentation

**Estimated Task Count**: 85-95 tasks

**Parallel Execution Markers**:
- Tasks marked [P] can run in parallel (independent files/modules)
- Theme → Components dependency is explicit (Components must wait for Theme)
- Icons are parallel to Components
- All contract tests are parallel to each other

**Key Decision Points in Task Execution**:
1. **After Theme Build**: Verify exports work before starting Components
2. **After Each Component Phase**: Run contract tests to ensure exports correct
3. **After All Packages Built**: Run integration tests before manual QA
4. **Bundle Size Check**: If exceeds tolerance, optimization sprint required

**Task Template Pattern**:
Each implementation task follows:
```
Task N: Implement [Component/Feature]
- Create [file path]
- Implement [interface] following [contract reference]
- Export from package index
- Verify contract test passes
- Dependencies: Task X, Task Y
- Parallel: [Yes/No]
```

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

---

**Phase 2 Planning Complete**: Task generation approach documented ✅

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

No constitutional violations. The CLI & HTTP-First exemption for frontend-only UI packages is now codified in Constitution v2.3.0 Section II.

**Analysis**:
- ✅ Library-First: Three standalone npm packages
- ✅ CLI & HTTP-First: Exemption applies per Constitution v2.3.0 Section II
- ✅ Test-First: Contract tests before implementation
- ✅ Contract & Integration Tests: Comprehensive test strategy
- ✅ Vendored Builds: Proper justification, source-vendored approach

All constitutional principles are satisfied. No deviations or complexity justifications required.


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
- [x] Initial Constitution Check: PASS (CLI/HTTP exemption applies per Constitution v2.3.0)
- [x] Post-Design Constitution Check: PASS (no new violations)
- [x] All NEEDS CLARIFICATION resolved (no items in Technical Context)
- [x] Complexity deviations documented (N/A - no deviations)

---
*Based on Constitution v2.3.0 - See `/memory/constitution.md`*
