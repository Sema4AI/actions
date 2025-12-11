import { test, expect } from '@playwright/test';

/**
 * Visual regression tests for state indicator components
 * Tests Badge, Loading, and ErrorBanner components across multiple viewports
 */

// Helper function to inject Tailwind CSS and base styles
async function setupStyles(page: any) {
  await page.addStyleTag({
    content: `
      @tailwind base;
      @tailwind components;
      @tailwind utilities;

      * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }

      body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
        background: #ffffff;
        padding: 20px;
      }

      /* Animation for spinner */
      @keyframes spin {
        to {
          transform: rotate(360deg);
        }
      }

      .animate-spin {
        animation: spin 1s linear infinite;
      }

      /* Tailwind-like utility classes */
      .inline-flex { display: inline-flex; }
      .flex { display: flex; }
      .flex-col { flex-direction: column; }
      .flex-1 { flex: 1 1 0%; }
      .items-center { align-items: center; }
      .items-start { align-items: flex-start; }
      .justify-center { justify-content: center; }
      .gap-2 { gap: 0.5rem; }
      .gap-3 { gap: 0.75rem; }
      .gap-4 { gap: 1rem; }
      .rounded-full { border-radius: 9999px; }
      .rounded-md { border-radius: 0.375rem; }
      .border { border-width: 1px; }
      .border-4 { border-width: 4px; }
      .px-2\\.5 { padding-left: 0.625rem; padding-right: 0.625rem; }
      .py-0\\.5 { padding-top: 0.125rem; padding-bottom: 0.125rem; }
      .px-4 { padding-left: 1rem; padding-right: 1rem; }
      .py-2 { padding-top: 0.5rem; padding-bottom: 0.5rem; }
      .p-1 { padding: 0.25rem; }
      .p-4 { padding: 1rem; }
      .ml-3 { margin-left: 0.75rem; }
      .text-xs { font-size: 0.75rem; line-height: 1rem; }
      .text-sm { font-size: 0.875rem; line-height: 1.25rem; }
      .font-medium { font-weight: 500; }
      .h-4 { height: 1rem; }
      .w-4 { width: 1rem; }
      .h-5 { height: 1.25rem; }
      .w-5 { width: 1.25rem; }
      .h-8 { height: 2rem; }
      .w-8 { width: 2rem; }
      .h-10 { height: 2.5rem; }
      .h-full { height: 100%; }

      /* Badge variants */
      .bg-green-100 { background-color: #dcfce7; }
      .text-green-700 { color: #15803d; }
      .border-green-200 { border-color: #bbf7d0; }

      .bg-red-100 { background-color: #fee2e2; }
      .text-red-700 { color: #b91c1c; }
      .border-red-200 { border-color: #fecaca; }

      .bg-yellow-100 { background-color: #fef3c7; }
      .text-yellow-700 { color: #a16207; }
      .border-yellow-200 { border-color: #fde68a; }

      .bg-blue-100 { background-color: #dbeafe; }
      .text-blue-700 { color: #1d4ed8; }
      .border-blue-200 { border-color: #bfdbfe; }

      .bg-gray-100 { background-color: #f3f4f6; }
      .text-gray-700 { color: #374151; }
      .border-gray-200 { border-color: #e5e7eb; }
      .text-gray-600 { color: #4b5563; }

      /* Loading spinner */
      .border-gray-200 { border-color: #e5e7eb; }
      .border-t-blue-600 { border-top-color: #2563eb; }

      /* ErrorBanner */
      .bg-red-50 { background-color: #fef2f2; }
      .text-red-600 { color: #dc2626; }
      .text-red-500 { color: #ef4444; }

      /* Button */
      .bg-white { background-color: #ffffff; }
      .text-gray-900 { color: #111827; }
      .border-gray-300 { border-color: #d1d5db; }
      .hover\\:bg-gray-100:hover { background-color: #f3f4f6; }
      .hover\\:bg-red-100:hover { background-color: #fee2e2; }

      button {
        cursor: pointer;
        transition: all 0.2s;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        border-radius: 0.375rem;
        font-size: 0.875rem;
        font-weight: 500;
        height: 2.5rem;
        padding: 0.5rem 1rem;
      }

      button:focus-visible {
        outline: 2px solid #3b82f6;
        outline-offset: 2px;
      }

      /* Container for visual tests */
      .test-container {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        padding: 2rem;
        background: white;
      }
    `,
  });
}

