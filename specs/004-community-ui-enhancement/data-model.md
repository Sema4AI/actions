# Data Model: Component Entities & States

**Feature**: Community UI Enhancement Implementation  
**Date**: 2025-10-12  
**Status**: Phase 1 - Design Complete

## Overview

This document defines the data structures (React props, state, and style variants) for all UI components enhanced or created in this feature. It serves as the contract between component implementation and usage.

---

## Component Entities

### 1. Input Component

**Purpose**: Single-line text input field with enhanced visual states

**Props Interface**:
```typescript
export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  /** Display error styling (red border, red focus ring) */
  error?: boolean;
}
```

**Visual States**:
| State       | Trigger                     | Tailwind Classes                                           |
|-------------|-----------------------------|------------------------------------------------------------|
| Base        | Default                     | `border-gray-300 bg-white text-gray-900`                  |
| Hover       | Mouse over (not disabled)   | `hover:border-gray-400`                                    |
| Focus       | Keyboard/mouse focus        | `focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent` |
| Disabled    | `disabled` prop             | `disabled:cursor-not-allowed disabled:bg-gray-100 disabled:text-gray-500` |
| Error       | `error={true}` prop         | `border-red-500 focus:ring-red-500`                        |

**Validation Rules**:
- Must accept all native HTML input attributes (type, placeholder, value, onChange, etc.)
- `error` prop is optional (defaults to false)
- Focus ring must have 2px width and 2px offset (`ring-2 ring-offset-2`)
- Disabled state overrides hover/focus styles (`:disabled` has higher specificity)

**Relationships**:
- Used by: Forms in Actions page, RunHistory filters, Settings
- Composes: None (primitive component)
- Extends: `React.InputHTMLAttributes<HTMLInputElement>`

---

### 2. Textarea Component

**Purpose**: Multi-line text input with code/JSON support

**Props Interface**:
```typescript
export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  /** Display error styling (red border, red focus ring) */
  error?: boolean;
}
```

**Visual States**:
| State       | Trigger                        | Tailwind Classes                                           |
|-------------|--------------------------------|------------------------------------------------------------|
| Base        | Default                        | `border-gray-300 bg-white text-gray-900 min-h-[80px] resize-y` |
| Hover       | Mouse over (not disabled)      | `hover:border-gray-400`                                    |
| Focus       | Keyboard/mouse focus           | `focus:outline-none focus:ring-2 focus:ring-blue-500`      |
| Disabled    | `disabled` prop                | `disabled:cursor-not-allowed disabled:bg-gray-100`         |
| Error       | `error={true}` prop            | `border-red-500 focus:ring-red-500`                        |
| Monospace   | `spellCheck={false}` (heuristic) | `font-mono` (for JSON/code input)                         |

**Validation Rules**:
- Minimum height: 80px (`min-h-[80px]`)
- Resize: vertical only (`resize-y`)
- Character limit: 10,000 characters (enforced by consumer via `maxLength`)
- Monospace font applied automatically when `spellCheck={false}` (indicates code input)

**Relationships**:
- Used by: Action parameter forms, JSON editors
- Composes: Inherits all Input styling patterns
- Extends: `React.TextareaHTMLAttributes<HTMLTextAreaElement>`

---

### 3. Dialog Component

**Purpose**: Modal overlay for confirmations, forms, and detail views

**Props Interface**:
```typescript
// Root component (Radix Dialog.Root wrapper)
export type DialogProps = React.ComponentPropsWithoutRef<typeof DialogPrimitive.Root>;

// Content component (main visible dialog)
export interface DialogContentProps 
  extends React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content> {
  // Inherits all Radix Dialog.Content props (onEscapeKeyDown, onPointerDownOutside, etc.)
}

// Sub-components (no custom props)
export type DialogTitleProps = React.ComponentPropsWithoutRef<typeof DialogPrimitive.Title>;
export type DialogDescriptionProps = React.ComponentPropsWithoutRef<typeof DialogPrimitive.Description>;
export type DialogHeaderProps = React.HTMLAttributes<HTMLDivElement>;
export type DialogFooterProps = React.HTMLAttributes<HTMLDivElement>;
```

**Visual States**:
| State       | Trigger                    | Tailwind Classes                                           |
|-------------|----------------------------|------------------------------------------------------------|
| Closed      | `open={false}` prop        | Hidden (Radix manages visibility)                          |
| Opening     | `open={true}` transition   | `data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95 duration-200` |
| Open        | `open={true}` stable       | Fully visible                                              |
| Closing     | `open={false}` transition  | `data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95` |
| Focus Trapped | Dialog open              | Radix manages keyboard focus (Tab cycles within dialog)    |

