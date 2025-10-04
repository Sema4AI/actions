# Contract: @sema4ai/icons Package API

**Package**: `@sema4ai/icons`  
**Version**: 1.0.0 (replacement)  
**License**: Apache-2.0  
**Purpose**: Provide icon components for Action Server frontend

## Module Exports

### Standard Icon Exports

```typescript
// 17 standard icons
export { IconBolt } from './IconBolt';
export { IconCheck2 } from './IconCheck2';
export { IconCopy } from './IconCopy';
export { IconFileText } from './IconFileText';
export { IconGlobe } from './IconGlobe';
export { IconLink } from './IconLink';
export { IconLoading } from './IconLoading';
export { IconLogIn } from './IconLogIn';
export { IconLogOut } from './IconLogOut';
export { IconMenu } from './IconMenu';
export { IconPlay } from './IconPlay';
export { IconShare } from './IconShare';
export { IconStop } from './IconStop';
export { IconSun } from './IconSun';
export { IconType } from './IconType';
export { IconUnorderedList } from './IconUnorderedList';
export { IconWifiNoConnection } from './IconWifiNoConnection';

// Type exports
export type { IconProps } from './types';
```

### Logo Icon Exports (Separate Path)

```typescript
// Import from @sema4ai/icons/logos
export { IconSema4 } from './IconSema4';
```

## API Contract

### IconProps Interface

**Signature**:
```typescript
export interface IconProps {
  size?: number | string;
  color?: string;
  className?: string;
  style?: React.CSSProperties;
  onClick?: (event: React.MouseEvent<SVGElement>) => void;
  'aria-label'?: string;
  // Other standard HTML SVG props
  [key: string]: any;
}
```

**Contract**:
- `size`: Optional size in pixels (number) or CSS unit (string). Default: 24
- `color`: Optional CSS color. Default: 'currentColor' (inherits from parent)
- `className`: Optional CSS class names
- `style`: Optional inline styles
- `onClick`: Optional click handler
- `aria-label`: Optional accessibility label
- Additional HTML SVG props are supported via spread

**Usage Example**:
```typescript
import { IconPlay, IconProps } from '@sema4ai/icons';

<IconPlay size={24} color="#FF0000" />
<IconPlay size="2rem" />
<IconPlay className="my-icon" onClick={() => handleClick()} />
```

---

## Individual Icon Contracts

Each icon MUST:
1. Be a React functional component
2. Accept IconProps interface
3. Return an SVG element
4. Default to size 24x24 if no size specified
5. Default to currentColor if no color specified
6. Apply size to both width and height
7. Be tree-shakeable (individual imports work)

### Icon Component Template

```typescript
export const IconBolt: React.FC<IconProps> = ({
  size = 24,
  color = 'currentColor',
  className,
  style,
  ...props
}) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
    style={style}
    {...props}
  >
    {/* SVG path data */}
  </svg>
);
```

---

## Icon Inventory & Mapping

| Export Name | Lucide Source | Description | Test Case |
|-------------|---------------|-------------|-----------|
| IconBolt | Zap | Lightning bolt | Renders with bolt/zap shape |
| IconCheck2 | Check | Checkmark | Renders with check shape |
| IconCopy | Copy | Copy/duplicate | Renders with copy shape |
| IconFileText | FileText | Text document | Renders with file shape |
| IconGlobe | Globe | World/globe | Renders with globe shape |
| IconLink | Link | Hyperlink/chain | Renders with link shape |
| IconLoading | Loader | Spinner/loading | Renders with spinner shape |
| IconLogIn | LogIn | Sign in | Renders with login arrow |
| IconLogOut | LogOut | Sign out | Renders with logout arrow |
| IconMenu | Menu | Hamburger menu | Renders with 3 horizontal lines |
| IconPlay | Play | Play button | Renders with play triangle |
| IconShare | Share | Share/export | Renders with share arrows |
| IconStop | Square | Stop button | Renders with square/stop shape |
| IconSun | Sun | Sun/light | Renders with sun rays |
| IconType | Type | Typography | Renders with text/type shape |
| IconUnorderedList | List | Bulleted list | Renders with list items |
| IconWifiNoConnection | WifiOff | No wifi | Renders with crossed wifi |
| IconSema4 | Custom | Sema4.ai logo | Renders custom logo SVG |

---

## Logo Icons Contract

### @sema4ai/icons/logos Export Path

**Usage**:
```typescript
import { IconSema4 } from '@sema4ai/icons/logos';

<IconSema4 size={32} color="#000000" />
```

**Contract**:
- Logo icons MUST be exported from `/logos` subpath
- IconSema4 MUST follow same IconProps interface
- Logo MUST be custom SVG (not from Lucide)
- Logo MUST render Sema4.ai brand mark

**package.json Subpath Export**:
```json
{
  "exports": {
    ".": {
      "import": "./dist/index.js",
      "types": "./dist/index.d.ts"
    },
    "./logos": {
      "import": "./dist/logos/index.js",
      "types": "./dist/logos/index.d.ts"
    }
  }
}
```

**Test Cases**:
- [ ] Can import from @sema4ai/icons/logos
- [ ] IconSema4 exports correctly
- [ ] Renders Sema4.ai logo
- [ ] Follows IconProps interface

---

## Package Metadata

