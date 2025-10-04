# Contract: @sema4ai/components Package API

**Package**: `@sema4ai/components`  
**Version**: 1.0.0 (replacement)  
**License**: Apache-2.0  
**Purpose**: Provide UI component library for Action Server frontend

## Module Exports

### Component Exports

```typescript
// Layout Components
export { Badge } from './Badge';
export { Box } from './Box';
export { Grid } from './Grid';
export { Scroll } from './Scroll';

// Typography
export { Header } from './Header';
export { Typography } from './Typography';

// Form Components
export { Button } from './Button';
export type { ButtonProps } from './Button';
export { Input } from './Input';
export type { InputProps } from './Input';

// Navigation
export { Link } from './Link';
export { SideNavigation } from './SideNavigation';
export { Tabs } from './Tabs';

// Overlays
export { Dialog } from './Dialog';
export { Drawer } from './Drawer';
export { Tooltip } from './Tooltip';

// Feedback
export { Progress } from './Progress';

// Data Display
export { Table } from './Table';
export type { Column, TableRowProps } from './Table';

// Code
export { Code } from './Code';
export { EditorView } from './EditorView';

// Utilities
export { componentWithRef } from './utils/componentWithRef';
export { useClipboard } from './hooks/useClipboard';
export { usePopover } from './hooks/usePopover';
export { useSystemTheme } from './hooks/useSystemTheme';
```

---

## Component Contracts

### 1. Badge

**Purpose**: Small label or status indicator

**Props**:
```typescript
interface BadgeProps {
  children: React.ReactNode;
  color?: 'primary' | 'secondary' | 'error' | 'success' | 'warning' | 'info';
  variant?: 'filled' | 'outlined';
  className?: string;
}
```

**Usage**:
```typescript
<Badge color="success">Active</Badge>
<Badge variant="outlined">Draft</Badge>
```

**Test Cases**:
- [ ] Renders children
- [ ] Accepts color prop
- [ ] Accepts variant prop
- [ ] Styled correctly

---

### 2. Box

**Purpose**: Flexible container with layout props

**Props**:
```typescript
interface BoxProps extends React.HTMLAttributes<HTMLDivElement> {
  children?: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  // Additional styled-system props as needed
}
```

**Usage**:
```typescript
<Box className="container">Content</Box>
<Box style={{ padding: '16px' }}>Content</Box>
```

**Test Cases**:
- [ ] Renders as div
- [ ] Accepts children
- [ ] Accepts className
- [ ] Accepts style
- [ ] Spreads HTML div props

---

### 3. Button

**Purpose**: Clickable button

**Props**:
```typescript
export interface ButtonProps {
  children: React.ReactNode;
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  disabled?: boolean;
  variant?: 'primary' | 'secondary' | 'text';
  size?: 'small' | 'medium' | 'large';
  type?: 'button' | 'submit' | 'reset';
  className?: string;
}
```

**Usage**:
```typescript
<Button onClick={handleClick}>Click Me</Button>
<Button variant="primary" disabled>Disabled</Button>
```

**Test Cases**:
- [ ] Renders button element
- [ ] Accepts onClick handler
- [ ] Respects disabled state
- [ ] Applies variant styles
- [ ] Supports type prop

---

### 4. Code

**Purpose**: Inline or block code display

**Props**:
```typescript
interface CodeProps {
  children: string;
  language?: string;
  className?: string;
  inline?: boolean;
}
```

**Usage**:
```typescript
<Code language="json">{jsonString}</Code>
<Code inline>const x = 5;</Code>
```

**Test Cases**:
- [ ] Renders code element
- [ ] Syntax highlighting works
- [ ] Inline variant works
- [ ] Accepts language prop

---

### 5. Column (Type)

**Purpose**: Table column definition

**Type**:
```typescript
export interface Column<T = any> {
  header: string;
  accessor: string | ((row: T) => any);
  Cell?: (props: { value: any; row: T }) => React.ReactNode;
  width?: string | number;
}
```

**Usage**:
```typescript
const columns: Column[] = [
  { header: 'Name', accessor: 'name' },
  { header: 'Status', accessor: 'status', Cell: ({ value }) => <Badge>{value}</Badge> },
];
```

**Test Cases**:
- [ ] Type is exported
- [ ] Compatible with Table component
- [ ] Supports accessor function
- [ ] Supports custom Cell renderer

---

### 6. Dialog

**Purpose**: Modal dialog overlay

**Props**:
```typescript
interface DialogProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
  maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
}
```

