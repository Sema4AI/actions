# Feature Specification: Community UI Enhancement Implementation

**Feature Branch**: `004-community-ui-enhancement`  
**Created**: 2025-10-12  
**Status**: Draft  
**Input**: User description: "Community UI Enhancement Implementation"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View and Interact with Forms (Priority: P0)

A developer using the Action Server community edition needs to configure actions, execute actions with input parameters, and view results. They interact with forms (inputs, textareas) to provide action parameters and expect a professional interface (no visual glitches, consistent spacing per Tailwind scale, WCAG AA compliant contrast, smooth transitions ≤200ms, clear visual hierarchy) with clear visual feedback.

**Why this priority**: Forms are the primary interaction point for action execution. Without proper styling, users cannot effectively provide input or understand validation states.

**Independent Test**: Can be fully tested by opening any action that requires parameters, entering values, and submitting. Delivers immediate value by making the core action execution workflow usable and professional.

**Acceptance Scenarios**:

1. **Given** a form with text inputs, **When** I click into an input field, **Then** I see a clear blue focus ring appear with 2px offset
2. **Given** a form with validation errors, **When** the error state is triggered, **Then** I see the input border turn red and focus ring color change to red
3. **Given** a disabled input field, **When** I hover over it, **Then** I see a gray background and not-allowed cursor
4. **Given** a textarea for JSON input, **When** I type, **Then** I see monospace font for better code readability
5. **Given** any form input, **When** I hover without focus, **Then** I see the border color change from gray-300 to gray-400

---

### User Story 2 - Navigate and Understand Data Tables (Priority: P0)

A developer needs to view action execution history, browse logs, and review artifacts. They interact with tables displaying this data and expect clear visual hierarchy with hover states to understand which row they're examining. Note: Logs and Artifacts pages reuse the same Table component patterns defined in this user story with no additional custom requirements.

**Why this priority**: Tables are the primary display for run history, logs, and artifacts. Without proper styling, users cannot easily scan or navigate data.

**Independent Test**: Can be fully tested by navigating to Run History or Logs pages, hovering over rows, and clicking entries. Delivers value by making data browsable and scannable.

**Acceptance Scenarios**:

1. **Given** a table with multiple rows, **When** I hover over a row, **Then** I see the background change to light gray (gray-50) with smooth transition
2. **Given** a table header, **When** I view the page, **Then** I see the header clearly distinguished with gray-50 background and medium font weight
3. **Given** a table with many rows, **When** I scroll to the bottom, **Then** I see no border on the last row
4. **Given** a clickable table row, **When** I hover, **Then** I see a pointer cursor indicating it's interactive
5. **Given** an empty table, **When** I view the page, **Then** I see a centered message with actionable guidance

---

### User Story 3 - Interact with Modal Dialogs (Priority: P0)

A developer needs to confirm dangerous actions (delete, stop), view detailed information, or configure settings through modal dialogs. They expect the dialog to clearly overlay the page with proper visual hierarchy and smooth animations.

**Why this priority**: Dialogs are critical for destructive actions and important workflows. Poor styling makes them hard to notice or understand, risking accidental actions.

**Independent Test**: Can be fully tested by triggering any confirmation dialog (e.g., delete action), viewing the overlay, and interacting with buttons. Delivers value by making critical interactions clear and safe.

**Acceptance Scenarios**:

1. **Given** an action that opens a dialog, **When** the dialog opens, **Then** I see a semi-transparent dark backdrop (black/50) with blur effect
2. **Given** an open dialog, **When** it animates in, **Then** I see it fade in and scale up smoothly over 200ms
3. **Given** a dialog with header and footer, **When** I view it, **Then** I see clear visual separation with borders and consistent spacing
4. **Given** an open dialog, **When** I press Escape, **Then** the dialog closes with smooth animation
5. **Given** an open dialog, **When** I press Tab, **Then** focus stays trapped within the dialog elements

---