test.describe('Badge Component', () => {
  test('Badge - success variant', async ({ page }) => {
    await page.setContent(`
      <div class="test-container">
        <span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-700 border border-green-200">
          Success
        </span>
      </div>
    `);
    await setupStyles(page);
    await expect(page).toHaveScreenshot('badge-success.png');
  });

  test('Badge - error variant', async ({ page }) => {
    await page.setContent(`
      <div class="test-container">
        <span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-700 border border-red-200">
          Error
        </span>
      </div>
    `);
    await setupStyles(page);
    await expect(page).toHaveScreenshot('badge-error.png');
  });

  test('Badge - warning variant', async ({ page }) => {
    await page.setContent(`
      <div class="test-container">
        <span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-700 border border-yellow-200">
          Warning
        </span>
      </div>
    `);
    await setupStyles(page);
    await expect(page).toHaveScreenshot('badge-warning.png');
  });

  test('Badge - info variant', async ({ page }) => {
    await page.setContent(`
      <div class="test-container">
        <span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-700 border border-blue-200">
          Info
        </span>
      </div>
    `);
    await setupStyles(page);
    await expect(page).toHaveScreenshot('badge-info.png');
  });

  test('Badge - neutral variant', async ({ page }) => {
    await page.setContent(`
      <div class="test-container">
        <span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-700 border border-gray-200">
          Neutral
        </span>
      </div>
    `);
    await setupStyles(page);
    await expect(page).toHaveScreenshot('badge-neutral.png');
  });

  test('Badge - all variants together', async ({ page }) => {
    await page.setContent(`
      <div class="test-container">
        <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
          <span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-700 border border-green-200">
            Success
          </span>
          <span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-700 border border-red-200">
            Error
          </span>
          <span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-700 border border-yellow-200">
            Warning
          </span>
          <span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-700 border border-blue-200">
            Info
          </span>
          <span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-700 border border-gray-200">
            Neutral
          </span>
        </div>
      </div>
    `);
    await setupStyles(page);
    await expect(page).toHaveScreenshot('badge-all-variants.png');
  });
});

test.describe('Loading Component', () => {
  test('Loading - spinner without text', async ({ page }) => {
    await page.setContent(`
      <div class="test-container">
        <div class="flex h-full items-center justify-center" style="height: 200px;">
          <div class="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-blue-600" aria-hidden></div>
        </div>
      </div>
    `);
    await setupStyles(page);
    await expect(page).toHaveScreenshot('loading-spinner-no-text.png');
  });

  test('Loading - spinner with text', async ({ page }) => {
    await page.setContent(`
      <div class="test-container">
        <div class="flex h-full items-center justify-center" style="height: 200px;">
          <div class="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-blue-600" aria-hidden></div>
          <span class="ml-3 text-sm text-gray-600">Loading data...</span>
        </div>
      </div>
    `);
    await setupStyles(page);
    await expect(page).toHaveScreenshot('loading-spinner-with-text.png');
  });

  test('Loading - timeout with retry button', async ({ page }) => {
    await page.setContent(`
      <div class="test-container">
        <div class="flex flex-col items-center justify-center gap-4" style="height: 200px;">
          <p class="text-sm text-gray-700 font-medium">Request timed out</p>
          <button class="border border-gray-300 bg-white hover:bg-gray-100 text-gray-900">
            Retry
          </button>
        </div>
      </div>
    `);
    await setupStyles(page);
    await expect(page).toHaveScreenshot('loading-timeout-retry.png');
  });

  test('Loading - timeout with retry button hovered', async ({ page }) => {
    await page.setContent(`
      <div class="test-container">
        <div class="flex flex-col items-center justify-center gap-4" style="height: 200px;">
          <p class="text-sm text-gray-700 font-medium">Request timed out</p>
          <button class="border border-gray-300 bg-white hover:bg-gray-100 text-gray-900" id="retry-btn">
            Retry
          </button>
        </div>
      </div>
    `);
    await setupStyles(page);
    await page.locator('#retry-btn').hover();
    await expect(page).toHaveScreenshot('loading-timeout-retry-hovered.png');
  });
});

