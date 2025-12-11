# Cross-Browser Testing Guide

This document outlines the cross-browser testing requirements and procedures for the Sema4.ai Action Server frontend to ensure consistent functionality and user experience across different browsers and devices.

## Browser Support Requirements

The Action Server frontend must be tested and verified to work correctly on the following browser versions:

### Desktop Browsers
- **Chrome 90+** (Chromium-based)
- **Firefox 88+** (Gecko)
- **Safari 14+** (WebKit)

### Mobile Browsers
- **iOS Safari 14+** (especially critical for modal overlays and touch interactions)
- **Chrome Mobile 90+** (Android)
- **Firefox Mobile 88+** (Android)

## Critical Testing Areas

### 1. Modal and Dialog Components

Modal and dialog components require special attention across browsers due to differences in backdrop rendering and scroll behavior.

#### Key Testing Points:
- **Backdrop-blur performance**: Safari may handle `backdrop-filter: blur()` differently than Chrome/Firefox
  - Test on Safari 14+ to ensure blur effects render smoothly
  - Check for performance degradation on lower-end devices
  - Verify backdrop opacity is sufficient if blur is not supported

- **Scroll locking**: When modal is open, background content should not scroll
  - Test body scroll lock on iOS Safari (known for scroll issues)
  - Verify touch events don't propagate to background content
  - Check for rubber-band scrolling behavior on iOS

- **Focus trap**: Focus should remain within modal when tabbing
  - Test keyboard navigation (Tab, Shift+Tab)
  - Verify Escape key closes modal
  - Ensure focus returns to trigger element on close

#### Test Procedure:
1. Open a modal/dialog component
2. Try to scroll background content (should be locked)
3. Tab through all focusable elements
4. Test Escape key to close
5. Verify backdrop blur renders correctly
6. Test on iOS Safari specifically for scroll behavior

### 2. Focus-Visible Behavior

Focus indicators must be consistent and accessible across all browsers.

#### Key Testing Points:
- **:focus-visible pseudo-class**: Modern browsers support this differently
  - Chrome 90+: Full support
  - Firefox 88+: Full support
  - Safari 14+: Limited support (may need fallback)

- **Keyboard vs. mouse interaction**: Focus rings should only appear for keyboard navigation
  - Test Tab navigation shows focus rings
  - Test mouse clicks don't show focus rings (unless appropriate)
  - Verify screen reader compatibility

#### Test Procedure:
1. Navigate site using only Tab key
2. Verify visible focus indicators on all interactive elements
3. Click elements with mouse and verify appropriate focus styling
4. Test on Safari to ensure fallback focus styles work

### 3. CSS Transitions and Animations

Animation consistency is crucial for perceived performance and polish.

#### Key Testing Points:
- **Transition timing**: Ensure animations run at same speed across browsers
  - Test modal open/close animations
  - Verify dropdown menu transitions
  - Check loading spinner and skeleton screens

- **Transform performance**: 3D transforms may render differently
  - Test on Safari for transform glitches
  - Verify GPU acceleration is working (smooth 60fps animations)
  - Check for flickering or jank

- **Reduced motion**: Respect user's motion preferences
  - Test with `prefers-reduced-motion: reduce`
  - Verify animations are disabled or simplified appropriately

#### Test Procedure:
1. Trigger all animated components
2. Record with DevTools performance monitor
3. Verify 60fps on all browsers
4. Enable reduced motion in OS settings and retest

### 4. Mobile Touch Targets

Touch targets must meet accessibility guidelines for mobile usability.

#### Key Testing Points:
- **Minimum size: 44px x 44px** (WCAG 2.5.5 Level AAA guideline)
  - All buttons must meet minimum size
  - Icon buttons need sufficient padding
  - Links in text may need increased tap area

- **Touch spacing**: Minimum 8px spacing between adjacent targets
  - Test densely packed button groups
  - Verify dropdown menus have adequate spacing
  - Check form inputs and labels