### User Story 4 - Use Dropdown Menus (Priority: P1)

A developer needs to access action options (run, edit, delete), change settings, or filter data through dropdown menus. They expect the menu to appear with smooth animation and clear hover states.

**Why this priority**: Dropdowns provide access to secondary actions and options. Without styling, users cannot easily identify available options or current focus.

**Independent Test**: Can be fully tested by clicking any action menu (three dots), hovering over items, and selecting an option. Delivers value by making secondary actions discoverable and accessible.

**Acceptance Scenarios**:

1. **Given** a closed dropdown menu, **When** I click the trigger, **Then** I see the menu fade in and slide down over 150ms
2. **Given** an open dropdown menu, **When** I hover over an item, **Then** I see the background change to gray-100
3. **Given** an open dropdown menu, **When** I use arrow keys, **Then** I see keyboard focus move between items with visual indicator
4. **Given** an open dropdown menu, **When** I click outside, **Then** the menu closes smoothly
5. **Given** dropdown items with icons, **When** I view the menu, **Then** I see icons properly aligned with text

---

### User Story 5 - Understand System State (Priority: P1)

A developer needs to know when the system is loading data, when errors occur, and the status of actions (running, success, failed). They expect clear visual feedback through loading indicators, error messages, and status badges.

**Why this priority**: State feedback is essential for understanding system behavior. Without it, users don't know if the system is working or broken.

**Independent Test**: Can be fully tested by triggering a loading state (refresh page), causing an error (invalid input), and viewing action statuses. Delivers value by making system state transparent.

**Acceptance Scenarios**:

1. **Given** a page loading data, **When** data is being fetched, **Then** I see a centered spinner with smooth rotation animation
2. **Given** a loading state, **When** data arrives, **Then** I see smooth transition from spinner to content without flash
3. **Given** an error condition, **When** the error occurs, **Then** I see a red banner with clear error message and optional dismiss button
4. **Given** multiple action statuses, **When** I view the list, **Then** I see color-coded badges (green=success, red=error, blue=running, yellow=warning, gray=neutral)
5. **Given** an empty state (no actions), **When** I view the page, **Then** I see helpful message with clear call-to-action button

---

### User Story 6 - Experience Smooth Micro-interactions (Priority: P2)

A developer interacts with various UI elements and expects professional polish through smooth transitions, consistent animations, and responsive feedback on all interactive elements.

**Why this priority**: Micro-interactions create a professional feel and reduce perceived latency. They're important for polish but not critical for core functionality.

**Independent Test**: Can be fully tested by interacting with buttons, links, and interactive elements, observing hover states and transitions. Delivers value by making the interface feel responsive and professional.

**Acceptance Scenarios**:

1. **Given** any button, **When** I hover over it, **Then** I see color change with 200ms transition
2. **Given** any interactive element, **When** I hover, **Then** I see the transition respect FR-UI-013 (prefers-reduced-motion support)
3. **Given** a clickable card or button, **When** I hover, **Then** I see subtle scale effect (1.02x) with smooth animation
4. **Given** page navigation, **When** I click a route, **Then** I see smooth fade transition between pages
5. **Given** all transitions, **When** they animate, **Then** they respect FR-UI-016 duration requirements and avoid jankiness

---

### User Story 7 - Navigate with Keyboard and Screen Reader (Priority: P0)

A developer using assistive technology (keyboard-only navigation or screen reader) needs to access all functionality without a mouse. They expect proper focus management, ARIA announcements, and keyboard shortcuts to work consistently across all components.

**Why this priority**: Accessibility is not optional. Users with disabilities must have equal access to all features per WCAG AA compliance requirements.

**Independent Test**: Can be fully tested by navigating the entire application using only keyboard (Tab, Enter, Escape, Arrow keys) and validating with screen reader (NVDA, JAWS, VoiceOver). Delivers value by making the application usable for 15-20% of developers with accessibility needs.

**Acceptance Scenarios**:

1. **Given** any interactive element (button, input, link), **When** I press Tab to navigate, **Then** I see a visible focus indicator and screen reader announces the element role and state
2. **Given** a form with multiple inputs, **When** I navigate with Tab, **Then** focus moves in logical order and screen reader announces label, type, and required status for each input
3. **Given** an open dialog, **When** I press Tab, **Then** focus stays trapped within the dialog and I can reach all interactive elements
4. **Given** a dropdown menu, **When** I press Enter or Space to open and use Arrow keys, **Then** focus moves between menu items and screen reader announces each item
5. **Given** a table with clickable rows, **When** I navigate with Tab and press Enter, **Then** the row action triggers and screen reader announces the result
6. **Given** a loading state, **When** data is being fetched, **Then** screen reader announces "loading" status with aria-live region
7. **Given** an error banner, **When** it appears, **Then** screen reader announces the error message immediately via aria-live="assertive"
8. **Given** a status badge, **When** I focus on it or its parent element, **Then** screen reader announces both the status label and semantic meaning (e.g., "success" or "error")
9. **Given** any page on mobile viewport (375px), **When** I tap interactive elements, **Then** all touch targets are ≥44px and don't trigger accidentally
10. **Given** any animation, **When** I have prefers-reduced-motion enabled, **Then** animations are disabled or reduced to opacity-only changes

---

### Edge Cases

- What happens when a table has zero rows? (Empty state per FR-UI-008 must be shown)
- What happens when a dialog's content is taller than the viewport? (Content should scroll, header/footer stay fixed)
- What happens when an input receives extremely long text? (Text should wrap or truncate with ellipsis; textareas support up to 10,000 characters without performance degradation)
- What happens when a user has prefers-reduced-motion enabled? (All animations should be disabled or minimal)
- What happens when a user has high-contrast mode enabled (OS accessibility feature)? (Remove backdrop-blur effects, increase border contrast to 7:1 ratio, use solid colors instead of transparency)
- What happens when form validation triggers on blur vs submit? (Visual states must update immediately)
- What happens when dropdown menu items exceed viewport height? (Menu should scroll or reposition)
- What happens on mobile viewports (375px minimum width)? (All components must remain usable with responsive spacing, touch targets ≥44px)
- What happens when a loading state takes longer than 30 seconds? (Replace spinner with timeout message and manual retry button)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-UI-001**: All interactive elements MUST have visible hover states with color or background change
- **FR-UI-002**: Form inputs MUST show focus rings (blue-500 color, 2px offset) when focused via keyboard or mouse
- **FR-UI-003**: Buttons MUST have disabled states with reduced opacity (0.5) and not-allowed cursor
- **FR-UI-004**: Tables MUST have hover states on rows (gray-50 background) with smooth transition
- **FR-UI-005**: Dialogs MUST have backdrop blur (backdrop-blur-sm) and semi-transparent overlay (black/50)
- **FR-UI-006**: Dialogs MUST animate open/close with fade and scale effect completing in exactly 200ms
- **FR-UI-007**: Loading states MUST show visual feedback through spinner (for indeterminate loading with unknown duration) or pulse animation (for determinate progress with known duration); default to spinner when duration is unknown
- **FR-UI-008**: Empty states MUST include clear heading, description, and actionable call-to-action button
- **FR-UI-009**: Status badges MUST use semantic colors (green=success, red=error, blue=running, yellow=warning, gray=neutral)
- **FR-UI-010**: Error states MUST show in red banner (red-50 background, red-700 text) with dismiss option
- **FR-UI-011**: Dropdown menus MUST animate open with fade + slide effect completing in exactly 150ms
- **FR-UI-012**: Dropdown menu items MUST have hover and keyboard focus states (gray-100 background)
- **FR-UI-013**: All animations MUST respect prefers-reduced-motion media query
- **FR-UI-014**: Form inputs MUST support error state with red border and red focus ring
- **FR-UI-015**: Textareas MUST display monospace font when used for code/JSON input
- **FR-UI-016**: All transitions MUST complete in 200ms or less
- **FR-UI-017**: Focus trap MUST keep keyboard navigation within open dialogs
- **FR-UI-018**: Tables MUST have no border on last row for clean visual ending
- **FR-UI-019**: Table headers MUST be visually distinct with gray-50 background and medium font weight
- **FR-UI-020**: Clickable table rows MUST show pointer cursor on hover
- **FR-UI-021**: Loading states exceeding 30 seconds MUST replace spinner with timeout message and manual retry button
- **FR-UI-022**: Textareas MUST handle up to 10,000 characters without performance degradation (lag, scroll jank)
- **FR-UI-023**: All interactive elements MUST have touch targets ≥44px (width and height) on mobile viewports (≤768px) per WCAG 2.5.5 Level AAA
- **FR-UI-024**: When multiple components load simultaneously, show page-level spinner until all critical data arrives, then transition to content smoothly
- **FR-UI-025**: All animations MUST use only GPU-accelerated CSS properties (transform, opacity) to maintain 60fps performance; animations on layout properties (width, height, margin, padding) are prohibited
- **FR-UI-026**: All transitions MUST use ease-in-out easing curve by default; dialog open/close MUST use cubic-bezier(0.16, 1, 0.3, 1) for smooth spring effect; hover states MUST use linear easing for immediate response
- **FR-UI-027**: All animations MUST maintain ≥60fps frame rate; if frame rate drops below 60fps during testing, reduce animation complexity or disable animation for that component

