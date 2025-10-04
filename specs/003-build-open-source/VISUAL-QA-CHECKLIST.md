# Visual & Functional Parity QA Checklist

**Feature**: 003-build-open-source  
**Purpose**: Measurable criteria for validating visual and functional parity between private packages and open-source replacements  
**Used by**: Task T084 (Manual QA validation)

## Overview

This checklist provides **objective criteria** for evaluating whether the open-source replacement packages match the visual appearance and functional behavior of the private @sema4ai packages.

**Pass Criteria**: All items must be checked OR documented exceptions must be approved by maintainer with rationale.

---

## Per-Component Validation

For **each of the 22 components**, validate the following categories:

### 1. Visual Appearance

#### Colors
- [ ] Primary colors match (brand colors, CTAs)
- [ ] Semantic colors match (success green, error red, warning amber, info blue)
- [ ] Neutral colors match (text colors, borders, backgrounds)
- [ ] Disabled state colors match (grayed out appearance)
- [ ] Hover state colors match (color shifts on mouseover)
- [ ] Active/pressed state colors match
- [ ] Focus ring colors match (keyboard navigation highlight)

#### Spacing & Layout
- [ ] Internal padding matches (space inside component)
- [ ] External margins match (space between components)
- [ ] Border radius matches (rounded corners)
- [ ] Border width and style match
- [ ] Component width matches (explicit or flex behavior)
- [ ] Component height matches
- [ ] Alignment matches (text alignment, vertical centering)

#### Typography
- [ ] Font family matches
- [ ] Font size matches for each variant (h1-h6, body1, body2, caption)
- [ ] Font weight matches (regular, medium, bold)
- [ ] Line height matches (text spacing)
- [ ] Letter spacing matches
- [ ] Text color matches default and variants

#### Shadows & Depth
- [ ] Box shadows match (dropdown shadows, card elevation)
- [ ] Shadow blur and spread match
- [ ] Shadow color and opacity match
- [ ] Elevation levels match (z-index stacking)

### 2. Interactive States

- [ ] **Default state**: Component appears identical at rest
- [ ] **Hover state**: Mouse-over appearance matches
- [ ] **Focus state**: Keyboard focus appearance matches (tab navigation)
- [ ] **Active/Pressed state**: Click/touch state matches
- [ ] **Disabled state**: Disabled appearance matches
- [ ] **Loading state**: Loading indicator appearance matches (if applicable)
- [ ] **Error state**: Error styling matches (inputs, forms)

### 3. Animations & Transitions

- [ ] Transition duration matches (e.g., 200ms, 300ms)
- [ ] Transition timing function matches (ease, ease-in-out, linear)
- [ ] Animation curves match
- [ ] Loading spinner animation matches (rotation speed, appearance)
- [ ] Slide-in animations match (Drawer, Dialog)
- [ ] Fade-in/fade-out animations match
- [ ] Expand/collapse animations match (Tabs, accordions if present)

### 4. Functional Behavior

#### General
- [ ] Click handlers fire correctly
- [ ] Keyboard navigation works (arrow keys, enter, space, tab)
- [ ] Disabled state prevents interaction
- [ ] Form submission behavior matches
- [ ] Validation behavior matches (error messages, timing)

#### Component-Specific
- [ ] **Dialog**: Opens, closes, backdrop click closes, ESC key closes, focus trap works
- [ ] **Drawer**: Slides from correct anchor, closes on backdrop, correct width/height
- [ ] **Tooltip**: Shows on hover, hides on mouse leave, correct placement, correct delay
- [ ] **Tabs**: Switches content, keyboard navigation works, active tab highlighted
- [ ] **Table**: Sorting works (if used), row click works, column widths correct
- [ ] **Input**: onChange fires correctly, value updates, validation works
- [ ] **Button**: onClick fires, form submission works (type="submit")
- [ ] **Link**: Navigation works, external links open in new tab
- [ ] **EditorView**: CodeMirror renders, value updates, syntax highlighting works

### 5. Accessibility (WCAG 2.1 AA)

