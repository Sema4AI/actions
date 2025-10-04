# Quickstart: Build Open-Source Design System Replacement

**Feature**: 003-build-open-source  
**Purpose**: Validate that external contributors can build the Action Server frontend without authentication  
**Audience**: External contributors, maintainers, CI systems

## Overview

This quickstart validates the primary user story:
> As an external open-source contributor, I want to clone the Action Server repository and build the frontend without requiring any private package registry authentication, so that I can contribute to the project without access barriers.

---

## Prerequisites

- **Node.js**: 20.x LTS
- **npm**: 9.x or later (comes with Node.js)
- **Git**: Any recent version
- **No GitHub Packages authentication** (this is the key test!)

## Success Criteria

✅ Build completes without authentication errors  
✅ No private package registry access required  
✅ All components render correctly  
✅ Bundle size within ±5% of baseline  
✅ Visual and functional parity validated (manual QA)

---

## Part 1: Fresh Clone Build (External Contributor Simulation)

This simulates a completely new contributor with zero Sema4.ai credentials.

### Step 1: Clean Environment

```bash
# Remove any existing GitHub Packages authentication
rm ~/.npmrc 2>/dev/null || true

# Ensure no environment variables with tokens
unset GITHUB_TOKEN
unset NPM_TOKEN

# Verify no authentication configured
npm config get @sema4ai:registry  # Should return "undefined" or empty
```

**Expected Output**: No registry configured for @sema4ai scope

---

### Step 2: Clone Repository

```bash
# Clone from GitHub
git clone https://github.com/robocorp/actions.git
cd actions

# Checkout the feature branch (or main after merge)
git checkout 003-build-open-source  # Or 'main' after feature merge
```

**Expected Output**: Repository cloned successfully

---

### Step 3: Install Dependencies

```bash
cd action_server/frontend

# Install all dependencies
npm ci
```

**Expected Output**:
- ✅ No authentication errors
- ✅ Dependencies installed from public npm registry
- ✅ Vendored packages linked via file: protocol
- ✅ Installation completes in < 2 minutes

**Common Errors to Watch For**:
- ❌ "401 Unauthorized" → FAIL (authentication required)
- ❌ "404 Not Found" → FAIL (package not accessible)
- ❌ "npm ERR! code E403" → FAIL (authentication required)

---

### Step 4: Run TypeScript Type Check

```bash
npm run test:types
```

**Expected Output**:
- ✅ TypeScript compilation successful
- ✅ No type errors
- ✅ All imports resolve correctly

**If This Fails**: TypeScript types are incompatible with frontend usage

---

### Step 5: Build Frontend

```bash
npm run build
```

**Expected Output**:
- ✅ Vite build completes successfully
- ✅ Output generated in `dist/` directory
- ✅ Single-file bundle created (`dist/index.html`)
- ✅ Build time < 30 seconds
- ✅ No errors or warnings about missing modules

**Build Output Example**:
```
vite v6.1.0 building for production...
✓ 156 modules transformed.
dist/index.html  825.34 kB
✓ built in 12.45s
```

---

### Step 6: Verify Bundle Size

```bash
# Measure bundle size
ls -lh dist/index.html

# Or for more detail
du -h dist/index.html
```

**Expected Output**:
- Bundle size: ~800-900 KB (within ±5% of baseline)
- If baseline was 850 KB, acceptable range: 807-892 KB

**If This Fails**: Bundle size exceeds tolerance, optimization needed

---

### Step 7: Run Development Server

```bash
npm run dev
```

**Expected Output**:
- ✅ Vite dev server starts
- ✅ Server listening on http://localhost:5173 (or similar)
- ✅ No console errors about missing modules
- ✅ Hot module replacement works

**Test Actions**:
1. Open browser to http://localhost:5173
2. Verify Action Server UI loads
3. Check browser console for errors (should be none)
4. Verify components render correctly

---

## Part 2: Component Validation (Manual QA)

This validates visual and functional parity per the clarification (manual QA review).

### Setup: Side-by-Side Comparison

**Option A**: Compare with existing deployment
1. Open production Action Server UI in one browser tab
2. Open local development server in another tab
3. Compare screens side-by-side

**Option B**: Compare with baseline screenshots
1. Use baseline screenshots from before replacement
2. Take screenshots of new implementation
3. Compare visually

---

### Component Checklist

For each component used in the frontend, verify:

#### Layout Components
- [ ] **Box**: Renders as container, accepts children
- [ ] **Grid**: Layout works correctly
- [ ] **Scroll**: Custom scrollbar visible and functional