### Component Enhancement Requirements

- **FR-COMP-001**: Input component MUST support base, focus, hover, disabled, and error states, and MUST support HTML input types: text, email, password, number, search, tel, url, date, time, datetime-local (all with consistent styling)
- **FR-COMP-002**: Input component MUST accept error prop to trigger error styling
- **FR-COMP-003**: Textarea component MUST inherit all Input styling patterns
- **FR-COMP-004**: Textarea component MUST have minimum height of 80px, allow vertical resize only, and support up to 10,000 characters (display character counter at 9,000 chars, show warning state at 9,500 chars, enforce hard stop at 10,000 with error message)
- **FR-COMP-005**: Dialog component MUST include backdrop, content container, header, footer, title, and description sub-components
- **FR-COMP-006**: Dialog component MUST use Radix UI primitives for accessibility and keyboard handling, and support states: open (visible with backdrop), closed (hidden), opening (fade-in animation), closing (fade-out animation)
- **FR-COMP-007**: Table component MUST include header row, body rows, and cell styling, and support states for rows: base (default), hover (gray-50 background), selected (blue-50 background), disabled (opacity 0.5)
- **FR-COMP-008**: Table component MUST support optional selected row state (blue-50 background)
- **FR-COMP-009**: Table component MUST maintain smooth scrolling (≥60fps) and hover states for up to 1,000 rows without virtualization; performance tests must validate at 100, 500, and 1,000 row thresholds
- **FR-COMP-010**: DropdownMenu component MUST use Button component for trigger, and support states: closed (hidden), open (visible with animation), opening (fade+slide in), closing (fade+slide out)
- **FR-COMP-011**: DropdownMenu component MUST support separator elements with gray-200 divider, and menu items must support states: base (default), hover (gray-100 background), focus (gray-100 background with focus ring), disabled (opacity 0.5, not-allowed cursor)
- **FR-COMP-012**: Badge component MUST be created with variants for each semantic status
- **FR-COMP-013**: Loading component MUST be created with spinner, optional text, and timeout state (30s) with retry button
- **FR-COMP-014**: ErrorBanner component MUST be created with dismiss functionality
- **FR-COMP-015**: All components MUST use cn() utility for className merging
- **FR-COMP-016**: All components MUST define TypeScript interfaces for props with explicit types for: className (string), children (ReactNode), variant enums, size enums, state booleans (disabled, error, loading), and event handlers (onClick, onChange, onSubmit)

