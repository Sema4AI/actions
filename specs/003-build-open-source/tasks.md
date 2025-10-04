# Tasks: Build Open-Source Design System Replacement

**Feature**: 003-build-open-source  
**Input**: Design documents from `/var/home/kdlocpanda/second_brain/Resources/robocorp-forks/actions/specs/003-build-open-source/`  
**Prerequisites**: plan.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

## Tech Stack Summary
- **Languages**: TypeScript 5.3.3, Node.js 20.x (LTS)
- **Framework**: React 18.2.0, Vite 6.1.0
- **Styling**: Emotion (@emotion/react, @emotion/styled)
- **Icons**: Lucide React (ISC license) + custom SVG
- **Build Tool**: tsup (for package builds)
- **Testing**: Vitest 3.1.3 (unit), pytest (contract/integration), manual QA

## Path Conventions
Repository root: `/var/home/kdlocpanda/second_brain/Resources/robocorp-forks/actions/`
- **Vendored packages**: `action_server/frontend/vendored/{theme|icons|components}/`
- **Frontend app**: `action_server/frontend/src/`
- **Tests**: `action_server/tests/action_server_tests/frontend_tests/`

---

## Phase 3.0: Prerequisites (MUST COMPLETE FIRST)

### T000: Measure and document baseline bundle size
**File**: `specs/003-build-open-source/BASELINE-METRICS.md`  
**Description**: **CRITICAL PREREQUISITE - MUST BE EXECUTED FIRST BEFORE ANY IMPLEMENTATION WORK**. This task establishes the bundle size baseline for ±5% tolerance validation in later tasks (T016, T074, T093).

**Workflow**:
1. Ensure you are on master branch: `git checkout master`
2. Navigate to frontend: `cd action_server/frontend`
3. Install dependencies with private packages: `npm ci`
4. Build production bundle: `npm run build`
5. Measure bundle size: `SIZE=$(stat -f%z dist/index.html 2>/dev/null || stat -c%s dist/index.html); echo "Baseline: $SIZE bytes"`
6. Document result: Create `specs/003-build-open-source/BASELINE-METRICS.md` with:
   - Bundle size in bytes
   - Date measured
   - Commit SHA of master branch
   - ±5% tolerance range (0.95x to 1.05x baseline)
7. Return to feature branch: `git checkout 003-build-open-source`

**Example BASELINE-METRICS.md content**:
```markdown
# Baseline Bundle Metrics
**Measured**: 2025-10-04
**Branch**: master
**Commit**: abc123def456
**Bundle Size**: 850000 bytes (850 KB)
**Tolerance Range**: 807500 - 892500 bytes (±5%)
```

**Dependencies**: None (FIRST TASK)  
**Parallel**: No  
**Validation**: T016, T074, T093 will read this file and fail with helpful error if missing

---

### T00A: Extract and document frontend component usage patterns
**File**: `specs/003-build-open-source/USAGE-ANALYSIS.md`  
**Description**: **CRITICAL PREREQUISITE** - Analyze actual usage of @sema4ai packages in frontend codebase to validate contract definitions match reality. This ensures we implement the correct APIs and props.

**Analysis Method**:
```bash
cd action_server/frontend/src
# Find all imports from @sema4ai packages
grep -r "from '@sema4ai" . -h | sort -u
# Or use TypeScript language server / ast-grep for deeper analysis
```

**Document in USAGE-ANALYSIS.md**:
- Which components are imported and from which files
- Which props are actually passed to each component
- Which TypeScript types are imported (ButtonProps, InputProps, Column, TableRowProps)
- Which icons are used
- How theme package is used (styled, ThemeProvider, tokens)

**Validation**:
- Cross-reference with contracts/components-api-contract.md
- Verify all 22 components are actually used (or update count if incorrect)
- Confirm all props in contracts match actual usage
- Identify any undocumented usage patterns

**Dependencies**: None (runs on existing codebase)  
**Parallel**: No  
**Output**: Updated USAGE-ANALYSIS.md with complete inventory

---

## Phase 3.1: Setup & Configuration

### T001: Create package structure for @sema4ai/theme
**File**: `action_server/frontend/vendored/theme/`  
**Description**: Create directory structure with package.json, tsconfig.json, src/ folder, and LICENSE file for theme package  
**Dependencies**: None  
**Parallel**: No

### T002: Create package structure for @sema4ai/icons
**File**: `action_server/frontend/vendored/icons/`  
**Description**: Create directory structure with package.json, tsconfig.json, src/ and src/logos/ folders, and LICENSE file for icons package  
**Dependencies**: None  
**Parallel**: No

### T003: Create package structure for @sema4ai/components
**File**: `action_server/frontend/vendored/components/`  
**Description**: Create directory structure with package.json, tsconfig.json, src/ folder with component subdirectories, and LICENSE file  
**Dependencies**: None  
**Parallel**: No

### T004: [P] Configure TypeScript for theme package
**File**: `action_server/frontend/vendored/theme/tsconfig.json`  
**Description**: Create TypeScript configuration with React JSX support, Emotion type definitions, and module augmentation for @emotion/react  
**Dependencies**: T001  
**Parallel**: Yes (with T005, T006)

### T005: [P] Configure TypeScript for icons package
**File**: `action_server/frontend/vendored/icons/tsconfig.json`  
**Description**: Create TypeScript configuration with React JSX support and SVG type definitions  
**Dependencies**: T002  
**Parallel**: Yes (with T004, T006)

### T006: [P] Configure TypeScript for components package
**File**: `action_server/frontend/vendored/components/tsconfig.json`  
**Description**: Create TypeScript configuration with React JSX support, references to theme package types  
**Dependencies**: T003  
**Parallel**: Yes (with T004, T005)

