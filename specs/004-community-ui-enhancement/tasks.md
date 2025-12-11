# Tasks: Community UI Enhancement Implementation

**Input**: Design documents from `/specs/004-community-ui-enhancement/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Tests are INCLUDED in this implementation per Constitution III (Test-First NON-NEGOTIABLE requirement)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions
- Frontend: `action_server/frontend/src/`
- Tests: `action_server/frontend/__tests__/`
- Components: `action_server/frontend/src/core/components/ui/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, testing infrastructure, and test utilities

- [x] T001 Add testing dependencies to `action_server/frontend/package.json`: @testing-library/react, @testing-library/user-event, jest-axe, @playwright/test (devDependencies only)
- [x] T002 [P] Create test utilities directory `action_server/frontend/__tests__/utils/` with render helper, accessibility matchers, and custom hooks
- [x] T003 [P] Create Lighthouse CI configuration in `action_server/frontend/.lighthouserc.json` with accessibility score ≥90 threshold
- [x] T004 [P] Create Playwright configuration in `action_server/frontend/playwright.config.ts` for visual regression tests
- [x] T005 Update `action_server/frontend/vite.config.js` to include test configuration for Vitest
- [x] T006 Create shared test fixtures in `action_server/frontend/__tests__/fixtures/` for mock data (actions, runs, logs)

**Checkpoint**: Testing infrastructure ready - component development can now begin

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core utilities and base components that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T007 Validate `action_server/frontend/src/shared/utils/cn.ts` utility exists and exports cn() function (className merger using clsx + tailwind-merge)
- [x] T008 Document safe color contrast pairings in `action_server/frontend/src/core/components/ui/README.md` (from data-model.md validation table)
- [x] T009 Create accessibility test suite base in `action_server/frontend/__tests__/a11y/setup.ts` with jest-axe configuration and custom matchers
- [x] T009.1 [P] Add motion-reduce utility support to `action_server/frontend/tailwind.config.js`: verify motion-reduce: prefix works, add @media (prefers-reduced-motion: reduce) support if needed for all component files
- [x] T009.2 [P] Add animation keyframes to `action_server/frontend/tailwind.config.js`: configure keyframes for dialog animations (fadeIn, fadeOut, zoomIn-95, zoomOut-95 at 200ms), dropdown animations (slideDownAndFade at 150ms), and corresponding animation utilities (animate-in, animate-out, fade-in-0, fade-out-0, zoom-in-95, zoom-out-95, slide-in-from-top-2) per FR-UI-006 and FR-UI-011

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - View and Interact with Forms (Priority: P0) 🎯 MVP

**Goal**: Enable developers to configure actions and execute them with input parameters through professional, accessible forms with clear visual feedback

**Independent Test**: Open any action requiring parameters, enter values in inputs/textareas, trigger error states, submit form, and verify all visual states work correctly

### Tests for User Story 1

**NOTE: Write these tests FIRST, ensure they FAIL before implementation**

  - [x] T010 [P] [US1] Create Input component unit tests in `action_server/frontend/__tests__/components/ui/Input.test.tsx`: test base, hover, focus, disabled, error states with visual class assertions
  - [x] T011 [P] [US1] Create Input accessibility tests in `action_server/frontend/__tests__/a11y/Input.a11y.test.tsx`: validate keyboard navigation (Tab focus), screen reader attributes (role, aria-invalid), and contrast ratios using jest-axe
  - [x] T012 [P] [US1] Create Textarea component unit tests in `action_server/frontend/__tests__/components/ui/Textarea.test.tsx`: test all states plus monospace font trigger (spellCheck={false}), character limit (10,000), and vertical resize
  - [x] T013 [P] [US1] Create Textarea accessibility tests in `action_server/frontend/__tests__/a11y/Textarea.a11y.test.tsx`: validate focus management, ARIA attributes, and contrast compliance
  - [x] T014 [P] [US1] Create visual regression tests for Input/Textarea in `action_server/frontend/__tests__/visual/form-components.spec.ts`: capture screenshots of all states using Playwright