#### Typography
- [ ] **Typography**: Text renders with correct styles
- [ ] **Header**: Section headers appear correctly

#### Form Components
- [ ] **Button**: All variants render correctly (primary, secondary, text)
  - [ ] onClick handlers work
  - [ ] Disabled state shows correctly
- [ ] **Input**: Text input accepts input
  - [ ] onChange fires correctly
  - [ ] Error state renders
  - [ ] Helper text appears

#### Navigation
- [ ] **Link**: Navigation links work
  - [ ] Internal navigation functions
  - [ ] External links open in new tab
- [ ] **SideNavigation**: Sidebar menu renders
  - [ ] Active item highlights
  - [ ] Click navigation works
- [ ] **Tabs**: Tab interface works
  - [ ] Tab switching functions
  - [ ] Active tab highlights

#### Overlays
- [ ] **Dialog**: Modal dialogs render
  - [ ] Opens and closes correctly
  - [ ] ESC key closes dialog
  - [ ] Backdrop click closes dialog
  - [ ] Focus trap works
- [ ] **Drawer**: Side panel renders
  - [ ] Slides in/out correctly
  - [ ] Close button works
- [ ] **Tooltip**: Tooltips appear on hover
  - [ ] Positioning correct
  - [ ] Disappears on mouse leave

#### Feedback
- [ ] **Badge**: Status badges render
  - [ ] Colors correct
  - [ ] Variants (filled/outlined) work
- [ ] **Progress**: Progress bars render
  - [ ] Determinate progress shows correctly
  - [ ] Indeterminate animation works

#### Data Display
- [ ] **Table**: Data tables render
  - [ ] Headers display correctly
  - [ ] Row data appears
  - [ ] Row click handlers work
  - [ ] Custom cell renderers work

#### Code Components
- [ ] **Code**: Code blocks render
  - [ ] Syntax highlighting works
  - [ ] Inline code displays correctly
- [ ] **EditorView**: CodeMirror editor works
  - [ ] Editing functions
  - [ ] Syntax highlighting active
  - [ ] Read-only mode works

#### Icons
- [ ] **All 18 icons render correctly**:
  - [ ] IconBolt, IconCheck2, IconCopy, IconFileText
  - [ ] IconGlobe, IconLink, IconLoading, IconLogIn, IconLogOut
  - [ ] IconMenu, IconPlay, IconShare, IconStop, IconSun
  - [ ] IconType, IconUnorderedList, IconWifiNoConnection
  - [ ] IconSema4 (logo)
- [ ] Icons scale correctly at different sizes
- [ ] Icon colors match theme

#### Theme & Styling
- [ ] **ThemeProvider**: Theme context works
- [ ] **Design tokens**: Colors, spacing, typography consistent
- [ ] **Dark/light mode**: System theme detection works
- [ ] **Styled components**: All components styled correctly

---

### Functional Testing

#### User Flows
1. **View Actions List**:
   - [ ] Navigate to Actions view
   - [ ] Table loads and displays actions
   - [ ] Click action to view details
   
2. **Run Action**:
   - [ ] Click "Run" button
   - [ ] Dialog opens with parameters
   - [ ] Submit action
   - [ ] Progress indicator shows
   - [ ] Results display correctly

3. **Edit JSON**:
   - [ ] Find JSON editor (EditorView)
   - [ ] Type in editor
   - [ ] Syntax highlighting works
   - [ ] Copy button works (useClipboard)

4. **Navigation**:
   - [ ] Click sidebar items
   - [ ] Navigation works
   - [ ] Active item highlights
   - [ ] Breadcrumbs update

5. **Responsive Behavior**:
   - [ ] Resize browser window
   - [ ] Layout adapts appropriately
   - [ ] Mobile drawer works

---

### Accessibility Testing

Run basic accessibility checks:

```bash
# Option 1: Use browser DevTools
# Open Chrome DevTools → Lighthouse → Run Accessibility Audit

# Option 2: Use axe DevTools extension
# Install axe DevTools extension
# Run scan on pages
```

**Accessibility Checklist**:
- [ ] All interactive elements keyboard accessible
- [ ] Focus indicators visible
- [ ] Screen reader labels present (aria-label)
- [ ] Color contrast meets WCAG AA
- [ ] Form inputs have labels
- [ ] Dialogs trap focus correctly

---

## Part 3: CI Validation

This validates that CI can build without credentials (per FR-003).

### GitHub Actions Workflow Test

