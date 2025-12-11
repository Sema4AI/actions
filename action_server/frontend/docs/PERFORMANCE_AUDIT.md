# Performance Audit Checklist

**Version**: 1.0
**Last Updated**: 2025-12-11
**Related Requirements**: SC-014, SC-015, FR-PERF-001, FR-PERF-002, FR-PERF-003

This document provides a comprehensive checklist and instructions for manually validating the performance of the Action Server frontend application.

---

## Table of Contents

1. [Overview](#overview)
2. [Performance Targets](#performance-targets)
3. [Prerequisites](#prerequisites)
4. [Audit Procedures](#audit-procedures)
   - [A. Page Load Performance](#a-page-load-performance)
   - [B. Bundle Size Validation](#b-bundle-size-validation)
   - [C. Animation Performance](#c-animation-performance)
   - [D. Layout Stability](#d-layout-stability)
   - [E. Runtime Performance](#e-runtime-performance)
5. [Chrome DevTools Instructions](#chrome-devtools-instructions)
6. [Lighthouse CI Audit](#lighthouse-ci-audit)
7. [Performance Regression Testing](#performance-regression-testing)
8. [Common Issues and Solutions](#common-issues-and-solutions)
9. [Reporting Template](#reporting-template)

---

## Overview

This audit validates that the Action Server frontend meets the performance requirements defined in the Community UI Enhancement specification (Spec 004). All measurements should be taken on production builds with realistic network conditions.

**Key Principles**:
- Performance audits must be conducted on **production builds** (minified, optimized)
- Network throttling should simulate real-world conditions (Fast 3G or 4G)
- CPU throttling should simulate mid-tier devices (4x slowdown)
- Multiple runs should be averaged to account for variance

---

## Performance Targets

| Metric | Target | Requirement | Priority |
|--------|--------|-------------|----------|
| **First Contentful Paint (FCP)** | ≤1.5s | SC-014 | P0 |
| **Time to Interactive (TTI)** | ≤3.5s | SC-015 | P0 |
| **Cumulative Layout Shift (CLS)** | ≤0.1 | FR-PERF-003 | P0 |
| **Bundle Size (uncompressed)** | ≤350KB | FR-PERF-001 | P0 |
| **Bundle Size (gzipped)** | ≤110KB | FR-PERF-001 | P0 |
| **Animation Frame Rate** | 60fps (16ms per frame) | FR-UI-016 | P1 |
| **Largest Contentful Paint (LCP)** | ≤2.5s | Best Practice | P1 |
| **Total Blocking Time (TBT)** | ≤200ms | Best Practice | P1 |

---

## Prerequisites

### 1. Build Production Bundle

```bash
cd action_server/frontend
npm run build
```

**Verify build output**:
- Check console for bundle size report
- Confirm no build warnings or errors
- Note the `dist/` directory size

### 2. Serve Production Build Locally

```bash
# Option 1: Using Python
python -m http.server 8000 -d dist

# Option 2: Using Node.js serve
npx serve -s dist -p 8000

# Option 3: Using action-server (preferred)
cd ../..
inv run-server --production
```

### 3. Browser Setup

Use **Google Chrome** (latest stable version) with:
- No extensions enabled (or use Incognito mode)
- Clear cache and cookies before each test
- Disable browser caching in DevTools (Network tab > "Disable cache")

---

## Audit Procedures

### A. Page Load Performance

**Objective**: Validate First Contentful Paint (FCP) ≤1.5s and Time to Interactive (TTI) ≤3.5s

#### Steps:

1. **Open Chrome DevTools**:
   - Press `F12` or `Ctrl+Shift+I` (Windows/Linux) / `Cmd+Option+I` (Mac)
   - Navigate to the **Performance** tab

2. **Configure Network and CPU Throttling**:
   - Click the gear icon (⚙️) in Performance tab
   - Set **Network**: `Fast 3G` (or `Slow 4G` for more realistic mobile)
   - Set **CPU**: `4x slowdown` (simulates mid-tier mobile device)

3. **Record Page Load**:
   - Click the **Record** button (circle icon) or press `Ctrl+E`
   - Navigate to `http://localhost:8000` in the browser
   - Wait for page to fully load (all spinners gone, content visible)
   - Click **Stop** recording (or press `Ctrl+E` again)

4. **Analyze Metrics**:
   - In the Performance recording, look for the **Timings** section
   - Find the following markers:
     - **FCP** (First Contentful Paint): Should be ≤1.5s
     - **LCP** (Largest Contentful Paint): Should be ≤2.5s
     - **TTI** (Time to Interactive): Should be ≤3.5s

   **Screenshot of Performance Timeline**:
   ```
   | 0s          | 1.5s (FCP)  | 2.5s (LCP)  | 3.5s (TTI)  | 5s
   |-------------|-------------|-------------|-------------|---------->
   | HTML load   | First paint | Large paint | Interactive | Idle
   ```

5. **Check Long Tasks**:
   - Look for red bars in the **Main** thread timeline
   - Long tasks (>50ms) should be minimal
   - No single task should exceed 200ms

6. **Repeat Test 3 Times**:
   - Clear cache between runs
   - Average the FCP and TTI values
   - Report if any run exceeds targets

#### Checklist:
- [ ] FCP ≤1.5s (averaged over 3 runs)
- [ ] TTI ≤3.5s (averaged over 3 runs)
- [ ] LCP ≤2.5s (best practice)
- [ ] No JavaScript errors in Console
- [ ] No long tasks >200ms

---

### B. Bundle Size Validation

**Objective**: Validate total bundle size ≤350KB (uncompressed) and ≤110KB (gzipped)

#### Steps:

1. **Check Build Output**:
   ```bash
   cd action_server/frontend
   npm run build
   ```

   Look for output similar to:
   ```
   dist/assets/index-a1b2c3d4.js    120.45 kB │ gzip: 42.67 kB
   dist/assets/vendor-e5f6g7h8.js  180.23 kB │ gzip: 65.12 kB
   dist/index.html                   1.23 kB │ gzip: 0.58 kB
   ```

2. **Calculate Total Sizes**:
   ```bash
   # Uncompressed total
   du -sh dist/assets/*.js | awk '{sum+=$1} END {print sum " KB"}'

   # Or manually check dist/ folder
   ls -lh dist/assets/
   ```

3. **Verify Gzipped Size**:
   ```bash
   # Gzip all JS files and check sizes
   gzip -c dist/assets/index-*.js | wc -c
   gzip -c dist/assets/vendor-*.js | wc -c
   ```

4. **Analyze Bundle Composition** (if size exceeds target):
   ```bash
   # Use source-map-explorer or rollup-plugin-visualizer
   npm run build -- --analyze
   ```

   Check for:
   - Large dependencies that could be replaced
   - Duplicate dependencies
   - Unused code that should be tree-shaken

#### Checklist:
- [ ] Total JS bundle ≤350KB (uncompressed)
- [ ] Total JS bundle ≤110KB (gzipped)
- [ ] No duplicate dependencies in bundle
- [ ] No unexpected large libraries included

---

### C. Animation Performance

**Objective**: Validate 60fps animations (no jank, ≤16ms per frame)

#### Steps:

1. **Open Chrome DevTools**:
   - Navigate to **Performance** tab
   - Enable **Screenshots** and **Memory** checkboxes (optional)

2. **Record Animation Interactions**:
   - Click **Record**
   - Perform the following interactions:
     - Open and close a **Dialog** component (modal)
     - Open and close a **DropdownMenu**
     - Hover over **Table** rows (watch hover state transitions)
     - Hover over **Buttons** and **Input** fields
     - Scroll through long tables (if applicable)
   - Click **Stop** recording

3. **Analyze Frame Rate**:
   - Look at the **Frames** section (top of timeline)
   - Green bars = good frames (≤16ms)
   - Yellow bars = warning frames (16-50ms)
   - Red bars = dropped frames (>50ms)

4. **Check Animation Timing**:
   - Zoom into animation sections (Dialog open/close)
   - Verify animation duration is **200ms** (per FR-UI-006)
   - Verify smooth frame progression (no stuttering)

5. **Validate GPU Acceleration**:
   - In the recording, expand the **Compositor** section
   - Verify animated elements use `transform` and `opacity` (GPU-accelerated)
   - No layout thrashing (repeated Layout → Paint cycles)

6. **Test `prefers-reduced-motion`**:
   - Open Chrome DevTools > **Rendering** tab
   - Enable "Emulate CSS media feature prefers-reduced-motion"
   - Repeat animations
   - Verify animations are disabled or simplified

#### Checklist:
- [ ] All animations run at 60fps (no red frames)
- [ ] Dialog animations complete in ~200ms
- [ ] DropdownMenu animations complete in ~150ms
- [ ] No layout thrashing during animations
- [ ] `prefers-reduced-motion` disables animations correctly
- [ ] Hover transitions are smooth (200ms duration)

---

### D. Layout Stability

**Objective**: Validate Cumulative Layout Shift (CLS) ≤0.1 (no unexpected movement)

#### Steps:

1. **Run Lighthouse Audit** (see [Lighthouse CI Audit](#lighthouse-ci-audit))
   - CLS score will be reported automatically

2. **Manual Visual Test**:
   - Open page in Chrome
   - Enable DevTools > **Rendering** > "Layout Shift Regions"
   - Reload page and watch for blue highlights
   - Interact with components (open dialogs, dropdowns)

3. **Check for Common CLS Causes**:
   - Images without width/height attributes
   - Fonts loading late (FOUT/FOIT)
   - Dynamic content inserted above existing content
   - Ads or embeds without reserved space

4. **Measure CLS Programmatically**:
   ```javascript
   // Paste in Console
   let clsValue = 0;
   let clsEntries = [];
   const observer = new PerformanceObserver((list) => {
     for (const entry of list.getEntries()) {
       if (!entry.hadRecentInput) {
         clsValue += entry.value;
         clsEntries.push(entry);
       }
     }
     console.log('Current CLS:', clsValue);
   });
   observer.observe({ type: 'layout-shift', buffered: true });
   ```

5. **Test Critical User Flows**:
   - Page load (homepage, actions list)
   - Opening dialogs (form dialogs, confirmation dialogs)
   - Loading data tables (run history, logs)
   - Switching tabs or routes

#### Checklist:
- [ ] CLS ≤0.1 on initial page load
- [ ] No layout shifts when opening dialogs
- [ ] No layout shifts during data loading (skeletons/spinners used)
- [ ] Images have explicit dimensions
- [ ] Fonts load without layout shift (font-display: swap)

---

### E. Runtime Performance

**Objective**: Validate smooth interactions, no memory leaks, fast response times

#### Steps:

1. **Test Table Rendering Performance**:
   - Navigate to **Run History** or **Logs** page with 100+ entries
   - Open DevTools > **Performance** tab
   - Record while scrolling through the table
   - Check for:
     - Smooth scrolling (60fps)
     - No excessive re-renders
     - Virtual scrolling if list is very long (>500 items)

2. **Test Memory Usage**:
   - Open DevTools > **Memory** tab
   - Take a heap snapshot
   - Perform user actions (open/close dialogs, navigate pages)
   - Take another heap snapshot
   - Compare snapshots:
     - Memory should not grow excessively
     - No detached DOM nodes (memory leaks)

3. **Test Event Handler Performance**:
   - Open DevTools > **Performance** tab
   - Record while clicking buttons, opening dropdowns
   - Verify event handlers execute in <10ms
   - No redundant event listeners

4. **Test API Response Times** (if applicable):
   - Open DevTools > **Network** tab
   - Trigger API calls (load actions, run action)
   - Check response times:
     - GET requests: <500ms
     - POST requests: <1000ms

#### Checklist:
- [ ] Scrolling through 100+ item tables is smooth (60fps)
- [ ] No memory leaks after 5 minutes of interaction
- [ ] Event handlers respond in <10ms
- [ ] No excessive re-renders (check React DevTools Profiler)
- [ ] API calls complete within reasonable time

---

## Chrome DevTools Instructions

### Quick Reference

#### 1. Performance Panel
- **Open**: `F12` > **Performance** tab
- **Record**: Click red circle or `Ctrl+E`
- **Throttling**: Gear icon > Set Network/CPU
- **Metrics**: Look for FCP, LCP, TTI in Timings section

#### 2. Network Panel
- **Open**: `F12` > **Network** tab
- **Disable Cache**: Check "Disable cache"
- **Throttling**: Dropdown > "Fast 3G" or "Slow 4G"
- **Filter**: JS, CSS, Img, XHR, All
- **Bundle Size**: Look at "Size" column (transferred vs. resource size)

#### 3. Lighthouse Panel
- **Open**: `F12` > **Lighthouse** tab
- **Mode**: "Navigation" (for page load)
- **Categories**: Check "Performance" and "Accessibility"
- **Device**: Desktop or Mobile
- **Throttling**: Simulated or Applied (use Simulated for consistency)
- **Run Audit**: Click "Analyze page load"

#### 4. Rendering Panel
- **Open**: `F12` > More tools (⋮) > **Rendering**
- **Layout Shifts**: Enable "Layout Shift Regions"
- **Reduced Motion**: Enable "Emulate CSS media feature prefers-reduced-motion"
- **Paint Flashing**: Enable "Paint flashing" to see repaint regions

#### 5. Coverage Panel
- **Open**: `F12` > More tools (⋮) > **Coverage**
- **Record**: Click "Start instrumenting coverage"
- **Use App**: Interact with the application
- **Stop**: Click red circle
- **Analyze**: Red bars = unused code (potential for tree-shaking)

---

## Lighthouse CI Audit

### Automated Performance Testing

#### Setup:

1. **Install Lighthouse CI**:
   ```bash
   npm install -g @lhci/cli
   ```

2. **Run Lighthouse Audit**:
   ```bash
   cd action_server/frontend
   npm run build

   # Start local server
   npx serve -s dist -p 8000 &

   # Run Lighthouse
   lhci autorun --config=.lighthouserc.json
   ```

3. **Check Configuration** (`.lighthouserc.json`):
   ```json
   {
     "ci": {
       "collect": {
         "url": ["http://localhost:8000"],
         "numberOfRuns": 3,
         "settings": {
           "preset": "desktop",
           "throttlingMethod": "simulate"
         }
       },
       "assert": {
         "assertions": {
           "categories:performance": ["error", { "minScore": 0.9 }],
           "categories:accessibility": ["error", { "minScore": 0.9 }],
           "first-contentful-paint": ["error", { "maxNumericValue": 1500 }],
           "interactive": ["error", { "maxNumericValue": 3500 }],
           "cumulative-layout-shift": ["error", { "maxNumericValue": 0.1 }]
         }
       }
     }
   }
   ```

#### Interpreting Results:

- **Performance Score**: Should be ≥90 (green)
- **FCP**: Should be ≤1.5s (green)
- **TTI**: Should be ≤3.5s (green)
- **CLS**: Should be ≤0.1 (green)

**Red flags**:
- Performance score <90
- Any metric in red/orange
- Opportunities section shows large savings (>50KB)

---

## Performance Regression Testing

### Baseline Capture

1. **Establish Baseline** (before changes):
   ```bash
   # Run Lighthouse and save results
   lhci autorun --config=.lighthouserc.json --upload.target=filesystem

   # Or manually save DevTools Performance recording
   # File > Save profile...
   ```

2. **Make Changes** (implement new features)

3. **Re-run Tests** (after changes):
   ```bash
   lhci autorun --config=.lighthouserc.json
   ```

4. **Compare Results**:
   - FCP/TTI should not increase by >10%
   - Bundle size should not increase by >10%
   - No new layout shifts introduced

### CI Integration

Add to `.github/workflows/frontend-build.yml`:

```yaml
- name: Run Lighthouse CI
  run: |
    npm run build
    npx serve -s dist -p 8000 &
    lhci autorun --config=.lighthouserc.json
    kill %1

- name: Check Bundle Size
  run: |
    BUNDLE_SIZE=$(du -sb dist/assets/*.js | awk '{sum+=$1} END {print sum}')
    if [ "$BUNDLE_SIZE" -gt 358400 ]; then
      echo "Bundle size exceeds 350KB: $BUNDLE_SIZE bytes"
      exit 1
    fi
```

---

## Common Issues and Solutions

### Issue 1: FCP >1.5s

**Symptoms**: First Contentful Paint takes too long

**Causes**:
- Large JavaScript bundle blocking rendering
- Render-blocking CSS
- Slow server response time
- No loading indicators

**Solutions**:
- Code-split routes (lazy loading)
- Inline critical CSS
- Use `<link rel="preload">` for critical resources
- Add loading spinners immediately

### Issue 2: TTI >3.5s

**Symptoms**: Page is not interactive within 3.5 seconds

**Causes**:
- Large JavaScript execution time
- Long tasks blocking main thread
- Heavy framework hydration

**Solutions**:
- Defer non-critical JavaScript
- Break up long tasks with `setTimeout`
- Use `requestIdleCallback` for low-priority work
- Optimize React components (memoization)

### Issue 3: CLS >0.1

**Symptoms**: Content jumps around during load

**Causes**:
- Images without dimensions
- Fonts loading late (FOUT)
- Dynamic content insertion

**Solutions**:
- Add `width` and `height` to images
- Use `font-display: optional` or `swap`
- Reserve space for dynamic content (skeleton screens)
- Avoid inserting content above viewport

### Issue 4: Animation Jank

**Symptoms**: Animations stutter or drop frames

**Causes**:
- Using non-GPU-accelerated properties (width, height, top, left)
- Layout thrashing (read-write-read-write)
- Too many elements animating simultaneously

**Solutions**:
- Use `transform` and `opacity` only
- Batch DOM reads and writes
- Use `will-change: transform` sparingly
- Reduce animation complexity

### Issue 5: Bundle Size >350KB

**Symptoms**: Build output exceeds size limit

**Causes**:
- Large dependencies (moment.js, lodash)
- Duplicate dependencies
- Unused code not tree-shaken

**Solutions**:
- Replace large libraries (moment → date-fns)
- Use bundle analyzer to identify duplicates
- Ensure `sideEffects: false` in package.json
- Enable minification and compression

---

## Reporting Template

### Performance Audit Report

**Date**: YYYY-MM-DD
**Auditor**: [Your Name]
**Build Version**: [Git commit SHA or version number]
**Environment**: [Local/Staging/Production]

#### Page Load Metrics

| Metric | Run 1 | Run 2 | Run 3 | Average | Target | Pass/Fail |
|--------|-------|-------|-------|---------|--------|-----------|
| FCP    |       |       |       |         | ≤1.5s  | ✅/❌     |
| LCP    |       |       |       |         | ≤2.5s  | ✅/❌     |
| TTI    |       |       |       |         | ≤3.5s  | ✅/❌     |
| CLS    |       |       |       |         | ≤0.1   | ✅/❌     |
| TBT    |       |       |       |         | ≤200ms | ✅/❌     |

#### Bundle Size

| Asset | Uncompressed | Gzipped | Target | Pass/Fail |
|-------|--------------|---------|--------|-----------|
| JS    |              |         | ≤350KB | ✅/❌     |
| CSS   |              |         | N/A    | ✅/❌     |
| Total |              |         | ≤350KB | ✅/❌     |

#### Animation Performance

| Component | Frame Rate | Duration | Smooth? | Pass/Fail |
|-----------|------------|----------|---------|-----------|
| Dialog    |            | ~200ms   | Yes/No  | ✅/❌     |
| Dropdown  |            | ~150ms   | Yes/No  | ✅/❌     |
| Table Hover|           | ~200ms   | Yes/No  | ✅/❌     |

#### Issues Found

1. **[Issue Title]**
   - **Severity**: Critical/High/Medium/Low
   - **Description**: [What is the problem?]
   - **Impact**: [How does it affect users?]
   - **Recommendation**: [How to fix?]

2. ...

#### Overall Assessment

- [ ] All targets met - Ready for production
- [ ] Minor issues - Acceptable with tracking
- [ ] Major issues - Requires fixes before release

**Summary**: [Overall assessment and next steps]

---

## Conclusion

This performance audit checklist ensures the Action Server frontend meets all performance requirements defined in Spec 004. Regular audits (at least before each release) help maintain performance standards and catch regressions early.

**Key Takeaways**:
- Always test on production builds with realistic throttling
- Automate performance testing in CI/CD pipeline
- Monitor bundle size with every commit
- Validate animations run at 60fps without jank
- Ensure no layout shifts during page load or interactions

For questions or issues, refer to:
- Spec 004: `/specs/004-community-ui-enhancement/spec.md`
- Performance Requirements: FR-PERF-001, FR-PERF-002, FR-PERF-003
- UI Requirements: FR-UI-006, FR-UI-016

**Next Steps**:
1. Run initial baseline audit before UI enhancement implementation
2. Set up Lighthouse CI in GitHub Actions workflow
3. Add bundle size checks to CI/CD pipeline
4. Schedule regular performance audits (monthly or per release)
