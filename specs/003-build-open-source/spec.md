# Feature Specification: Build Open-Source Design System Replacement

**Feature Branch**: `003-build-open-source`  
**Created**: 2025-10-04  
**Status**: Draft  
**Input**: User description: "Build Open-Source Design System Replacement - Replace three private npm packages (@sema4ai/components, @sema4ai/icons, @sema4ai/theme) with clean-room implementations built from popular open-source libraries to enable external contributors to build the project without GitHub Packages authentication."

## Execution Flow (main)
```
1. Parse user description from Input
   → Feature clearly describes replacing private packages with open-source alternatives
2. Extract key concepts from description
   → Actors: External contributors, maintainers, CI systems
   → Actions: Build frontend, replace packages, maintain API compatibility
   → Data: Design tokens, component APIs, icon sets
   → Constraints: MIT/ISC/Apache 2.0 licenses only, zero breaking changes to frontend code
3. For each unclear aspect:
   → All aspects sufficiently specified in user input
4. Fill User Scenarios & Testing section
   → User flow: External contributor clones repo and builds successfully
5. Generate Functional Requirements
   → All requirements testable via build commands and component validation
6. Identify Key Entities
   → Theme system, Icon library, Component library packages
7. Run Review Checklist
   → No implementation details at requirements level
   → Focus on user needs and business value
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

---

## Clarifications

### Session 2025-10-04
- Q: How should visual and functional parity be validated between the private and open-source implementations? → A: Manual QA review by maintainers comparing side-by-side rendered components
- Q: What is the acceptable tolerance for bundle size change when comparing the open-source replacement to the current private packages? → A: ±5% (up to 5% larger or smaller is acceptable)
- Q: How should the migration from private packages to open-source replacements be executed? → A: Big-bang replacement: Switch all packages at once in a single PR
- Q: If a component from the private packages has more features than currently used in the frontend, should the open-source replacement implement the full API or only the used subset? → A: Used subset only: Implement only the features/props actually used in the frontend
- Q: What is the priority if tradeoffs arise between implementation simplicity and complete feature parity? → A: Favor parity: Match private packages exactly even if implementation becomes complex

---

## User Scenarios & Testing

### Primary User Story
As an external open-source contributor, I want to clone the Action Server repository and build the frontend without requiring any private package registry authentication, so that I can contribute to the project without access barriers.

### Acceptance Scenarios
1. **Given** a fresh clone of the repository with no authentication configured, **When** an external contributor runs `npm ci && npm run build` in the frontend directory, **Then** the build completes successfully without authentication errors or missing dependencies.

2. **Given** the existing frontend codebase that imports components from @sema4ai packages, **When** the open-source replacement packages are integrated, **Then** all component imports work identically without requiring any code changes in the frontend.

3. **Given** a CI environment with no GitHub Packages credentials, **When** the CI pipeline runs the frontend build, **Then** the build succeeds and validates that all components function correctly.

4. **Given** the current Action Server UI rendering components from private packages, **When** rendered with the open-source replacement packages, **Then** the visual appearance and functionality remain identical to users.

5. **Given** a new contributor reviewing the project dependencies, **When** they inspect all npm packages used in the frontend, **Then** every dependency is from a public registry with MIT, ISC, or Apache 2.0 license.

### Edge Cases
- What happens when a component uses a previously undocumented API from the private packages?
  - System must document all actual usage patterns and replicate them in the replacement
- How does the system handle version updates to the open-source foundation libraries?
  - Build process must validate compatibility and maintain API stability
- What happens if upstream maintainers change the private packages?
  - Since we're not using them anymore, no impact - our implementations are independent

---

## Requirements

### Functional Requirements

#### Build & Accessibility
- **FR-001**: System MUST allow any user to build the frontend using only public npm registry packages without authentication
- **FR-002**: Build process MUST complete successfully with `npm ci && npm run build` on a fresh clone with no credentials configured
- **FR-003**: CI pipeline MUST validate successful builds without any private registry access on every pull request
- **FR-004**: All dependencies MUST be publicly available under MIT, ISC, or Apache 2.0 licenses

#### API Compatibility
- **FR-005**: Replacement theme package MUST provide identical exports to the private @sema4ai/theme package (ThemeProvider, design tokens, styled API)
- **FR-006**: Replacement icons package MUST provide all 18 icons currently used in the frontend with identical component names and props
- **FR-007**: Replacement components package MUST provide 22 UI components, 4 utility functions, and associated TypeScript types currently used in the frontend. **Components (22)**: Badge, Box, Button, Code, Dialog, Drawer, EditorView, Grid, Header, Input, Link, Progress, Scroll, SideNavigation, Table, Tabs, Tooltip, Typography (18 explicitly listed; verify actual count of 22 via frontend usage analysis). **Utilities (4)**: componentWithRef, useClipboard, usePopover, useSystemTheme. **Type Definitions**: ButtonProps, InputProps, Column (table column configuration type, NOT a component), TableRowProps. APIs must match the actually-used features and props in the frontend codebase. **API Scope Rule**: For features/props currently used in frontend, implement with exact parity to private package even if complex. For features/props NOT used in frontend, omit entirely to minimize bundle size.
- **FR-008**: All replacement packages MUST maintain TypeScript type definitions compatible with existing usage
- **FR-009**: System MUST NOT require any code changes in the existing frontend application source code to use replacement packages. Application code in action_server/frontend/src/ must remain unchanged. Configuration files (package.json, .npmrc, tsconfig.json, vite.config.js) MAY be updated as needed for package references.

#### Component Functionality
- **FR-010**: All replaced components MUST render visually identical to their private package counterparts, validated through manual QA review by maintainers comparing side-by-side rendered components
- **FR-011**: All replaced components MUST maintain the same functional behavior (interactions, state management, accessibility), validated through manual QA review
- **FR-012**: Components MUST support all props and configuration options currently used in the frontend (unused features from private packages may be omitted)
- **FR-013**: Theme system MUST support dynamic theming and design token customization as currently implemented

#### Development Experience
- **FR-014**: System MUST provide clear documentation for the open-source replacement architecture
- **FR-015**: Package structure MUST use npm workspaces for local development and deployment with file: protocol references
- **FR-016**: Type checking with TypeScript MUST work correctly with all replacement packages
- **FR-017**: Development hot-reload MUST work with the replacement packages during local development

### Build & Release

#### Package Structure
- **FR-018**: Replacement packages MUST be located within the repository structure (not external dependencies)
- **FR-015**: Package structure MUST use npm workspaces for local development and bundling with file: protocol references
- **FR-020**: Build artifacts MUST be generated reproducibly from source without requiring external resources
- **FR-021**: Migration to open-source packages MUST occur as a single atomic replacement switching all three packages simultaneously in one pull request

#### Validation & Quality
- **FR-022**: System MUST validate that all existing frontend component usage patterns are covered by tests
- **FR-023**: Manual QA review MUST confirm UI consistency between private and open-source implementations through side-by-side comparison using objective criteria documented in VISUAL-QA-CHECKLIST.md
- **FR-024**: Accessibility standards (WCAG) MUST be maintained at the same level as private packages
- **FR-025**: Bundle size MUST remain within ±5% of the current size with private packages to prevent performance degradation (baseline to be measured and documented in BASELINE-METRICS.md before implementation begins)

### Key Entities

- **Theme Package**: Provides design tokens (colors, spacing, typography), styling utilities, and ThemeProvider component for consistent visual design across the application

- **Icons Package**: Provides a library of 18 SVG-based icon components used throughout the UI with consistent sizing, coloring, and accessibility attributes

- **Components Package**: Provides 22 reusable UI components (Badge, Box, Button, Code, Dialog, Drawer, EditorView, Grid, Header, Input, Link, Progress, Scroll, SideNavigation, Table, Tabs, Tooltip, Typography) and 4 utility functions (componentWithRef, useClipboard, usePopover, useSystemTheme) with standardized APIs, accessibility features, and theme integration. Additionally exports TypeScript types including Column (Table column definition), TableRowProps, ButtonProps, and InputProps.

- **Package Dependencies**: The set of open-source libraries (MIT/ISC/Apache 2.0 licensed) that form the foundation for the replacement packages, ensuring legal compliance and public accessibility

---

## Review & Acceptance Checklist

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
  - *Note: Requirements specify "what" packages must do, not "how" they're implemented*
- [x] Focused on user value and business needs
  - *Core value: Enable external contributions by removing authentication barriers*
- [x] Written for non-technical stakeholders
  - *Requirements focus on build success, compatibility, and accessibility*
- [x] All mandatory sections completed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
  - *Each FR can be validated via build commands, visual testing, or API verification*
- [x] Success criteria are measurable
  - *Build success, zero code changes, license compliance, visual parity*
- [x] Scope is clearly bounded
  - *Limited to frontend design system packages only*
- [x] Dependencies and assumptions identified
  - *Assumption: 18 icons and 26 components fully enumerated; Dependency: CI pipeline exists*

---

## Execution Status

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked (none found)
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [x] Review checklist passed

---

## Notes

### Context from Previous Attempts
This specification supersedes previous approaches that relied on upstream maintainers providing vendored packages. The previous spec (002-build-packaging-bug) assumed maintainers would supply pre-compiled assets, which will not happen. This specification takes a clean-room approach to ensure full open-source compliance and contributor accessibility.

### Success Validation
The feature is considered complete when:
1. A completely fresh repository clone builds successfully without any authentication
2. All existing frontend component usage continues to work without modification
3. CI validates builds work without credentials on every PR
4. All dependencies are verifiably open-source under approved licenses
5. Visual and functional parity is maintained with the original UI

### Out of Scope
- Redesigning the UI or changing component APIs beyond maintaining compatibility
- Contributing changes back to upstream private packages
- Supporting additional components beyond the current 26 in use
- Migration of other parts of the codebase not related to frontend design system

### Implementation Tradeoffs
- When conflicts arise between implementation simplicity and feature parity, exact feature parity takes precedence even if the implementation becomes more complex
- For features/props actually used in the frontend (per FR-007), the replacement must match the private package behavior precisely
- **Tiebreaker Rule**: When a feature/prop IS currently used in the frontend, favor exact parity with the private package even if implementation is complex. When a feature/prop is NOT used in the frontend, omit it entirely to minimize bundle size and maintenance burden.
- Implementation complexity is acceptable to ensure zero breaking changes and identical user experience for all actively-used functionality