test.describe('ErrorBanner Component', () => {
  test('ErrorBanner - without dismiss button', async ({ page }) => {
    await page.setContent(`
      <div class="test-container">
        <div class="bg-red-50 border border-red-200 rounded-md p-4 flex items-start gap-3">
          <svg class="h-5 w-5 text-red-600" viewBox="0 0 24 24" fill="none" aria-hidden>
            <path d="M12 9v4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
            <path d="M12 17h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
            <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2" />
          </svg>
          <p class="text-sm text-red-700 flex-1">Failed to load data. Please try again later.</p>
        </div>
      </div>
    `);
    await setupStyles(page);
    await expect(page).toHaveScreenshot('error-banner-no-dismiss.png');
  });

  test('ErrorBanner - with dismiss button', async ({ page }) => {
    await page.setContent(`
      <div class="test-container">
        <div class="bg-red-50 border border-red-200 rounded-md p-4 flex items-start gap-3">
          <svg class="h-5 w-5 text-red-600" viewBox="0 0 24 24" fill="none" aria-hidden>
            <path d="M12 9v4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
            <path d="M12 17h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
            <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2" />
          </svg>
          <p class="text-sm text-red-700 flex-1">An error occurred while processing your request.</p>
          <button class="text-red-500 hover:bg-red-100 rounded-md p-1" aria-label="Dismiss" id="dismiss-btn">
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" aria-hidden>
              <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </button>
        </div>
      </div>
    `);
    await setupStyles(page);
    await expect(page).toHaveScreenshot('error-banner-with-dismiss.png');
  });

  test('ErrorBanner - with dismiss button hovered', async ({ page }) => {
    await page.setContent(`
      <div class="test-container">
        <div class="bg-red-50 border border-red-200 rounded-md p-4 flex items-start gap-3">
          <svg class="h-5 w-5 text-red-600" viewBox="0 0 24 24" fill="none" aria-hidden>
            <path d="M12 9v4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
            <path d="M12 17h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
            <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2" />
          </svg>
          <p class="text-sm text-red-700 flex-1">Network connection error. Check your internet and try again.</p>
          <button class="text-red-500 hover:bg-red-100 rounded-md p-1" aria-label="Dismiss" id="dismiss-btn">
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" aria-hidden>
              <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </button>
        </div>
      </div>
    `);
    await setupStyles(page);
    await page.locator('#dismiss-btn').hover();
    await expect(page).toHaveScreenshot('error-banner-dismiss-hovered.png');
  });

  test('ErrorBanner - long error message', async ({ page }) => {
    await page.setContent(`
      <div class="test-container">
        <div class="bg-red-50 border border-red-200 rounded-md p-4 flex items-start gap-3">
          <svg class="h-5 w-5 text-red-600" viewBox="0 0 24 24" fill="none" aria-hidden>
            <path d="M12 9v4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
            <path d="M12 17h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
            <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2" />
          </svg>
          <p class="text-sm text-red-700 flex-1">
            Unable to complete the action due to a server error. The server encountered an unexpected condition
            that prevented it from fulfilling the request. This might be a temporary issue. Please wait a few
            moments and try again. If the problem persists, contact support.
          </p>
          <button class="text-red-500 hover:bg-red-100 rounded-md p-1" aria-label="Dismiss">
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" aria-hidden>
              <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </button>
        </div>
      </div>
    `);
    await setupStyles(page);
    await expect(page).toHaveScreenshot('error-banner-long-message.png');
  });
});

test.describe('Responsive Tests', () => {
  const viewports = [
    { name: 'mobile', width: 375, height: 667 },
    { name: 'tablet', width: 768, height: 1024 },
    { name: 'desktop', width: 1280, height: 800 },
  ];

  for (const viewport of viewports) {
    test(`All state indicators at ${viewport.name} viewport`, async ({ page }) => {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });

      await page.setContent(`
        <div class="test-container">
          <h2 style="font-size: 1.125rem; font-weight: 600; margin-bottom: 1rem;">Badges</h2>
          <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 2rem;">
            <span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-green-100 text-green-700 border border-green-200">
              Success
            </span>
            <span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-red-100 text-red-700 border border-red-200">
              Error
            </span>
            <span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-700 border border-yellow-200">
              Warning
            </span>
            <span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-blue-100 text-blue-700 border border-blue-200">
              Info
            </span>
            <span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-gray-100 text-gray-700 border border-gray-200">
              Neutral
            </span>
          </div>

          <h2 style="font-size: 1.125rem; font-weight: 600; margin-bottom: 1rem;">Loading States</h2>
          <div style="margin-bottom: 2rem;">
            <div class="flex h-full items-center justify-center" style="height: 100px; margin-bottom: 1rem;">
              <div class="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-blue-600" aria-hidden></div>
              <span class="ml-3 text-sm text-gray-600">Loading...</span>
            </div>
            <div class="flex flex-col items-center justify-center gap-4" style="height: 100px;">
              <p class="text-sm text-gray-700 font-medium">Request timed out</p>
              <button class="border border-gray-300 bg-white hover:bg-gray-100 text-gray-900">
                Retry
              </button>
            </div>
          </div>

          <h2 style="font-size: 1.125rem; font-weight: 600; margin-bottom: 1rem;">Error Banners</h2>
          <div style="display: flex; flex-direction: column; gap: 1rem;">
            <div class="bg-red-50 border border-red-200 rounded-md p-4 flex items-start gap-3">
              <svg class="h-5 w-5 text-red-600" viewBox="0 0 24 24" fill="none" aria-hidden>
                <path d="M12 9v4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                <path d="M12 17h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2" />
              </svg>
              <p class="text-sm text-red-700 flex-1">Error without dismiss button</p>
            </div>
            <div class="bg-red-50 border border-red-200 rounded-md p-4 flex items-start gap-3">
              <svg class="h-5 w-5 text-red-600" viewBox="0 0 24 24" fill="none" aria-hidden>
                <path d="M12 9v4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                <path d="M12 17h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2" />
              </svg>
              <p class="text-sm text-red-700 flex-1">Error with dismiss button</p>
              <button class="text-red-500 hover:bg-red-100 rounded-md p-1" aria-label="Dismiss">
                <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" aria-hidden>
                  <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      `);

      await setupStyles(page);
      await expect(page).toHaveScreenshot(`all-state-indicators-${viewport.name}.png`);
    });
  }
});
