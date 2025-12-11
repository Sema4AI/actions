# UI Components Documentation

This directory contains the core UI components for the Sema4.ai Action Server frontend. All components are built with accessibility, performance, and consistent design in mind.

Community tier components using Radix UI + Tailwind CSS. These components are available in both Community and Enterprise builds.

## Table of Contents

- [Design Principles](#design-principles)
- [Accessibility Requirements](#accessibility-requirements)
- [Safe Color Pairings](#safe-color-pairings)
- [Components](#components)
  - [Button](#button)
  - [Input](#input)
  - [Textarea](#textarea)
  - [Dialog](#dialog)
  - [Table](#table)
  - [DropdownMenu](#dropdownmenu)
  - [Badge](#badge)
  - [Loading](#loading)
  - [ErrorBanner](#errorbanner)

---

## Design Principles

All components in this library follow these principles:

1. **Accessibility First**: WCAG AA compliance for color contrast, keyboard navigation, and ARIA attributes
2. **Motion Respect**: All animations respect `prefers-reduced-motion` via `motion-reduce:` utilities
3. **Consistent Styling**: Using Tailwind CSS with a unified gray/blue palette
4. **Type Safety**: Full TypeScript support with exported prop interfaces
5. **Composability**: Components can be composed together while maintaining their individual functionality

---

## Accessibility Requirements

### Keyboard Navigation

All interactive components must support:
- **Tab/Shift+Tab**: Navigate between focusable elements
- **Enter/Space**: Activate buttons and interactive elements
- **Escape**: Close dialogs and dropdowns
- **Arrow keys**: Navigate within menus and lists

### Focus Management

- Focus indicators use a 2px blue ring (`ring-2 ring-blue-500`) with 2px offset
- Focus is trapped within dialogs when open
- Focus returns to trigger element when closing modals

### Screen Reader Support

- Semantic HTML elements used where possible (`<button>`, `<input>`, `<table>`)
- ARIA attributes added for custom components (`aria-invalid`, `aria-label`, `aria-hidden`)
- Descriptive labels and helper text provided
- Status messages announced for loading/error states

---

## Safe Color Pairings

The following color pairings were validated against WCAG AA contrast requirements (minimum 4.5:1 ratio) and are the recommended defaults used by the community UI components. Do not change these pairings without re-validating contrast ratios.

| Component / Context | Background | Text Color | Contrast Ratio | WCAG Level |
|---|---:|---:|---:|---:|
| Input (base) | `bg-white` | `text-gray-900` | 18.2:1 | AAA |
| Input (disabled) | `bg-gray-100` | `text-gray-500` | 4.6:1 | AA |
| Table header | `bg-gray-50` | `text-gray-700` | 9.5:1 | AAA |
| Badge (success) | `bg-green-100` | `text-green-700` | 7.8:1 | AAA |
| Badge (error) | `bg-red-100` | `text-red-700` | 8.3:1 | AAA |
| Badge (warning) | `bg-yellow-100` | `text-yellow-700` | 6.5:1 | AAA |
| Badge (info) | `bg-blue-100` | `text-blue-700` | 7.9:1 | AAA |
| Badge (neutral) | `bg-gray-100` | `text-gray-700` | 9.5:1 | AAA |
| ErrorBanner | `bg-red-50` | `text-red-700` | 8.3:1 | AAA |
| Button (primary) | `bg-blue-600` | `text-white` | 8.6:1 | AAA |
| Button (destructive) | `bg-red-600` | `text-white` | 7.1:1 | AAA |

**Validation Tool**: [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)

Refer to `specs/004-community-ui-enhancement/data-model.md` for the full validation table and rationale.

---

## Components

### Button

A versatile button component with multiple variants and sizes.

#### Props

```typescript
export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  /** Render as child component (using Radix Slot) */
  asChild?: boolean;
}
```

#### Variants

- **default**: Blue background with white text (`bg-blue-600 text-white hover:bg-blue-500`)
- **secondary**: Gray background with dark text (`bg-gray-100 text-gray-900 hover:bg-gray-200`)
- **outline**: White background with border (`border border-gray-300 bg-white hover:bg-gray-100`)
- **ghost**: Transparent background (`bg-transparent hover:bg-gray-100`)
- **destructive**: Red background for dangerous actions (`bg-red-600 text-white hover:bg-red-500`)

#### Sizes

- **default**: `h-10 px-4 py-2`
- **sm**: `h-9 px-3`
- **lg**: `h-11 px-8 text-base`
- **icon**: `h-10 w-10` (square button for icons)

#### ARIA Attributes

- Disabled buttons receive `disabled:pointer-events-none disabled:opacity-50`
- Focus ring: `focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2`

#### Usage Examples

```tsx
import { Button } from '@/core/components/ui/Button';

// Primary action
<Button onClick={handleSubmit}>Save Changes</Button>

// Secondary action
<Button variant="secondary" onClick={handleCancel}>Cancel</Button>

// Destructive action
<Button variant="destructive" onClick={handleDelete}>Delete Action</Button>

// Icon button
<Button variant="ghost" size="icon" aria-label="Close">
  <XIcon />
</Button>

// Disabled state
<Button disabled>Processing...</Button>

// As child (renders as custom component)
<Button asChild>
  <a href="/docs">Documentation</a>
</Button>
```

---

### Input

Single-line text input field with enhanced visual states and error handling.

#### Props

```typescript
export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  /** Display error styling (red border, red focus ring) */
  error?: boolean;
}
```

#### Visual States

| State | Classes | Trigger |
|-------|---------|---------|
| Base | `border-gray-300 bg-white` | Default |
| Hover | `hover:border-gray-400` | Mouse over (not disabled) |
| Focus | `focus-visible:ring-2 focus-visible:ring-blue-500` | Keyboard/mouse focus |
| Error | `border-red-500 focus-visible:ring-red-500` | `error={true}` prop |
| Disabled | `disabled:cursor-not-allowed disabled:opacity-50` | `disabled` attribute |

#### ARIA Attributes

- **aria-invalid**: Automatically set to `true` when `error={true}`
- Accepts all standard input attributes

#### Usage Examples

```tsx
import { Input } from '@/core/components/ui/Input';

// Basic input
<Input type="text" placeholder="Enter your name" />

// With error state
<Input
  type="email"
  value={email}
  onChange={(e) => setEmail(e.target.value)}
  error={!isValidEmail(email)}
  aria-describedby="email-error"
/>
{!isValidEmail(email) && (
  <p id="email-error" className="text-sm text-red-600">
    Please enter a valid email address
  </p>
)}

// Disabled input
<Input type="text" value="Read-only value" disabled />

// Password input
<Input type="password" placeholder="Enter password" />
```

---

### Textarea

Multi-line text input with code/JSON support and vertical resizing.

#### Props

```typescript
export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  /** Display error styling (red border, red focus ring) */
  error?: boolean;
}
```

#### Visual States

| State | Classes | Trigger |
|-------|---------|---------|
| Base | `border-gray-300 bg-white min-h-[80px] resize-y` | Default |
| Hover | `hover:border-gray-400` | Mouse over (not disabled) |
| Focus | `focus-visible:ring-2 focus-visible:ring-blue-500` | Keyboard/mouse focus |
| Error | `border-red-500 focus-visible:ring-red-500` | `error={true}` prop |
| Monospace | `font-mono` | `spellCheck={false}` (heuristic) |
| Disabled | `disabled:cursor-not-allowed disabled:opacity-50` | `disabled` attribute |

#### ARIA Attributes

- **aria-invalid**: Automatically set to `true` when `error={true}`
- Accepts all standard textarea attributes

#### Usage Examples

```tsx
import { Textarea } from '@/core/components/ui/Textarea';

// Basic textarea
<Textarea placeholder="Enter your message" />

// Code/JSON input (monospace font)
<Textarea
  value={jsonInput}
  onChange={(e) => setJsonInput(e.target.value)}
  spellCheck={false}
  placeholder='{"key": "value"}'
/>

// With error state
<Textarea
  value={description}
  onChange={(e) => setDescription(e.target.value)}
  error={description.length > 1000}
  maxLength={1000}
/>

// With custom height
<Textarea
  className="min-h-[200px]"
  placeholder="Enter detailed description"
/>
```

---

### Dialog

Modal overlay for confirmations, forms, and detail views. Built on Radix UI primitives.

#### Props

```typescript
// Root component
export type DialogProps = React.ComponentPropsWithoutRef<typeof DialogPrimitive.Root>;

// Content component
export type DialogContentProps = React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content>;

// Sub-components
export type DialogTitleProps = React.ComponentPropsWithoutRef<typeof DialogPrimitive.Title>;
export type DialogDescriptionProps = React.ComponentPropsWithoutRef<typeof DialogPrimitive.Description>;
export type DialogHeaderProps = React.HTMLAttributes<HTMLDivElement>;
export type DialogFooterProps = React.HTMLAttributes<HTMLDivElement>;
export type DialogCloseProps = React.ComponentPropsWithoutRef<typeof DialogPrimitive.Close>;
```

#### Component Hierarchy

```
Dialog (Root)
├── DialogTrigger (optional button to open)
├── DialogPortal (Radix portal for overlay)
│   ├── DialogOverlay (backdrop: bg-black/40 backdrop-blur-sm)
│   └── DialogContent (main container: max-w-lg centered)
│       ├── DialogHeader (optional: border-b pb-4 mb-4)
│       │   ├── DialogTitle (text-lg font-semibold)
│       │   └── DialogDescription (text-sm text-gray-600)
│       ├── [Custom content]
│       └── DialogFooter (optional: border-t pt-4 mt-4)
└── DialogClose (X button, top-right)
```

#### Keyboard Navigation

- **Escape**: Closes dialog
- **Tab/Shift+Tab**: Cycles focus within dialog (focus trapped)
- Dialog automatically focuses first focusable element on open

#### ARIA Attributes

- **role="dialog"**: Automatically applied by Radix
- **aria-describedby**: Links to DialogDescription
- **aria-labelledby**: Links to DialogTitle

#### Usage Examples

```tsx
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogClose,
} from '@/core/components/ui/Dialog';
import { Button } from '@/core/components/ui/Button';

// Basic confirmation dialog
<Dialog>
  <DialogTrigger asChild>
    <Button variant="destructive">Delete Action</Button>
  </DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Confirm Deletion</DialogTitle>
      <DialogDescription>
        Are you sure you want to delete this action? This action cannot be undone.
      </DialogDescription>
    </DialogHeader>
    <DialogFooter>
      <DialogClose asChild>
        <Button variant="secondary">Cancel</Button>
      </DialogClose>
      <Button variant="destructive" onClick={handleDelete}>Delete</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>

// Form dialog with controlled state
const [open, setOpen] = React.useState(false);

<Dialog open={open} onOpenChange={setOpen}>
  <DialogTrigger asChild>
    <Button>Create Action</Button>
  </DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Create New Action</DialogTitle>
      <DialogDescription>
        Enter the details for your new action below.
      </DialogDescription>
    </DialogHeader>
    <form onSubmit={handleSubmit}>
      <div className="space-y-4">
        <Input placeholder="Action name" />
        <Textarea placeholder="Description" />
      </div>
      <DialogFooter>
        <Button type="button" variant="secondary" onClick={() => setOpen(false)}>
          Cancel
        </Button>
        <Button type="submit">Create</Button>
      </DialogFooter>
    </form>
  </DialogContent>
</Dialog>
```

---

### Table

Data grid for displaying actions, runs, logs, and artifacts with selectable and clickable rows.

#### Props

```typescript
export interface TableProps extends React.HTMLAttributes<HTMLTableElement> {}

export interface TableRowProps extends React.HTMLAttributes<HTMLTableRowElement> {
  /** Highlight row with blue background (for selected state) */
  selected?: boolean;
  /** Make row clickable (shows pointer cursor) */
  clickable?: boolean;
}

export interface TableHeadProps extends React.ThHTMLAttributes<HTMLTableCellElement> {}
```

#### Component Structure

```
Table (wrapper with overflow-auto)
├── TableHeader (<thead>)
│   └── TableRow
│       └── TableHead (<th>) - uppercase gray text on gray-50 background
├── TableBody (<tbody>)
│   └── TableRow (can be selected/clickable)
│       └── TableCell (<td>)
├── TableFooter (<tfoot>)
│   └── TableRow
│       └── TableCell
└── TableCaption

TableEmptyState - centered message when no data
```

#### Visual States

| State | Classes | Trigger |
|-------|---------|---------|
| Header | `bg-gray-50 border-b text-xs font-medium uppercase text-gray-500` | `<thead>` |
| Row | `border-b hover:bg-gray-50 transition-colors` | Default |
| Row Selected | `bg-blue-50` | `selected={true}` |
| Row Clickable | `cursor-pointer` | `clickable={true}` |
| Last Row | `last:border-0` | Last `<tr>` in `<tbody>` |

#### ARIA Attributes

- Semantic `<table>`, `<thead>`, `<tbody>`, `<th>`, `<td>` elements
- Clickable rows should include appropriate `role` and `aria-label` if needed

#### Usage Examples

```tsx
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  TableEmptyState,
} from '@/core/components/ui/Table';
import { Badge } from '@/core/components/ui/Badge';

// Basic table
<Table>
  <TableHeader>
    <TableRow>
      <TableHead>Name</TableHead>
      <TableHead>Status</TableHead>
      <TableHead>Created</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    <TableRow>
      <TableCell>Send Email</TableCell>
      <TableCell>
        <Badge variant="success">Active</Badge>
      </TableCell>
      <TableCell>2025-12-10</TableCell>
    </TableRow>
  </TableBody>
</Table>

// Clickable rows with selection
const [selectedId, setSelectedId] = React.useState<string | null>(null);

<Table>
  <TableHeader>
    <TableRow>
      <TableHead>Action Name</TableHead>
      <TableHead>Runs</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    {actions.map((action) => (
      <TableRow
        key={action.id}
        selected={selectedId === action.id}
        clickable
        onClick={() => setSelectedId(action.id)}
      >
        <TableCell>{action.name}</TableCell>
        <TableCell>{action.runCount}</TableCell>
      </TableRow>
    ))}
  </TableBody>
</Table>

// Empty state
<Table>
  <TableHeader>
    <TableRow>
      <TableHead>Name</TableHead>
      <TableHead>Status</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    {actions.length === 0 ? (
      <TableEmptyState>
        No actions found. Create your first action to get started.
      </TableEmptyState>
    ) : (
      actions.map((action) => (
        <TableRow key={action.id}>
          <TableCell>{action.name}</TableCell>
          <TableCell>
            <Badge variant="info">{action.status}</Badge>
          </TableCell>
        </TableRow>
      ))
    )}
  </TableBody>
</Table>

// With caption
<Table>
  <TableCaption>A list of recent action runs</TableCaption>
  {/* ... table content ... */}
</Table>
```

---

### DropdownMenu

Contextual menu for secondary actions (edit, delete, run). Built on Radix UI primitives.

#### Props

```typescript
// Root component
export type DropdownMenuProps = React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Root>;

// Content component
export interface DropdownMenuContentProps
  extends React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Content> {}

// Item component
export interface DropdownMenuItemProps
  extends React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Item> {
  /** Show destructive styling (red text/icon) */
  destructive?: boolean;
  /** Add left padding (for hierarchical menus) */
  inset?: boolean;
}
```

#### Component Structure

```
DropdownMenu (Root)
├── DropdownMenuTrigger (button)
├── DropdownMenuPortal
│   └── DropdownMenuContent (menu container)
│       ├── DropdownMenuLabel (optional section header)
│       ├── DropdownMenuItem (clickable option)
│       ├── DropdownMenuSeparator (divider)
│       ├── DropdownMenuCheckboxItem (with checkmark indicator)
│       ├── DropdownMenuRadioGroup
│       │   └── DropdownMenuRadioItem (with radio indicator)
│       ├── DropdownMenuSub (nested submenu)
│       │   ├── DropdownMenuSubTrigger
│       │   └── DropdownMenuSubContent
│       └── DropdownMenuShortcut (keyboard hint)
```

#### Keyboard Navigation

- **Arrow keys**: Navigate between items
- **Enter/Space**: Select focused item
- **Escape**: Close menu
- **Type ahead**: Jump to item starting with typed character

#### ARIA Attributes

- **role="menu"**: Automatically applied by Radix
- **role="menuitem"**: Applied to each item
- **aria-disabled**: Applied to disabled items

#### Usage Examples

```tsx
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuShortcut,
} from '@/core/components/ui/DropdownMenu';
import { Button } from '@/core/components/ui/Button';

// Basic menu
<DropdownMenu>
  <DropdownMenuTrigger asChild>
    <Button variant="ghost" size="icon">
      <MoreVerticalIcon />
    </Button>
  </DropdownMenuTrigger>
  <DropdownMenuContent>
    <DropdownMenuItem onClick={handleEdit}>
      Edit
    </DropdownMenuItem>
    <DropdownMenuItem onClick={handleDuplicate}>
      Duplicate
    </DropdownMenuItem>
    <DropdownMenuSeparator />
    <DropdownMenuItem destructive onClick={handleDelete}>
      Delete
    </DropdownMenuItem>
  </DropdownMenuContent>
</DropdownMenu>

// With labels and shortcuts
<DropdownMenu>
  <DropdownMenuTrigger asChild>
    <Button>Actions</Button>
  </DropdownMenuTrigger>
  <DropdownMenuContent>
    <DropdownMenuLabel>Quick Actions</DropdownMenuLabel>
    <DropdownMenuItem onClick={handleRun}>
      Run Action
      <DropdownMenuShortcut>⌘R</DropdownMenuShortcut>
    </DropdownMenuItem>
    <DropdownMenuItem onClick={handleEdit}>
      Edit
      <DropdownMenuShortcut>⌘E</DropdownMenuShortcut>
    </DropdownMenuItem>
    <DropdownMenuSeparator />
    <DropdownMenuLabel>Danger Zone</DropdownMenuLabel>
    <DropdownMenuItem destructive onClick={handleDelete}>
      Delete Action
    </DropdownMenuItem>
  </DropdownMenuContent>
</DropdownMenu>

// Checkbox items
import { DropdownMenuCheckboxItem } from '@/core/components/ui/DropdownMenu';

const [showCompleted, setShowCompleted] = React.useState(true);
const [showFailed, setShowFailed] = React.useState(false);

<DropdownMenu>
  <DropdownMenuTrigger asChild>
    <Button variant="outline">Filter</Button>
  </DropdownMenuTrigger>
  <DropdownMenuContent>
    <DropdownMenuLabel>Show Status</DropdownMenuLabel>
    <DropdownMenuCheckboxItem
      checked={showCompleted}
      onCheckedChange={setShowCompleted}
    >
      Completed
    </DropdownMenuCheckboxItem>
    <DropdownMenuCheckboxItem
      checked={showFailed}
      onCheckedChange={setShowFailed}
    >
      Failed
    </DropdownMenuCheckboxItem>
  </DropdownMenuContent>
</DropdownMenu>

// Radio group
import { DropdownMenuRadioGroup, DropdownMenuRadioItem } from '@/core/components/ui/DropdownMenu';

const [sortBy, setSortBy] = React.useState('date');

<DropdownMenu>
  <DropdownMenuTrigger asChild>
    <Button variant="outline">Sort By</Button>
  </DropdownMenuTrigger>
  <DropdownMenuContent>
    <DropdownMenuLabel>Sort Options</DropdownMenuLabel>
    <DropdownMenuRadioGroup value={sortBy} onValueChange={setSortBy}>
      <DropdownMenuRadioItem value="date">Date</DropdownMenuRadioItem>
      <DropdownMenuRadioItem value="name">Name</DropdownMenuRadioItem>
      <DropdownMenuRadioItem value="status">Status</DropdownMenuRadioItem>
    </DropdownMenuRadioGroup>
  </DropdownMenuContent>
</DropdownMenu>
```

---

### Badge

Status indicator with semantic color coding for action states.

#### Props

```typescript
export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  /** Semantic variant for status representation */
  variant?: 'success' | 'error' | 'warning' | 'info' | 'neutral';
}
```

#### Variants

| Variant | Use Case | Background | Text | Border |
|---------|----------|------------|------|--------|
| `success` | Action succeeded, run completed | `bg-green-100` | `text-green-700` | `border-green-200` |
| `error` | Action failed, validation error | `bg-red-100` | `text-red-700` | `border-red-200` |
| `warning` | Pending action, partial success | `bg-yellow-100` | `text-yellow-700` | `border-yellow-200` |
| `info` | Running action, in progress | `bg-blue-100` | `text-blue-700` | `border-blue-200` |
| `neutral` | Unknown state, draft | `bg-gray-100` | `text-gray-700` | `border-gray-200` |

#### ARIA Attributes

- Inherits all `HTMLSpanElement` attributes
- Consider adding `aria-label` for status context

#### Usage Examples

```tsx
import { Badge } from '@/core/components/ui/Badge';

// Success state
<Badge variant="success">Completed</Badge>

// Error state
<Badge variant="error">Failed</Badge>

// Warning state
<Badge variant="warning">Pending</Badge>

// Info state
<Badge variant="info">Running</Badge>

// Neutral (default)
<Badge>Draft</Badge>
<Badge variant="neutral">Unknown</Badge>

// In table cells
<TableCell>
  <Badge variant={run.status === 'success' ? 'success' : 'error'}>
    {run.status}
  </Badge>
</TableCell>

// With custom styling
<Badge variant="success" className="font-bold">
  All Tests Passed
</Badge>

// Multiple badges
<div className="flex gap-2">
  <Badge variant="info">v2.0</Badge>
  <Badge variant="success">Active</Badge>
</div>
```

---

### Loading

Visual feedback during async operations with timeout handling.

#### Props

```typescript
export interface LoadingProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Optional loading message */
  text?: string;
  /** Show timeout state after 30 seconds */
  timeout?: boolean;
  /** Callback when retry button is clicked (only shown when timeout=true) */
  onRetry?: () => void;
}
```

#### Visual States

| State | Display | Trigger |
|-------|---------|---------|
| Loading | Spinning blue circle with optional text | Default |
| Timeout | "Request timed out" message with retry button | `timeout={true}` |

#### ARIA Attributes

- Spinner includes `aria-hidden` (decorative)
- Consider adding `role="status"` and `aria-live="polite"` to container for screen readers

#### Usage Examples

```tsx
import { Loading } from '@/core/components/ui/Loading';

// Basic loading spinner
<Loading />

// With loading text
<Loading text="Loading actions..." />

// Timeout state with retry
const [isTimeout, setIsTimeout] = React.useState(false);
const [isLoading, setIsLoading] = React.useState(true);

React.useEffect(() => {
  const timer = setTimeout(() => setIsTimeout(true), 30000);
  return () => clearTimeout(timer);
}, []);

const handleRetry = () => {
  setIsTimeout(false);
  setIsLoading(true);
  // Re-fetch data
};

{isLoading && (
  <Loading
    text="Loading data..."
    timeout={isTimeout}
    onRetry={handleRetry}
  />
)}

// Full page loading
<div className="flex h-screen items-center justify-center">
  <Loading text="Initializing application..." />
</div>

// Inline loading (e.g., in button)
<Button disabled>
  <Loading className="h-4 w-4" />
  <span className="ml-2">Processing...</span>
</Button>
```

---

### ErrorBanner

Dismissible error message display with icon and optional close button.

#### Props

```typescript
export interface ErrorBannerProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Error message to display */
  message: string;
  /** Callback when dismiss button is clicked */
  onDismiss?: () => void;
}
```

#### Visual Elements

- Red background with red border (`bg-red-50 border-red-200`)
- Error icon (circle with exclamation mark)
- Error message text (`text-red-700`)
- Optional dismiss button (X icon)

#### ARIA Attributes

- Consider adding `role="alert"` for immediate screen reader announcement
- Dismiss button includes `aria-label="Dismiss"`

#### Usage Examples

```tsx
import { ErrorBanner } from '@/core/components/ui/ErrorBanner';

// Basic error banner
<ErrorBanner message="Failed to load actions. Please try again." />

// Dismissible error
const [showError, setShowError] = React.useState(true);

{showError && (
  <ErrorBanner
    message="Failed to connect to server."
    onDismiss={() => setShowError(false)}
  />
)}

// Form validation error
{formError && (
  <ErrorBanner
    message={formError}
    onDismiss={() => setFormError(null)}
  />
)}

// API error with details
{apiError && (
  <ErrorBanner
    message={`Error ${apiError.status}: ${apiError.message}`}
    onDismiss={() => setApiError(null)}
  />
)}

// Multiple errors
<div className="space-y-2">
  {errors.map((error, index) => (
    <ErrorBanner
      key={index}
      message={error.message}
      onDismiss={() => removeError(index)}
    />
  ))}
</div>

// With custom styling
<ErrorBanner
  message="Custom error message"
  className="mb-4"
/>
```

---

## Component Composition Examples

### Form with Validation

```tsx
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/core/components/ui/Dialog';
import { Input } from '@/core/components/ui/Input';
import { Textarea } from '@/core/components/ui/Textarea';
import { Button } from '@/core/components/ui/Button';
import { ErrorBanner } from '@/core/components/ui/ErrorBanner';

const [name, setName] = React.useState('');
const [description, setDescription] = React.useState('');
const [error, setError] = React.useState<string | null>(null);
const [nameError, setNameError] = React.useState(false);

const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();

  // Validation
  if (!name.trim()) {
    setNameError(true);
    setError('Action name is required');
    return;
  }

  try {
    await createAction({ name, description });
  } catch (err) {
    setError(err.message);
  }
};

<Dialog>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Create New Action</DialogTitle>
    </DialogHeader>

    {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
          Action Name
        </label>
        <Input
          id="name"
          value={name}
          onChange={(e) => {
            setName(e.target.value);
            setNameError(false);
          }}
          error={nameError}
          placeholder="e.g., Send Email"
        />
      </div>

      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
          Description
        </label>
        <Textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Describe what this action does..."
        />
      </div>

      <DialogFooter>
        <Button type="button" variant="secondary">Cancel</Button>
        <Button type="submit">Create Action</Button>
      </DialogFooter>
    </form>
  </DialogContent>
</Dialog>
```

### Data Table with Actions

```tsx
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/core/components/ui/Table';
import { Badge } from '@/core/components/ui/Badge';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/core/components/ui/DropdownMenu';
import { Button } from '@/core/components/ui/Button';
import { Loading } from '@/core/components/ui/Loading';

const [isLoading, setIsLoading] = React.useState(true);
const [actions, setActions] = React.useState([]);

<div className="w-full">
  {isLoading ? (
    <Loading text="Loading actions..." />
  ) : (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Last Run</TableHead>
          <TableHead className="w-[50px]"></TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {actions.map((action) => (
          <TableRow key={action.id} clickable onClick={() => handleViewDetails(action.id)}>
            <TableCell className="font-medium">{action.name}</TableCell>
            <TableCell>
              <Badge variant={action.status === 'active' ? 'success' : 'neutral'}>
                {action.status}
              </Badge>
            </TableCell>
            <TableCell>{formatDate(action.lastRun)}</TableCell>
            <TableCell>
              <DropdownMenu>
                <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                  <Button variant="ghost" size="icon">
                    <MoreVerticalIcon />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => handleEdit(action.id)}>
                    Edit
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => handleRun(action.id)}>
                    Run Now
                  </DropdownMenuItem>
                  <DropdownMenuItem destructive onClick={() => handleDelete(action.id)}>
                    Delete
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )}
</div>
```

---

## Performance Considerations

### Animations and Motion

All components respect the `prefers-reduced-motion` media query:

```css
/* Example from Button component */
transition-colors duration-200 motion-reduce:transition-none
```

Users who have enabled "Reduce motion" in their OS settings will see instant state changes instead of animations.

### Table Rendering

Tables are designed to handle 100-500 rows efficiently without virtualization. For larger datasets, consider:

1. Implementing pagination
2. Using virtual scrolling libraries (e.g., `react-virtual`)
3. Lazy loading rows as user scrolls

### Dialog and Dropdown

Radix UI primitives handle:
- Portal rendering (dialogs/dropdowns rendered at document root)
- Focus management (trap and restoration)
- Scroll locking (body scroll disabled when dialog open)
- Collision detection (dropdown positioning)

---

## Testing Recommendations

### Unit Tests

Each component should have tests covering:

1. **Rendering**: Component renders without errors
2. **Props**: All prop variants work correctly
3. **Interactions**: Click handlers, keyboard navigation
4. **Accessibility**: ARIA attributes, focus management
5. **Styling**: Correct classes applied for each state

### Integration Tests

Test component compositions:

1. Form submission with validation
2. Table row selection and actions
3. Dialog open/close flows
4. Dropdown menu interactions

### Accessibility Tests

Use tools like:
- **axe-core**: Automated accessibility testing
- **jest-axe**: Integration with Jest
- **@testing-library/react**: User-centric queries
- **Playwright**: E2E visual regression and keyboard navigation tests

---

## Migration Guide

### From Old Components

If you're migrating from older component implementations:

1. **Update imports**: Components are in `@/core/components/ui/`
2. **Check prop changes**: Review prop interfaces for breaking changes
3. **Update styles**: Components use Tailwind classes, not CSS modules
4. **Test accessibility**: New components have improved ARIA support
5. **Update animations**: All animations now respect `prefers-reduced-motion`

### Common Changes

| Old | New |
|-----|-----|
| `<input className="input" />` | `<Input />` |
| `<button className="btn-primary" />` | `<Button variant="default" />` |
| `<div className="modal">` | `<Dialog><DialogContent>` |
| `<span className="badge-success">` | `<Badge variant="success">` |

---

## Contributing

When adding new components or modifying existing ones:

1. Follow the established naming conventions and file structure
2. Export TypeScript interfaces for all props
3. Add JSDoc comments for complex props
4. Ensure WCAG AA compliance for all color combinations
5. Add `motion-reduce:` variants for all animations
6. Include usage examples in this README
7. Write comprehensive tests (unit + accessibility)
8. Update the component dependency graph if needed

---

## Resources

- [Radix UI Primitives](https://www.radix-ui.com/primitives/docs/overview/introduction)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [MDN: ARIA](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA)