### Implementation for User Story 1

  - [x] T015 [P] [US1] Create Input component in `action_server/frontend/src/core/components/ui/Input.tsx`: implement all visual states (base, hover, focus, disabled, error) using Tailwind utilities, accept error prop, use cn() for className merging, export InputProps interface
  - [x] T016 [P] [US1] Create Textarea component in `action_server/frontend/src/core/components/ui/Textarea.tsx`: inherit Input styling, add min-h-[80px], resize-y, monospace font for spellCheck={false}, export TextareaProps interface
 - [x] T017 [US1] Update existing form pages to use new Input component in `action_server/frontend/src/core/pages/Actions.tsx`: replace basic input elements with <Input>, add error prop bindings to validation state
 - [x] T018 [US1] Add form validation integration example in `action_server/frontend/src/core/pages/Actions.tsx`: demonstrate error state triggering on invalid email/required field patterns

**Checkpoint**: At this point, User Story 1 should be fully functional - forms have professional styling with all visual states working

---

## Phase 4: User Story 2 - Navigate and Understand Data Tables (Priority: P0)

**Goal**: Enable developers to view action execution history, browse logs, and review artifacts through scannable, visually clear tables with hover states

**Independent Test**: Navigate to Run History or Logs pages, hover over rows, click entries, and verify table styling (header distinction, row hover, border handling)

### Tests for User Story 2

- [x] T019 [P] [US2] Create Table component unit tests in `action_server/frontend/__tests__/components/ui/Table.test.tsx`: test header styling, row hover states, selected state, clickable cursor, last row border removal
- [x] T020 [P] [US2] Create Table accessibility tests in `action_server/frontend/__tests__/a11y/Table.a11y.test.tsx`: validate semantic HTML (thead, tbody, th scope), keyboard navigation, screen reader announcements for row selection
- [x] T021 [P] [US2] Create Table performance tests in `action_server/frontend/__tests__/performance/Table.perf.test.tsx`: render 100, 500, and 1000 rows, measure render time and scroll performance (must not exceed 16ms per frame for 60fps)
- [x] T022 [P] [US2] Create visual regression tests for Table in `action_server/frontend/__tests__/visual/table.spec.ts`: capture header, hover states, selected row, empty state

### Implementation for User Story 2

 - [x] T023 [P] [US2] Create Table root component in `action_server/frontend/src/core/components/ui/Table.tsx`: export Table, TableHeader, TableBody, TableRow, TableHead, TableCell components with proper semantic HTML and styling, MUST include role="table" on container, role="row" on TableRow, role="columnheader" on TableHead, role="cell" on TableCell, and aria-label prop on Table per FR-A11Y-004
 - [x] T024 [P] [US2] Implement TableRow component with hover state in `action_server/frontend/src/core/components/ui/Table.tsx`: add hover:bg-gray-50 transition-colors duration-200, support selected prop (bg-blue-50), clickable prop (cursor-pointer)
 - [x] T025 [P] [US2] Implement TableHeader styling in `action_server/frontend/src/core/components/ui/Table.tsx`: add bg-gray-50 border-b font-medium to distinguish from body rows
 - [x] T026 [US2] Update RunHistory page to use new Table component in `action_server/frontend/src/core/pages/RunHistory.tsx`: replace existing table markup with new components, add hover states and clickable rows
 - [x] T027 [US2] Update Logs page to use new Table component in `action_server/frontend/src/core/pages/Logs.tsx`: apply table styling to log entries (Loading/ErrorBanner integration applied)
 - [x] T028 [US2] Update Artifacts page to use new Table component in `action_server/frontend/src/core/pages/Artifacts.tsx`: apply table styling to artifact list (Badge/Loading integration applied)
 - [x] T029 [US2] Add empty state component for tables in `action_server/frontend/src/core/components/ui/Table.tsx`: create TableEmptyState sub-component with centered message and CTA button

