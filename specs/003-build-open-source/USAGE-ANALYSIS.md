# Frontend Component Usage Analysis

**Feature**: 003-build-open-source  
**Status**: To be completed in T00A  
**Purpose**: Document actual usage patterns of @sema4ai packages in frontend to validate contract definitions

## Instructions

This file should be populated by analyzing the frontend codebase (`action_server/frontend/src/`) to extract:

1. **Component Imports**: Which components from @sema4ai/components are actually imported
2. **Props Usage**: Which props are passed to each component in actual usage
3. **Type References**: Which TypeScript types are imported and used
4. **Icon Usage**: Which icons from @sema4ai/icons are used
5. **Theme Usage**: How @sema4ai/theme is used (styled API, ThemeProvider, tokens)

## Analysis Method

Recommended approach:
```bash
# Find all imports from @sema4ai packages
cd action_server/frontend/src
grep -r "from '@sema4ai" . -A 5

# Or use TypeScript language server analysis
# Or use ast-grep or similar static analysis tool
```

## Expected Output Format

### Components Usage
```
Component: Button
Files: src/pages/Actions.tsx, src/components/Header.tsx
Props used:
  - onClick (function)
  - variant ('primary' | 'secondary')
  - disabled (boolean)
  - children (ReactNode)
Not used from ButtonProps: size, type

Component: Dialog
...
```

### Icons Usage
```
Icon: IconPlay
Files: src/components/ActionCard.tsx
Props used: size (24), color ('currentColor')

Icon: IconStop
...
```

### Theme Usage
```
ThemeProvider: Used in src/App.tsx
styled: Used in 15 component files
tokens: Direct access in src/theme/customizations.ts
```

## Validation Checklist

- [ ] All components listed in contracts/components-api-contract.md are verified as used OR marked unused
- [ ] All props in contract match actual usage patterns
- [ ] All 18 icons are confirmed used in codebase
- [ ] TypeScript type exports (ButtonProps, InputProps, Column, TableRowProps) are verified as imported
- [ ] No unknown/undocumented usage patterns discovered

## Status

**PENDING**: This analysis must be completed in task T00A before contract tests (T011-T013) are written.

---

*This file will be populated during implementation of T00A*