### T007: [P] Setup tsup build configuration for theme
**File**: `action_server/frontend/vendored/theme/package.json` (scripts section)  
**Description**: Add build scripts using tsup for ESM output with TypeScript declarations  
**Dependencies**: T001, T004  
**Parallel**: Yes (with T008, T009)

### T008: [P] Setup tsup build configuration for icons
**File**: `action_server/frontend/vendored/icons/package.json` (scripts section)  
**Description**: Add build scripts using tsup for ESM output with subpath exports for /logos  
**Dependencies**: T002, T005  
**Parallel**: Yes (with T007, T009)

### T009: [P] Setup tsup build configuration for components
**File**: `action_server/frontend/vendored/components/package.json` (scripts section)  
**Description**: Add build scripts using tsup for ESM output with tree-shaking support  
**Dependencies**: T003, T006  
**Parallel**: Yes (with T007, T008)

### T010: Install dependencies for vendored packages
**File**: `action_server/frontend/` (run npm install)  
**Description**: Install Emotion, Lucide React, tsup, and other dependencies for all three packages  
**Dependencies**: T007, T008, T009  
**Parallel**: No

---

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### T011: [P] Contract test for theme package exports
**File**: `action_server/tests/action_server_tests/frontend_tests/test_theme_contract.py`  
**Description**: Create pytest test validating ThemeProvider, styled, Color, ThemeOverrides, and tokens are exported from @sema4ai/theme. Test must verify module imports without errors and type definitions exist. **ADDITIONALLY**: Validate all dependencies have MIT, ISC, or Apache-2.0 licenses (FR-004 compliance). Use license-checker or parse package.json of dependencies.  
**Dependencies**: T010, T00A (usage analysis complete)  
**Parallel**: Yes (with T012, T013)

### T012: [P] Contract test for icons package exports
**File**: `action_server/tests/action_server_tests/frontend_tests/test_icons_contract.py`  
**Description**: Create pytest test validating all 18 icon components (IconBolt through IconWifiNoConnection) and IconSema4 from /logos subpath are exported. Test must verify IconProps type exists and all icons are importable. **ADDITIONALLY**: Validate lucide-react dependency license is ISC (FR-004 compliance).  
**Dependencies**: T010, T00A (usage analysis complete)  
**Parallel**: Yes (with T011, T013)

### T013: [P] Contract test for components package exports
**File**: `action_server/tests/action_server_tests/frontend_tests/test_components_contract.py`  
**Description**: Create pytest test validating all 22 components (Badge, Box, Button, Code, Dialog, Drawer, EditorView, Grid, Header, Input, Link, Progress, Scroll, SideNavigation, Table, Tabs, Tooltip, Typography - actual count to be verified via T00A usage analysis) and 4 utilities (componentWithRef, useClipboard, usePopover, useSystemTheme) are exported with correct type definitions. **ADDITIONALLY**: Validate all dependencies (including CodeMirror for EditorView) have compliant licenses (FR-004).  
**Dependencies**: T010, T00A (usage analysis complete)  
**Parallel**: Yes (with T011, T012)

### T014: [P] Integration test for frontend TypeScript compilation
**File**: `action_server/tests/action_server_tests/frontend_tests/test_typescript_integration.py`  
**Description**: Create pytest test that runs tsc --noEmit on frontend to verify all imports resolve and no type errors exist after package replacement. Verify TypeScript version is 5.3.3 as specified.  
**Dependencies**: T010  
**Parallel**: Yes (with T015, T016)

### T015: [P] Integration test for frontend build success
**File**: `action_server/tests/action_server_tests/frontend_tests/test_build_integration.py`  
**Description**: Create pytest test that runs npm run build and verifies successful completion with exit code 0 and dist/ output created  
**Dependencies**: T010  
**Parallel**: Yes (with T014, T016)

### T016: [P] Integration test for bundle size validation
**File**: `action_server/tests/action_server_tests/frontend_tests/test_bundle_size.py`  
**Description**: Create pytest test that measures dist/index.html size and validates it's within ±5% of baseline documented in BASELINE-METRICS.md (created in T000). Test MUST fail with helpful error if BASELINE-METRICS.md does not exist, instructing to run T000 first. Test should fail if bundle size is outside tolerance in EITHER direction (too large OR too small indicates potential issues).  
**Dependencies**: T010, T000 (baseline must exist)  
**Parallel**: Yes (with T014, T015)

---

## Phase 3.3: Core Implementation - Theme Package (Foundation)
**Run tests from Phase 3.2 to verify they fail before starting implementation**

### T017: Implement design tokens
**File**: `action_server/frontend/vendored/theme/src/tokens.ts`  
**Description**: Define design tokens object with colors (primary, secondary, semantic, neutral, surface), spacing (4px scale), typography (fontFamily, fontSize, fontWeight, lineHeight), borderRadius, shadows, and breakpoints. Ensure all values are valid CSS values and serializable.  
**Dependencies**: T011 (failing test exists)  
**Parallel**: No

### T018: Implement Theme type and module augmentation
**File**: `action_server/frontend/vendored/theme/src/types.ts`  
**Description**: Create Theme interface matching tokens structure, Color type (string), ThemeOverrides type (DeepPartial<Theme>), and module augmentation for @emotion/react to extend Theme interface  
**Dependencies**: T017  
**Parallel**: No

### T019: Implement ThemeProvider component
**File**: `action_server/frontend/vendored/theme/src/ThemeProvider.tsx`  
**Description**: Create ThemeProvider component that wraps Emotion's ThemeProvider, accepts optional theme prop (defaults to tokens), and provides theme context to children  
**Dependencies**: T017, T018  
**Parallel**: No