**Checkpoint**: At this point, User Story 2 should be fully functional - tables are scannable with clear visual hierarchy

---

## Phase 5: User Story 3 - Interact with Modal Dialogs (Priority: P0)

**Goal**: Enable developers to confirm dangerous actions, view detailed information, and configure settings through clearly visible modal dialogs with proper animations

**Independent Test**: Trigger any confirmation dialog (e.g., delete action), view overlay/backdrop, interact with buttons, press Escape to close, verify animations

### Tests for User Story 3

- [x] T030 [P] [US3] Create Dialog component unit tests in `action_server/frontend/__tests__/components/ui/Dialog.test.tsx`: test open/close states (data-state attribute changes), animation classes present (animate-in, fade-in-0, zoom-in-95), backdrop renders with bg-black/50 backdrop-blur-sm, focus trap cycles through dialog elements only (Tab key stays within dialog), Escape key triggers onOpenChange(false)
- [x] T031 [P] [US3] Create Dialog accessibility tests in `action_server/frontend/__tests__/a11y/Dialog.a11y.test.tsx`: validate role="dialog", aria-modal="true", aria-labelledby links to DialogTitle id, aria-describedby links to DialogDescription id, Tab key cycles focus within dialog (focus trap per FR-UI-017), Escape closes dialog, jest-axe returns no violations
- [ ] T032 [P] [US3] Create Dialog animation tests in `action_server/frontend/__tests__/components/ui/Dialog.animation.test.tsx`: verify prefers-reduced-motion:reduce disables zoom/fade animations (motion-reduce:animate-none class applied), validate animation duration is exactly 200ms per FR-UI-006, test data-state transitions from closed→open→closed
- [x] T033 [P] [US3] Create visual regression tests for Dialog in `action_server/frontend/__tests__/visual/dialog.spec.ts`: capture open state, backdrop, header/footer separation, animation frames

### Implementation for User Story 3

- [x] T034 [P] [US3] Create Dialog component in `action_server/frontend/src/core/components/ui/Dialog.tsx`: implement Dialog (Root), DialogTrigger, DialogPortal, DialogOverlay (bg-black/50 backdrop-blur-sm), DialogContent (centered with animations)
- [x] T035 [P] [US3] Implement Dialog animation states in `action_server/frontend/src/core/components/ui/Dialog.tsx`: add data-[state=open]:animate-in fade-in-0 zoom-in-95 duration-200, data-[state=closed]:animate-out fade-out-0 zoom-out-95, AND motion-reduce:animate-none motion-reduce:transition-none for accessibility compliance per FR-UI-013 (requires T009.2 keyframes)
- [x] T036 [P] [US3] Create Dialog sub-components in `action_server/frontend/src/core/components/ui/Dialog.tsx`: DialogHeader (with border-b), DialogFooter (with border-t), DialogTitle, DialogDescription, DialogClose (X button)
- [ ] T037 [US3] Update Actions page to use Dialog for delete confirmation in `action_server/frontend/src/core/pages/Actions.tsx`: replace existing modal with Dialog component, add destructive button styling
- [ ] T038 [US3] Add Dialog example for action execution in `action_server/frontend/src/core/pages/Actions.tsx`: create form dialog with Input/Textarea components for parameters

**Checkpoint**: At this point, User Story 3 should be fully functional - dialogs are clearly visible with smooth animations and keyboard support

---

## Phase 6: User Story 4 - Use Dropdown Menus (Priority: P1)

**Goal**: Enable developers to access action options (run, edit, delete), change settings, and filter data through discoverable dropdown menus with clear hover states

**Independent Test**: Click any action menu (three dots), hover over items, use arrow keys for keyboard navigation, select an option, click outside to close

### Tests for User Story 4