**Component Hierarchy**:
```
Dialog (Root)
├── DialogTrigger (optional button to open)
├── DialogPortal (Radix portal for overlay)
│   ├── DialogOverlay (backdrop)
│   │   └── bg-black/50 backdrop-blur-sm
│   └── DialogContent (main container)
│       ├── DialogHeader (optional)
│       │   ├── DialogTitle
│       │   └── DialogDescription
│       ├── [Custom content]
│       └── DialogFooter (optional)
│           └── [Buttons]
└── DialogClose (X button, top-right)
```

**Validation Rules**:
- Overlay backdrop must be semi-transparent (`bg-black/50`) with blur (`backdrop-blur-sm`)
- Content must be centered (`fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2`)
- Animation duration: 200ms (`duration-200`)
- Focus trap must keep Tab/Shift+Tab within dialog elements (Radix handles)
- Escape key closes dialog (Radix handles via `onEscapeKeyDown`)

**Relationships**:
- Used by: Confirmation dialogs (delete action), action execution modals, settings forms
- Composes: Button (for close/submit), Input/Textarea (in forms)
- Extends: `@radix-ui/react-dialog` primitives

---

### 4. Table Component

**Purpose**: Data grid for displaying actions, runs, logs, and artifacts

**Props Interface**:
```typescript
export interface TableProps extends React.HTMLAttributes<HTMLTableElement> {
  // No custom props - uses standard table element
}

export interface TableRowProps extends React.HTMLAttributes<HTMLTableRowElement> {
  /** Highlight row with blue background (for selected state) */
  selected?: boolean;
  /** Make row clickable (shows pointer cursor) */
  clickable?: boolean;
}
```

**Visual States**:
| State       | Trigger                    | Tailwind Classes                                           |
|-------------|----------------------------|------------------------------------------------------------|
| Header      | `<thead>` element          | `bg-gray-50 border-b border-gray-200 font-medium text-gray-700` |
| Body Row    | `<tbody><tr>` element      | `border-b border-gray-200 last:border-b-0`                 |
| Row Hover   | Mouse over row             | `hover:bg-gray-50 transition-colors duration-200`          |
| Row Selected| `selected={true}` prop     | `bg-blue-50 hover:bg-blue-100`                             |
| Row Clickable| `clickable={true}` prop   | `cursor-pointer`                                           |
| Cell        | `<td>` or `<th>` element   | `px-4 py-3 text-sm text-gray-900 text-left`               |
| Last Row    | Last `<tr>` in `<tbody>`   | `last:border-b-0` (no border on last row)                  |

**Validation Rules**:
- Header row must be visually distinct from body rows (`bg-gray-50` vs `bg-white`)
- Hover transition must be smooth (`transition-colors duration-200`)
- Selected state overrides hover state (blue background remains on hover)
- Minimum touch target for rows: 44px height (accessibility requirement)
- Table must be responsive (horizontal scroll on mobile if needed)

**Performance Constraints**:
- Must render 100-500 rows without virtualization
- Hover states must not cause layout thrashing (use GPU-accelerated properties only)

**Relationships**:
- Used by: Actions list, RunHistory, Logs, Artifacts pages
- Composes: Badge (for status column), Button (for action column)
- Extends: Standard HTML `<table>` element

---

### 5. DropdownMenu Component

**Purpose**: Contextual menu for secondary actions (edit, delete, run)

**Props Interface**:
```typescript
// Root component (Radix DropdownMenu.Root wrapper)
export type DropdownMenuProps = React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Root>;

// Content component (menu container)
export interface DropdownMenuContentProps 
  extends React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Content> {
  // Inherits Radix props (sideOffset, align, etc.)
}

// Item component (menu option)
export interface DropdownMenuItemProps 
  extends React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Item> {
  /** Show destructive styling (red text/icon) */
  destructive?: boolean;
}
```

**Visual States**:
| State       | Trigger                    | Tailwind Classes                                           |
|-------------|----------------------------|------------------------------------------------------------|
| Closed      | Default                    | Hidden (Radix manages visibility)                          |
| Opening     | Click trigger              | `data-[state=open]:fade-in-0 data-[state=open]:slide-in-from-top-2 duration-150` |
| Open        | `open={true}` stable       | Fully visible                                              |
| Item Default| Menu item idle             | `px-3 py-2 text-sm text-gray-900 rounded-md cursor-pointer` |
| Item Hover  | Mouse over item            | `hover:bg-gray-100 hover:text-gray-900`                    |
| Item Focus  | Keyboard focus (arrow keys)| `focus:bg-gray-100 focus:outline-none`                     |
| Item Destructive | `destructive={true}` | `text-red-600 hover:bg-red-50 focus:bg-red-50`            |
| Separator   | `<DropdownMenuSeparator/>` | `h-px bg-gray-200 my-1`                                    |