### T020: Create theme package main exports
**File**: `action_server/frontend/vendored/theme/src/index.ts`  
**Description**: Export ThemeProvider, styled (from @emotion/styled), types (Color, ThemeOverrides, Theme), and tokens from package entry point  
**Dependencies**: T019  
**Parallel**: No

### T021: Build theme package
**File**: `action_server/frontend/vendored/theme/` (run build)  
**Description**: Run npm run build in theme package directory to generate dist/ output with index.js, index.d.ts, and verify exports work correctly  
**Dependencies**: T020  
**Parallel**: No

### T022: Verify theme contract test passes
**File**: Run `pytest action_server/tests/action_server_tests/frontend_tests/test_theme_contract.py`  
**Description**: Execute theme contract test (T011) and verify it now passes with all exports available  
**Dependencies**: T021  
**Parallel**: No

---

## Phase 3.4: Core Implementation - Icons Package (Parallel to Components Start)

### T023: [P] Implement IconProps interface
**File**: `action_server/frontend/vendored/icons/src/types.ts`  
**Description**: Create IconProps interface with size (number|string), color (string), className, style, onClick, aria-label, and spread props support  
**Dependencies**: T012 (failing test exists)  
**Parallel**: Yes (with T024-T040)

### T024: [P] Implement IconBolt (Lucide Zap wrapper)
**File**: `action_server/frontend/vendored/icons/src/IconBolt.tsx`  
**Description**: Create IconBolt component wrapping Lucide's Zap icon with IconProps interface  
**Dependencies**: T023  
**Parallel**: Yes (with other icon implementations)

### T025: [P] Implement IconCheck2 (Lucide Check wrapper)
**File**: `action_server/frontend/vendored/icons/src/IconCheck2.tsx`  
**Description**: Create IconCheck2 component wrapping Lucide's Check icon with IconProps interface  
**Dependencies**: T023  
**Parallel**: Yes

### T026: [P] Implement IconCopy (Lucide Copy wrapper)
**File**: `action_server/frontend/vendored/icons/src/IconCopy.tsx`  
**Description**: Create IconCopy component wrapping Lucide's Copy icon with IconProps interface  
**Dependencies**: T023  
**Parallel**: Yes

### T027: [P] Implement IconFileText (Lucide FileText wrapper)
**File**: `action_server/frontend/vendored/icons/src/IconFileText.tsx`  
**Description**: Create IconFileText component wrapping Lucide's FileText icon with IconProps interface  
**Dependencies**: T023  
**Parallel**: Yes

### T028: [P] Implement IconGlobe (Lucide Globe wrapper)
**File**: `action_server/frontend/vendored/icons/src/IconGlobe.tsx`  
**Description**: Create IconGlobe component wrapping Lucide's Globe icon with IconProps interface  
**Dependencies**: T023  
**Parallel**: Yes

### T029: [P] Implement IconLink (Lucide Link wrapper)
**File**: `action_server/frontend/vendored/icons/src/IconLink.tsx`  
**Description**: Create IconLink component wrapping Lucide's Link icon with IconProps interface  
**Dependencies**: T023  
**Parallel**: Yes

### T030: [P] Implement IconLoading (Lucide Loader wrapper)
**File**: `action_server/frontend/vendored/icons/src/IconLoading.tsx`  
**Description**: Create IconLoading component wrapping Lucide's Loader icon with IconProps interface  
**Dependencies**: T023  
**Parallel**: Yes

### T031: [P] Implement IconLogIn (Lucide LogIn wrapper)
**File**: `action_server/frontend/vendored/icons/src/IconLogIn.tsx`  
**Description**: Create IconLogIn component wrapping Lucide's LogIn icon with IconProps interface  
**Dependencies**: T023  
**Parallel**: Yes

### T032: [P] Implement IconLogOut (Lucide LogOut wrapper)
**File**: `action_server/frontend/vendored/icons/src/IconLogOut.tsx`  
**Description**: Create IconLogOut component wrapping Lucide's LogOut icon with IconProps interface  
**Dependencies**: T023  
**Parallel**: Yes

### T033: [P] Implement IconMenu (Lucide Menu wrapper)
**File**: `action_server/frontend/vendored/icons/src/IconMenu.tsx`  
**Description**: Create IconMenu component wrapping Lucide's Menu icon with IconProps interface  
**Dependencies**: T023  
**Parallel**: Yes

### T034: [P] Implement IconPlay (Lucide Play wrapper)
**File**: `action_server/frontend/vendored/icons/src/IconPlay.tsx`  
**Description**: Create IconPlay component wrapping Lucide's Play icon with IconProps interface  
**Dependencies**: T023  
**Parallel**: Yes

### T035: [P] Implement IconShare (Lucide Share wrapper)
**File**: `action_server/frontend/vendored/icons/src/IconShare.tsx`  
**Description**: Create IconShare component wrapping Lucide's Share icon with IconProps interface  
**Dependencies**: T023  
**Parallel**: Yes

### T036: [P] Implement IconStop (Lucide Square wrapper)
**File**: `action_server/frontend/vendored/icons/src/IconStop.tsx`  
**Description**: Create IconStop component wrapping Lucide's Square icon with IconProps interface  
**Dependencies**: T023  
**Parallel**: Yes

### T037: [P] Implement IconSun (Lucide Sun wrapper)
**File**: `action_server/frontend/vendored/icons/src/IconSun.tsx`  
**Description**: Create IconSun component wrapping Lucide's Sun icon with IconProps interface  
**Dependencies**: T023  
**Parallel**: Yes

### T038: [P] Implement IconType (Lucide Type wrapper)
**File**: `action_server/frontend/vendored/icons/src/IconType.tsx`  
**Description**: Create IconType component wrapping Lucide's Type icon with IconProps interface  
**Dependencies**: T023  
**Parallel**: Yes