- [x] T039 [P] [US4] Create DropdownMenu component unit tests in `action_server/frontend/__tests__/components/ui/DropdownMenu.test.tsx`: test open/close, item hover states, keyboard navigation (arrow keys, Enter, Escape), destructive styling
- [x] T040 [P] [US4] Create DropdownMenu accessibility tests in `action_server/frontend/__tests__/a11y/DropdownMenu.a11y.test.tsx`: validate ARIA attributes (role="menu", aria-expanded), keyboard navigation (Up/Down arrows, Home/End), focus management
- [x] T041 [P] [US4] Create visual regression tests for DropdownMenu in `action_server/frontend/__tests__/visual/dropdown.spec.ts`: capture menu open state, item hover, destructive item styling, separator

### Implementation for User Story 4

- [x] T042 [P] [US4] Create DropdownMenu component in `action_server/frontend/src/core/components/ui/DropdownMenu.tsx`: implement DropdownMenu (Root), DropdownMenuTrigger, DropdownMenuContent (with animation), DropdownMenuItem, DropdownMenuSeparator
- [x] T043 [P] [US4] Implement DropdownMenuItem hover and focus states in `action_server/frontend/src/core/components/ui/DropdownMenu.tsx`: add hover:bg-gray-100 focus:bg-gray-100, support destructive prop (text-red-600 hover:bg-red-50)
- [x] T044 [P] [US4] Add DropdownMenu animation in `action_server/frontend/src/core/components/ui/DropdownMenu.tsx`: data-[state=open]:animate-slide-down-fade duration-150, data-[state=closed]:animate-fade-out, AND motion-reduce:animate-none motion-reduce:transition-none per FR-UI-013 (requires T009.2 keyframes)
- [ ] T045 [US4] Update Actions page to use DropdownMenu for action options in `action_server/frontend/src/core/pages/Actions.tsx`: replace existing menu with DropdownMenu component, add Edit/Delete/View Logs items
- [x] T046 [US4] Update RunHistory page to use DropdownMenu in `action_server/frontend/src/core/pages/RunHistory.tsx`: add options menu for each run (View Details, Download Logs)

**Checkpoint**: At this point, User Story 4 should be fully functional - dropdown menus provide clear access to secondary actions

---

## Phase 7: User Story 5 - Understand System State (Priority: P1)

**Goal**: Enable developers to know when system is loading, when errors occur, and action status through clear visual feedback (spinners, error banners, status badges)

**Independent Test**: Trigger loading state (refresh page), cause error (invalid input), view action statuses, and verify all feedback components work

### Tests for User Story 5

 - [x] T047 [P] [US5] Create Badge component unit tests in `action_server/frontend/__tests__/components/ui/Badge.test.tsx`: test all variants (success, error, warning, info, neutral), validate color classes
 - [x] T048 [P] [US5] Create Badge accessibility tests in `action_server/frontend/__tests__/a11y/Badge.a11y.test.tsx`: validate contrast ratios for all variants (must meet WCAG AA 4.5:1), screen reader text
 - [x] T049 [P] [US5] Create Loading component unit tests in `action_server/frontend/__tests__/components/ui/Loading.test.tsx`: test spinner render, timeout state (30s), retry button, motion-reduce spinner disabling
 - [x] T050 [P] [US5] Create ErrorBanner component unit tests in `action_server/frontend/__tests__/components/ui/ErrorBanner.test.tsx`: test message display, dismiss button callback, icon rendering
 - [x] T051 [P] [US5] Create visual regression tests for state components in `action_server/frontend/__tests__/visual/state-indicators.spec.ts`: capture all badge variants, loading spinner, error banner