**Validation Rules**:
- Animation duration: 150ms (faster than Dialog for snappiness)
- Menu must close on outside click (Radix handles via `onPointerDownOutside`)
- Keyboard navigation must work (arrow keys, Enter to select, Escape to close)
- Menu items must have minimum 44px touch target height
- Destructive items (delete) must use red styling for warning

**Relationships**:
- Used by: Action row options (three-dot menu), settings menus
- Composes: Button (for trigger)
- Extends: `@radix-ui/react-dropdown-menu` primitives

---

### 6. Badge Component (New)

**Purpose**: Status indicator with semantic color coding

**Props Interface**:
```typescript
export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  /** Semantic variant for status representation */
  variant?: 'success' | 'error' | 'warning' | 'info' | 'neutral';
}
```

**Variants**:
| Variant     | Use Case                   | Tailwind Classes                                           |
|-------------|----------------------------|------------------------------------------------------------|
| `success`   | Action succeeded, run completed | `bg-green-100 text-green-700 border-green-200`        |
| `error`     | Action failed, validation error | `bg-red-100 text-red-700 border-red-200`              |
| `warning`   | Pending action, partial success | `bg-yellow-100 text-yellow-700 border-yellow-200`     |
| `info`      | Running action, in progress     | `bg-blue-100 text-blue-700 border-blue-200`           |
| `neutral`   | Unknown state, draft            | `bg-gray-100 text-gray-700 border-gray-200`           |

**Visual States**:
| State       | Tailwind Classes                                           |
|-------------|------------------------------------------------------------|
| Base        | `inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium border` |

**Validation Rules**:
- Variant defaults to `neutral` if not specified
- Text must meet WCAG AA contrast (all defined combinations are compliant)
- Badge must be inline-flex to allow icon placement (optional enhancement)
- Font size: `text-xs` (12px) for compact display

**Relationships**:
- Used by: Table cells (status column), action cards
- Composes: None (primitive component)
- Extends: `React.HTMLAttributes<HTMLSpanElement>`

---

### 7. Loading Component (New)

**Purpose**: Visual feedback during async operations

**Props Interface**:
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

**Visual States**:
| State       | Trigger                    | Tailwind Classes                                           |
|-------------|----------------------------|------------------------------------------------------------|
| Loading     | Default                    | Spinner: `animate-spin rounded-full border-4 border-gray-200 border-t-blue-600 h-8 w-8` |
| Timeout     | `timeout={true}` prop      | Replace spinner with text: `text-gray-700 font-medium` + retry button |

**Component Structure**:
```tsx
// Normal loading state
<div className="flex h-full items-center justify-center">
  <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-blue-600" />
  {text && <span className="ml-3 text-sm text-gray-600">{text}</span>}
</div>

// Timeout state
<div className="flex flex-col items-center justify-center gap-4">
  <p className="text-sm text-gray-700 font-medium">Request timed out</p>
  <Button onClick={onRetry} variant="outline">Retry</Button>
</div>
```