```yaml
# Simulate CI environment
name: Frontend Build Test
on: [push, pull_request]

jobs:
  build-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      # Explicitly clear any auth (not needed but for demonstration)
      - name: Clear npm authentication
        run: rm -f ~/.npmrc
      
      - name: Install dependencies
        run: |
          cd action_server/frontend
          npm ci
        env:
          # No GITHUB_TOKEN, no NPM_TOKEN - prove it's not needed
          GITHUB_TOKEN: ''
      
      - name: Type check
        run: |
          cd action_server/frontend
          npm run test:types
      
      - name: Build
        run: |
          cd action_server/frontend
          npm run build
      
      - name: Verify bundle size
        run: |
          cd action_server/frontend
          SIZE=$(stat -f%z dist/index.html 2>/dev/null || stat -c%s dist/index.html)
          echo "Bundle size: $SIZE bytes"
          # Add assertions for ±5% tolerance if baseline known
```

**Expected CI Outcome**:
- ✅ All steps pass
- ✅ No authentication errors
- ✅ Build artifacts generated

---

## Part 4: Integration Tests

### Automated Tests

```bash
cd action_server

# Run contract tests
pytest tests/action_server_tests/frontend_tests/test_component_contracts.py -v

# Run integration tests
pytest tests/action_server_tests/frontend_tests/test_build_integration.py -v

# Run bundle size validation
pytest tests/action_server_tests/frontend_tests/test_bundle_size.py -v

# Run vendor integrity tests
pytest tests/action_server_tests/test_vendored_integrity.py -v
```

**Expected Output**:
- ✅ All contract tests pass (components exported, types correct)
- ✅ Integration test passes (build succeeds)
- ✅ Bundle size test passes (within ±5%)
- ✅ Integrity tests pass (checksums valid)

---

## Troubleshooting

### Issue: "Cannot find module '@sema4ai/components'"

**Cause**: npm didn't properly install vendored packages

**Solution**:
```bash
cd action_server/frontend
rm -rf node_modules package-lock.json
npm install
```

---

### Issue: TypeScript errors on import

**Cause**: Type definitions not generated or incorrect

**Solution**:
```bash
# Rebuild vendored packages
cd action_server/frontend/vendored/theme
npm run build

cd ../icons
npm run build

cd ../components
npm run build

# Retry type check
cd ../..
npm run test:types
```

---

### Issue: Bundle size exceeds tolerance

**Cause**: Replacement packages larger than expected

**Investigation**:
```bash
# Analyze bundle
cd action_server/frontend
npm run build -- --mode=analyze

# Check individual package sizes
du -h vendored/*/dist/
```

**Solution**: Optimize components, remove unused code

---

### Issue: Visual differences

**Cause**: Styling not matching private packages

**Investigation**:
1. Use browser DevTools to inspect styles
2. Compare computed styles between implementations
3. Check theme tokens match

**Solution**: Adjust component styles to match

---

## Success Metrics

### Build Success (MUST PASS)
- [x] Clean clone builds without authentication
- [x] TypeScript compilation succeeds
- [x] Vite build completes successfully
- [x] CI pipeline builds without credentials
- [x] Bundle size within ±5% tolerance

### Component Parity (MUST PASS)
- [x] All 22 components render without errors
- [x] All 18 icons display correctly
- [x] Theme system works as expected
- [x] Visual appearance matches private packages (manual QA)
- [x] Functional behavior matches private packages (manual QA)

### Quality (SHOULD PASS)
- [x] No console errors or warnings
- [x] Accessibility standards maintained
- [x] Performance metrics acceptable
- [x] All automated tests pass

---

## Acceptance

Feature is accepted when:
1. ✅ An external contributor (without Sema4.ai credentials) successfully completes Part 1
2. ✅ Maintainer QA review confirms visual/functional parity (Part 2)
3. ✅ CI pipeline validates automated build (Part 3)
4. ✅ All integration tests pass (Part 4)
5. ✅ No blocking issues remain

---

## Validation Record

**Date**: ___________  
**Validator**: ___________  
**Result**: ☐ PASS  ☐ FAIL  ☐ CONDITIONAL

**Part 1 - Fresh Build**: ☐ PASS  ☐ FAIL  
**Part 2 - Component Validation**: ☐ PASS  ☐ FAIL  
**Part 3 - CI Validation**: ☐ PASS  ☐ FAIL  
**Part 4 - Integration Tests**: ☐ PASS  ☐ FAIL

**Notes**:
___________________________________________
___________________________________________
___________________________________________

**Signature**: _____________________________

---

**Quickstart Version**: 1.0  
**Last Updated**: 2025-10-04  
**Status**: Ready for validation after implementation ✅