#### Test Procedure:
1. Use device emulation at 375px width (iPhone SE)
2. Enable "Show rulers" in DevTools
3. Measure all interactive elements
4. Test actual touch interaction on physical devices
5. Verify no accidental taps on adjacent elements

## Device Emulation Setup

### Chrome DevTools Device Toolbar

1. **Open DevTools**: Press `F12` or right-click and select "Inspect"
2. **Enable Device Toolbar**: Press `Ctrl+Shift+M` (Windows/Linux) or `Cmd+Shift+M` (Mac)
3. **Select Preset Device**: Choose from dropdown or create custom dimensions
4. **Enable Touch Simulation**: Click device toolbar settings (three dots) and enable "Show rulers"

### Recommended Test Viewports

#### Mobile (Portrait)
- **iPhone SE**: 375px x 667px (minimum mobile width)
- **iPhone 12 Pro**: 390px x 844px (common modern size)
- **Pixel 5**: 393px x 851px (Android reference)

#### Tablet
- **iPad Mini**: 768px x 1024px (small tablet)
- **iPad Pro**: 1024px x 1366px (large tablet)

#### Desktop
- **Small Desktop**: 1280px x 720px (minimum desktop)
- **Standard Desktop**: 1920px x 1080px (common size)
- **Large Desktop**: 2560px x 1440px (high-res)

## Touch Target Testing Procedure

### Using Chrome DevTools

1. **Open Device Toolbar**: `Ctrl+Shift+M` / `Cmd+Shift+M`
2. **Set Viewport**: 375px width (iPhone SE)
3. **Enable Rulers**: Device toolbar menu > Show rulers
4. **Measure Elements**:
   ```
   - Click element to inspect
   - Check computed height/width in Styles panel
   - Verify minimum 44px x 44px
   ```

5. **Enable Touch Simulation**:
   - Device toolbar menu > Add device pixel ratio
   - Set DPR to 2 or 3 for realistic mobile simulation

6. **Test Interactions**:
   - Use mouse to simulate touch events
   - Try tapping adjacent elements rapidly
   - Verify correct element receives interaction

### Physical Device Testing

While emulation is useful, physical device testing is essential:

1. **iOS Safari Testing** (Critical):
   - Test on actual iPhone/iPad if possible
   - Focus on modal scroll behavior
   - Verify touch target sizes feel comfortable
   - Check for rubber-band scrolling issues

2. **Android Chrome Testing**:
   - Test on physical Android device
   - Verify touch responsiveness
   - Check for any Android-specific rendering issues

## Automated Testing

### Browser Stack Integration

Consider using BrowserStack or similar services for automated cross-browser testing:

```bash
# Example: Run Playwright tests across browsers
npm run test:visual -- --project=chromium --project=firefox --project=webkit
```

### Visual Regression Testing

Use Playwright for visual regression testing:

```bash
# Run visual regression tests
npm run test:visual

# Update snapshots if changes are intentional
npm run test:visual -- --update-snapshots
```

## Common Cross-Browser Issues

### Safari-Specific Issues

1. **Backdrop Blur**: May not render or perform poorly
   - **Solution**: Provide fallback solid background with sufficient opacity
   ```css
   .backdrop {
     backdrop-filter: blur(8px);
     /* Fallback for Safari */
     background-color: rgba(0, 0, 0, 0.5);
   }
   @supports (backdrop-filter: blur(8px)) {
     .backdrop {
       background-color: rgba(0, 0, 0, 0.3);
     }
   }
   ```

2. **Focus-Visible**: Limited support before Safari 15.4
   - **Solution**: Use Polyfill or fallback to `:focus`
   ```css
   button:focus-visible {
     outline: 2px solid blue;
   }
   /* Fallback for older Safari */
   button:focus {
     outline: 2px solid blue;
   }
   button:active {
     outline: none;
   }
   ```

3. **iOS Modal Scroll**: Background scrolls when modal is open
   - **Solution**: Use body scroll lock library or fixed positioning
   ```javascript
   // Lock body scroll when modal opens
   document.body.style.overflow = 'hidden';
   document.body.style.position = 'fixed';
   document.body.style.width = '100%';
   ```