- [ ] Screen reader labels present (aria-label, aria-labelledby)
- [ ] Keyboard navigation works without mouse
- [ ] Focus indicators visible (not hidden)
- [ ] Color contrast ratios meet WCAG AA (4.5:1 for normal text)
- [ ] Interactive elements are keyboard accessible
- [ ] Form labels associated with inputs
- [ ] Error messages announced to screen readers
- [ ] Modal dialogs trap focus appropriately
- [ ] ARIA roles correct (button, dialog, menu, etc.)

---

## Theme Package Validation

### ThemeProvider
- [ ] Wraps application without errors
- [ ] Custom theme prop works
- [ ] Theme context accessible via useTheme hook
- [ ] Theme types work in TypeScript

### Design Tokens
- [ ] Color palette matches (compare side-by-side with color picker)
- [ ] Spacing scale matches (measure with browser devtools)
- [ ] Typography scale matches
- [ ] Border radius values match
- [ ] Shadow definitions match
- [ ] Breakpoint values match

### styled API
- [ ] styled.div and other elements work
- [ ] Theme props accessible in template literals
- [ ] TypeScript autocomplete works for theme properties
- [ ] Styled components render correctly

---

## Icons Package Validation

### Per Icon (18 total)
- [ ] Icon renders without errors
- [ ] Icon shape matches visually (compare side-by-side)
- [ ] Icon size prop works (24, 32, "2rem", etc.)
- [ ] Icon color prop works (hex, rgb, currentColor)
- [ ] Icon maintains aspect ratio at all sizes
- [ ] Icon renders cleanly without pixelation/aliasing
- [ ] IconSema4 logo matches brand guidelines

### Icon Props
- [ ] className prop works
- [ ] style prop works
- [ ] onClick handler works
- [ ] aria-label works
- [ ] All IconProps accepted

---

## Bundle Size Validation

- [ ] Built bundle size measured (dist/index.html)
- [ ] Bundle size within ±5% of baseline (see BASELINE-METRICS.md)
- [ ] If outside tolerance: documented reason and optimization plan

---

## Browser Compatibility

Test in:
- [ ] Chrome/Chromium (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest, if macOS available)
- [ ] Edge (latest)

Verify:
- [ ] Components render correctly
- [ ] Interactions work
- [ ] Animations smooth
- [ ] No console errors

---

## Side-by-Side Comparison Method

### Setup
1. **Terminal 1**: Run current master branch with private packages
   ```bash
   git checkout master
   cd action_server/frontend
   npm ci
   npm run dev
   # Opens on http://localhost:5173
   ```

2. **Terminal 2**: Run feature branch with open-source packages
   ```bash
   git checkout 003-build-open-source
   cd action_server/frontend
   npm ci
   npm run dev -- --port 5174
   # Opens on http://localhost:5174
   ```

3. Open both URLs in browser tabs side-by-side (or use split screen)

### Comparison Process
1. Navigate to same page in both tabs
2. Compare visually (take screenshots if needed)
3. Interact with same components in both tabs
4. Use browser DevTools to measure spacing, colors, sizes
5. Check checkbox if identical OR document difference

### Tools
- Browser DevTools Inspector (measure spacing, colors)
- Browser DevTools Color Picker (compare hex values)
- Screenshot tools (side-by-side comparison)
- Browser accessibility auditing tools (axe DevTools)

---

## Approval & Sign-Off

### QA Reviewer Information
- **Reviewer Name**: _________________
- **Date**: _________________
- **Branch**: 003-build-open-source
- **Commit SHA**: _________________

### Results Summary
- **Total Items Checked**: _____ / _____
- **Items Passing**: _____
- **Items with Exceptions**: _____
- **Critical Issues Found**: _____

### Documented Exceptions

| Component/Area | Issue Description | Severity | Approved? | Rationale |
|----------------|-------------------|----------|-----------|-----------|
| | | | [ ] | |
| | | | [ ] | |

### Final Approval

- [ ] **APPROVED**: All items pass OR all exceptions approved with documented rationale
- [ ] **REJECTED**: Critical issues found requiring fixes before approval

**Maintainer Signature**: _________________  
**Date**: _________________

---

## Notes

- This checklist should be completed AFTER all automated tests pass (T078)
- Use this checklist during task T084 execution
- Save completed checklist to this file or print/sign physical copy
- Attach screenshots of any exceptions to PR for review
- If significant issues found, pause and create remediation tasks

**Status**: Ready for use in T084 ✅
