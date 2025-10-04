# Contract: @sema4ai/theme Package API

**Package**: `@sema4ai/theme`  
**Version**: 1.0.0 (replacement)  
**License**: Apache-2.0  
**Purpose**: Provide theming foundation for Action Server frontend

## Module Exports

### Primary Exports

```typescript
// Re-export from Emotion
export { styled } from '@emotion/styled';

// Theme provider component
export { ThemeProvider } from './ThemeProvider';

// Type exports
export type { Color, ThemeOverrides, Theme } from './types';

// Token exports
export { tokens } from './tokens';
```

## API Contract

### 1. ThemeProvider Component

**Signature**:
```typescript
interface ThemeProviderProps {
  theme?: Theme;
  children: React.ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps>;
```

**Contract**:
- MUST accept optional `theme` prop of type Theme
- MUST accept `children` prop
- MUST wrap children in Emotion's ThemeProvider
- MUST provide default theme if none specified
- MUST make theme accessible via useTheme hook
- MUST make theme accessible in styled components

**Usage Example**:
```typescript
import { ThemeProvider } from '@sema4ai/theme';

<ThemeProvider>
  <App />
</ThemeProvider>

// Or with custom theme
<ThemeProvider theme={customTheme}>
  <App />
</ThemeProvider>
```

**Test Cases**:
- [ ] Renders children without errors
- [ ] Accepts custom theme prop
- [ ] Provides theme to styled components
- [ ] Works with useTheme hook

---

### 2. styled Function

**Signature**:
```typescript
export { styled } from '@emotion/styled';
```

**Contract**:
- MUST be Emotion's styled function (re-exported)
- MUST support all HTML elements (styled.div, styled.span, etc.)
- MUST support styled components (styled(Component))
- MUST provide theme via props in template literals
- MUST support TypeScript with theme typing

**Usage Example**:
```typescript
import { styled } from '@sema4ai/theme';

const StyledBox = styled.div`
  color: ${props => props.theme.colors.primary};
  padding: ${props => props.theme.spacing[4]};
`;

const StyledButton = styled.button<{ variant: 'primary' | 'secondary' }>`
  background: ${props => props.variant === 'primary' 
    ? props.theme.colors.primary 
    : props.theme.colors.secondary};
`;
```

**Test Cases**:
- [ ] styled.div creates styled component
- [ ] Theme props are accessible
- [ ] TypeScript types work correctly
- [ ] Can style existing components

---

### 3. Color Type

**Signature**:
```typescript
export type Color = string;
```

**Contract**:
- MUST be string type representing CSS color
- MUST accept hex, rgb, rgba, hsl, hsla, named colors
- Used for component prop typing

**Usage Example**:
```typescript
import { Color } from '@sema4ai/theme';

interface MyComponentProps {
  color: Color;
}
```

**Test Cases**:
- [ ] Type accepts string values
- [ ] Compatible with CSS color values

---

### 4. ThemeOverrides Type

**Signature**:
```typescript
export type ThemeOverrides = DeepPartial<Theme>;
```

**Contract**:
- MUST be partial version of Theme type
- MUST allow selective property overrides
- MUST maintain type safety (no invalid properties)

**Usage Example**:
```typescript
import { ThemeOverrides } from '@sema4ai/theme';

const overrides: ThemeOverrides = {
  colors: {
    primary: '#FF0000', // Override only primary color
  },
};
```

**Test Cases**:
- [ ] Type accepts partial theme objects
- [ ] TypeScript validates property names
- [ ] Can be merged with base theme

---

### 5. tokens Object

**Signature**:
```typescript
export const tokens: {
  colors: Record<string, string>;
  spacing: string[] | Record<string, string>;
  typography: {
    fontFamily: string;
    fontSize: Record<string, string>;
    fontWeight: Record<string, number>;
    lineHeight: Record<string, number>;
  };
  borderRadius: Record<string, string>;
  shadows: Record<string, string>;
  breakpoints: Record<string, string>;
};
```

**Contract**:
- MUST export design tokens object
- MUST include colors, spacing, typography, borderRadius, shadows, breakpoints
- Colors MUST be valid CSS color values
- Spacing MUST be numeric or CSS units
- Typography MUST include fontFamily, fontSize, fontWeight, lineHeight
- All values MUST be serializable

**Usage Example**:
```typescript
import { tokens } from '@sema4ai/theme';

const primaryColor = tokens.colors.primary;
const baseSpacing = tokens.spacing[4]; // or tokens.spacing.md
```

**Test Cases**:
- [ ] tokens object is exported
- [ ] Contains all required sections
- [ ] Values are valid CSS values
- [ ] Can be imported and used

---

## TypeScript Module Augmentation

**Contract**:
- Package MUST augment @emotion/react module with Theme interface
- Theme interface MUST match tokens structure
- Enables type-safe theme access in styled components

**Required Declaration**:
```typescript
// In package
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

**Test Cases**:
- [ ] Theme types available in styled components
- [ ] Autocomplete works for theme properties
- [ ] TypeScript errors on invalid theme properties

---

## Package Metadata

**package.json Contract**:
```json
{
  "name": "@sema4ai/theme",
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
  "peerDependencies": {
    "react": "^18.0.0",
    "@emotion/react": "^11.0.0",
    "@emotion/styled": "^11.0.0"
  }
}
```

**Contract**:
- MUST declare peer dependencies on React and Emotion
- MUST provide ESM build in dist/
- MUST provide TypeScript definitions
- MUST include LICENSE file
- MUST use semantic versioning

**Test Cases**:
- [ ] package.json is valid
- [ ] Peer dependencies specified correctly
- [ ] Can be installed via npm
- [ ] TypeScript definitions are generated

---

## Compatibility Requirements

### With @sema4ai/components
- Components package MUST be able to import and use styled
- Components MUST have access to theme via ThemeProvider
- Theme tokens MUST be accessible for component styling

### With Frontend Application
- MUST be importable via: `import { styled, ThemeProvider } from '@sema4ai/theme'`
- MUST work with existing Vite build configuration
- MUST work with TypeScript 5.3.3
- MUST work with React 18.2.0
- MUST NOT break existing imports or usage patterns

---

## Non-Functional Requirements

### Bundle Size
- Base package (without tree-shaking): < 15 KB minified+gzipped
- Emotion dependencies are peer deps (not included in size)
- Theme tokens: < 5 KB

### Performance
- Theme application: < 1ms overhead
- No runtime theme computation (tokens are static)
- Efficient theme prop access in styled components

### Browser Support
- Modern browsers supporting ES2020+
- Same support as Emotion library

---

## Breaking Changes from Private Package

**Acceptable Changes** (internal implementation):
- ✅ Using Emotion instead of different CSS-in-JS
- ✅ Different token structure internally
- ✅ Different file organization

**Unacceptable Changes** (external API):
- ❌ Changing export names
- ❌ Changing ThemeProvider props API
- ❌ Removing styled export
- ❌ Changing type names

---

## Validation Checklist

Contract compliance requires:
- [x] All exports listed above are present
- [x] ThemeProvider accepts documented props
- [x] styled function is Emotion's styled
- [x] Type definitions are correct
- [x] Module augmentation is present
- [x] package.json matches contract
- [x] Compatible with frontend usage patterns
- [x] Bundle size is acceptable
- [x] No breaking API changes

**Contract Status**: ✅ Ready for implementation
