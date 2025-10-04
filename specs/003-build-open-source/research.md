# Research: Open-Source Design System Replacement

**Feature**: 003-build-open-source  
**Date**: 2025-10-04  
**Purpose**: Evaluate open-source alternatives for building replacement packages for @sema4ai/components, @sema4ai/icons, @sema4ai/theme

## Research Questions

### 1. Component Library Foundation
**Question**: Which open-source React component library should serve as the foundation for @sema4ai/components replacement?

**Requirements**:
- MIT, ISC, or Apache 2.0 license
- Provides components matching our 22 components: Badge, Box, Button, Code, Column, Dialog, Drawer, EditorView, Grid, Header, Input, Link, Progress, Scroll, SideNavigation, Table, Tabs, Tooltip, Typography
- TypeScript support
- Active maintenance
- Bundle size efficiency
- Customizable/themeable

**Options Evaluated**:

#### Option A: Radix UI Primitives
- **License**: MIT ✅
- **Coverage**: Provides Dialog, Drawer (Sheet), Tabs, Tooltip as unstyled primitives
- **Missing**: Badge, Box, Button, Code, EditorView, Grid, Header, Input, Link, Progress, Scroll, SideNavigation, Table, Typography
- **Bundle Size**: ~50KB for primitives used
- **Pros**: Unstyled (full styling control), excellent accessibility, TypeScript first, tree-shakeable
- **Cons**: Would need to build many components from scratch, no styled components out-of-box
- **Verdict**: Too much custom work required

#### Option B: Material-UI (MUI)
- **License**: MIT ✅
- **Coverage**: Has Badge, Box, Button, Dialog, Drawer, Grid, Input (TextField), Link, Progress (LinearProgress/CircularProgress), Table, Tabs, Tooltip, Typography
- **Missing**: Code (CodeMirror integration), EditorView, Header, Scroll, SideNavigation (could adapt Drawer/List), Column
- **Bundle Size**: ~300KB base + ~10-30KB per component
- **Pros**: Comprehensive, excellent TypeScript, well-documented, battle-tested
- **Cons**: Large bundle size, opinionated styling system, may be hard to match exact visual parity
- **Verdict**: Bundle size likely exceeds ±5% tolerance

#### Option C: Chakra UI
- **License**: MIT ✅
- **Coverage**: Badge, Box, Button, Code, Drawer, Grid, Heading (Header equivalent), Input, Link, Progress, Table, Tabs, Tooltip, Text (Typography)
- **Missing**: Dialog (has Modal), EditorView, Scroll, SideNavigation, Column (can use Flex/Stack)
- **Bundle Size**: ~80KB core + components
- **Pros**: Excellent theming system compatible with styled API pattern, good TypeScript, accessible
- **Cons**: Some missing components, styling system may differ from current approach
- **Verdict**: Strong candidate but theming approach needs investigation

#### Option D: Build from Scratch using styled-components/Emotion
- **License**: styled-components (MIT ✅), Emotion (MIT ✅)
- **Coverage**: 100% (we build everything)
- **Bundle Size**: Minimal (only what we implement)
- **Pros**: Complete control, exact API match, optimal bundle size, no unnecessary features
- **Cons**: Most implementation work, need to ensure accessibility, testing burden
- **Verdict**: Best for parity and bundle size control

**Decision**: **Build from scratch using Emotion** (@emotion/react + @emotion/styled)

**Rationale**:
1. **Bundle Size Control**: Only include exactly what's used, ensuring ±5% tolerance is met
2. **API Compatibility**: Complete control over component APIs to match existing usage exactly
3. **Exact Parity**: Can replicate visual styling precisely (requirement per clarification)
4. **Theming Alignment**: Emotion's styled API aligns with existing `styled` import from @sema4ai/theme
5. **TypeScript**: Full TypeScript support with custom type definitions matching existing usage
6. **License**: MIT-licensed ✅
7. **Maintenance**: Emotion is actively maintained, stable, and widely used

**Alternatives Considered**: Chakra UI was close but its theming system and component APIs would require adaptation that could break parity. Radix UI would require too much custom work. MUI's bundle size is prohibitive.

---

### 2. Icon Library
**Question**: Which open-source icon library should provide the 18 icons needed?

**Requirements**:
- MIT, ISC, or Apache 2.0 license
- Provides or allows custom implementation of 18 specific icons
- SVG-based React components
- TypeScript support
- Tree-shakeable
- Small bundle size

**Icons Needed**:
IconBolt, IconCheck2, IconCopy, IconFileText, IconGlobe, IconLink, IconLoading, IconLogIn, IconLogOut, IconMenu, IconPlay, IconShare, IconStop, IconSun, IconType, IconUnorderedList, IconWifiNoConnection, IconSema4 (custom logo)

**Options Evaluated**:

#### Option A: Lucide React
- **License**: ISC ✅
- **Icon Count**: 1,300+ icons
- **Coverage**: Check ✓, Copy ✓, FileText ✓, Globe ✓, Link ✓, Loader (Loading) ✓, LogIn ✓, LogOut ✓, Menu ✓, Play ✓, Share ✓, Square (Stop) ~, Sun ✓, Type ✓, List (UnorderedList) ✓, WifiOff (WifiNoConnection) ~, Bolt ✓
- **Missing**: IconSema4 (custom logo - must implement separately)
- **Bundle Size**: ~1KB per icon
- **Pros**: Excellent coverage, consistent design, TypeScript, tree-shakeable, actively maintained, matches most icon names
- **Cons**: Need custom implementation for IconSema4, some icons have slightly different names
- **Verdict**: Strong candidate with excellent coverage

#### Option B: React Icons (aggregates multiple sets)
- **License**: MIT ✅
- **Icon Count**: 20,000+ from multiple sets
- **Coverage**: Has icons from Feather, Font Awesome, Material, etc.
- **Bundle Size**: ~1-2KB per icon
- **Pros**: Huge selection, likely has all needed icons
- **Cons**: Inconsistent design across sets, larger bundle, less cohesive
- **Verdict**: Too inconsistent for professional UI

#### Option C: Tabler Icons React
- **License**: MIT ✅
- **Icon Count**: 4,400+ icons
- **Coverage**: Excellent coverage including Bolt, Check, Copy, FileText, World (Globe), Link, Loader, Login, Logout, Menu, PlayerPlay, Share, Square, Sun, Typography, List, WifiOff
- **Bundle Size**: ~1KB per icon
- **Pros**: Very comprehensive, consistent design system, tree-shakeable, TypeScript
- **Cons**: Need custom IconSema4
- **Verdict**: Excellent alternative to Lucide

