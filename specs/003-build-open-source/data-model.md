# Data Model: Open-Source Design System Packages

**Feature**: 003-build-open-source  
**Date**: 2025-10-04  
**Purpose**: Define the structure, interfaces, and relationships for the three replacement packages

## Overview

This feature involves three npm packages that together form a design system:

1. **@sema4ai/theme** - Theming foundation (tokens, styled API, ThemeProvider)
2. **@sema4ai/icons** - Icon component library (18 SVG icons)
3. **@sema4ai/components** - UI component library (22 components + 4 utilities)

All packages are TypeScript-first with full type definitions. They are vendored in the repository and referenced via npm workspaces.

---

## Package: @sema4ai/theme

### Entities

#### ThemeTokens
Design tokens providing the visual foundation of the design system.

**Attributes**:
- `colors`: Object containing color palette
  - Primary colors (brand colors)
  - Semantic colors (success, error, warning, info)
  - Neutral colors (grays, black, white)
  - Surface colors (backgrounds, cards)
- `spacing`: Array or object of spacing values (4px scale)
- `typography`: Object containing font definitions
  - Font families
  - Font sizes
  - Font weights
  - Line heights
- `borderRadius`: Object of border radius values
- `shadows`: Object of box shadow values
- `breakpoints`: Object of responsive breakpoints

**Usage**: Consumed by components and application code for consistent styling

**Validation**:
- Colors must be valid CSS color values (hex, rgb, hsl)
- Spacing values must be numeric or CSS units
- Font sizes should follow a consistent scale

**State**: Immutable (defined once, consumed throughout application)

#### Theme (Interface)
Complete theme object structure used by ThemeProvider.

**Attributes**:
- Inherits all properties from ThemeTokens
- Additional theme-specific configuration
- Must be compatible with Emotion's theme typing

**Relationships**:
- Extended by ThemeOverrides for partial theme customization
- Consumed by ThemeProvider
- Accessed via styled components and useTheme hook

#### ThemeOverrides (Type)
Partial theme object allowing selective overrides without replacing entire theme.

**Attributes**:
- `DeepPartial<Theme>` - any subset of Theme properties
- Used for component-level or view-level theme customization

**Validation**:
- Must match Theme structure (type-checked)
- No additional properties beyond Theme definition

### Exports

```typescript
// Main exports from @sema4ai/theme
export { ThemeProvider } from './ThemeProvider';
export { styled } from '@emotion/styled';
export type { Color } from './types';
export type { ThemeOverrides } from './types';
export { tokens } from './tokens';
```

### API Contract

**ThemeProvider Component**:
```typescript
interface ThemeProviderProps {
  theme?: Theme;           // Optional custom theme
  children: React.ReactNode;
}

// Usage
<ThemeProvider theme={customTheme}>
  {children}
</ThemeProvider>
```

**styled Function**:
```typescript
// Emotion's styled API
import { styled } from '@sema4ai/theme';

const StyledDiv = styled.div`
  color: ${props => props.theme.colors.primary};
  padding: ${props => props.theme.spacing[4]};
`;
```

**Color Type**:
```typescript
type Color = string; // CSS color value
```

---

## Package: @sema4ai/icons

### Entities

#### IconComponent
React component representing a single SVG icon.

**Attributes**:
- `size`: number | string (default: 24) - Icon size in pixels or CSS unit
- `color`: string - CSS color value for icon fill/stroke
- `className`: string - Additional CSS classes
- `style`: React.CSSProperties - Inline styles
- Other standard React props (onClick, aria-label, etc.)

**Common Interface**:
```typescript
export interface IconProps {
  size?: number | string;
  color?: string;
  className?: string;
  style?: React.CSSProperties;
  onClick?: (event: React.MouseEvent) => void;
  'aria-label'?: string;
}

// All icons are React.FC<IconProps>
```

**Behavior**:
- Renders inline SVG element
- Responsive to size prop (width and height)
- Defaults to currentColor for color (inherits from parent text color)
- Supports standard HTML element events and props

