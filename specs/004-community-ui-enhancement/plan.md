````markdown
# Implementation Plan: Community UI Enhancement

**Branch**: `004-community-ui-enhancement` | **Date**: 2025-10-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-community-ui-enhancement/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Enhance the Action Server community tier frontend with professional UI styling while maintaining functional parity with enterprise tier but with visual differentiation. The feature adds polished styling to existing React components using Tailwind CSS + Radix UI (no new dependencies), improving form inputs, dialogs, tables, dropdowns, and feedback states. Target WCAG AA accessibility, maintain bundle size ≤350KB (110KB gzipped), and keep build time ≤5 minutes.

## Technical Context

**Language/Version**: TypeScript 5.3.3, React 18.2.0  
**Primary Dependencies**: Vite 6.1.0 (build), Radix UI 1.0.x (headless components), Tailwind CSS 3.4.1 (styling), class-variance-authority 0.7.0 (variants), clsx 2.1.0 + tailwind-merge 2.2.0 (className utility), React Router DOM 6.21.3 (navigation), TanStack Query 5.28.0 (data fetching)  
**Storage**: N/A (frontend only, no persistence layer)  
**Testing**: Vitest 3.1.3 (unit tests), React Testing Library (component tests), Lighthouse (accessibility audits), axe DevTools (a11y validation)  
**Target Platform**: Modern browsers (Chrome 90+, Firefox 88+, Safari 14+), mobile viewports ≥375px  
**Project Type**: Web application (frontend only, action-server package)  
**Performance Goals**: Bundle ≤350KB total (≤110KB gzipped), build time ≤5 minutes, First Contentful Paint ≤1.5s, Time to Interactive ≤3.5s, Lighthouse Accessibility score ≥90  
**Constraints**: No new npm dependencies allowed, must use existing Radix UI + Tailwind, no DOMPurify unless innerHTML is used, WCAG 2.1 AA compliance (4.5:1 contrast), respect prefers-reduced-motion, 100-500 table rows without virtualization, 10k character textarea limit  
**Scale/Scope**: Community tier frontend only (action_server/frontend/src/core/), 6 core components to enhance (Input, Textarea, Dialog, Table, DropdownMenu, Button already done), 4 main pages (Actions, RunHistory, Logs, Artifacts), ~20 functional requirements

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Library-First Action Design
**Status**: ✅ COMPLIANT (N/A - Frontend Enhancement)  
**Rationale**: This feature enhances UI components within the action-server frontend package. It does not create a new Action or library for external reuse. Components are scoped to action-server only per spec clarification.

### II. CLI & HTTP-First Interface
**Status**: ✅ COMPLIANT (N/A - Frontend Enhancement)  
**Rationale**: This feature is frontend-only. No CLI or HTTP contract changes are made.

### III. Test-First (NON-NEGOTIABLE)
**Status**: ⚠️ REQUIRES ACTION  
**Rationale**: Component tests MUST be written before implementation. Each enhanced component (Input, Textarea, Dialog, Table, DropdownMenu) MUST have:
- Unit tests for all visual states (base, hover, focus, disabled, error)
- Accessibility tests (keyboard navigation, focus management, ARIA attributes)
- Integration tests for user workflows (form submission, dialog open/close, table interaction)

**Action Required**: 
- Write failing tests for each component before styling changes
- Add visual regression tests (screenshot comparisons)
- Add Lighthouse accessibility test in CI
- Tests must validate FR-UI-001 through FR-UI-022 from spec

### IV. Contract & Integration Testing
**Status**: ✅ COMPLIANT (Component API Stability)  
**Rationale**: Component props interfaces (InputProps, DialogProps, etc.) remain unchanged. Styling is additive (className overrides). No breaking changes to component contracts. Existing pages continue to work with enhanced components.

**Validation**:
- All existing component usages in pages must continue to function
- React prop types remain backward compatible
- No removal of public component exports