#### Option D: Custom SVG Components
- **License**: N/A (our own)
- **Coverage**: 100% (implement exactly what's needed)
- **Bundle Size**: Minimal (~0.5KB per icon)
- **Pros**: Exact match for any existing icon designs, smallest bundle, complete control
- **Cons**: Most manual work, need to create/source 18 SVGs
- **Verdict**: Best if we have existing icon designs to replicate

**Decision**: **Lucide React** with custom IconSema4 implementation

**Rationale**:
1. **Coverage**: 17 of 18 icons available with excellent name matches
2. **Consistency**: Professional, cohesive design system
3. **Bundle Size**: ~18KB total for 18 icons (well within tolerance)
4. **License**: ISC ✅
5. **Maintenance**: Actively maintained, stable API
6. **TypeScript**: Full TypeScript support
7. **Tree-shaking**: Excellent support for only importing needed icons
8. **Custom Icons**: Simple pattern for adding IconSema4 as custom SVG component

**Icon Mapping**:
- IconBolt → Zap (from Lucide)
- IconCheck2 → Check (or CheckCheck if double check needed)
- IconCopy → Copy
- IconFileText → FileText
- IconGlobe → Globe
- IconLink → Link
- IconLoading → Loader
- IconLogIn → LogIn
- IconLogOut → LogOut
- IconMenu → Menu
- IconPlay → Play
- IconShare → Share
- IconStop → Square (or StopCircle)
- IconSun → Sun
- IconType → Type
- IconUnorderedList → List
- IconWifiNoConnection → WifiOff
- IconSema4 → Custom SVG (implement separately in /logos subfolder)

**Alternatives Considered**: Tabler Icons React is equally good but Lucide has better name alignment with our existing names. Custom SVG would be most work. React Icons is too inconsistent.

---

### 3. Theming Solution
**Question**: Which styling/theming solution should power @sema4ai/theme replacement?

**Requirements**:
- MIT, ISC, or Apache 2.0 license
- Provides `styled` API (CSS-in-JS)
- Supports ThemeProvider pattern
- TypeScript support
- Works with React 18
- Supports design tokens

**Options Evaluated**:

#### Option A: Emotion (@emotion/react + @emotion/styled)
- **License**: MIT ✅
- **API**: `styled` function, `css` prop, ThemeProvider
- **TypeScript**: Excellent support with theme typing
- **Bundle Size**: ~8KB core
- **Pros**: Widely used, actively maintained, flexible, excellent DX, SSR support, theme typing
- **Cons**: Requires babel plugin for optimal DX (optional)
- **Verdict**: Excellent match for our needs

#### Option B: styled-components
- **License**: MIT ✅
- **API**: `styled` function, ThemeProvider
- **TypeScript**: Good support
- **Bundle Size**: ~16KB
- **Pros**: Most popular CSS-in-JS solution, stable, well-documented
- **Cons**: Larger bundle than Emotion, slightly less flexible
- **Verdict**: Good but larger bundle size

#### Option C: Vanilla Extract
- **License**: MIT ✅
- **API**: Zero-runtime CSS-in-TypeScript
- **Bundle Size**: 0KB runtime
- **Pros**: Zero runtime cost, type-safe, fast
- **Cons**: Different API pattern (not `styled`), build-time only, would break API compatibility
- **Verdict**: API incompatible with existing usage

#### Option D: Stitches
- **License**: MIT ✅
- **API**: `styled` function, theme support
- **Bundle Size**: ~6KB
- **Pros**: Near-zero runtime, excellent DX, type-safe variants
- **Cons**: Project appears less actively maintained (last update 2022)
- **Verdict**: Maintenance concerns

**Decision**: **Emotion (@emotion/react + @emotion/styled)**

**Rationale**:
1. **API Compatibility**: Provides `styled` API that matches existing usage exactly
2. **ThemeProvider**: Built-in ThemeProvider component matching existing pattern
3. **Bundle Size**: Small (~8KB), well within ±5% tolerance
4. **TypeScript**: Excellent TypeScript support with theme typing via module augmentation
5. **License**: MIT ✅
6. **Maintenance**: Actively maintained, used by major projects (MUI uses Emotion)
7. **Features**: Supports all needed features (design tokens, dynamic theming, color utilities)
8. **Performance**: Efficient runtime with style caching

**Theme Structure**:
```typescript
// Design tokens
export const tokens = {
  colors: { /* color palette */ },
  spacing: { /* spacing scale */ },
  typography: { /* font sizes, weights */ },
  // ... other tokens
};

// Emotion ThemeProvider wrapper
export const ThemeProvider: React.FC<{ theme: Theme, children }>;

// styled API (from @emotion/styled)
export { styled } from '@emotion/styled';

// Color utility type
export type Color = string;
export type ThemeOverrides = DeepPartial<Theme>;
```

**Alternatives Considered**: styled-components is good but larger. Vanilla Extract breaks API compatibility. Stitches has maintenance concerns.

---

### 4. Build & Package Structure
**Question**: How should the three packages be structured and built within the repository?

**Requirements**:
- npm workspace compatible
- TypeScript compilation to dist/
- Tree-shakeable exports
- Development and production builds
- Type definitions (.d.ts files)

**Best Practices Researched**:

#### Package Structure Pattern
```
vendored/{package}/
├── package.json           # Package definition with proper exports
├── src/                   # TypeScript source
│   ├── index.ts          # Main entry (re-exports all)
│   └── components/       # Individual component folders
├── dist/                  # Built output
│   ├── index.js          # ESM build
│   ├── index.d.ts        # Type definitions
│   └── index.css         # Extracted styles (if needed)
├── tsconfig.json         # TypeScript config
└── LICENSE               # License file
```

#### Build Tool Options

**Option A: TypeScript Compiler (tsc)**
- Simple, no additional tools
- Good for libraries
- Handles types automatically
- Cons: No bundling, no CSS handling

**Option B: tsup**
- Fast bundler for TypeScript libraries
- Handles ESM + CJS + types
- Zero config
- Supports CSS
- Used by many modern libraries

**Option C: Rollup + TypeScript**
- Full control over bundling
- Excellent tree-shaking
- Plugin ecosystem
- More configuration needed

**Decision**: **tsup** for components/icons/theme packages

**Rationale**:
- Zero-config setup
- Handles TypeScript compilation + bundling
- Generates type definitions
- Supports multiple formats (ESM for Vite)
- Fast build times
- Used by modern React libraries

#### Package.json Exports Pattern
```json
{
  "name": "@sema4ai/components",
  "type": "module",
  "main": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "exports": {
    ".": {
      "import": "./dist/index.js",
      "types": "./dist/index.d.ts"
    }
  },
  "files": ["dist", "LICENSE"]
}
```

#### Workspace Setup
Update frontend package.json:
```json
{
  "dependencies": {
    "@sema4ai/components": "file:./vendored/components",
    "@sema4ai/icons": "file:./vendored/icons",
    "@sema4ai/theme": "file:./vendored/theme"
  }
}
```

---

### 5. Component Implementation Strategy
**Question**: What patterns should guide component implementation for exact parity?

**Research Findings**:

#### API Analysis Strategy
1. **Extract actual usage** from frontend codebase via static analysis
2. **Document props used** for each component (not full API)
3. **Match TypeScript types** exactly as used in frontend
4. **Preserve ref forwarding** where used (componentWithRef utility)

#### Component Categories

**Layout Components** (Box, Grid, Column):
- Simple styled div wrappers with layout props
- Use Emotion styled API
- Support common props: padding, margin, flex, etc.

**Interactive Components** (Button, Input, Link):
- Standard HTML element wrappers with styling
- Support disabled, onClick, onChange, etc.
- Match existing visual styling via CSS

**Overlay Components** (Dialog, Drawer, Tooltip):
- Complex components with portal rendering
- Consider using Radix UI primitives for accessibility
- Wrap with custom styling to match visual parity

**Data Display** (Table, Badge, Typography):
- Semantic HTML with styling
- Table may need custom implementation for Column API
- Typography variants system

**Specialized** (Code, EditorView, Progress, SideNavigation):
- Code/EditorView: Integrate CodeMirror (already a dependency)
- Progress: Simple progress bar with animation
- SideNavigation: Custom navigation component
- Scroll: Wrapper with custom scrollbar styling

**Utilities** (useClipboard, usePopover, useSystemTheme, componentWithRef):
- Custom React hooks
- componentWithRef: React.forwardRef wrapper utility
- useSystemTheme: Match system dark/light mode detection

#### TypeScript Strategy
```typescript
// Extract existing type usage
export interface ButtonProps {
  // Only props actually used in frontend
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  variant?: 'primary' | 'secondary';
}

// Use module augmentation for theme types
declare module '@emotion/react' {
  export interface Theme {
    colors: typeof tokens.colors;
    spacing: typeof tokens.spacing;
    // ... other token categories
  }
}
```

---

### 6. Bundle Size Optimization
**Question**: How to ensure bundle stays within ±5% tolerance?

**Current Baseline**: Need to measure current bundle with private packages

**Optimization Techniques**:

1. **Tree-shaking**: Use named exports, avoid default exports
2. **Code Splitting**: Not applicable (single-file build per vite-plugin-singlefile)
3. **Minification**: Already handled by Vite (esbuild)
4. **Dependency Selection**: Choose minimal dependencies
5. **Custom Implementation**: Build simple components from scratch vs heavy libraries
6. **Icon Optimization**: Tree-shakeable icon imports
7. **CSS Extraction**: Minimal runtime CSS-in-JS overhead with Emotion

**Measurement Strategy**:
```bash
# Measure current bundle
npm run build
du -h dist/index.html

# Measure with replacements
# Compare sizes, ensure within ±5%
```

**Expected Impact**:
- **Emotion**: +8KB
- **Lucide Icons**: +18KB (18 icons)
- **Custom Components**: Variable, optimized per component
- **Net Change**: Target <±5% of current size

---

## Summary of Decisions

| Component | Decision | License | Rationale |
|-----------|----------|---------|-----------|
| **Component Library** | Build from scratch with Emotion | MIT | Best bundle size control, exact API match, visual parity |
| **Icon Library** | Lucide React + custom IconSema4 | ISC | 17/18 coverage, consistent design, small bundle |
| **Theming** | Emotion (@emotion/react + @emotion/styled) | MIT | API compatible, TypeScript support, actively maintained |
| **Build Tool** | tsup | MIT | Zero-config, fast, handles TypeScript + types |
| **Package Structure** | npm workspaces with file: protocol | N/A | Standard approach, no external deps needed |

## Implementation Approach

1. **Phase 1a - Theme Package** (foundation):
   - Implement design tokens
   - Create ThemeProvider wrapper around Emotion
   - Export styled API
   - Implement Color type and ThemeOverrides

2. **Phase 1b - Icons Package**:
   - Wrap Lucide icons with consistent API
   - Implement custom IconSema4 SVG
   - Create logos/ subfolder structure
   - Export all 18 icons with Icon* naming

3. **Phase 1c - Components Package**:
   - Implement 22 components using Emotion + theme
   - Prioritize by usage frequency
   - Implement 4 utilities
   - Ensure ref forwarding works

4. **Phase 1d - Integration**:
   - Update frontend package.json
   - Verify imports work unchanged
   - Run TypeScript compiler
   - Measure bundle size

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Bundle size exceeds ±5% | High | Measure continuously, optimize components, consider lighter alternatives |
| Visual parity difficult to achieve | Medium | Manual QA with side-by-side comparison, iterate on styling |
| TypeScript types mismatch | Medium | Extract actual usage patterns first, test with tsc --noEmit |
| Component behavior differs | Medium | Thorough manual QA testing of all interactions |
| Missing component features | Low | Comprehensive prop usage analysis before implementation |
| Emotion API incompatibility | Low | Test styled API early, Emotion is well-established |
| Lucide icon names mismatch | Low | Icon mapping documented above, easy to adjust |

## Next Steps

Proceed to **Phase 1: Design & Contracts** to:
1. Create data model for component props, theme tokens
2. Generate API contracts for each package's exports
3. Create failing tests for component rendering, API compatibility
4. Document quickstart validation process
5. Update agent context file

---

**Research Complete**: 2025-10-04  
**Ready for Phase 1**: Yes ✅