**Usage**:
```typescript
<Dialog
  open={isOpen}
  onClose={handleClose}
  title="Confirm Action"
  actions={<Button onClick={handleConfirm}>Confirm</Button>}
>
  Are you sure?
</Dialog>
```

**Test Cases**:
- [ ] Renders when open is true
- [ ] Does not render when open is false
- [ ] Calls onClose when backdrop clicked
- [ ] Calls onClose on ESC key
- [ ] Renders title
- [ ] Renders children
- [ ] Renders actions
- [ ] Focus trap works
- [ ] Portal rendered

---

### 7. Drawer

**Purpose**: Slide-in side panel

**Props**:
```typescript
interface DrawerProps {
  open: boolean;
  onClose: () => void;
  anchor?: 'left' | 'right' | 'top' | 'bottom';
  children: React.ReactNode;
}
```

**Usage**:
```typescript
<Drawer open={isOpen} onClose={handleClose} anchor="right">
  <SideNavigation />
</Drawer>
```

**Test Cases**:
- [ ] Renders when open
- [ ] Does not render when closed
- [ ] Calls onClose appropriately
- [ ] Slides from correct anchor
- [ ] Portal rendered

---

### 8. EditorView

**Purpose**: CodeMirror code editor

**Props**:
```typescript
interface EditorViewProps {
  value: string;
  onChange?: (value: string) => void;
  language?: string;
  readOnly?: boolean;
  className?: string;
}
```

**Usage**:
```typescript
<EditorView
  value={code}
  onChange={setCode}
  language="json"
/>
```

**Test Cases**:
- [ ] Renders CodeMirror editor
- [ ] Displays value
- [ ] Calls onChange on edits
- [ ] Respects readOnly
- [ ] Language syntax works

---

### 9. Grid

**Purpose**: CSS Grid layout container

**Props**:
```typescript
interface GridProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  columns?: number | string;
  rows?: number | string;
  gap?: number | string;
  className?: string;
}
```

**Usage**:
```typescript
<Grid columns={3} gap={16}>
  <div>Item 1</div>
  <div>Item 2</div>
  <div>Item 3</div>
</Grid>
```

**Test Cases**:
- [ ] Renders with CSS Grid
- [ ] Applies columns
- [ ] Applies gap
- [ ] Accepts children

---

### 10. Header

**Purpose**: Section header

**Props**:
```typescript
interface HeaderProps {
  children: React.ReactNode;
  level?: 1 | 2 | 3 | 4 | 5 | 6;
  className?: string;
}
```

**Usage**:
```typescript
<Header level={2}>Section Title</Header>
<Header>Default Header</Header>
```

**Test Cases**:
- [ ] Renders heading element
- [ ] Respects level prop
- [ ] Accepts children
- [ ] Styled correctly

---

### 11. Input

**Purpose**: Text input field

**Props**:
```typescript
export interface InputProps {
  value: string;
  onChange: (value: string, event: React.ChangeEvent<HTMLInputElement>) => void;
  placeholder?: string;
  disabled?: boolean;
  error?: boolean;
  helperText?: string;
  type?: string;
  className?: string;
}
```

**Usage**:
```typescript
<Input
  value={text}
  onChange={(value) => setText(value)}
  placeholder="Enter text"
  error={hasError}
  helperText="Required field"
/>
```

**Test Cases**:
- [ ] Renders input element
- [ ] Displays value
- [ ] Calls onChange with value
- [ ] Shows error state
- [ ] Shows helperText
- [ ] Respects disabled

---

### 12. Link

**Purpose**: Navigation link

**Props**:
```typescript
interface LinkProps {
  to?: string;
  href?: string;
  children: React.ReactNode;
  external?: boolean;
  className?: string;
  onClick?: () => void;
}
```

**Usage**:
```typescript
<Link to="/actions">Actions</Link>
<Link href="https://example.com" external>External</Link>
```

**Test Cases**:
- [ ] Renders anchor element
- [ ] Supports to prop (React Router)
- [ ] Supports href prop
- [ ] Opens external links in new tab
- [ ] Accepts onClick

---

### 13. Progress

**Purpose**: Progress indicator

**Props**:
```typescript
interface ProgressProps {
  value?: number; // 0-100 for determinate
  variant?: 'determinate' | 'indeterminate';
  color?: 'primary' | 'secondary';
  className?: string;
}
```

**Usage**:
```typescript
<Progress value={75} />
<Progress variant="indeterminate" />
```