### Styling Requirements

- **FR-STYLE-001**: All colors MUST come from Tailwind's default palette (blue, gray, red, green, yellow)
- **FR-STYLE-002**: Primary color MUST be blue-600 for buttons, blue-500 for focus rings
- **FR-STYLE-003**: Text colors MUST provide 4.5:1 contrast ratio for WCAG AA compliance
- **FR-STYLE-004**: Spacing MUST use Tailwind's scale (1, 2, 3, 4, 6, 8, 12, 16, 24)
- **FR-STYLE-005**: Border radius MUST use rounded-md (6px) for standard elements
- **FR-STYLE-006**: Shadows MUST use Tailwind's shadow utilities (sm, md, lg, xl)
- **FR-STYLE-007**: Font sizes MUST follow Tailwind's typography scale (xs, sm, base, lg, xl, 2xl)
- **FR-STYLE-008**: All utility classes MUST be applied via Tailwind (no custom CSS unless necessary)
- **FR-STYLE-009**: Tailwind CSS purge configuration MUST scan all TSX files in src/ directory to remove unused styles; production builds MUST enable minification and purge to maintain bundle size ≤350KB total (≤110KB gzipped)

### Security Requirements

- **FR-SEC-001**: All text content MUST be rendered through React JSX (automatic escaping)
- **FR-SEC-002**: Any use of `dangerouslySetInnerHTML` MUST sanitize input with DOMPurify library (version ≥3.0.0 with default safe configuration)
- **FR-SEC-003**: Form inputs MUST NOT render untrusted HTML; display as escaped text only
- **FR-SEC-004**: DOMPurify MUST be added as dependency only if innerHTML rendering is required

### Accessibility Requirements

- **FR-A11Y-001**: Input component MUST include aria-label or aria-labelledby, aria-invalid (when error=true), aria-required (when required=true), aria-describedby (linking to error message)
- **FR-A11Y-002**: Button component MUST include aria-label (when no visible text), aria-disabled (when disabled=true), aria-pressed (for toggle buttons), aria-expanded (for dropdown triggers)
- **FR-A11Y-003**: Dialog component MUST include role="dialog", aria-modal="true", aria-labelledby (linking to dialog title), aria-describedby (linking to dialog description), and focus trap implementation
- **FR-A11Y-004**: Table component MUST include role="table" on container, role="row" on rows, role="columnheader" on headers, role="cell" on cells, and aria-label on the table describing its purpose
- **FR-A11Y-005**: DropdownMenu component MUST include role="menu" on menu container, role="menuitem" on items, aria-haspopup="menu" on trigger, aria-expanded on trigger, and keyboard navigation (Arrow keys, Enter, Escape)
- **FR-A11Y-006**: Badge component MUST include aria-label describing both the status text and semantic meaning (e.g., aria-label="Status: Success" for green success badge)
- **FR-A11Y-007**: Loading component MUST include role="status", aria-live="polite", and aria-label="Loading" (or descriptive text if provided)
- **FR-A11Y-008**: ErrorBanner component MUST include role="alert", aria-live="assertive" for immediate announcement, and aria-atomic="true" for complete message announcement

### Testing Requirements

- **FR-TEST-001**: All components MUST have failing unit and accessibility tests written before implementation per Constitution Principle III (Test-First NON-NEGOTIABLE)
- **FR-TEST-002**: Security validation MUST verify React JSX escaping throughout all components and confirm DOMPurify is NOT added unless innerHTML is required

### Key Entities *(include if feature involves data)*