### Icon Inventory

| Icon Name | Source | Description |
|-----------|--------|-------------|
| IconBolt | Lucide: Zap | Lightning bolt / power symbol |
| IconCheck2 | Lucide: Check | Checkmark |
| IconCopy | Lucide: Copy | Copy to clipboard |
| IconFileText | Lucide: FileText | Text document |
| IconGlobe | Lucide: Globe | Globe / world |
| IconLink | Lucide: Link | Hyperlink / chain |
| IconLoading | Lucide: Loader | Loading spinner |
| IconLogIn | Lucide: LogIn | Log in / sign in |
| IconLogOut | Lucide: LogOut | Log out / sign out |
| IconMenu | Lucide: Menu | Hamburger menu |
| IconPlay | Lucide: Play | Play button |
| IconShare | Lucide: Share | Share / external link |
| IconStop | Lucide: Square | Stop button |
| IconSun | Lucide: Sun | Sun / light mode |
| IconType | Lucide: Type | Typography / text |
| IconUnorderedList | Lucide: List | Bulleted list |
| IconWifiNoConnection | Lucide: WifiOff | No wifi / disconnected |
| IconSema4 | Custom SVG | Sema4.ai logo |

### Package Structure

```
icons/
├── index.ts              # Main exports
├── logos/
│   └── index.ts          # Logo exports (IconSema4)
└── types.ts              # IconProps interface
```

### Exports

```typescript
// Standard icons
export { IconBolt } from './IconBolt';
export { IconCheck2 } from './IconCheck2';
// ... (all 17 standard icons)

// Logo icons (separate export path)
export { IconSema4 } from './logos/IconSema4';

// Types
export type { IconProps } from './types';
```

### Implementation Pattern

Each icon is a simple wrapper around Lucide with consistent naming:

```typescript
import { Zap } from 'lucide-react';
import type { IconProps } from './types';

export const IconBolt: React.FC<IconProps> = (props) => {
  return <Zap {...props} />;
};
```

IconSema4 is a custom SVG component following the same props interface.

---

## Package: @sema4ai/components

### Component Categories

#### 1. Layout Components

**Box**
- **Purpose**: Flexible container with layout props
- **Props**: Common CSS props (padding, margin, display, flex properties, width, height, etc.)
- **Extends**: HTML div element
- **Usage Pattern**: General-purpose layout container

**Grid**
- **Purpose**: CSS Grid container
- **Props**: Grid-specific props (columns, rows, gap, areas)
- **Extends**: HTML div element
- **Usage Pattern**: Grid-based layouts

**Scroll**
- **Purpose**: Scrollable container with custom scrollbar styling
- **Props**: `children`, scrollbar appearance customization
- **Extends**: HTML div element
- **Usage Pattern**: Overflow containers

**Note on Column**: Column is NOT a standalone component. It is a TypeScript type definition used by the Table component to define table column configuration. See Table component below for details.

#### 2. Typography Components

**Typography**
- **Purpose**: Text rendering with variants
- **Props**: 
  - `variant`: 'h1' | 'h2' | 'h3' | 'body1' | 'body2' | 'caption' | etc.
  - `color`: CSS color or theme color key
  - `align`: 'left' | 'center' | 'right'
  - `gutterBottom`: boolean
- **Extends**: Polymorphic (renders as specified HTML element)
- **Usage Pattern**: All text content

**Header**
- **Purpose**: Section header component
- **Props**: `children`, styling props
- **Extends**: HTML heading element
- **Usage Pattern**: Section titles, page headers

#### 3. Form Components

**Input**
- **Purpose**: Text input field
- **Props** (InputProps):
  - `value`: string
  - `onChange`: (value: string) => void
  - `placeholder`: string
  - `disabled`: boolean
  - `error`: boolean
  - `helperText`: string
- **Extends**: HTML input element
- **Usage Pattern**: Forms, inline editing