**Test Cases**:
- [ ] Renders progress bar
- [ ] Shows determinate progress
- [ ] Shows indeterminate animation
- [ ] Applies color

---

### 14. Scroll

**Purpose**: Scrollable container

**Props**:
```typescript
interface ScrollProps {
  children: React.ReactNode;
  className?: string;
  maxHeight?: string | number;
}
```

**Usage**:
```typescript
<Scroll maxHeight="400px">
  <LongContent />
</Scroll>
```

**Test Cases**:
- [ ] Renders with overflow scroll
- [ ] Custom scrollbar styling
- [ ] Respects maxHeight

---

### 15. SideNavigation

**Purpose**: Sidebar navigation menu

**Props**:
```typescript
interface SideNavigationProps {
  items: Array<{
    label: string;
    icon?: React.ReactNode;
    value: string;
    href?: string;
  }>;
  activeItem?: string;
  onNavigate?: (value: string) => void;
  className?: string;
}
```

**Usage**:
```typescript
<SideNavigation
  items={navItems}
  activeItem="/actions"
  onNavigate={handleNavigate}
/>
```

**Test Cases**:
- [ ] Renders navigation items
- [ ] Highlights active item
- [ ] Calls onNavigate on click
- [ ] Renders icons

---

### 16. Table

**Purpose**: Data table

**Props**:
```typescript
interface TableProps<T = any> {
  columns: Column<T>[];
  data: T[];
  onRowClick?: (row: T) => void;
  className?: string;
}

export type TableRowProps = Record<string, any>;
```

**Usage**:
```typescript
<Table
  columns={columns}
  data={rows}
  onRowClick={handleRowClick}
/>
```

**Test Cases**:
- [ ] Renders table element
- [ ] Renders headers from columns
- [ ] Renders rows from data
- [ ] Calls onRowClick
- [ ] Custom Cell renderers work
- [ ] Accessor functions work

---

### 17. Tabs

**Purpose**: Tabbed interface

**Props**:
```typescript
interface TabsProps {
  tabs: Array<{
    label: string;
    value: string;
    content?: React.ReactNode;
  }>;
  activeTab: string;
  onChange: (value: string) => void;
  className?: string;
}
```

**Usage**:
```typescript
<Tabs
  tabs={tabList}
  activeTab={currentTab}
  onChange={setCurrentTab}
/>
```

**Test Cases**:
- [ ] Renders tab headers
- [ ] Highlights active tab
- [ ] Calls onChange on tab click
- [ ] Renders tab content if provided

---

### 18. Tooltip

**Purpose**: Hover tooltip

**Props**:
```typescript
interface TooltipProps {
  title: string;
  children: React.ReactElement;
  placement?: 'top' | 'bottom' | 'left' | 'right';
  className?: string;
}
```

**Usage**:
```typescript
<Tooltip title="Click to copy">
  <Button>Copy</Button>
</Tooltip>
```

**Test Cases**:
- [ ] Shows tooltip on hover
- [ ] Hides tooltip on mouse leave
- [ ] Respects placement
- [ ] Portal rendered
- [ ] Wraps single child

---

### 19. Typography

**Purpose**: Text component with variants

**Props**:
```typescript
interface TypographyProps {
  children: React.ReactNode;
  variant?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6' | 'body1' | 'body2' | 'caption';
  color?: string;
  align?: 'left' | 'center' | 'right';
  gutterBottom?: boolean;
  className?: string;
  component?: React.ElementType;
}
```

**Usage**:
```typescript
<Typography variant="h1">Title</Typography>
<Typography variant="body1" color="primary">Body text</Typography>
```

**Test Cases**:
- [ ] Renders with variant styles
- [ ] Accepts color
- [ ] Accepts align
- [ ] Adds bottom margin if gutterBottom
- [ ] Renders as custom component if specified

---

## Utility Contracts

### 20. componentWithRef

**Purpose**: Utility for forwarding refs

**Signature**:
```typescript
function componentWithRef<T, P>(
  component: React.ForwardRefRenderFunction<T, P>
): React.ForwardRefExoticComponent<P & React.RefAttributes<T>>;
```

**Usage**:
```typescript
const MyComponent = componentWithRef<HTMLDivElement, MyProps>((props, ref) => {
  return <div ref={ref} {...props} />;
});
```

**Test Cases**:
- [ ] Forwards refs correctly
- [ ] Preserves TypeScript types
- [ ] Works with generic types

---

### 21. useClipboard

**Purpose**: Hook for clipboard operations