### Implementation for User Story 5

 - [x] T052 [P] [US5] Create Badge component in `action_server/frontend/src/core/components/ui/Badge.tsx`: implement variants (success=green, error=red, warning=yellow, info=blue, neutral=gray) with proper contrast ratios, default to neutral, use inline-flex for icon support, MUST include aria-label prop describing status text AND semantic meaning (e.g., aria-label="Status: Success") per FR-A11Y-006
 - [x] T053 [P] [US5] Create Loading component in `action_server/frontend/src/core/components/ui/Loading.tsx`: implement spinner (animate-spin, border-4, border-gray-200 border-t-blue-600), support text prop, timeout prop (replace spinner with retry button), motion-reduce:animate-none, MUST include role="status" aria-live="polite" aria-label="Loading" (or custom text from text prop) per FR-A11Y-007
 - [x] T054 [P] [US5] Create ErrorBanner component in `action_server/frontend/src/core/components/ui/ErrorBanner.tsx`: implement red banner (bg-red-50 border-red-200), required message prop, optional onDismiss callback, include error icon, MUST include role="alert" aria-live="assertive" aria-atomic="true" for immediate screen reader announcement per FR-A11Y-008
 - [x] T055 [US5] Integrate Badge component into Table cells in `action_server/frontend/src/core/pages/Actions.tsx` and `RunHistory.tsx`: replace plain text status with Badge components, map status values to variants
 - [x] T056 [US5] Add Loading component to all data-fetching pages in `action_server/frontend/src/core/pages/`: Actions.tsx, RunHistory.tsx, Logs.tsx, Artifacts.tsx - wrap content with loading state checks (Applied to Actions.tsx dialog and recent runs list)
 - [x] T056.1 [US5] Implement coordinated page-level loading in `action_server/frontend/src/core/pages/Actions.tsx`: use TanStack Query's useIsFetching() hook to show single Loading spinner when multiple queries are pending (actions list + recent runs), transition to content only when ALL critical data arrives per FR-UI-024
 - [x] T057 [US5] Add ErrorBanner to page error states in `action_server/frontend/src/core/pages/Actions.tsx`: integrate with TanStack Query error handling, provide dismiss functionality (Applied to run dialog error display)

**Checkpoint**: At this point, User Story 5 should be fully functional - system state is transparent through clear visual feedback

---

## Phase 8: User Story 6 - Experience Smooth Micro-interactions (Priority: P2)

**Goal**: Create professional polish through smooth transitions, consistent animations, and responsive feedback on all interactive elements

**Independent Test**: Interact with buttons, links, cards, observe hover states and transitions, enable prefers-reduced-motion and verify animations disable

### Tests for User Story 6

- [x] T058 [P] [US6] Create micro-interaction tests in `action_server/frontend/__tests__/components/ui/animations.test.tsx`: test all transition durations ≤200ms, motion-reduce disabling, hover state transitions
- [ ] T059 [P] [US6] Create browser compatibility tests in `action_server/frontend/__tests__/browser/compat.spec.ts`: use Playwright to test animations in Chrome, Firefox, Safari (validate backdrop-filter performance)

### Implementation for User Story 6

- [ ] T060 [P] [US6] Add transition utilities and motion-reduce fallbacks to all interactive components in `action_server/frontend/src/core/components/ui/`: audit Button, Input, Table, Dialog, DropdownMenu for consistent transition-colors duration-200 AND motion-reduce:transition-none on all transitions per FR-UI-013
- [x] T061 [P] [US6] Add motion-reduce fallbacks to animated components in `action_server/frontend/src/core/components/ui/Dialog.tsx` and `DropdownMenu.tsx`: ensure motion-reduce:transition-none motion-reduce:animate-none on all animations
- [ ] T062 [US6] Add subtle hover effects to clickable cards in `action_server/frontend/src/core/pages/Actions.tsx`: apply hover:scale-[1.02] transition-transform to action cards (if present)
- [ ] T063 [US6] Add page transition animations in `action_server/frontend/src/App.tsx`: implement fade transitions between routes using React Router DOM (if not already present)

**Checkpoint**: All user stories should now have polished interactions - interface feels responsive and professional

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements affecting multiple user stories