- **Input Component**: Text input field with states (base, focus, hover, disabled, error), supports all HTML input types
- **Textarea Component**: Multi-line text input with vertical resize, optional monospace font
- **Dialog Component**: Modal overlay with backdrop, content, header, footer, title, description
- **Table Component**: Data grid with header, body rows, cells, hover states, optional selection
- **DropdownMenu Component**: Contextual menu with trigger, items, separators, keyboard navigation
- **Badge Component**: Status indicator with semantic color variants
- **Loading Component**: Visual feedback indicator with spinner animation
- **ErrorBanner Component**: Error message display with dismiss option

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All interactive elements show visible hover states within 50ms of cursor entry
- **SC-002**: Form inputs display focus rings immediately on keyboard Tab navigation
- **SC-003**: Dialog animations complete open/close cycle in exactly 200ms
- **SC-004**: Dropdown menus animate open in exactly 150ms
- **SC-005**: Loading spinners appear within 100ms of data fetch initiation
- **SC-006**: Page bundle size remains at or below 350KB total (110KB gzipped)
- **SC-007**: Build time remains at or below 5 minutes for full frontend build
- **SC-008**: Lighthouse Accessibility score achieves 90 or higher
- **SC-009**: Color contrast ratios meet or exceed 4.5:1 for all text elements (WCAG AA)
- **SC-010**: Users can complete primary workflows (execute action, view results) without visual confusion
- **SC-011**: Zero console errors or warnings in browser DevTools during normal operation
- **SC-012**: Visual quality receives 4/5 rating in user testing (compared to enterprise tier 5/5)
- **SC-013**: Task completion success rate reaches 100% for core workflows
- **SC-014**: First Contentful Paint occurs within 1.5 seconds on standard connection
- **SC-015**: Time to Interactive occurs within 3.5 seconds on standard connection
- **SC-016**: All transitions respect prefers-reduced-motion when enabled
- **SC-017**: Keyboard navigation works for 100% of interactive elements (Tab, Enter, Escape)
- **SC-018**: Screen readers correctly announce element roles and states for all components
- **SC-019**: All interactive elements on mobile viewports (375px-768px) have touch targets ≥44px and work correctly with touch gestures (tap, swipe)
- **SC-020**: Animations maintain ≥60fps frame rate on standard devices; no janky animations on low-end devices (tested with CPU throttling 4x slowdown)

## Clarifications

### Session 2025-10-12

- Q: For form inputs displaying user-entered JSON or action parameters, how should the implementation handle potential XSS (cross-site scripting) risks? → A: React escapes by default; add explicit DOMPurify only for innerHTML use cases
- Q: When displaying action execution history in tables, what is the expected maximum number of rows that must render without performance degradation (scrolling lag, janky animations)? → A: 100-500 rows
- Q: The spec mentions both "375px" (in Assumptions) and "320px-768px" (in Edge Cases) for mobile viewport support. What is the minimum supported viewport width for the community UI? → A: 375px
- Q: When a loading state exceeds the mentioned "30 seconds" threshold (from edge cases), what should the UI display to the user? → A: Show timeout message with manual retry button
- Q: When users enter JSON or multi-line text into form inputs/textareas, what is the maximum character limit that should be supported without UX degradation (lag, scroll issues)? → A: 10,000 characters
- Q: Are the enhanced UI components being built exclusively for the action-server frontend, or should they be designed as reusable components that could be shared across other packages in the monorepo (actions, mcp, etc.)? → A: Action-server only

### Session 2025-10-12 (Critical Gaps Addressed)

- Q: What does "smooth transition" mean precisely? → A: Use ease-in-out easing curve (cubic-bezier(0.42, 0, 0.58, 1)) for standard transitions; use cubic-bezier(0.16, 1, 0.3, 1) for dialog spring effect; use linear easing for instant-response hover states
- Q: What does "clear visual separation" mean for dialog header/footer? → A: 1px border (gray-200) with 16px padding on header and footer
- Q: What does "prominent" mean when describing UI elements? → A: Higher z-index (≥10), bold font-weight (600), or larger font size (+1 scale step) than surrounding elements
- Q: What does "professional polish" mean? → A: Visual quality that achieves 4/5 user rating (defined in SC-012), with consistent spacing, smooth 60fps animations, and no visual glitches
- Q: What does "actionable call-to-action button" mean in empty states? → A: Primary Button variant (blue-600 background) with clear action text (e.g., "Create Action", "Import Data")
- Q: What does "properly aligned" mean for dropdown icons? → A: Use flexbox with items-center to vertically center icons with text; apply 8px (space-2) gap between icon and text
- Q: What is a "standard connection" for performance requirements? → A: 3G network simulation (3 Mbps download, 1.6 Mbps upload, 50ms latency) per Lighthouse default throttling