### T039: [P] Implement IconUnorderedList (Lucide List wrapper)
**File**: `action_server/frontend/vendored/icons/src/IconUnorderedList.tsx`  
**Description**: Create IconUnorderedList component wrapping Lucide's List icon with IconProps interface  
**Dependencies**: T023  
**Parallel**: Yes

### T040: [P] Implement IconWifiNoConnection (Lucide WifiOff wrapper)
**File**: `action_server/frontend/vendored/icons/src/IconWifiNoConnection.tsx`  
**Description**: Create IconWifiNoConnection component wrapping Lucide's WifiOff icon with IconProps interface  
**Dependencies**: T023  
**Parallel**: Yes

### T041: Implement custom IconSema4 SVG component
**File**: `action_server/frontend/vendored/icons/src/logos/IconSema4.tsx`  
**Description**: Create custom IconSema4 component with Sema4.ai logo SVG path, following IconProps interface  
**Dependencies**: T023  
**Parallel**: No

### T042: Create icons package main exports
**File**: `action_server/frontend/vendored/icons/src/index.ts`  
**Description**: Export all 17 standard icon components and IconProps type from package entry point  
**Dependencies**: T024-T040  
**Parallel**: No

### T043: Create logos subpath exports
**File**: `action_server/frontend/vendored/icons/src/logos/index.ts`  
**Description**: Export IconSema4 from logos subpath entry point  
**Dependencies**: T041  
**Parallel**: No

### T044: Build icons package
**File**: `action_server/frontend/vendored/icons/` (run build)  
**Description**: Run npm run build in icons package directory to generate dist/ output with main and logos subpath builds  
**Dependencies**: T042, T043  
**Parallel**: No

### T045: Verify icons contract test passes
**File**: Run `pytest action_server/tests/action_server_tests/frontend_tests/test_icons_contract.py`  
**Description**: Execute icons contract test (T012) and verify it passes with all 18 icons exported correctly  
**Dependencies**: T044  
**Parallel**: No

---

## Phase 3.5: Core Implementation - Components Package (Depends on Theme)

### T046: [P] Implement Badge component
**File**: `action_server/frontend/vendored/components/src/Badge/index.tsx`  
**Description**: Create Badge component with children, color (primary|secondary|error|success|warning|info), variant (filled|outlined) props using styled from theme  
**Dependencies**: T022 (theme built)  
**Parallel**: Yes (with T047, T048, T049)

### T047: [P] Implement Box component
**File**: `action_server/frontend/vendored/components/src/Box/index.tsx`  
**Description**: Create Box component as flexible container extending HTMLDivElement with common layout props using styled from theme  
**Dependencies**: T022  
**Parallel**: Yes (with T046, T048, T049)

### T048: [P] Implement Grid component
**File**: `action_server/frontend/vendored/components/src/Grid/index.tsx`  
**Description**: Create Grid component with columns, rows, gap props for CSS Grid layout using styled from theme  
**Dependencies**: T022  
**Parallel**: Yes (with T046, T047, T049)

### T049: [P] Implement Scroll component
**File**: `action_server/frontend/vendored/components/src/Scroll/index.tsx`  
**Description**: Create Scroll component with custom scrollbar styling and maxHeight prop using styled from theme  
**Dependencies**: T022  
**Parallel**: Yes (with T046, T047, T048)

### T050: [P] Implement Header component
**File**: `action_server/frontend/vendored/components/src/Header/index.tsx`  
**Description**: Create Header component with level (1-6) prop rendering semantic heading elements using styled from theme  
**Dependencies**: T022  
**Parallel**: Yes (with T051)

### T051: [P] Implement Typography component
**File**: `action_server/frontend/vendored/components/src/Typography/index.tsx`  
**Description**: Create Typography component with variant (h1-h6|body1|body2|caption), color, align, gutterBottom props using styled from theme  
**Dependencies**: T022  
**Parallel**: Yes (with T050)

### T052: [P] Implement Code component
**File**: `action_server/frontend/vendored/components/src/Code/index.tsx`  
**Description**: Create Code component with language, inline props for code display with syntax highlighting using styled from theme  
**Dependencies**: T022  
**Parallel**: Yes (with T046-T051)

### T053: [P] Implement Button component
**File**: `action_server/frontend/vendored/components/src/Button/index.tsx`  
**Description**: Create Button component with ButtonProps interface (onClick, disabled, variant, size, type) using styled from theme. Export ButtonProps type.  
**Dependencies**: T022  
**Parallel**: Yes (with T054)

### T054: [P] Implement Input component
**File**: `action_server/frontend/vendored/components/src/Input/index.tsx`  
**Description**: Create Input component with InputProps interface (value, onChange, placeholder, disabled, error, helperText, type) using styled from theme. Export InputProps type.  
**Dependencies**: T022  
**Parallel**: Yes (with T053)

### T055: [P] Implement Link component
**File**: `action_server/frontend/vendored/components/src/Link/index.tsx`  
**Description**: Create Link component with to/href, external, onClick props supporting React Router and external links using styled from theme  
**Dependencies**: T022  
**Parallel**: Yes (with T056)

### T056: [P] Implement Tabs component
**File**: `action_server/frontend/vendored/components/src/Tabs/index.tsx`  
**Description**: Create Tabs component with tabs array, activeTab, onChange props for tabbed interface using styled from theme  
**Dependencies**: T022  
**Parallel**: Yes (with T055)

### T057: Implement SideNavigation component
**File**: `action_server/frontend/vendored/components/src/SideNavigation/index.tsx`  
**Description**: Create SideNavigation component with items array, activeItem, onNavigate props for sidebar menu using styled from theme and Link component  
**Dependencies**: T055 (uses Link internally)  
**Parallel**: No

