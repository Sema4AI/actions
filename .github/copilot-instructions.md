# actions Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-12-11

## Active Technologies
- Node.js (LTS 20.x) / TypeScript 5.3.3 for frontend; Python 3.11.x for build automation + Vite 6.1.0, React 18.2.0, design system packages to be vendored (002-build-packaging-bug)
- Node.js 20.x LTS / TypeScript 5.3.3 (frontend), Python 3.11.x (backend/build automation) + Vite 6.1.0, React 18.2.0, Radix UI + Tailwind CSS (community), @sema4ai/* design system (enterprise), invoke (build tasks), PyInstaller (backend packaging) (003-open-core-build)
- File-based (vendored packages in `action_server/frontend/vendored/`, build artifacts) (003-open-core-build)
- TypeScript 5.3.3, React 18.2.0 + Vite 6.1.0 (build), Radix UI 1.0.x (headless components), Tailwind CSS 3.4.1 (styling), class-variance-authority 0.7.0 (variants), clsx 2.1.0 + tailwind-merge 2.2.0 (className utility), React Router DOM 6.21.3 (navigation), TanStack Query 5.28.0 (data fetching) (004-community-ui-enhancement)
- N/A (frontend only, no persistence layer) (004-community-ui-enhancement)

## UI Components

### Available Components (action_server/frontend/src/core/components/ui/)

#### Form Components
- **Input** - Text input with error states, focus rings, and hover states
  - States: base, hover, focus, disabled, error
  - Supports all HTML input types: text, email, password, number, search, tel, url, date, time, datetime-local
  - Required props: none (forwards all standard input props)
  - Optional props: `error?: boolean` (triggers red border and focus ring)
  - Accessibility: aria-invalid, aria-required, aria-describedby

- **Textarea** - Multi-line text input with vertical resize
  - Inherits all Input styling patterns
  - Min height: 80px, vertical resize only
  - Monospace font when `spellCheck={false}` (for code/JSON)
  - Character limit: 10,000 characters (warning at 9,500)
  - Accessibility: same as Input component

#### Dialog Components
- **Dialog** - Modal dialogs with Radix UI primitives
  - Sub-components: DialogTrigger, DialogPortal, DialogOverlay, DialogContent, DialogHeader, DialogFooter, DialogTitle, DialogDescription, DialogClose
  - Animations: fade-in + zoom-in on open (200ms), fade-out + zoom-out on close
  - Backdrop: semi-transparent (black/50) with blur effect (backdrop-blur-sm)
  - Focus trap: Tab key cycles within dialog only, Escape closes
  - Accessibility: role="dialog", aria-modal="true", aria-labelledby, aria-describedby

#### Data Display Components
- **Table** - Data tables with hover states and semantic HTML
  - Sub-components: Table, TableHeader, TableBody, TableRow, TableHead, TableCell, TableEmptyState
  - Row states: base, hover (gray-50), selected (blue-50), disabled
  - Header styling: gray-50 background, medium font-weight
  - Performance: smooth scrolling up to 1,000 rows without virtualization
  - Accessibility: role="table", role="row", role="columnheader", role="cell", aria-label on table

- **Badge** - Status indicators with semantic colors
  - Variants: success (green), error (red), warning (yellow), info (blue), neutral (gray)
  - Default: neutral
  - Accessibility: aria-label describing status and semantic meaning

#### Interaction Components
- **DropdownMenu** - Context menus with Radix UI
  - Sub-components: DropdownMenu (Root), DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator
  - Animations: fade + slide-down on open (150ms)
  - Item states: base, hover (gray-100), focus, disabled
  - Destructive variant: red-600 text with red-50 hover
  - Keyboard: Arrow keys, Enter, Escape
  - Accessibility: role="menu", role="menuitem", aria-haspopup, aria-expanded

#### Feedback Components
- **Loading** - Spinner with timeout state
  - Spinner animation: rotating border (animate-spin)
  - Optional text prop for custom loading message
  - Timeout: 30s (shows retry button after timeout)
  - Motion-reduce support: disables animation
  - Accessibility: role="status", aria-live="polite", aria-label="Loading"

- **ErrorBanner** - Dismissible error messages
  - Red banner: bg-red-50, border-red-200, text-red-700
  - Required prop: `message: string`
  - Optional prop: `onDismiss?: () => void`
  - Includes error icon
  - Accessibility: role="alert", aria-live="assertive", aria-atomic="true"

### Component Usage Patterns

```typescript
// Import components
import { Input } from '@/core/components/ui/Input';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/core/components/ui/Dialog';
import { Badge } from '@/core/components/ui/Badge';

// Input with error state
<Input
  type="email"
  placeholder="Enter email"
  error={hasError}
  aria-invalid={hasError}
  aria-describedby="error-message"
/>

// Dialog with sub-components
<Dialog open={isOpen} onOpenChange={setIsOpen}>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Confirm Delete</DialogTitle>
    </DialogHeader>
    <p>Are you sure?</p>
  </DialogContent>
</Dialog>

// Badge for status display
<Badge variant="success" aria-label="Status: Success">
  Completed
</Badge>
```

## Styling Guidelines

### Tailwind CSS Best Practices
- **Always use Tailwind utility classes** - No custom CSS unless absolutely necessary
- **Use cn() utility for className merging** - Import from `@/shared/utils/cn.ts`
- **Follow Tailwind's spacing scale** - Use values: 1, 2, 3, 4, 6, 8, 12, 16, 24
- **Use semantic colors from Tailwind palette** - blue, gray, red, green, yellow
- **Border radius** - Use `rounded-md` (6px) for standard elements
- **Shadows** - Use Tailwind's shadow utilities: sm, md, lg, xl

### Color Contrast Requirements (WCAG AA)
All text must meet 4.5:1 contrast ratio:
- **Primary blue**: blue-600 (buttons), blue-500 (focus rings)
- **Success**: green-600 text on white, green-50 background with green-700 text
- **Error**: red-600 text on white, red-50 background with red-700 text
- **Warning**: yellow-600 text on white, yellow-50 background with yellow-800 text
- **Info**: blue-600 text on white, blue-50 background with blue-700 text
- **Neutral**: gray-600 text on white, gray-50 background with gray-700 text

### Animation Guidelines
- **Always add motion-reduce support** - Use `motion-reduce:animate-none` and `motion-reduce:transition-none`
- **Keep animations short** - Max 200ms for dialogs, 150ms for dropdowns
- **Use GPU-accelerated properties only** - `transform` and `opacity` (never animate width, height, margin, padding)
- **Maintain 60fps** - Test with Chrome DevTools Performance panel
- **Easing curves**:
  - Standard transitions: `ease-in-out` (default)
  - Dialog open/close: `cubic-bezier(0.16, 1, 0.3, 1)` (spring effect)
  - Hover states: `linear` (immediate response)

### Example: Proper Animation Implementation
```typescript
// Dialog content with motion-reduce support
<div className={cn(
  "animate-in fade-in-0 zoom-in-95 duration-200",
  "motion-reduce:animate-none motion-reduce:transition-none",
  "data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95"
)}>
  {children}
</div>
```

## Testing Requirements

### Test-First Development (NON-NEGOTIABLE)
Per Constitution Principle III:
1. **Write tests FIRST** - Tests must fail before implementation
2. **Verify tests fail** - Run tests to confirm they fail as expected
3. **Implement feature** - Write code to make tests pass
4. **Verify tests pass** - Run tests again to confirm success

### Test Structure
- **Unit tests**: `action_server/frontend/__tests__/components/ui/ComponentName.test.tsx`
- **Accessibility tests**: `action_server/frontend/__tests__/a11y/ComponentName.a11y.test.tsx`
- **Visual regression tests**: `action_server/frontend/__tests__/visual/component-name.spec.ts`
- **Performance tests**: `action_server/frontend/__tests__/performance/ComponentName.perf.test.tsx`

### Required Tests for Each Component

#### Unit Tests
```typescript
import { render, screen } from '@testing-library/react';
import { ComponentName } from '@/core/components/ui/ComponentName';

describe('ComponentName', () => {
  it('renders base state with correct classes', () => {
    render(<ComponentName>Content</ComponentName>);
    expect(screen.getByText('Content')).toHaveClass('expected-class');
  });

  it('renders hover state', () => {
    // Test hover classes are present
  });

  it('renders disabled state', () => {
    render(<ComponentName disabled>Content</ComponentName>);
    expect(screen.getByRole('button')).toBeDisabled();
  });
});
```

#### Accessibility Tests (using jest-axe)
```typescript
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { ComponentName } from '@/core/components/ui/ComponentName';

expect.extend(toHaveNoViolations);

describe('ComponentName Accessibility', () => {
  it('should not have accessibility violations', async () => {
    const { container } = render(<ComponentName>Content</ComponentName>);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('has correct ARIA attributes', () => {
    render(<ComponentName aria-label="Test">Content</ComponentName>);
    expect(screen.getByRole('button')).toHaveAttribute('aria-label', 'Test');
  });

  it('supports keyboard navigation', () => {
    // Test Tab, Enter, Escape key handling
  });
});
```

#### Visual Regression Tests (using Playwright)
```typescript
import { test, expect } from '@playwright/test';

test.describe('ComponentName Visual Tests', () => {
  test('renders all states correctly', async ({ page }) => {
    await page.goto('/component-test-page');

    // Base state
    await expect(page.locator('.component')).toHaveScreenshot('base-state.png');

    // Hover state
    await page.hover('.component');
    await expect(page.locator('.component')).toHaveScreenshot('hover-state.png');

    // Focus state
    await page.focus('.component');
    await expect(page.locator('.component')).toHaveScreenshot('focus-state.png');
  });
});
```

### Test Coverage Requirements
- **Unit tests**: All component states (base, hover, focus, disabled, error)
- **Accessibility tests**: ARIA attributes, keyboard navigation, screen reader announcements, contrast ratios
- **Visual regression tests**: Screenshots of all visual states
- **Performance tests**: Render time, scroll performance (for tables), animation frame rate

## Accessibility Requirements

### WCAG 2.1 AA Compliance (Mandatory)
All components MUST meet WCAG 2.1 Level AA standards:

#### Color Contrast
- **Text contrast**: 4.5:1 minimum for normal text
- **Large text contrast**: 3:1 minimum (18pt+ or 14pt+ bold)
- **UI component contrast**: 3:1 minimum for interactive elements
- Test with: Chrome DevTools Lighthouse, axe DevTools browser extension

#### Keyboard Navigation
- **Tab navigation**: All interactive elements must be reachable via Tab key
- **Focus indicators**: Visible focus ring on all focusable elements (blue-500, 2px offset)
- **Keyboard shortcuts**:
  - Enter/Space: Activate buttons, open dialogs
  - Escape: Close dialogs and dropdowns
  - Arrow keys: Navigate dropdown menu items
  - Tab: Cycle through form inputs (trapped within dialogs)

#### Screen Reader Support
Required ARIA attributes by component type:

**Input/Textarea**:
- `aria-label` or `aria-labelledby` (labels the input)
- `aria-invalid="true"` (when error state)
- `aria-required="true"` (for required fields)
- `aria-describedby` (links to error message)

**Button**:
- `aria-label` (when no visible text)
- `aria-disabled="true"` (when disabled)
- `aria-pressed` (for toggle buttons)
- `aria-expanded` (for dropdown triggers)

**Dialog**:
- `role="dialog"`
- `aria-modal="true"`
- `aria-labelledby` (links to DialogTitle)
- `aria-describedby` (links to DialogDescription)

**Table**:
- `role="table"` (on container)
- `role="row"` (on TableRow)
- `role="columnheader"` (on TableHead)
- `role="cell"` (on TableCell)
- `aria-label` (describes table purpose)

**DropdownMenu**:
- `role="menu"` (on menu container)
- `role="menuitem"` (on items)
- `aria-haspopup="menu"` (on trigger)
- `aria-expanded` (on trigger)

**Badge**:
- `aria-label` (describes status and meaning, e.g., "Status: Success")

**Loading**:
- `role="status"`
- `aria-live="polite"`
- `aria-label="Loading"` (or custom text)

**ErrorBanner**:
- `role="alert"`
- `aria-live="assertive"` (immediate announcement)
- `aria-atomic="true"` (reads complete message)

#### Touch Target Sizes (Mobile)
- **Minimum size**: 44x44px for all interactive elements on mobile viewports (≤768px)
- Test at: 375px viewport width (iPhone SE standard)
- Use Chrome DevTools device emulation for testing

### Testing Accessibility

```bash
# Run accessibility test suite
cd action_server/frontend
npm run test:a11y

# Run Lighthouse audit (requires running dev server)
npm run dev
# In another terminal:
npx lighthouse http://localhost:5173 --only-categories=accessibility

# Manual testing checklist:
# 1. Navigate entire app using only keyboard (no mouse)
# 2. Test with screen reader (NVDA on Windows, VoiceOver on Mac)
# 3. Enable "prefers-reduced-motion" in OS and verify animations disable
# 4. Test at 375px viewport width (mobile)
# 5. Run axe DevTools browser extension on all pages
```

## Project Structure
```
action_server/frontend/
├── src/
│   ├── core/
│   │   ├── components/
│   │   │   └── ui/           # UI components (Input, Dialog, Table, etc.)
│   │   └── pages/            # Page components (Actions, RunHistory, etc.)
│   └── shared/
│       └── utils/
│           └── cn.ts         # className utility (clsx + tailwind-merge)
├── __tests__/
│   ├── components/ui/        # Unit tests
│   ├── a11y/                 # Accessibility tests
│   ├── visual/               # Visual regression tests (Playwright)
│   ├── performance/          # Performance tests
│   └── utils/                # Test utilities and helpers
└── package.json
```

## Commands

### Python (Backend)
```bash
# Run tests
cd action_server && pytest
cd actions && pytest
cd common && pytest

# Lint code
ruff check .

# Build tasks (invoke)
inv --list  # Show all available tasks
```

### Frontend Build (Node.js + TypeScript)
```bash
# Community tier (open-source, no credentials required)
cd action_server && inv build-frontend --tier=community
# OR use alias
cd action_server && inv build-frontend-community

# Enterprise tier (requires NPM_TOKEN for private registry)
cd action_server && inv build-frontend --tier=enterprise
# OR use alias
cd action_server && inv build-frontend-enterprise

# Build options
inv build-frontend --tier=community --json  # JSON output for CI
inv build-frontend --tier=community --debug  # Debug build (no minification)
inv build-frontend --tier=community --source=vendored  # Use vendored packages
```

### Artifact Validation
```bash
# Validate built artifacts
cd action_server
python build-binary/artifact_validator.py \
  --artifact=frontend/dist \
  --tier=community \
  --checks=all \
  --json
```

## Code Style
Node.js (LTS 20.x) / TypeScript 5.3.3 for frontend; Python 3.11.x for build automation: Follow standard conventions

## Recent Changes
- 2025-12-11: Added comprehensive UI component documentation from 004-community-ui-enhancement feature (Input, Textarea, Dialog, Table, DropdownMenu, Badge, Loading, ErrorBanner with shadcn/ui patterns, Test-First requirements, WCAG 2.1 AA accessibility standards, motion-reduce support, and Tailwind CSS guidelines)
- 004-community-ui-enhancement: Added TypeScript 5.3.3, React 18.2.0 + Vite 6.1.0 (build), Radix UI 1.0.x (headless components), Tailwind CSS 3.4.1 (styling), class-variance-authority 0.7.0 (variants), clsx 2.1.0 + tailwind-merge 2.2.0 (className utility), React Router DOM 6.21.3 (navigation), TanStack Query 5.28.0 (data fetching)
- 003-open-core-build: Added Node.js 20.x LTS / TypeScript 5.3.3 (frontend), Python 3.11.x (backend/build automation) + Vite 6.1.0, React 18.2.0, Radix UI + Tailwind CSS (community), @sema4ai/* design system (enterprise), invoke (build tasks), PyInstaller (backend packaging)
- 002-build-packaging-bug: Added Node.js (LTS 20.x) / TypeScript 5.3.3 for frontend; Python 3.11.x for build automation + Vite 6.1.0, React 18.2.0, design system packages to be vendored

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
## Vendored Builds
When present, vendored build artifacts and their manifests will be listed here with the producing CI run link and
short justification. Manual additions about vendored artifacts should be kept between the MANUAL ADDITIONS markers.