## Assumptions

- Users are accessing the community edition on modern browsers (Chrome 90+, Firefox 88+, Safari 14+)
- The existing Radix UI + Tailwind CSS architecture is maintained (no framework changes)
- The shadcn/ui copy-paste pattern continues (no npm package dependency for components)
- Visual design targets functional elegance, not marketing polish (community vs enterprise differentiation)
- Performance budgets are based on current baseline (310KB bundle, 2.5 min build)
- Accessibility targets WCAG 2.1 AA compliance (not AAA)
- Mobile viewports down to 375px width must be supported (iPhone SE 2020+ standard)
- Dark mode is deferred to future iteration (not in scope)
- No new npm dependencies allowed (use only existing Radix UI + Tailwind)
- Component enhancements follow existing file structure in `frontend/src/core/components/ui/`
- Components are scoped exclusively to action-server frontend (not designed for cross-package reuse)

## Out of Scope

- Enterprise tier components or styling (located in `frontend/src/enterprise/`)
- Dark mode implementation
- Custom illustrations or iconography
- Advanced animations beyond basic transitions
- Skeleton loading screens (simple spinners acceptable)
- Backend API changes
- New npm package dependencies
- Changes to Vite build configuration (unless required for performance)
- Internationalization (i18n)
- Right-to-left (RTL) language support
- Print stylesheets and PDF rendering optimization

## Dependencies

- Existing Radix UI primitives installation (no version changes)
- Existing Tailwind CSS configuration (tailwind.config.js)
- Vite build system with single-file plugin
- React 18.2.0 runtime
- TypeScript 5.3.3 type checking
- Existing cn() utility function in `shared/utils/cn.ts`

## Risks

- **Risk**: Increased bundle size due to additional CSS utility classes
  - **Mitigation**: Monitor build output, use PurgeCSS in production builds, validate against 350KB limit
  
- **Risk**: Performance degradation from CSS transitions on older devices
  - **Mitigation**: Use transform and opacity only (GPU-accelerated), respect prefers-reduced-motion
  
- **Risk**: Accessibility regressions if custom styling overrides Radix UI defaults
  - **Mitigation**: Test with screen readers, validate keyboard navigation, run Lighthouse audits
  
- **Risk**: Inconsistent styling across components due to manual implementation
  - **Mitigation**: Create shared Tailwind class constants, code review for consistency
  
- **Risk**: Breaking changes to components currently used in pages
  - **Mitigation**: Incremental rollout, visual regression testing, staging environment validation

## Timeline Estimate

**Phase 1 (P0 - Must Have)**: 1 week
- Input/Textarea styling
- Dialog styling  
- Table styling
- Total: ~20-24 hours development

**Phase 2 (P1 - Should Have)**: 3-5 days
- DropdownMenu styling
- Loading states component
- Error states component
- Status badges component
- Total: ~12-16 hours development

**Phase 3 (P2 - Nice to Have)**: 2-3 days
- Micro-interactions and animations
- Empty state enhancements
- Polish and refinements
- Total: ~8-12 hours development

**Testing & QA**: 2-3 days (across all phases)
- Visual regression testing
- Accessibility audits (Lighthouse, axe DevTools)
- Cross-browser testing
- Mobile viewport testing
- Performance validation

**Total Estimated Effort**: 2-3 weeks for experienced React/Tailwind developer (estimates assume familiarity with Radix UI patterns; variance ±30% based on team experience and existing component complexity)