### T058: Implement Table component and types
**File**: `action_server/frontend/vendored/components/src/Table/index.tsx`  
**Description**: Create Table component with columns (Column type), data (TableRowProps[]), onRowClick props. Export Column and TableRowProps types. Use styled from theme.  
**Dependencies**: T047 (may use Box internally)  
**Parallel**: No

### T059: Implement Tooltip component
**File**: `action_server/frontend/vendored/components/src/Tooltip/index.tsx`  
**Description**: Create Tooltip component with title, placement props, portal rendering, hover interactions using styled from theme  
**Dependencies**: T022  
**Parallel**: No

### T060: Implement Dialog component
**File**: `action_server/frontend/vendored/components/src/Dialog/index.tsx`  
**Description**: Create Dialog component with open, onClose, title, actions props, portal rendering, focus trap, ESC/backdrop close using styled from theme  
**Dependencies**: T059 (complex overlay, similar patterns)  
**Parallel**: No

### T061: Implement Drawer component
**File**: `action_server/frontend/vendored/components/src/Drawer/index.tsx`  
**Description**: Create Drawer component with open, onClose, anchor (left|right|top|bottom) props, portal rendering, slide animation using styled from theme  
**Dependencies**: T060 (similar overlay patterns)  
**Parallel**: No

### T062: Implement Progress component
**File**: `action_server/frontend/vendored/components/src/Progress/index.tsx`  
**Description**: Create Progress component with value, variant (determinate|indeterminate), color props with animation using styled from theme  
**Dependencies**: T022  
**Parallel**: No

### T063: Implement EditorView component
**File**: `action_server/frontend/vendored/components/src/EditorView/index.tsx`  
**Description**: Create EditorView component wrapping CodeMirror with value, onChange, language, readOnly props using styled from theme  
**Dependencies**: T022  
**Parallel**: No

### T064: [P] Implement componentWithRef utility
**File**: `action_server/frontend/vendored/components/src/utils/componentWithRef.ts`  
**Description**: Create componentWithRef higher-order function for ref forwarding with proper TypeScript generics  
**Dependencies**: T022  
**Parallel**: Yes (with T065, T066, T067)

### T065: [P] Implement useClipboard hook
**File**: `action_server/frontend/vendored/components/src/hooks/useClipboard.ts`  
**Description**: Create useClipboard hook with copy function, copied state, error state using Clipboard API  
**Dependencies**: T022  
**Parallel**: Yes (with T064, T066, T067)

### T066: [P] Implement usePopover hook
**File**: `action_server/frontend/vendored/components/src/hooks/usePopover.ts`  
**Description**: Create usePopover hook with anchorEl, open, handleOpen, handleClose for popover state management  
**Dependencies**: T022  
**Parallel**: Yes (with T064, T065, T067)

### T067: [P] Implement useSystemTheme hook
**File**: `action_server/frontend/vendored/components/src/hooks/useSystemTheme.ts`  
**Description**: Create useSystemTheme hook returning 'light'|'dark' based on prefers-color-scheme media query  
**Dependencies**: T022  
**Parallel**: Yes (with T064, T065, T066)

### T068: Create components package main exports
**File**: `action_server/frontend/vendored/components/src/index.ts`  
**Description**: Export all 22 components, 4 utilities, and type definitions (ButtonProps, InputProps, Column, TableRowProps) from package entry point  
**Dependencies**: T046-T067  
**Parallel**: No

### T069: Build components package
**File**: `action_server/frontend/vendored/components/` (run build)  
**Description**: Run npm run build in components package directory to generate dist/ output with all exports  
**Dependencies**: T068  
**Parallel**: No

### T070: Verify components contract test passes
**File**: Run `pytest action_server/tests/action_server_tests/frontend_tests/test_components_contract.py`  
**Description**: Execute components contract test (T013) and verify it passes with all components and utilities exported correctly  
**Dependencies**: T069  
**Parallel**: No

---

## Phase 3.6: Integration & Build Validation

### T071: Verify frontend TypeScript compilation
**File**: Run `pytest action_server/tests/action_server_tests/frontend_tests/test_typescript_integration.py`  
**Description**: Execute TypeScript integration test (T014) to verify tsc --noEmit passes with no type errors  
**Dependencies**: T022, T045, T070  
**Parallel**: No

### T072: Verify zero frontend source code changes (FR-009)
**File**: Run `git diff action_server/frontend/src/`  
**Description**: Verify that no code changes were made to frontend application source code. The git diff of action_server/frontend/src/ directory should be completely empty, proving zero breaking changes to application code per FR-009. Configuration files (package.json, .npmrc, tsconfig.json, vite.config.js) in frontend/ root may have changes and are validated separately in T090.  
**Dependencies**: T071  
**Parallel**: No

### T073: Verify frontend build succeeds
**File**: Run `pytest action_server/tests/action_server_tests/frontend_tests/test_build_integration.py`  
**Description**: Execute build integration test (T015) to verify npm run build completes successfully  
**Dependencies**: T072  
**Parallel**: No

### T074: Verify bundle size is within tolerance
**File**: Run `pytest action_server/tests/action_server_tests/frontend_tests/test_bundle_size.py`  
**Description**: Execute bundle size test (T016) to verify dist/index.html size is within ±5% of baseline established in T000 and documented in BASELINE-METRICS.md. Test will fail if baseline file missing or if size outside tolerance range.  
**Dependencies**: T073, T000 (baseline measured)  
**Parallel**: No