- [ ] T064 [P] Create component documentation in `action_server/frontend/src/core/components/ui/README.md`: document usage patterns, prop interfaces, accessibility requirements, safe color pairings
- [x] T065 [P] Add bundle size validation to CI in `.github/workflows/frontend-build.yml`: fail build if bundle exceeds 350KB (110KB gzipped) threshold
- [ ] T066 [P] Add Lighthouse CI workflow in `.github/workflows/lighthouse.yml`: run accessibility audits on PR, require score ≥90
- [ ] T067 Run full test suite and fix any remaining failures: `cd action_server/frontend && npm run test` for unit tests, `npm run test:a11y` for accessibility, `npm run test:visual` for visual regression
- [ ] T068 Validate quickstart.md examples in `specs/004-community-ui-enhancement/quickstart.md`: manually test all code snippets work as documented
- [x] T069 [P] Performance audit documentation created in `action_server/frontend/docs/PERFORMANCE_AUDIT.md`: comprehensive checklist for validating First Contentful Paint ≤1.5s, Time to Interactive ≤3.5s, no layout shifts during transitions, bundle size ≤350KB (110KB gzipped), 60fps animations, includes Chrome DevTools instructions and reporting template
- [x] T070 [P] Cross-browser testing documentation created in `action_server/frontend/docs/CROSS_BROWSER_TESTING.md`: comprehensive guide for testing in Chrome 90+, Firefox 88+, Safari 14+ (especially iOS Safari for modal overlays); includes FR-UI-023 touch targets ≥44px validation procedures on 375px viewport using Chrome DevTools device emulation
- [x] T071 Update `.github/copilot-instructions.md` with new component patterns and testing requirements from this feature

**Checkpoint**: Feature complete - all user stories working, tests passing, performance validated

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion (T001-T006) - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion (T007-T009)
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (US1 → US2 → US3 → US4 → US5 → US6)
- **Polish (Phase 9)**: Depends on all user stories being complete (T010-T063)

### User Story Dependencies

- **User Story 1 (US1 - Forms)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (US2 - Tables)**: Can start after Foundational - Independent (but will integrate Badge from US5 later)
- **User Story 3 (US3 - Dialogs)**: Can start after Foundational - Uses Input/Textarea from US1 in forms (soft dependency)
- **User Story 4 (US4 - Dropdowns)**: Can start after Foundational - Independent (uses existing Button component)
- **User Story 5 (US5 - State)**: Can start after Foundational - Independent, but integrates into all pages
- **User Story 6 (US6 - Animations)**: Depends on all other stories (applies polish across components)

### Within Each User Story

- Tests MUST be written and FAIL before implementation (per Constitution III)
- Component implementation before page integration
- Core functionality before enhancements
- Story complete and independently testable before moving to next priority

### Parallel Opportunities

- **Setup (Phase 1)**: T002, T003, T004 can run in parallel (different config files)
- **Foundational (Phase 2)**: T007, T008, T009 can run in parallel (different files)
- **US1 Tests**: T010, T011, T012, T013, T014 can all run in parallel (different test files)
- **US1 Implementation**: T015, T016 can run in parallel (different component files)
- **US2 Tests**: T019, T020, T021, T022 can all run in parallel
- **US2 Implementation**: T023, T024, T025 can run in parallel (same file, different components/functions)
- **US3 Tests**: T030, T031, T032, T033 can all run in parallel
- **US3 Implementation**: T034, T035, T036 can run in parallel (same file, but different sub-components)
- **US4 Tests**: T039, T040, T041 can all run in parallel
- **US4 Implementation**: T042, T043, T044 can run in parallel (same file, but different functions)
- **US5 Tests**: T047, T048, T049, T050, T051 can all run in parallel
- **US5 Implementation**: T052, T053, T054 can run in parallel (different component files)
- **US6 Tests**: T058, T059 can run in parallel
- **US6 Implementation**: T060, T061 can run in parallel (different components)
- **Polish**: T064, T065, T066, T069, T070 can run in parallel (different concerns)

**Full Parallel**: Once Foundational (Phase 2) completes, 6 different developers could work on US1-US6 simultaneously without conflicts

---

## Parallel Example: User Story 1 (Forms)