**Button**
- **Purpose**: Clickable button
- **Props** (ButtonProps):
  - `children`: React.ReactNode
  - `onClick`: () => void
  - `disabled`: boolean
  - `variant`: 'primary' | 'secondary' | 'text'
  - `size`: 'small' | 'medium' | 'large'
- **Extends**: HTML button element
- **Usage Pattern**: Actions, form submission

#### 4. Navigation Components

**Link**
- **Purpose**: Hyperlink with routing
- **Props**:
  - `to`: string (URL or route)
  - `children`: React.ReactNode
  - `external`: boolean (opens in new tab if true)
- **Extends**: React Router's Link or HTML anchor
- **Usage Pattern**: Navigation between views

**SideNavigation**
- **Purpose**: Sidebar navigation menu
- **Props**:
  - `items`: Array of navigation items
  - `activeItem`: string (current route)
  - `onNavigate`: (item) => void
- **Usage Pattern**: Main application navigation

**Tabs**
- **Purpose**: Tabbed interface
- **Props**:
  - `tabs`: Array of {label, value, content}
  - `activeTab`: string
  - `onChange`: (value: string) => void
- **Usage Pattern**: Multi-view panels

#### 5. Overlay Components

**Dialog**
- **Purpose**: Modal dialog overlay
- **Props**:
  - `open`: boolean
  - `onClose`: () => void
  - `title`: string
  - `children`: React.ReactNode
  - `actions`: React.ReactNode (footer buttons)
- **Implementation**: Portal-rendered, focus trap, esc to close
- **Usage Pattern**: Confirmations, forms, alerts

**Drawer**
- **Purpose**: Side panel overlay
- **Props**:
  - `open`: boolean
  - `onClose`: () => void
  - `anchor`: 'left' | 'right' | 'top' | 'bottom'
  - `children`: React.ReactNode
- **Implementation**: Portal-rendered, slide-in animation
- **Usage Pattern**: Navigation panels, settings

**Tooltip**
- **Purpose**: Contextual hint on hover
- **Props**:
  - `title`: string (tooltip content)
  - `children`: React.ReactElement (trigger element)
  - `placement`: 'top' | 'bottom' | 'left' | 'right'
- **Implementation**: Portal-rendered, position-aware
- **Usage Pattern**: Icon explanations, hints

#### 6. Feedback Components

**Badge**
- **Purpose**: Small label/indicator
- **Props**:
  - `children`: React.ReactNode
  - `color`: 'primary' | 'secondary' | 'error' | 'success'
  - `variant`: 'filled' | 'outlined'
- **Extends**: HTML span
- **Usage Pattern**: Status indicators, counts

**Progress**
- **Purpose**: Progress indicator
- **Props**:
  - `value`: number (0-100 for determinate)
  - `variant`: 'determinate' | 'indeterminate'
  - `color`: 'primary' | 'secondary'
- **Extends**: HTML div
- **Usage Pattern**: Loading states, progress tracking

#### 7. Data Display Components

**Table**
- **Purpose**: Data table with columns
- **Props**:
  - `columns`: Array<Column> (column definitions - TypeScript type, not component)
  - `data`: Array (row data)
  - `onRowClick`: (row) => void
- **Sub-components**: Internal Row, Cell components
- **Usage Pattern**: Action lists, data grids
- **Column Type Definition**: Column is a TypeScript interface exported by the Table component, not a standalone component

**TableRowProps** (Type)
- **Purpose**: TypeScript interface for table row data
- **Attributes**: Varies based on table usage

**Column** (Type)
- **Purpose**: TypeScript interface for table column configuration
- **Attributes**: `header` (string), `accessor` (string or function), `Cell` (optional custom renderer), `width` (optional)
- **Note**: This is a TYPE DEFINITION, not a React component. It configures Table behavior.

#### 8. Code Components

**Code**
- **Purpose**: Inline code display
- **Props**:
  - `children`: string (code content)
  - `language`: string (syntax highlighting)
- **Extends**: HTML code element
- **Usage Pattern**: Code snippets, inline code

**EditorView**
- **Purpose**: CodeMirror editor integration
- **Props**:
  - `value`: string
  - `onChange`: (value: string) => void
  - `language`: string
  - `readOnly`: boolean