### T075: Verify hot-reload functionality (FR-017)
**File**: Manual testing with npm run dev  
**Description**: **MOVED FROM T089** - Verify development hot-reload works: Start dev server (npm run dev), edit a vendored component source file (e.g., change Button background color), verify browser auto-refreshes without full page reload, verify changes appear correctly. Test early to validate development workflow before QA phase.  
**Dependencies**: T073 (build working)  
**Parallel**: No

---

## Phase 3.7: Testing & Validation

### T076: Generate vendored packages manifest
**File**: `action_server/frontend/vendored/manifest.json`  
**Description**: Create manifest.json with package metadata (name, version, license) and SHA256 checksums for each package's dist/ contents  
**Dependencies**: T070, T045, T022  
**Parallel**: No

### T077: Update vendor integrity test for new checksums
**File**: `action_server/tests/action_server_tests/test_vendored_integrity.py`  
**Description**: Update vendored integrity test to include checksums for new theme, icons, components packages  
**Dependencies**: T076 (manifest must exist first)  
**Parallel**: No

### T078: Verify vendor integrity test passes
**File**: Run `pytest action_server/tests/action_server_tests/test_vendored_integrity.py`  
**Description**: Execute updated vendor integrity test (T077) and verify checksums match manifest  
**Dependencies**: T077  
**Parallel**: No

### T079: Run all automated tests
**File**: Run `pytest action_server/tests/action_server_tests/frontend_tests/ -v`  
**Description**: Execute full test suite (contract tests + integration tests) and verify all pass  
**Dependencies**: T075, T078  
**Parallel**: No

### T076: Update vendor integrity test for new checksums
**File**: `action_server/tests/action_server_tests/test_vendored_integrity.py`  
**Description**: Update vendored integrity test to include checksums for new theme, icons, components packages  
**Dependencies**: T075 (manifest must exist first)  
**Parallel**: No

### T077: Verify vendor integrity test passes
**File**: Run `pytest action_server/tests/action_server_tests/test_vendored_integrity.py`  
**Description**: Execute updated vendor integrity test (T076) and verify checksums match manifest  
**Dependencies**: T076  
**Parallel**: No

### T078: Run all automated tests
**File**: Run `pytest action_server/tests/action_server_tests/frontend_tests/ -v`  
**Description**: Execute full test suite (contract tests + integration tests) and verify all pass  
**Dependencies**: T074, T077  
**Parallel**: No

---

## Phase 3.8: Documentation & Licensing

### T080: [P] Document Lucide React attribution
**File**: `action_server/frontend/vendored/icons/LICENSE`  
**Description**: Add Lucide React license attribution (ISC) to icons package LICENSE file noting icon source  
**Dependencies**: T045  
**Parallel**: Yes (with T081, T082)

### T081: [P] Update vendored packages README
**File**: `action_server/frontend/vendored/README.md`  
**Description**: Update or create README documenting the three replacement packages, their purpose, build process, and license information  
**Dependencies**: T070, T045, T022  
**Parallel**: Yes (with T080, T082)

### T082: [P] Update .github/copilot-instructions.md with feature completion
**File**: `.github/copilot-instructions.md` (using update-agent-context.sh)  
**Description**: Run .specify/scripts/bash/update-agent-context.sh copilot to add feature completion notes to agent context file  
**Dependencies**: T079  
**Parallel**: Yes (with T080, T081)

### T083: Create license review documentation
**File**: `specs/003-build-open-source/LICENSE-REVIEW.md`  
**Description**: Document all dependency licenses (Emotion: MIT, Lucide React: ISC, tsup: MIT, CodeMirror: MIT for EditorView) and confirm Apache-2.0 compatibility. Reference automated license validation from T011-T013 contract tests.  
**Dependencies**: T070, T045, T022  
**Parallel**: No

---

## Phase 3.9: Manual QA & Validation (Following quickstart.md)

### T084: Execute quickstart Part 1 - Fresh clone build test
**File**: Follow `specs/003-build-open-source/quickstart.md` Part 1  
**Description**: Simulate external contributor build: clear auth, fresh clone, npm ci, verify no authentication errors, TypeScript compilation, build success  
**Dependencies**: T079  
**Parallel**: No

### T085: Execute quickstart Part 2 - Component visual validation
**File**: Follow `specs/003-build-open-source/quickstart.md` Part 2  
**Description**: Manual QA review using VISUAL-QA-CHECKLIST.md: side-by-side comparison of all 22 components, 18 icons, theme. Verify visual and functional parity using objective criteria checklist. Document any exceptions with screenshots. Obtain maintainer approval per documented process.  
**Dependencies**: T084  
**Parallel**: No

### T086: Execute quickstart Part 3 - CI validation test
**File**: Follow `specs/003-build-open-source/quickstart.md` Part 3  
**Description**: Verify GitHub Actions workflow can build without credentials (simulate CI environment)  
**Dependencies**: T084  
**Parallel**: No

### T087: Execute quickstart Part 4 - Integration test validation
**File**: Follow `specs/003-build-open-source/quickstart.md` Part 4  
**Description**: Run all automated integration tests and verify acceptance criteria met  
**Dependencies**: T086  
**Parallel**: No

### T088: Accessibility audit
**File**: Manual testing with browser DevTools and axe DevTools  
**Description**: Run accessibility audit on frontend with new components, verify WCAG AA compliance, keyboard navigation, screen reader support  
**Dependencies**: T085  
**Parallel**: No

### T089: Document validation results
**File**: `specs/003-build-open-source/VALIDATION-REPORT.md`  
**Description**: Complete quickstart validation record with PASS/FAIL status for each phase, document any issues found, attach completed VISUAL-QA-CHECKLIST.md. Obtain maintainer sign-off per team approval process (reference existing team workflow or document inline if none exists).  
**Dependencies**: T088  
**Parallel**: No