```bash
# Launch all tests for User Story 1 together (Test-First):
Task: "T010 [P] [US1] Create Input component unit tests in __tests__/components/ui/Input.test.tsx"
Task: "T011 [P] [US1] Create Input accessibility tests in __tests__/a11y/Input.a11y.test.tsx"
Task: "T012 [P] [US1] Create Textarea component unit tests in __tests__/components/ui/Textarea.test.tsx"
Task: "T013 [P] [US1] Create Textarea accessibility tests in __tests__/a11y/Textarea.a11y.test.tsx"
Task: "T014 [P] [US1] Create visual regression tests in __tests__/visual/form-components.spec.ts"

# After tests fail, launch implementations:
Task: "T015 [P] [US1] Create Input component in src/core/components/ui/Input.tsx"
Task: "T016 [P] [US1] Create Textarea component in src/core/components/ui/Textarea.tsx"

# Then integrate sequentially:
Task: "T017 [US1] Update Actions.tsx to use Input component"
Task: "T018 [US1] Add form validation integration example in Actions.tsx"
```

---

## Implementation Strategy

### MVP First (User Stories 1-3 Only - P0 Priority)

1. Complete Phase 1: Setup (T001-T006)
2. Complete Phase 2: Foundational (T007-T009) - CRITICAL checkpoint
3. Complete Phase 3: User Story 1 - Forms (T010-T018)
4. Complete Phase 4: User Story 2 - Tables (T019-T029)
5. Complete Phase 5: User Story 3 - Dialogs (T030-T038)
6. **STOP and VALIDATE**: Test all P0 stories independently, validate accessibility, check bundle size
7. Deploy MVP if ready (forms, tables, dialogs working professionally)

### Full Feature (All User Stories)

1. Complete MVP (US1-US3)
2. Add Phase 6: User Story 4 - Dropdowns (T039-T046)
3. Add Phase 7: User Story 5 - State Indicators (T047-T057)
4. Add Phase 8: User Story 6 - Micro-interactions (T058-T063)
5. Complete Phase 9: Polish (T064-T071)
6. Final validation and deployment

### Parallel Team Strategy (3 Developers)

After completing Setup + Foundational together:

- **Developer A**: User Story 1 (Forms) → User Story 4 (Dropdowns)
- **Developer B**: User Story 2 (Tables) → User Story 5 (State)
- **Developer C**: User Story 3 (Dialogs) → User Story 6 (Animations)

Each developer owns their story end-to-end (tests → implementation → integration)

---

## Notes

- **[P]** tasks = different files, no dependencies, can run in parallel
- **[Story]** label maps task to specific user story for traceability and independent testing
- Each user story should be independently completable and testable
- **Test-First is MANDATORY** (Constitution III) - all tests must fail before implementation
- Verify tests fail, implement, verify tests pass before moving to next task
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Bundle size must stay ≤350KB (monitor with `npm run build` after each component)
- Accessibility tests must pass (Lighthouse score ≥90, jest-axe no violations)
- All animations must respect `prefers-reduced-motion`
- Use existing cn() utility for className merging (no custom CSS unless necessary)
- No new npm dependencies beyond test tools (use existing Tailwind + Radix UI only)

---

## Success Metrics

- **Code Quality**: All tests passing (unit, accessibility, visual regression), zero console errors
- **Performance**: Bundle ≤350KB (110KB gzipped), build time ≤5 minutes, FCP ≤1.5s, TTI ≤3.5s
- **Accessibility**: Lighthouse score ≥90, all contrast ratios ≥4.5:1 (WCAG AA), keyboard navigation 100% functional
- **User Experience**: All 6 user stories independently functional and testable, smooth animations (200ms), professional visual polish
- **Deliverables**: 8 enhanced/new components (Input, Textarea, Dialog, Table, DropdownMenu, Badge, Loading, ErrorBanner), 4 updated pages (Actions, RunHistory, Logs, Artifacts)