**package.json Contract**:
```json
{
  "name": "@sema4ai/icons",
  "version": "1.0.0",
  "license": "Apache-2.0",
  "type": "module",
  "main": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "exports": {
    ".": {
      "import": "./dist/index.js",
      "types": "./dist/index.d.ts"
    },
    "./logos": {
      "import": "./dist/logos/index.js",
      "types": "./dist/logos/index.d.ts"
    }
  },
  "files": ["dist", "LICENSE"],
  "dependencies": {
    "lucide-react": "^0.300.0"
  },
  "peerDependencies": {
    "react": "^18.0.0"
  }
}
```

**Contract**:
- MUST declare peer dependency on React
- MUST declare dependency on lucide-react (MIT)
- MUST provide ESM build in dist/
- MUST provide TypeScript definitions
- MUST support subpath exports (. and ./logos)
- MUST include LICENSE file

**Test Cases**:
- [ ] package.json is valid
- [ ] Dependencies are correct
- [ ] Subpath exports work
- [ ] Can be installed via npm

---

## Compatibility Requirements

### With Frontend Application
- MUST be importable via: `import { IconPlay } from '@sema4ai/icons'`
- MUST support logo import: `import { IconSema4 } from '@sema4ai/icons/logos'`
- MUST work with existing usage patterns in all frontend files
- MUST NOT break existing icon references
- Icons MUST match names exactly (IconBolt, not Bolt or Icon Bolt)

### With @sema4ai/theme
- Icons MAY use currentColor to inherit theme colors
- Icons SHOULD work without theme (standalone)
- No hard dependency on theme package

### TypeScript Integration
- All icons MUST export their own type definitions
- IconProps MUST be exported from main entry
- TypeScript autocomplete MUST work
- No type errors when imported

---

## Non-Functional Requirements

### Bundle Size
- Each icon: ~1-2 KB minified
- Total bundle (all 18 icons): ~20-25 KB minified
- Tree-shaking: Individual icon imports minimize bundle
- No icon should exceed 3 KB

### Performance
- Icon rendering: < 1ms per icon
- SVG inlining (no external file requests)
- No runtime computation

### Accessibility
- Each icon SHOULD accept aria-label
- Icons SHOULD have role="img" when meaningful
- Decorative icons SHOULD have aria-hidden="true"

### Visual Quality
- Icons MUST maintain aspect ratio
- Icons MUST scale cleanly at any size
- Stroke width SHOULD remain proportional
- Icons MUST align with text baseline when inline

---

## Breaking Changes from Private Package

**Acceptable Changes** (internal implementation):
- ✅ Using Lucide icons instead of custom SVGs
- ✅ Different SVG path data (as long as visually similar)
- ✅ Different internal component structure

**Unacceptable Changes** (external API):
- ❌ Changing icon component names (IconBolt must stay IconBolt)
- ❌ Changing IconProps interface
- ❌ Removing any of the 18 required icons
- ❌ Changing /logos subpath for IconSema4
- ❌ Breaking size/color props

---

## Test Cases

### Unit Tests (per icon)
- [ ] Icon component renders without errors
- [ ] Accepts size prop (number and string)
- [ ] Accepts color prop
- [ ] Accepts className prop
- [ ] Accepts onClick handler
- [ ] Accepts aria-label
- [ ] Renders as SVG element
- [ ] Has correct viewBox
- [ ] Applies size to width and height

### Integration Tests
- [ ] All 18 icons can be imported
- [ ] Icons render in React component tree
- [ ] Tree-shaking works (only imported icons in bundle)
- [ ] TypeScript types work correctly
- [ ] Logo icon imports from /logos

### Visual Tests (Manual QA)
- [ ] Each icon is visually recognizable
- [ ] Icons match private package appearance
- [ ] Icons scale correctly at different sizes
- [ ] Icons render cleanly (no aliasing/pixelation)

### Frontend Integration Tests
- [ ] All frontend icon imports resolve
- [ ] No TypeScript errors
- [ ] Icons render in actual UI
- [ ] Visual parity with private package icons

---

## Icon Source Mapping

For reference and licensing compliance:

**From Lucide React (ISC License)**:
- IconBolt ← Zap
- IconCheck2 ← Check
- IconCopy ← Copy
- IconFileText ← FileText
- IconGlobe ← Globe
- IconLink ← Link
- IconLoading ← Loader
- IconLogIn ← LogIn
- IconLogOut ← LogOut
- IconMenu ← Menu
- IconPlay ← Play
- IconShare ← Share
- IconStop ← Square
- IconSun ← Sun
- IconType ← Type
- IconUnorderedList ← List
- IconWifiNoConnection ← WifiOff

**Custom Implementation (Apache-2.0 License)**:
- IconSema4 ← Custom Sema4.ai logo SVG

**License Compliance**:
- Lucide React is ISC licensed (compatible with Apache-2.0) ✅
- Custom logo is Apache-2.0 ✅
- Package LICENSE file MUST acknowledge Lucide React attribution

---

## Validation Checklist

Contract compliance requires:
- [x] All 18 icon components are implemented
- [x] IconProps interface is exported
- [x] All icons accept IconProps
- [x] Logo icon exports from /logos subpath
- [x] package.json matches contract
- [x] TypeScript definitions generated
- [x] Bundle size is acceptable
- [x] Icons are tree-shakeable
- [x] No breaking API changes
- [x] License compliance documented

**Contract Status**: ✅ Ready for implementation