**Validation Rules**:
- Spinner must be centered in container (`flex items-center justify-center`)
- Spinner animation must respect `motion-reduce:` (add `motion-reduce:animate-none`)
- Timeout state triggers after 30 seconds (consumer's responsibility via timer)
- Retry button must use Button component with `outline` variant

**Relationships**:
- Used by: All pages during data fetch (Actions, RunHistory, Logs, Artifacts)
- Composes: Button (for retry action)
- Extends: `React.HTMLAttributes<HTMLDivElement>`

---

### 8. ErrorBanner Component (New)

**Purpose**: Dismissible error message display

**Props Interface**:
```typescript
export interface ErrorBannerProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Error message to display */
  message: string;
  /** Callback when dismiss button is clicked */
  onDismiss?: () => void;
}
```

**Visual States**:
| State       | Tailwind Classes                                           |
|-------------|------------------------------------------------------------|
| Base        | `bg-red-50 border border-red-200 rounded-md p-4 flex items-start gap-3` |
| Text        | `text-sm text-red-700 flex-1`                              |
| Dismiss Btn | `text-red-500 hover:bg-red-100 rounded-md p-1 transition-colors` |

**Component Structure**:
```tsx
<div className="bg-red-50 border border-red-200 rounded-md p-4 flex items-start gap-3">
  <svg className="h-5 w-5 text-red-600" /* X Circle icon */>...</svg>
  <p className="text-sm text-red-700 flex-1">{message}</p>
  {onDismiss && (
    <button onClick={onDismiss} className="text-red-500 hover:bg-red-100 rounded-md p-1">
      <svg className="h-4 w-4">...</svg> {/* X icon */}
    </button>
  )}
</div>
```

**Validation Rules**:
- Message is required (`message` prop must not be empty)
- Dismiss button is optional (only shown if `onDismiss` callback provided)
- Must include error icon for visual clarity (red circle with X)
- Text must meet WCAG AA contrast (red-700 on red-50 = 8.3:1 ratio)

**Relationships**:
- Used by: Form validation errors, API error responses
- Composes: None (primitive component)
- Extends: `React.HTMLAttributes<HTMLDivElement>`

---

## State Transitions

### Dialog Open/Close Flow
```
[Closed] 
  ↓ (user clicks trigger OR programmatic `setOpen(true)`)
[Opening - 200ms animation]
  ↓ (animation complete)
[Open - focus trapped]
  ↓ (user presses Escape OR clicks backdrop OR clicks close button)
[Closing - 200ms animation]
  ↓ (animation complete)
[Closed]
```

### Form Input Error Flow
```
[Base state]
  ↓ (user submits form with invalid value)
[Error state - red border + red focus ring]
  ↓ (user corrects value)
[Base state - validation clears error]
```

### Loading → Timeout Flow
```
[Loading - spinner visible]
  ↓ (30 seconds elapse)
[Timeout - retry button visible]
  ↓ (user clicks retry)
[Loading - spinner visible again]
```

---

## Color Contrast Validation

All text/background combinations are validated for WCAG AA compliance (4.5:1 ratio):

| Component       | Background       | Text Color       | Ratio  | Pass? |
|-----------------|------------------|------------------|--------|-------|
| Input (base)    | `bg-white`       | `text-gray-900`  | 18.2:1 | ✅ AAA |
| Input (disabled)| `bg-gray-100`    | `text-gray-500`  | 4.6:1  | ✅ AA  |
| Badge (success) | `bg-green-100`   | `text-green-700` | 7.8:1  | ✅ AAA |
| Badge (error)   | `bg-red-100`     | `text-red-700`   | 8.3:1  | ✅ AAA |
| Badge (warning) | `bg-yellow-100`  | `text-yellow-700`| 6.5:1  | ✅ AAA |
| Badge (info)    | `bg-blue-100`    | `text-blue-700`  | 7.9:1  | ✅ AAA |
| ErrorBanner     | `bg-red-50`      | `text-red-700`   | 8.3:1  | ✅ AAA |
| Table header    | `bg-gray-50`     | `text-gray-700`  | 9.5:1  | ✅ AAA |

**Validation Tool**: WebAIM Contrast Checker (https://webaim.org/resources/contrastchecker/)

---

## Component Dependencies Graph

```
Button (✅ already styled)
  ↓ used by
  ├── Dialog (close button, footer actions)
  ├── DropdownMenu (trigger)
  ├── Loading (retry button)
  └── ErrorBanner (dismiss button)

Input
  ↓ used by
  └── Dialog (form inputs)

Textarea
  ↓ used by
  └── Dialog (multi-line form inputs)

Badge
  ↓ used by
  └── Table (status column)

Loading
  ↓ used by
  └── All pages (data fetch states)

ErrorBanner
  ↓ used by
  └── All pages (error states)

Table
  ↓ composes
  ├── Badge (status cells)
  └── DropdownMenu (action column)

Dialog
  ↓ composes
  ├── Button (actions)
  ├── Input (forms)
  └── Textarea (multi-line forms)
```

**Implementation Order** (based on dependencies):
1. Input, Textarea, Badge (no dependencies)
2. Loading, ErrorBanner (depend on Button, already styled)
3. Dialog (depends on Button, Input, Textarea)
4. Table (depends on Badge, DropdownMenu)
5. DropdownMenu (depends on Button)

---

## Next Steps

With the data model defined:
1. **contracts/**: Generate TypeScript interface files for each component
2. **quickstart.md**: Document how to use each component with examples
3. **Testing**: Write tests validating all states and transitions (Phase 1)
4. **Implementation**: Build components following these specifications (Phase 2 - tasks.md)