### V. Vendored Builds & Reproducible Releases
**Status**: ✅ COMPLIANT (N/A - No Vendoring)  
**Rationale**: This feature does not introduce vendored build artifacts. All styling changes are source code modifications (TypeScript + Tailwind classes). No new binaries, no external dependencies to vendor.

**Build Validation**:
- CI must validate bundle size remains ≤350KB (110KB gzipped)
- Build time must remain ≤5 minutes
- Deterministic builds enforced by existing Vite configuration

---

**GATE RESULT**: ⚠️ CONDITIONAL PASS  
**Blocker**: Test-First requirement must be satisfied before implementation begins (Phase 0 → Phase 1)  
**Re-check**: After Phase 1 design, validate that component tests cover all acceptance scenarios from spec

## Project Structure

### Documentation (this feature)

```
specs/004-community-ui-enhancement/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
action_server/frontend/
├── src/
│   ├── core/                          # Community tier (target for enhancements)
│   │   ├── components/
│   │   │   └── ui/                   # UI component primitives (Radix + Tailwind)
│   │   │       ├── Button.tsx        # ✅ Already styled (5 variants, 4 sizes)
│   │   │       ├── Input.tsx         # 🎯 Enhancement target (add states)
│   │   │       ├── Textarea.tsx      # 🎯 Enhancement target (add states)
│   │   │       ├── Dialog.tsx        # 🎯 Enhancement target (backdrop, animation)
│   │   │       ├── Table.tsx         # 🎯 Enhancement target (hover, header)
│   │   │       ├── DropdownMenu.tsx  # 🎯 Enhancement target (menu items, animation)
│   │   │       ├── Badge.tsx         # 🆕 New component (status indicators)
│   │   │       ├── Loading.tsx       # 🆕 New component (spinner, timeout)
│   │   │       └── ErrorBanner.tsx   # 🆕 New component (error display)
│   │   ├── pages/
│   │   │   ├── Actions.tsx           # Uses: Button, Input, Table, Dialog, Badge
│   │   │   ├── RunHistory.tsx        # Uses: Table, Badge, DropdownMenu
│   │   │   ├── Logs.tsx              # Uses: Table, Loading
│   │   │   └── Artifacts.tsx         # Uses: Table, Loading
│   │   └── services/
│   ├── shared/                        # Tier-agnostic utilities
│   │   ├── utils/
│   │   │   └── cn.ts                 # ✅ Already exists (clsx + twMerge)
│   │   ├── hooks/                    # Custom React hooks
│   │   ├── types.ts                  # Shared TypeScript types
│   │   └── constants/                # App constants
│   ├── enterprise/                    # ⚠️ Do not modify (out of scope)
│   ├── App.tsx                        # Main app component
│   ├── index.tsx                      # Entry point
│   └── index.css                      # Global styles + Tailwind directives
├── __tests__/                         # 🆕 Component tests (to be created)
│   ├── components/
│   │   └── ui/
│   │       ├── Input.test.tsx
│   │       ├── Textarea.test.tsx
│   │       ├── Dialog.test.tsx
│   │       ├── Table.test.tsx
│   │       ├── DropdownMenu.test.tsx
│   │       ├── Badge.test.tsx
│   │       ├── Loading.test.tsx
│   │       └── ErrorBanner.test.tsx
│   └── a11y/                          # Accessibility tests
│       └── component-contrast.test.tsx
├── vite.config.js                     # ✅ Existing Vite config (tier separation)
├── tailwind.config.js                 # ✅ Existing Tailwind config
├── tsconfig.json                      # TypeScript config
└── package.json                       # ✅ Dependencies locked (no additions)
```

**Structure Decision**: Web application (frontend-only). This feature operates entirely within `action_server/frontend/src/core/` and does not touch backend, enterprise tier, or other monorepo packages. New components will be added to `src/core/components/ui/`, and tests will be created in `__tests__/components/ui/`. All styling uses existing Tailwind CSS + Radix UI infrastructure with no new dependencies.


## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

**No complexity violations to track.** All Constitution principles are compliant or N/A for this frontend enhancement feature.

````