**Signature**:
```typescript
interface UseClipboardReturn {
  copy: (text: string) => Promise<void>;
  copied: boolean;
  error: Error | null;
}

function useClipboard(): UseClipboardReturn;
```

**Usage**:
```typescript
const { copy, copied, error } = useClipboard();

<Button onClick={() => copy(text)}>
  {copied ? 'Copied!' : 'Copy'}
</Button>
```

**Test Cases**:
- [ ] copy function writes to clipboard
- [ ] copied state updates after copy
- [ ] error state captures failures
- [ ] copied resets after timeout

---

### 22. usePopover

**Purpose**: Hook for popover state management

**Signature**:
```typescript
interface UsePopoverReturn {
  anchorEl: HTMLElement | null;
  open: boolean;
  handleOpen: (event: React.MouseEvent<HTMLElement>) => void;
  handleClose: () => void;
}

function usePopover(): UsePopoverReturn;
```

**Usage**:
```typescript
const popover = usePopover();

<Button onClick={popover.handleOpen}>Open</Button>
<Menu
  anchorEl={popover.anchorEl}
  open={popover.open}
  onClose={popover.handleClose}
>
  ...
</Menu>
```

**Test Cases**:
- [ ] handleOpen sets anchorEl and opens
- [ ] handleClose clears anchorEl and closes
- [ ] open state tracks correctly

---

### 23. useSystemTheme

**Purpose**: Hook for system theme detection

**Signature**:
```typescript
type SystemTheme = 'light' | 'dark';

function useSystemTheme(): SystemTheme;
```

**Usage**:
```typescript
const systemTheme = useSystemTheme();

<Button onClick={() => setTheme(systemTheme)}>
  Use System Theme
</Button>
```

**Test Cases**:
- [ ] Returns 'light' or 'dark'
- [ ] Detects system preference
- [ ] Updates when system theme changes
- [ ] Works with prefers-color-scheme media query

---

## Package Metadata

**package.json Contract**:
```json
{
  "name": "@sema4ai/components",
  "version": "1.0.0",
  "license": "Apache-2.0",
  "type": "module",
  "main": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "exports": {
    ".": {
      "import": "./dist/index.js",
      "types": "./dist/index.d.ts"
    }
  },
  "files": ["dist", "LICENSE"],
  "dependencies": {
    "@codemirror/view": "^6.28.0",
    "@codemirror/language": "^6.10.0"
  },
  "peerDependencies": {
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "@sema4ai/theme": "*",
    "@emotion/react": "^11.0.0",
    "@emotion/styled": "^11.0.0"
  }
}
```

**Contract**:
- MUST declare peer dependencies on React, ReactDOM, @sema4ai/theme, Emotion
- MAY declare dependencies on CodeMirror for EditorView
- MUST provide ESM build
- MUST provide TypeScript definitions

---

## Compatibility Requirements

### With @sema4ai/theme
- Components MUST import styled from @sema4ai/theme
- Components MUST use theme tokens for styling
- Components MUST work within ThemeProvider context

### With Frontend Application
- MUST match all existing import patterns
- MUST support all props currently used (not full API)
- MUST NOT break any existing component usage
- TypeScript types MUST match actual usage

---

## Non-Functional Requirements

### Bundle Size
- Target: Within ±5% of current bundle with private packages
- Tree-shaking: Must support individual component imports
- Code splitting: Vite handles automatically

### Performance
- Component render: < 16ms (60 FPS)
- No unnecessary re-renders
- Memoization where appropriate

### Accessibility
- WCAG 2.1 Level AA compliance
- Keyboard navigation support
- Screen reader support
- Focus management (especially Dialog, Drawer, Tooltip)
- ARIA attributes where needed

---

## Breaking Changes from Private Package

**Acceptable**:
- ✅ Internal implementation details
- ✅ Unused props omitted (per clarification)
- ✅ Different component hierarchy internally

**Unacceptable**:
- ❌ Changing component names
- ❌ Changing exported types (ButtonProps, InputProps, etc.)
- ❌ Removing used props
- ❌ Changing import paths

---

## Validation Checklist

Contract compliance requires:
- [ ] All 22 components + 4 utilities implemented
- [ ] All exports match contract
- [ ] Props match actual frontend usage
- [ ] TypeScript types exported
- [ ] Components use @sema4ai/theme
- [ ] Accessibility standards met
- [ ] Bundle size within tolerance
- [ ] Tree-shaking works
- [ ] No breaking changes to frontend

**Contract Status**: ✅ Ready for implementation
