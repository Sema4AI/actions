import { test, expect } from '@playwright/test';

/**
 * Visual regression tests for Dialog component
 *
 * These tests document the expected visual appearance of the Dialog component
 * following a test-first approach. The Dialog component should be implemented
 * to match these visual specifications.
 *
 * Expected Dialog structure:
 * - Backdrop overlay with semi-transparent black background and blur
 * - Dialog container centered on screen with animation
 * - Header section with border-bottom separation
 * - Content section with padding
 * - Footer section with border-top separation
 * - Close button in header
 */

test.describe('Dialog Visual Regression', () => {
  test.beforeEach(async ({ page }) => {
    // Set up page with base styles matching the app's design system
    await page.setContent(`
      <!DOCTYPE html>
      <html>
        <head>
          <script src="https://cdn.tailwindcss.com"></script>
          <style>
            /* Design system CSS variables */
            :root {
              --background: 0 0% 100%;
              --foreground: 222.2 84% 4.9%;
              --border: 214.3 31.8% 91.4%;
              --radius: 0.5rem;
            }

            /* Animation keyframes */
            @keyframes dialogFadeIn {
              from {
                opacity: 0;
              }
              to {
                opacity: 1;
              }
            }

            @keyframes dialogSlideIn {
              from {
                transform: translate(-50%, -45%) scale(0.95);
                opacity: 0;
              }
              to {
                transform: translate(-50%, -50%) scale(1);
                opacity: 1;
              }
            }

            .dialog-backdrop {
              animation: dialogFadeIn 150ms ease-out;
            }

            .dialog-content {
              animation: dialogSlideIn 150ms ease-out;
            }
          </style>
        </head>
        <body>
          <div id="root"></div>
        </body>
      </html>
    `);
  });

  test('Dialog open state - basic structure', async ({ page }) => {
    // Create Dialog with basic structure
    await page.evaluate(() => {
      const root = document.getElementById('root');
      if (!root) return;

      root.innerHTML = `
        <div class="dialog-backdrop fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
          <div class="dialog-content bg-white rounded-lg shadow-lg w-full max-w-md mx-4 relative"
               style="position: fixed; left: 50%; top: 50%; transform: translate(-50%, -50%);">
            <div class="dialog-header border-b px-6 py-4">
              <h2 class="text-lg font-semibold">Dialog Title</h2>
              <button class="absolute top-4 right-4 text-gray-500 hover:text-gray-700">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>
            <div class="dialog-body px-6 py-4">
              <p class="text-sm text-gray-600">This is the dialog content area.</p>
            </div>
            <div class="dialog-footer border-t px-6 py-4 flex justify-end gap-2">
              <button class="px-4 py-2 text-sm border border-gray-300 rounded hover:bg-gray-50">Cancel</button>
              <button class="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">Confirm</button>
            </div>
          </div>
        </div>
      `;
    });

    await expect(page).toHaveScreenshot('dialog-open-basic.png', {
      maxDiffPixels: 100,
    });
  });

  test('Dialog backdrop - opacity and blur', async ({ page }) => {
    // Test backdrop visual appearance
    await page.evaluate(() => {
      const root = document.getElementById('root');
      if (!root) return;

      // Add some background content to verify backdrop blur effect
      root.innerHTML = `
        <div style="padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
          <h1 style="color: white; font-size: 24px; margin-bottom: 16px;">Background Content</h1>
          <p style="color: white;">This content should be blurred and darkened by the dialog backdrop.</p>
          <div style="margin-top: 20px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;">
            <div style="background: white; height: 100px; border-radius: 8px;"></div>
            <div style="background: white; height: 100px; border-radius: 8px;"></div>
            <div style="background: white; height: 100px; border-radius: 8px;"></div>
          </div>
        </div>
        <div class="dialog-backdrop fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
          <div class="dialog-content bg-white rounded-lg shadow-lg w-full max-w-sm mx-4"
               style="position: fixed; left: 50%; top: 50%; transform: translate(-50%, -50%);">
            <div class="px-6 py-4">
              <h2 class="text-lg font-semibold mb-2">Dialog with Backdrop</h2>
              <p class="text-sm text-gray-600">Notice the blurred background</p>
            </div>
          </div>
        </div>
      `;
    });

    await expect(page).toHaveScreenshot('dialog-backdrop-blur.png', {
      maxDiffPixels: 100,
    });
  });

  test('Dialog header with border separation', async ({ page }) => {
    // Focus on header section with close button
    await page.evaluate(() => {
      const root = document.getElementById('root');
      if (!root) return;

      root.innerHTML = `
        <div class="dialog-backdrop fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
          <div class="dialog-content bg-white rounded-lg shadow-lg w-full max-w-md mx-4"
               style="position: fixed; left: 50%; top: 50%; transform: translate(-50%, -50%);">
            <div class="dialog-header border-b border-gray-200 px-6 py-4 relative">
              <h2 class="text-lg font-semibold pr-8">Dialog with Header Border</h2>
              <button class="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>
            <div class="dialog-body px-6 py-4">
              <p class="text-sm text-gray-600">The header has a distinct border separation from the content.</p>
            </div>
          </div>
        </div>
      `;
    });

    await expect(page).toHaveScreenshot('dialog-header-border.png', {
      maxDiffPixels: 100,
    });
  });

  test('Dialog footer with border separation', async ({ page }) => {
    // Focus on footer section with action buttons
    await page.evaluate(() => {
      const root = document.getElementById('root');
      if (!root) return;

      root.innerHTML = `
        <div class="dialog-backdrop fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
          <div class="dialog-content bg-white rounded-lg shadow-lg w-full max-w-md mx-4"
               style="position: fixed; left: 50%; top: 50%; transform: translate(-50%, -50%);">
            <div class="dialog-header border-b border-gray-200 px-6 py-4">
              <h2 class="text-lg font-semibold">Confirm Action</h2>
            </div>
            <div class="dialog-body px-6 py-4">
              <p class="text-sm text-gray-600">Are you sure you want to proceed with this action?</p>
            </div>
            <div class="dialog-footer border-t border-gray-200 px-6 py-4 flex justify-end gap-3">
              <button class="px-4 py-2 text-sm font-medium border border-gray-300 rounded-md hover:bg-gray-50 transition-colors">
                Cancel
              </button>
              <button class="px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors">
                Confirm
              </button>
            </div>
          </div>
        </div>
      `;
    });

    await expect(page).toHaveScreenshot('dialog-footer-border.png', {
      maxDiffPixels: 100,
    });
  });

  test('Dialog animation - initial frame', async ({ page }) => {
    // Capture animation initial state (start of slide-in)
    await page.evaluate(() => {
      const root = document.getElementById('root');
      if (!root) return;

      root.innerHTML = `
        <div class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center"
             style="opacity: 0.3;">
          <div class="bg-white rounded-lg shadow-lg w-full max-w-md mx-4"
               style="position: fixed; left: 50%; top: 50%; transform: translate(-50%, -45%) scale(0.95); opacity: 0.5;">
            <div class="border-b border-gray-200 px-6 py-4">
              <h2 class="text-lg font-semibold">Animation Start</h2>
            </div>
            <div class="px-6 py-4">
              <p class="text-sm text-gray-600">Dialog appears with slide-in animation</p>
            </div>
          </div>
        </div>
      `;
    });

    await expect(page).toHaveScreenshot('dialog-animation-start.png', {
      maxDiffPixels: 100,
    });
  });

  test('Dialog animation - mid frame', async ({ page }) => {
    // Capture animation mid state
    await page.evaluate(() => {
      const root = document.getElementById('root');
      if (!root) return;

      root.innerHTML = `
        <div class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center"
             style="opacity: 0.7;">
          <div class="bg-white rounded-lg shadow-lg w-full max-w-md mx-4"
               style="position: fixed; left: 50%; top: 50%; transform: translate(-50%, -48%) scale(0.98); opacity: 0.75;">
            <div class="border-b border-gray-200 px-6 py-4">
              <h2 class="text-lg font-semibold">Animation Mid</h2>
            </div>
            <div class="px-6 py-4">
              <p class="text-sm text-gray-600">Dialog transitioning into view</p>
            </div>
          </div>
        </div>
      `;
    });

    await expect(page).toHaveScreenshot('dialog-animation-mid.png', {
      maxDiffPixels: 100,
    });
  });

  test('Dialog animation - end frame', async ({ page }) => {
    // Capture animation end state (fully visible)
    await page.evaluate(() => {
      const root = document.getElementById('root');
      if (!root) return;

      root.innerHTML = `
        <div class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center"
             style="opacity: 1;">
          <div class="bg-white rounded-lg shadow-lg w-full max-w-md mx-4"
               style="position: fixed; left: 50%; top: 50%; transform: translate(-50%, -50%) scale(1); opacity: 1;">
            <div class="border-b border-gray-200 px-6 py-4">
              <h2 class="text-lg font-semibold">Animation Complete</h2>
            </div>
            <div class="px-6 py-4">
              <p class="text-sm text-gray-600">Dialog fully visible and animated in</p>
            </div>
          </div>
        </div>
      `;
    });

    await expect(page).toHaveScreenshot('dialog-animation-end.png', {
      maxDiffPixels: 100,
    });
  });

  test('Dialog sizes - small', async ({ page }) => {
    // Test small dialog variant
    await page.evaluate(() => {
      const root = document.getElementById('root');
      if (!root) return;

      root.innerHTML = `
        <div class="dialog-backdrop fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
          <div class="dialog-content bg-white rounded-lg shadow-lg w-full max-w-sm mx-4"
               style="position: fixed; left: 50%; top: 50%; transform: translate(-50%, -50%);">
            <div class="border-b border-gray-200 px-4 py-3">
              <h2 class="text-base font-semibold">Small Dialog</h2>
            </div>
            <div class="px-4 py-3">
              <p class="text-sm text-gray-600">Compact dialog for simple confirmations.</p>
            </div>
            <div class="border-t border-gray-200 px-4 py-3 flex justify-end gap-2">
              <button class="px-3 py-1.5 text-sm border border-gray-300 rounded">Cancel</button>
              <button class="px-3 py-1.5 text-sm bg-blue-600 text-white rounded">OK</button>
            </div>
          </div>
        </div>
      `;
    });

    await expect(page).toHaveScreenshot('dialog-size-small.png', {
      maxDiffPixels: 100,
    });
  });

  test('Dialog sizes - medium', async ({ page }) => {
    // Test medium dialog variant (default)
    await page.evaluate(() => {
      const root = document.getElementById('root');
      if (!root) return;

      root.innerHTML = `
        <div class="dialog-backdrop fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
          <div class="dialog-content bg-white rounded-lg shadow-lg w-full max-w-md mx-4"
               style="position: fixed; left: 50%; top: 50%; transform: translate(-50%, -50%);">
            <div class="border-b border-gray-200 px-6 py-4">
              <h2 class="text-lg font-semibold">Medium Dialog</h2>
            </div>
            <div class="px-6 py-4">
              <p class="text-sm text-gray-600 mb-4">Standard dialog size for most use cases.</p>
              <p class="text-sm text-gray-600">Can accommodate moderate amounts of content.</p>
            </div>
            <div class="border-t border-gray-200 px-6 py-4 flex justify-end gap-3">
              <button class="px-4 py-2 text-sm border border-gray-300 rounded-md">Cancel</button>
              <button class="px-4 py-2 text-sm bg-blue-600 text-white rounded-md">Confirm</button>
            </div>
          </div>
        </div>
      `;
    });

    await expect(page).toHaveScreenshot('dialog-size-medium.png', {
      maxDiffPixels: 100,
    });
  });

  test('Dialog sizes - large', async ({ page }) => {
    // Test large dialog variant
    await page.evaluate(() => {
      const root = document.getElementById('root');
      if (!root) return;

      root.innerHTML = `
        <div class="dialog-backdrop fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
          <div class="dialog-content bg-white rounded-lg shadow-lg w-full max-w-2xl mx-4"
               style="position: fixed; left: 50%; top: 50%; transform: translate(-50%, -50%);">
            <div class="border-b border-gray-200 px-6 py-4">
              <h2 class="text-xl font-semibold">Large Dialog</h2>
            </div>
            <div class="px-6 py-4">
              <p class="text-sm text-gray-600 mb-4">Large dialog for complex forms or detailed content.</p>
              <div class="grid grid-cols-2 gap-4">
                <div class="border border-gray-200 rounded p-3">
                  <h3 class="text-sm font-medium mb-2">Section 1</h3>
                  <p class="text-xs text-gray-500">Content area</p>
                </div>
                <div class="border border-gray-200 rounded p-3">
                  <h3 class="text-sm font-medium mb-2">Section 2</h3>
                  <p class="text-xs text-gray-500">Content area</p>
                </div>
              </div>
            </div>
            <div class="border-t border-gray-200 px-6 py-4 flex justify-end gap-3">
              <button class="px-4 py-2 text-sm border border-gray-300 rounded-md">Cancel</button>
              <button class="px-4 py-2 text-sm bg-blue-600 text-white rounded-md">Save</button>
            </div>
          </div>
        </div>
      `;
    });

    await expect(page).toHaveScreenshot('dialog-size-large.png', {
      maxDiffPixels: 100,
    });
  });

  test('Dialog with scrollable content', async ({ page }) => {
    // Test dialog with overflow content requiring scroll
    await page.evaluate(() => {
      const root = document.getElementById('root');
      if (!root) return;

      root.innerHTML = `
        <div class="dialog-backdrop fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
          <div class="dialog-content bg-white rounded-lg shadow-lg w-full max-w-md mx-4"
               style="position: fixed; left: 50%; top: 50%; transform: translate(-50%, -50%); max-height: 80vh; display: flex; flex-direction: column;">
            <div class="border-b border-gray-200 px-6 py-4 flex-shrink-0">
              <h2 class="text-lg font-semibold">Scrollable Dialog</h2>
            </div>
            <div class="px-6 py-4 overflow-y-auto flex-grow" style="max-height: 400px;">
              <p class="text-sm text-gray-600 mb-4">This dialog has scrollable content.</p>
              ${Array.from({ length: 20 }, (_, i) =>
                `<p class="text-sm text-gray-600 mb-2">Content line ${i + 1}</p>`
              ).join('')}
            </div>
            <div class="border-t border-gray-200 px-6 py-4 flex-shrink-0 flex justify-end gap-3">
              <button class="px-4 py-2 text-sm border border-gray-300 rounded-md">Close</button>
            </div>
          </div>
        </div>
      `;
    });

    await expect(page).toHaveScreenshot('dialog-scrollable.png', {
      maxDiffPixels: 100,
    });
  });

  test('Dialog close button hover state', async ({ page }) => {
    // Test close button hover styling
    await page.evaluate(() => {
      const root = document.getElementById('root');
      if (!root) return;

      root.innerHTML = `
        <div class="dialog-backdrop fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
          <div class="dialog-content bg-white rounded-lg shadow-lg w-full max-w-md mx-4"
               style="position: fixed; left: 50%; top: 50%; transform: translate(-50%, -50%);">
            <div class="border-b border-gray-200 px-6 py-4 relative">
              <h2 class="text-lg font-semibold pr-8">Hover State Test</h2>
              <button class="absolute top-4 right-4 text-gray-600 hover:text-gray-900 transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>
            <div class="px-6 py-4">
              <p class="text-sm text-gray-600">Hover over the close button to see the color change.</p>
            </div>
          </div>
        </div>
      `;
    });

    // Hover over close button
    const closeButton = page.locator('.dialog-header button');
    await closeButton.hover();

    await expect(page).toHaveScreenshot('dialog-close-button-hover.png', {
      maxDiffPixels: 100,
    });
  });

  test('Dialog without header', async ({ page }) => {
    // Test dialog variant without header section
    await page.evaluate(() => {
      const root = document.getElementById('root');
      if (!root) return;

      root.innerHTML = `
        <div class="dialog-backdrop fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
          <div class="dialog-content bg-white rounded-lg shadow-lg w-full max-w-md mx-4 relative"
               style="position: fixed; left: 50%; top: 50%; transform: translate(-50%, -50%);">
            <button class="absolute top-4 right-4 text-gray-400 hover:text-gray-600">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
            <div class="px-6 py-4 pt-8">
              <p class="text-sm text-gray-600">Dialog without a header section.</p>
            </div>
            <div class="border-t border-gray-200 px-6 py-4 flex justify-end gap-3">
              <button class="px-4 py-2 text-sm border border-gray-300 rounded-md">Close</button>
            </div>
          </div>
        </div>
      `;
    });

    await expect(page).toHaveScreenshot('dialog-no-header.png', {
      maxDiffPixels: 100,
    });
  });

  test('Dialog without footer', async ({ page }) => {
    // Test dialog variant without footer section
    await page.evaluate(() => {
      const root = document.getElementById('root');
      if (!root) return;

      root.innerHTML = `
        <div class="dialog-backdrop fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
          <div class="dialog-content bg-white rounded-lg shadow-lg w-full max-w-md mx-4"
               style="position: fixed; left: 50%; top: 50%; transform: translate(-50%, -50%);">
            <div class="border-b border-gray-200 px-6 py-4 relative">
              <h2 class="text-lg font-semibold pr-8">Information</h2>
              <button class="absolute top-4 right-4 text-gray-400 hover:text-gray-600">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>
            <div class="px-6 py-4 pb-6">
              <p class="text-sm text-gray-600">Dialog without a footer section. Close using the X button.</p>
            </div>
          </div>
        </div>
      `;
    });

    await expect(page).toHaveScreenshot('dialog-no-footer.png', {
      maxDiffPixels: 100,
    });
  });

  test('Dialog with form content', async ({ page }) => {
    // Test dialog containing form elements
    await page.evaluate(() => {
      const root = document.getElementById('root');
      if (!root) return;

      root.innerHTML = `
        <div class="dialog-backdrop fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
          <div class="dialog-content bg-white rounded-lg shadow-lg w-full max-w-md mx-4"
               style="position: fixed; left: 50%; top: 50%; transform: translate(-50%, -50%);">
            <div class="border-b border-gray-200 px-6 py-4">
              <h2 class="text-lg font-semibold">Create New Item</h2>
            </div>
            <div class="px-6 py-4 space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input type="text" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Enter name" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[80px]" placeholder="Enter description"></textarea>
              </div>
            </div>
            <div class="border-t border-gray-200 px-6 py-4 flex justify-end gap-3">
              <button class="px-4 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50">Cancel</button>
              <button class="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700">Create</button>
            </div>
          </div>
        </div>
      `;
    });

    await expect(page).toHaveScreenshot('dialog-with-form.png', {
      maxDiffPixels: 100,
    });
  });

  test('Dialog destructive action variant', async ({ page }) => {
    // Test dialog with destructive action styling
    await page.evaluate(() => {
      const root = document.getElementById('root');
      if (!root) return;

      root.innerHTML = `
        <div class="dialog-backdrop fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
          <div class="dialog-content bg-white rounded-lg shadow-lg w-full max-w-md mx-4"
               style="position: fixed; left: 50%; top: 50%; transform: translate(-50%, -50%);">
            <div class="border-b border-gray-200 px-6 py-4">
              <h2 class="text-lg font-semibold text-red-600">Delete Confirmation</h2>
            </div>
            <div class="px-6 py-4">
              <p class="text-sm text-gray-600">Are you sure you want to delete this item? This action cannot be undone.</p>
            </div>
            <div class="border-t border-gray-200 px-6 py-4 flex justify-end gap-3">
              <button class="px-4 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50">Cancel</button>
              <button class="px-4 py-2 text-sm bg-red-600 text-white rounded-md hover:bg-red-700">Delete</button>
            </div>
          </div>
        </div>
      `;
    });

    await expect(page).toHaveScreenshot('dialog-destructive.png', {
      maxDiffPixels: 100,
    });
  });
});