- **Implementation**: Wraps CodeMirror (existing dependency)
- **Usage Pattern**: JSON editing, code input

### Utility Functions

#### componentWithRef
Higher-order component/utility for forwarding refs.

```typescript
function componentWithRef<T, P>(
  component: React.ForwardRefRenderFunction<T, P>
): React.ForwardRefExoticComponent<P & React.RefAttributes<T>>;
```

**Purpose**: Simplify ref forwarding in component definitions  
**Usage**: Internal utility for building components with ref support

#### useClipboard
React hook for clipboard operations.

```typescript
interface UseClipboardReturn {
  copy: (text: string) => Promise<void>;
  copied: boolean;
  error: Error | null;
}

function useClipboard(): UseClipboardReturn;
```

**Purpose**: Copy text to clipboard with success/error feedback  
**Usage**: Copy buttons, share functionality

#### usePopover
React hook for popover positioning and state.

```typescript
interface UsePopoverReturn {
  anchorEl: HTMLElement | null;
  open: boolean;
  handleOpen: (event: React.MouseEvent<HTMLElement>) => void;
  handleClose: () => void;
}

function usePopover(): UsePopoverReturn;
```

**Purpose**: Manage popover/dropdown state and positioning  
**Usage**: Dropdown menus, context menus

#### useSystemTheme
React hook for detecting system color scheme preference.

```typescript
type SystemTheme = 'light' | 'dark';

function useSystemTheme(): SystemTheme;
```

**Purpose**: Detect user's system dark/light mode preference  
**Usage**: Automatic theme switching, theme toggle buttons

### Package Exports

```typescript
// Components
export { Badge } from './Badge';
export { Box } from './Box';
export { Button } from './Button';
export type { ButtonProps } from './Button';
export { Code } from './Code';
export { Dialog } from './Dialog';
export { Drawer } from './Drawer';
export { EditorView } from './EditorView';
export { Grid } from './Grid';
export { Header } from './Header';
export { Input } from './Input';
export type { InputProps } from './Input';
export { Link } from './Link';
export { Progress } from './Progress';
export { Scroll } from './Scroll';
export { SideNavigation } from './SideNavigation';
export { Table } from './Table';
export type { Column, TableRowProps } from './Table';
export { Tabs } from './Tabs';
export { Tooltip } from './Tooltip';
export { Typography } from './Typography';

// Utilities
export { componentWithRef } from './utils/componentWithRef';
export { useClipboard } from './hooks/useClipboard';
export { usePopover } from './hooks/usePopover';
export { useSystemTheme } from './hooks/useSystemTheme';
```

---

## Relationships Between Packages

```
@sema4ai/theme
  ↓ (provides theming foundation)
@sema4ai/components
  ↑ (imports styled, ThemeProvider, uses theme tokens)

@sema4ai/icons
  → (standalone, may use theme colors via currentColor)

Frontend Application
  ↑ (imports from all three packages)
```

**Dependency Graph**:
- `@sema4ai/theme` has zero dependencies on other packages (foundation)
- `@sema4ai/components` depends on `@sema4ai/theme` for styling
- `@sema4ai/icons` is independent (may optionally use theme)
- Frontend imports from all three packages

**Build Order**:
1. Build `@sema4ai/theme` first
2. Build `@sema4ai/icons` (parallel with step 3)
3. Build `@sema4ai/components` (depends on theme)
4. Frontend build (depends on all three)

---

## TypeScript Type Definitions

### Module Augmentation for Emotion Theme

```typescript
// In @sema4ai/theme/src/types.ts
import '@emotion/react';
import { tokens } from './tokens';

declare module '@emotion/react' {
  export interface Theme {
    colors: typeof tokens.colors;
    spacing: typeof tokens.spacing;
    typography: typeof tokens.typography;
    borderRadius: typeof tokens.borderRadius;
    shadows: typeof tokens.shadows;
    breakpoints: typeof tokens.breakpoints;
  }
}
```