### T090: Execute atomic package replacement (FR-021)
**File**: `action_server/frontend/package.json`, `.npmrc` (if exists)  
**Description**: Execute big-bang migration - atomic replacement of all three packages simultaneously. Verify frontend package.json references file:./vendored/* paths (update only if references are incorrect or missing). Remove any .npmrc entries for @sema4ai scope if present (enables public registry access). This completes the migration from private to open-source packages per FR-021.  
**Dependencies**: T070, T045, T022 (all packages built)  
**Parallel**: No

---

## Phase 3.10: Optimization & Polish (If bundle size exceeds tolerance)

### T091: [CONDITIONAL] Bundle size analysis
**File**: Run `npm run build -- --mode=analyze` in action_server/frontend/  
**Description**: If T073 fails (bundle too large OR too small beyond ±5% tolerance), analyze bundle composition to identify size contributors  
**Dependencies**: T073 (only if fails)  
**Parallel**: No

### T092: [CONDITIONAL] Optimize component implementations
**File**: Various component files based on T091 analysis  
**Description**: Reduce bundle size by optimizing component code, removing unused features, optimizing imports  
**Dependencies**: T091  
**Parallel**: No

### T093: [CONDITIONAL] Re-verify bundle size after optimization
**File**: Run `pytest action_server/tests/action_server_tests/frontend_tests/test_bundle_size.py`  
**Description**: Re-run bundle size test after optimization to verify now within ±5% tolerance  
**Dependencies**: T092  
**Parallel**: No

---

## Dependencies Graph

```
Setup Phase (T001-T010):
  T001, T002, T003 (sequential - create package structures)
    ↓
  T004, T005, T006 [P] (parallel - configure TypeScript)
    ↓
  T007, T008, T009 [P] (parallel - configure builds)
    ↓
  T010 (install dependencies)

Tests First Phase (T011-T016):
  T010 → T011, T012, T013 [P] (parallel - contract tests)
  T010 → T014, T015, T016 [P] (parallel - integration tests)
  ALL MUST FAIL before Phase 3.3

Theme Implementation (T017-T022):
  T011 (failing test) → T017 (tokens)
    → T018 (types)
    → T019 (ThemeProvider)
    → T020 (exports)
    → T021 (build)
    → T022 (verify test passes)

Icons Implementation (T023-T045):
  T012 (failing test) → T023 (types)
    → T024-T040 [P] (parallel - 17 icon wrappers)
    → T041 (custom logo)
    → T042 (main exports)
    → T043 (logos exports)
    → T044 (build)
    → T045 (verify test passes)

Components Implementation (T046-T070):
  T022 (theme ready) + T013 (failing test)
    → T046-T049 [P] (parallel - layout components)
    → T050, T051 [P] (parallel - typography)
    → T052 [P] (code component)
    → T053, T054 [P] (parallel - form components)
    → T055, T056 [P] (parallel - navigation start)
    → T057 (SideNavigation, depends on Link)
    → T058 (Table)
    → T059 (Tooltip foundation)
    → T060, T061 (Dialog, Drawer - sequential overlays)
    → T062, T063 (Progress, EditorView)
    → T064-T067 [P] (parallel - utilities)
    → T068 (exports)
    → T069 (build)
    → T070 (verify test passes)

Integration Phase (T071-T073):
  T022 + T045 + T070 → T071 (TypeScript check)
    → T072 (build)
    → T073 (bundle size)

Testing Phase (T075-T078):
  T073 → T075 (all tests)
  T070 + T045 + T022 → T076 (update integrity test)
    → T077 (manifest)
    → T078 (verify integrity)

Documentation Phase (T079-T082):
  T045 → T079 [P] (Lucide attribution)
  T070 + T045 + T022 → T080 [P] (README)
  T075 → T081 [P] (CLAUDE.md)
  T070 + T045 + T022 → T082 (license review)

Validation Phase (T083-T088):
  T075 → T083 (fresh build)
    → T084 (visual QA)
    → T085 (CI test)
    → T086 (integration validation)
    → T087 (accessibility)
    → T088 (validation report)

Optimization Phase (T089-T091) [CONDITIONAL]:
  T073 (if fails) → T089 (analyze)
    → T090 (optimize)
    → T091 (re-verify)
```

---

## Parallel Execution Examples

### Setup Phase Parallelization
```bash
# After T001-T003 complete, run TypeScript configs in parallel:
Task: "Configure TypeScript for theme package in action_server/frontend/vendored/theme/tsconfig.json"
Task: "Configure TypeScript for icons package in action_server/frontend/vendored/icons/tsconfig.json"
Task: "Configure TypeScript for components package in action_server/frontend/vendored/components/tsconfig.json"

# After T004-T006 complete, configure builds in parallel:
Task: "Setup tsup build for theme in action_server/frontend/vendored/theme/package.json"
Task: "Setup tsup build for icons in action_server/frontend/vendored/icons/package.json"
Task: "Setup tsup build for components in action_server/frontend/vendored/components/package.json"
```

### Test Creation Parallelization
```bash
# Create all contract tests in parallel (independent files):
Task: "Contract test for theme package in action_server/tests/action_server_tests/frontend_tests/test_theme_contract.py"
Task: "Contract test for icons package in action_server/tests/action_server_tests/frontend_tests/test_icons_contract.py"
Task: "Contract test for components package in action_server/tests/action_server_tests/frontend_tests/test_components_contract.py"

# Create integration tests in parallel:
Task: "TypeScript integration test in action_server/tests/action_server_tests/frontend_tests/test_typescript_integration.py"
Task: "Build integration test in action_server/tests/action_server_tests/frontend_tests/test_build_integration.py"
Task: "Bundle size test in action_server/tests/action_server_tests/frontend_tests/test_bundle_size.py"
```

### Icon Implementation Parallelization
```bash
# After IconProps type (T023), implement all 17 Lucide wrappers in parallel:
Task: "Implement IconBolt in action_server/frontend/vendored/icons/src/IconBolt.tsx"
Task: "Implement IconCheck2 in action_server/frontend/vendored/icons/src/IconCheck2.tsx"
Task: "Implement IconCopy in action_server/frontend/vendored/icons/src/IconCopy.tsx"
# ... (all 17 icons can run in parallel)
```

### Component Implementation Parallelization
```bash
# Layout components (Phase 5a) - all parallel:
Task: "Implement Badge in action_server/frontend/vendored/components/src/Badge/index.tsx"
Task: "Implement Box in action_server/frontend/vendored/components/src/Box/index.tsx"
Task: "Implement Grid in action_server/frontend/vendored/components/src/Grid/index.tsx"
Task: "Implement Scroll in action_server/frontend/vendored/components/src/Scroll/index.tsx"

# Utilities - all parallel:
Task: "Implement componentWithRef in action_server/frontend/vendored/components/src/utils/componentWithRef.ts"
Task: "Implement useClipboard in action_server/frontend/vendored/components/src/hooks/useClipboard.ts"
Task: "Implement usePopover in action_server/frontend/vendored/components/src/hooks/usePopover.ts"
Task: "Implement useSystemTheme in action_server/frontend/vendored/components/src/hooks/useSystemTheme.ts"
```

### Documentation Parallelization
```bash
# All documentation tasks in parallel:
Task: "Document Lucide attribution in action_server/frontend/vendored/icons/LICENSE"
Task: "Update vendored README in action_server/frontend/vendored/README.md"
Task: "Update CLAUDE.md via update-agent-context.sh"
```

---

## Critical Path

The critical path (longest dependency chain) for this feature is:

```
Setup (T001-T010: ~10 tasks)
  → Tests (T011-T016: ~6 tasks, parallel groups)
  → Theme (T017-T022: ~6 tasks, sequential)
  → Components (T046-T070: ~25 tasks, with parallel groups)
  → Integration (T071-T073: ~3 tasks, sequential)
  → Testing (T075-T078: ~4 tasks)
  → Validation (T083-T088: ~6 tasks, mostly sequential)
```

**Estimated Total**: ~91 tasks (excluding conditional optimization tasks T089-T091)

**Estimated Completion Time** (single developer):
- Setup: 1-2 days
- Tests: 1 day
- Theme: 1 day
- Icons: 1-2 days (highly parallel)
- Components: 5-7 days (largest phase)
- Integration: 0.5 days
- Testing: 0.5 days
- Documentation: 0.5 days
- Manual QA: 1-2 days

**Total**: 12-16 days (single developer, sequential)  
**With Parallelization**: 8-12 days (multiple developers or automated parallelization)

---

## Validation Checklist

**GATE: All items must pass before feature acceptance**

- [ ] All 93 core tasks completed (T000-T090, plus conditional T091-T093)
- [ ] Baseline bundle size measured (T000) before implementation
- [ ] All contract tests exist and pass (T011-T013, T022, T045, T070)
- [ ] All integration tests exist and pass (T014-T016, T071-T073)
- [ ] Theme package exports ThemeProvider, styled, Color, ThemeOverrides, tokens
- [ ] Icons package exports all 18 icons and IconProps type
- [ ] Icons /logos subpath exports IconSema4
- [ ] Components package exports 22 components and 4 utilities
- [ ] Frontend TypeScript compilation succeeds with no errors
- [ ] Frontend build completes successfully
- [ ] Bundle size within ±5% tolerance of baseline
- [ ] Zero code changes in frontend src/ directory (T072)
- [ ] Hot-reload functionality verified (T089)
- [ ] Atomic package replacement executed (T090)
- [ ] All vendor integrity tests pass with correct checksums
- [ ] Fresh clone build succeeds without authentication (T083)
- [ ] Visual/functional parity validated by maintainer QA (T084)
- [ ] CI pipeline validates build without credentials (T085)
- [ ] Accessibility standards maintained (T087)
- [ ] License compliance documented (T082)
- [ ] Validation report completed with maintainer sign-off (T088)

---

## Notes

1. **CRITICAL: Run T000 First**: Baseline bundle size measurement MUST be completed before any implementation work begins
2. **Test-Driven Development**: Phase 3.2 tests MUST be written and MUST FAIL before implementation begins
3. **Parallelization**: Tasks marked [P] are in separate files with no dependencies and can run in parallel
3. **Theme Dependency**: Components package CANNOT start until theme package is built (T022 complete)
4. **Icons Independence**: Icons package can be built in parallel with components (both depend only on theme completion)
5. **Bundle Size**: If T073 fails, conditional optimization tasks (T089-T091) become mandatory
6. **Manual QA**: T084 requires maintainer review and cannot be automated - allow sufficient time
7. **Baseline Measurement**: T000 must be run on master branch BEFORE starting implementation to establish bundle size baseline
8. **Commit Strategy**: Commit after each completed task for easy rollback and progress tracking
9. **Vendored Builds**: This feature creates source-vendored packages (built from repo source) not binary-vendored (downloaded artifacts)
10. **License Attribution**: Lucide React (ISC) attribution is required in icons package LICENSE (T079)
11. **Zero Code Changes**: T072 explicitly verifies FR-009 requirement that frontend src/ code remains unchanged

---

**Tasks Generation Complete**: 2025-10-04  
**Ready for Execution**: Yes ✅  
**Estimated Completion**: 8-16 days depending on parallelization and team size