### Firefox-Specific Issues

1. **Smooth Scrolling**: May behave differently than Chrome
   - **Solution**: Test scroll animations explicitly

2. **Flexbox Rendering**: Minor differences in flex-basis calculations
   - **Solution**: Use explicit min-width/max-width when needed

### Chrome-Specific Issues

1. **Form Autofill Styling**: Chrome applies default blue background
   - **Solution**: Override with custom styling
   ```css
   input:-webkit-autofill {
     -webkit-box-shadow: 0 0 0 1000px white inset;
   }
   ```

## Testing Checklist

Use this checklist for each release:

### Pre-Release Testing

- [ ] Test all modal/dialog components on Chrome 90+
- [ ] Test all modal/dialog components on Firefox 88+
- [ ] Test all modal/dialog components on Safari 14+ (especially iOS)
- [ ] Verify backdrop-blur performance on Safari
- [ ] Test focus-visible behavior on all browsers
- [ ] Verify keyboard navigation (Tab, Escape) works consistently
- [ ] Test CSS transitions/animations on all browsers
- [ ] Verify 60fps animation performance
- [ ] Test with `prefers-reduced-motion` enabled
- [ ] Measure all touch targets at 375px viewport width
- [ ] Verify minimum 44px x 44px touch targets
- [ ] Test touch target spacing (minimum 8px)
- [ ] Test on physical iOS device (if available)
- [ ] Test on physical Android device (if available)
- [ ] Run automated visual regression tests
- [ ] Verify no console errors in any browser

### Mobile-Specific Testing

- [ ] Test at 375px width (iPhone SE)
- [ ] Verify horizontal scrolling not required
- [ ] Test modal scroll behavior on iOS Safari
- [ ] Verify touch targets comfortable to tap
- [ ] Test pinch-to-zoom behavior
- [ ] Check viewport meta tag configuration
- [ ] Verify text remains legible at mobile sizes
- [ ] Test form inputs work correctly on mobile keyboards

### Accessibility Testing

- [ ] Test with screen reader (VoiceOver on Safari, NVDA on Firefox)
- [ ] Verify ARIA labels are announced correctly
- [ ] Test keyboard-only navigation
- [ ] Verify focus order is logical
- [ ] Check color contrast ratios meet WCAG AA standards
- [ ] Test with browser zoom at 200%

## Reporting Issues

When reporting cross-browser issues, include:

1. **Browser and Version**: e.g., "Safari 14.1 on iOS 14.5"
2. **Device**: e.g., "iPhone 12, Physical device" or "Chrome DevTools emulation"
3. **Viewport Size**: e.g., "375px x 667px"
4. **Steps to Reproduce**: Clear, numbered steps
5. **Expected Behavior**: What should happen
6. **Actual Behavior**: What actually happens
7. **Screenshots/Video**: Visual evidence of the issue
8. **Console Errors**: Any JavaScript errors from DevTools

## Resources

- [Can I Use](https://caniuse.com/): Browser compatibility tables
- [MDN Web Docs](https://developer.mozilla.org/): Browser compatibility info
- [WebKit Feature Status](https://webkit.org/status/): Safari/iOS feature tracking
- [Chrome Platform Status](https://chromestatus.com/): Chrome feature tracking
- [Firefox Release Notes](https://www.mozilla.org/firefox/releases/): Firefox features
- [WCAG 2.5.5 Touch Target Size](https://www.w3.org/WAI/WCAG21/Understanding/target-size.html): Accessibility guidelines
- [BrowserStack](https://www.browserstack.com/): Cross-browser testing service

## Continuous Integration

Consider adding cross-browser testing to CI pipeline:

```yaml
# Example GitHub Actions workflow
name: Cross-Browser Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      - run: npm ci
      - run: npm run build
      - run: npx playwright install --with-deps
      - run: npm run test:visual
```

## Maintenance

This document should be reviewed and updated:
- When browser support requirements change
- When new critical components are added
- When common issues are identified
- Quarterly review of minimum browser versions