This allows typed theme access in styled components:
```typescript
styled.div`
  color: ${props => props.theme.colors.primary}; // ✅ Typed
`;
```

### Component Prop Types

All components export their props interfaces:
- Enables TypeScript checking at usage sites
- Provides intellisense/autocomplete
- Documents component APIs

Example:
```typescript
import { Button, ButtonProps } from '@sema4ai/components';

const props: ButtonProps = {
  onClick: () => {},
  variant: 'primary', // ✅ Autocomplete
  disabled: false,
};
```

---

## Validation Rules

### Theme Package
- [ ] All color values are valid CSS colors
- [ ] Spacing scale is consistent (e.g., 4px multiples)
- [ ] Typography scale follows consistent ratio
- [ ] Theme type matches Emotion's Theme interface
- [ ] ThemeProvider accepts children prop
- [ ] styled function matches Emotion API

### Icons Package
- [ ] All 18 icons are exported
- [ ] IconSema4 is exported from /logos subpath
- [ ] All icons accept IconProps interface
- [ ] Icons render as SVG elements
- [ ] Icons default to 24px size
- [ ] Icons inherit color via currentColor

### Components Package
- [ ] All 22 components are exported
- [ ] All 4 utilities are exported
- [ ] Props match actual usage in frontend codebase
- [ ] TypeScript types are exported for Button, Input, Table types
- [ ] Components use theme from ThemeProvider
- [ ] Refs are forwarded where needed
- [ ] Accessibility attributes are preserved

### Integration
- [ ] Frontend imports work without path changes
- [ ] TypeScript compilation succeeds
- [ ] No import errors at build time
- [ ] Bundle size within ±5% tolerance
- [ ] Visual appearance matches (manual QA)
- [ ] Functional behavior matches (manual QA)

---

## Migration Impact

### Files Modified
- `action_server/frontend/package.json` - Already uses file: protocol, no change needed
- `action_server/frontend/vendored/*/` - Complete replacement of package contents

### Files Unchanged
- All files in `action_server/frontend/src/` - Zero code changes
- `action_server/frontend/vite.config.js` - No changes expected
- `action_server/frontend/tsconfig.json` - No changes expected

### Backwards Compatibility
- ✅ Import paths identical: `from '@sema4ai/components'`
- ✅ Component names identical: `<Button>`, `<Dialog>`, etc.
- ✅ Prop interfaces match actual usage
- ✅ TypeScript types compatible
- ⚠️ Internal implementation completely different (users don't see this)

---

## State Transitions

### Package Lifecycle States

**Development**:
1. Source code edited in `vendored/{package}/src/`
2. Run build: `npm run build` (in package directory)
3. Output generated in `vendored/{package}/dist/`
4. Frontend hot-reloads during `npm run dev`

**Testing**:
1. Contract tests validate exports exist
2. Integration tests validate frontend builds
3. Manual QA validates visual/functional parity

**Production Build**:
1. All three packages built to dist/
2. Frontend Vite build bundles packages
3. Single-file output generated via vite-plugin-singlefile
4. Bundle size validated against ±5% tolerance

**No States for**:
- Packages don't have runtime state (static imports)
- No server-side state
- No database state
- Theme state is managed by React context (ThemeProvider)

---

## Data Flow

### Theme Application Flow
```
1. tokens.ts defines design tokens (static)
2. ThemeProvider wraps application (runtime)
3. Components access theme via Emotion's useTheme or styled props
4. Optional ThemeOverrides applied at component/view level
```

### Icon Rendering Flow
```
1. Import icon component
2. Render with props (size, color, etc.)
3. SVG element rendered inline
4. CSS styling applied (size, color, transform)
```

### Component Rendering Flow
```
1. Import component from @sema4ai/components
2. Pass props matching component interface
3. Component uses styled-components from theme
4. Theme tokens applied via Emotion
5. React renders to DOM
```

---

**Data Model Complete**: 2025-10-04  
**Ready for Contract Generation**: Yes ✅
