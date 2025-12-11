import { test, expect } from '@playwright/test';

// Viewport sizes for responsive testing
const viewports = [
  { width: 1280, height: 800, name: 'desktop' },
  { width: 768, height: 1024, name: 'tablet' },
  { width: 375, height: 667, name: 'mobile' },
];

test.describe('Table Visual Regression Tests', () => {
  test('Table with header styling renders correctly', async ({ page }) => {
    await page.setContent(`
      <style>
        /* Import Tailwind or inline styles */
        .w-full { width: 100%; }
        .caption-bottom { caption-side: bottom; }
        .text-sm { font-size: 0.875rem; line-height: 1.25rem; }
        .text-xs { font-size: 0.75rem; line-height: 1rem; }
        .text-gray-900 { color: rgb(17 24 39); }
        .text-gray-500 { color: rgb(107 114 128); }
        .text-gray-700 { color: rgb(55 65 81); }
        .bg-gray-50 { background-color: rgb(249 250 251); }
        .border-b { border-bottom-width: 1px; }
        .border-gray-200 { border-color: rgb(229 231 235); }
        .h-11 { height: 2.75rem; }
        .px-4 { padding-left: 1rem; padding-right: 1rem; }
        .p-4 { padding: 1rem; }
        .text-left { text-align: left; }
        .align-middle { vertical-align: middle; }
        .font-medium { font-weight: 500; }
        .uppercase { text-transform: uppercase; }
        .tracking-wide { letter-spacing: 0.025em; }
        table { border-collapse: collapse; }
        tr { border-color: rgb(229 231 235); }
      </style>
      <div style="padding: 20px; font-family: system-ui, -apple-system, sans-serif;">
        <div class="w-full" style="overflow: auto;">
          <table class="w-full caption-bottom text-sm text-gray-900">
            <thead>
              <tr class="border-b bg-gray-50">
                <th class="h-11 px-4 text-left align-middle text-xs font-medium uppercase tracking-wide text-gray-500 bg-gray-50 border-b">
                  Name
                </th>
                <th class="h-11 px-4 text-left align-middle text-xs font-medium uppercase tracking-wide text-gray-500 bg-gray-50 border-b">
                  Status
                </th>
                <th class="h-11 px-4 text-left align-middle text-xs font-medium uppercase tracking-wide text-gray-500 bg-gray-50 border-b">
                  Date
                </th>
              </tr>
            </thead>
            <tbody>
              <tr class="border-b">
                <td class="p-4 align-middle text-sm text-gray-700">Action One</td>
                <td class="p-4 align-middle text-sm text-gray-700">Active</td>
                <td class="p-4 align-middle text-sm text-gray-700">2025-12-11</td>
              </tr>
              <tr class="border-b">
                <td class="p-4 align-middle text-sm text-gray-700">Action Two</td>
                <td class="p-4 align-middle text-sm text-gray-700">Pending</td>
                <td class="p-4 align-middle text-sm text-gray-700">2025-12-10</td>
              </tr>
              <tr>
                <td class="p-4 align-middle text-sm text-gray-700">Action Three</td>
                <td class="p-4 align-middle text-sm text-gray-700">Completed</td>
                <td class="p-4 align-middle text-sm text-gray-700">2025-12-09</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    `);

    await expect(page).toHaveScreenshot('table-header-styling.png');
  });

  test('Table row hover state renders correctly', async ({ page }) => {
    await page.setContent(`
      <style>
        .w-full { width: 100%; }
        .caption-bottom { caption-side: bottom; }
        .text-sm { font-size: 0.875rem; line-height: 1.25rem; }
        .text-xs { font-size: 0.75rem; line-height: 1rem; }
        .text-gray-900 { color: rgb(17 24 39); }
        .text-gray-500 { color: rgb(107 114 128); }
        .text-gray-700 { color: rgb(55 65 81); }
        .bg-gray-50 { background-color: rgb(249 250 251); }
        .border-b { border-bottom-width: 1px; }
        .h-11 { height: 2.75rem; }
        .px-4 { padding-left: 1rem; padding-right: 1rem; }
        .p-4 { padding: 1rem; }
        .text-left { text-align: left; }
        .align-middle { vertical-align: middle; }
        .font-medium { font-weight: 500; }
        .uppercase { text-transform: uppercase; }
        .tracking-wide { letter-spacing: 0.025em; }
        .cursor-pointer { cursor: pointer; }
        .transition-colors { transition-property: color, background-color, border-color; transition-duration: 150ms; }
        table { border-collapse: collapse; }
        tr { border-color: rgb(229 231 235); }
        tr:hover { background-color: rgb(249 250 251); }
      </style>
      <div style="padding: 20px; font-family: system-ui, -apple-system, sans-serif;">
        <div class="w-full" style="overflow: auto;">
          <table class="w-full caption-bottom text-sm text-gray-900">
            <thead>
              <tr class="border-b bg-gray-50">
                <th class="h-11 px-4 text-left align-middle text-xs font-medium uppercase tracking-wide text-gray-500 bg-gray-50 border-b">
                  Name
                </th>
                <th class="h-11 px-4 text-left align-middle text-xs font-medium uppercase tracking-wide text-gray-500 bg-gray-50 border-b">
                  Status
                </th>
                <th class="h-11 px-4 text-left align-middle text-xs font-medium uppercase tracking-wide text-gray-500 bg-gray-50 border-b">
                  Date
                </th>
              </tr>
            </thead>
            <tbody>
              <tr class="border-b transition-colors cursor-pointer" data-testid="row-1">
                <td class="p-4 align-middle text-sm text-gray-700">Action One</td>
                <td class="p-4 align-middle text-sm text-gray-700">Active</td>
                <td class="p-4 align-middle text-sm text-gray-700">2025-12-11</td>
              </tr>
              <tr class="border-b transition-colors cursor-pointer" data-testid="row-2">
                <td class="p-4 align-middle text-sm text-gray-700">Action Two</td>
                <td class="p-4 align-middle text-sm text-gray-700">Pending</td>
                <td class="p-4 align-middle text-sm text-gray-700">2025-12-10</td>
              </tr>
              <tr class="transition-colors cursor-pointer" data-testid="row-3">
                <td class="p-4 align-middle text-sm text-gray-700">Action Three</td>
                <td class="p-4 align-middle text-sm text-gray-700">Completed</td>
                <td class="p-4 align-middle text-sm text-gray-700">2025-12-09</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    `);

    // Hover over the second row
    const row = page.getByTestId('row-2');
    await row.hover();

    await expect(page).toHaveScreenshot('table-row-hover.png');
  });

  test('Table selected row styling renders correctly', async ({ page }) => {
    await page.setContent(`
      <style>
        .w-full { width: 100%; }
        .caption-bottom { caption-side: bottom; }
        .text-sm { font-size: 0.875rem; line-height: 1.25rem; }
        .text-xs { font-size: 0.75rem; line-height: 1rem; }
        .text-gray-900 { color: rgb(17 24 39); }
        .text-gray-500 { color: rgb(107 114 128); }
        .text-gray-700 { color: rgb(55 65 81); }
        .bg-gray-50 { background-color: rgb(249 250 251); }
        .bg-blue-50 { background-color: rgb(239 246 255); }
        .border-b { border-bottom-width: 1px; }
        .h-11 { height: 2.75rem; }
        .px-4 { padding-left: 1rem; padding-right: 1rem; }
        .p-4 { padding: 1rem; }
        .text-left { text-align: left; }
        .align-middle { vertical-align: middle; }
        .font-medium { font-weight: 500; }
        .uppercase { text-transform: uppercase; }
        .tracking-wide { letter-spacing: 0.025em; }
        .cursor-pointer { cursor: pointer; }
        .transition-colors { transition-property: color, background-color, border-color; transition-duration: 150ms; }
        table { border-collapse: collapse; }
        tr { border-color: rgb(229 231 235); }
        tr:hover { background-color: rgb(249 250 251); }
      </style>
      <div style="padding: 20px; font-family: system-ui, -apple-system, sans-serif;">
        <div class="w-full" style="overflow: auto;">
          <table class="w-full caption-bottom text-sm text-gray-900">
            <thead>
              <tr class="border-b bg-gray-50">
                <th class="h-11 px-4 text-left align-middle text-xs font-medium uppercase tracking-wide text-gray-500 bg-gray-50 border-b">
                  Name
                </th>
                <th class="h-11 px-4 text-left align-middle text-xs font-medium uppercase tracking-wide text-gray-500 bg-gray-50 border-b">
                  Status
                </th>
                <th class="h-11 px-4 text-left align-middle text-xs font-medium uppercase tracking-wide text-gray-500 bg-gray-50 border-b">
                  Date
                </th>
              </tr>
            </thead>
            <tbody>
              <tr class="border-b transition-colors cursor-pointer">
                <td class="p-4 align-middle text-sm text-gray-700">Action One</td>
                <td class="p-4 align-middle text-sm text-gray-700">Active</td>
                <td class="p-4 align-middle text-sm text-gray-700">2025-12-11</td>
              </tr>
              <tr class="border-b transition-colors cursor-pointer bg-blue-50" data-state="selected">
                <td class="p-4 align-middle text-sm text-gray-700">Action Two</td>
                <td class="p-4 align-middle text-sm text-gray-700">Pending</td>
                <td class="p-4 align-middle text-sm text-gray-700">2025-12-10</td>
              </tr>
              <tr class="transition-colors cursor-pointer">
                <td class="p-4 align-middle text-sm text-gray-700">Action Three</td>
                <td class="p-4 align-middle text-sm text-gray-700">Completed</td>
                <td class="p-4 align-middle text-sm text-gray-700">2025-12-09</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    `);

    await expect(page).toHaveScreenshot('table-selected-row.png');
  });

  test('Table empty state renders correctly', async ({ page }) => {
    await page.setContent(`
      <style>
        .w-full { width: 100%; }
        .caption-bottom { caption-side: bottom; }
        .text-sm { font-size: 0.875rem; line-height: 1.25rem; }
        .text-xs { font-size: 0.75rem; line-height: 1rem; }
        .text-gray-900 { color: rgb(17 24 39); }
        .text-gray-500 { color: rgb(107 114 128); }
        .text-gray-700 { color: rgb(55 65 81); }
        .bg-gray-50 { background-color: rgb(249 250 251); }
        .border-b { border-bottom-width: 1px; }
        .h-11 { height: 2.75rem; }
        .px-4 { padding-left: 1rem; padding-right: 1rem; }
        .p-4 { padding: 1rem; }
        .p-12 { padding: 3rem; }
        .text-left { text-align: left; }
        .text-center { text-align: center; }
        .align-middle { vertical-align: middle; }
        .font-medium { font-weight: 500; }
        .uppercase { text-transform: uppercase; }
        .tracking-wide { letter-spacing: 0.025em; }
        .flex { display: flex; }
        .items-center { align-items: center; }
        .justify-center { justify-content: center; }
        table { border-collapse: collapse; }
        tr { border-color: rgb(229 231 235); }
      </style>
      <div style="padding: 20px; font-family: system-ui, -apple-system, sans-serif;">
        <div class="w-full" style="overflow: auto;">
          <table class="w-full caption-bottom text-sm text-gray-900">
            <thead>
              <tr class="border-b bg-gray-50">
                <th class="h-11 px-4 text-left align-middle text-xs font-medium uppercase tracking-wide text-gray-500 bg-gray-50 border-b">
                  Name
                </th>
                <th class="h-11 px-4 text-left align-middle text-xs font-medium uppercase tracking-wide text-gray-500 bg-gray-50 border-b">
                  Status
                </th>
                <th class="h-11 px-4 text-left align-middle text-xs font-medium uppercase tracking-wide text-gray-500 bg-gray-50 border-b">
                  Date
                </th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td colspan="3">
                  <div class="flex items-center justify-center p-12 text-center text-sm text-gray-500">
                    No data available
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    `);

    await expect(page).toHaveScreenshot('table-empty-state.png');
  });

  test('Table with footer renders correctly', async ({ page }) => {
    await page.setContent(`
      <style>
        .w-full { width: 100%; }
        .caption-bottom { caption-side: bottom; }
        .text-sm { font-size: 0.875rem; line-height: 1.25rem; }
        .text-xs { font-size: 0.75rem; line-height: 1rem; }
        .text-gray-900 { color: rgb(17 24 39); }
        .text-gray-500 { color: rgb(107 114 128); }
        .text-gray-700 { color: rgb(55 65 81); }
        .bg-gray-50 { background-color: rgb(249 250 251); }
        .bg-gray-100 { background-color: rgb(243 244 246); }
        .border-b { border-bottom-width: 1px; }
        .h-11 { height: 2.75rem; }
        .px-4 { padding-left: 1rem; padding-right: 1rem; }
        .p-4 { padding: 1rem; }
        .text-left { text-align: left; }
        .align-middle { vertical-align: middle; }
        .font-medium { font-weight: 500; }
        .uppercase { text-transform: uppercase; }
        .tracking-wide { letter-spacing: 0.025em; }
        table { border-collapse: collapse; }
        tr { border-color: rgb(229 231 235); }
      </style>
      <div style="padding: 20px; font-family: system-ui, -apple-system, sans-serif;">
        <div class="w-full" style="overflow: auto;">
          <table class="w-full caption-bottom text-sm text-gray-900">
            <thead>
              <tr class="border-b bg-gray-50">
                <th class="h-11 px-4 text-left align-middle text-xs font-medium uppercase tracking-wide text-gray-500 bg-gray-50 border-b">
                  Item
                </th>
                <th class="h-11 px-4 text-left align-middle text-xs font-medium uppercase tracking-wide text-gray-500 bg-gray-50 border-b">
                  Quantity
                </th>
                <th class="h-11 px-4 text-left align-middle text-xs font-medium uppercase tracking-wide text-gray-500 bg-gray-50 border-b">
                  Price
                </th>
              </tr>
            </thead>
            <tbody>
              <tr class="border-b">
                <td class="p-4 align-middle text-sm text-gray-700">Widget A</td>
                <td class="p-4 align-middle text-sm text-gray-700">10</td>
                <td class="p-4 align-middle text-sm text-gray-700">$100</td>
              </tr>
              <tr class="border-b">
                <td class="p-4 align-middle text-sm text-gray-700">Widget B</td>
                <td class="p-4 align-middle text-sm text-gray-700">5</td>
                <td class="p-4 align-middle text-sm text-gray-700">$50</td>
              </tr>
            </tbody>
            <tfoot class="bg-gray-100 font-medium text-gray-900">
              <tr>
                <td class="p-4 align-middle text-sm" colspan="2">Total</td>
                <td class="p-4 align-middle text-sm">$150</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    `);

    await expect(page).toHaveScreenshot('table-with-footer.png');
  });

  test('Table with caption renders correctly', async ({ page }) => {
    await page.setContent(`
      <style>
        .w-full { width: 100%; }
        .caption-bottom { caption-side: bottom; }
        .text-sm { font-size: 0.875rem; line-height: 1.25rem; }
        .text-xs { font-size: 0.75rem; line-height: 1rem; }
        .text-gray-900 { color: rgb(17 24 39); }
        .text-gray-500 { color: rgb(107 114 128); }
        .text-gray-700 { color: rgb(55 65 81); }
        .bg-gray-50 { background-color: rgb(249 250 251); }
        .border-b { border-bottom-width: 1px; }
        .h-11 { height: 2.75rem; }
        .px-4 { padding-left: 1rem; padding-right: 1rem; }
        .p-4 { padding: 1rem; }
        .mt-4 { margin-top: 1rem; }
        .text-left { text-align: left; }
        .align-middle { vertical-align: middle; }
        .font-medium { font-weight: 500; }
        .uppercase { text-transform: uppercase; }
        .tracking-wide { letter-spacing: 0.025em; }
        table { border-collapse: collapse; }
        tr { border-color: rgb(229 231 235); }
      </style>
      <div style="padding: 20px; font-family: system-ui, -apple-system, sans-serif;">
        <div class="w-full" style="overflow: auto;">
          <table class="w-full caption-bottom text-sm text-gray-900">
            <caption class="mt-4 text-sm text-gray-500">
              A list of recent actions and their status
            </caption>
            <thead>
              <tr class="border-b bg-gray-50">
                <th class="h-11 px-4 text-left align-middle text-xs font-medium uppercase tracking-wide text-gray-500 bg-gray-50 border-b">
                  Name
                </th>
                <th class="h-11 px-4 text-left align-middle text-xs font-medium uppercase tracking-wide text-gray-500 bg-gray-50 border-b">
                  Status
                </th>
                <th class="h-11 px-4 text-left align-middle text-xs font-medium uppercase tracking-wide text-gray-500 bg-gray-50 border-b">
                  Date
                </th>
              </tr>
            </thead>
            <tbody>
              <tr class="border-b">
                <td class="p-4 align-middle text-sm text-gray-700">Action One</td>
                <td class="p-4 align-middle text-sm text-gray-700">Active</td>
                <td class="p-4 align-middle text-sm text-gray-700">2025-12-11</td>
              </tr>
              <tr>
                <td class="p-4 align-middle text-sm text-gray-700">Action Two</td>
                <td class="p-4 align-middle text-sm text-gray-700">Pending</td>
                <td class="p-4 align-middle text-sm text-gray-700">2025-12-10</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    `);

    await expect(page).toHaveScreenshot('table-with-caption.png');
  });

  // Responsive tests for multiple viewport sizes
  for (const viewport of viewports) {
    test(`Table renders correctly on ${viewport.name} viewport`, async ({ page }) => {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });

      await page.setContent(`
        <style>
          .w-full { width: 100%; }
          .caption-bottom { caption-side: bottom; }
          .text-sm { font-size: 0.875rem; line-height: 1.25rem; }
          .text-xs { font-size: 0.75rem; line-height: 1rem; }
          .text-gray-900 { color: rgb(17 24 39); }
          .text-gray-500 { color: rgb(107 114 128); }
          .text-gray-700 { color: rgb(55 65 81); }
          .bg-gray-50 { background-color: rgb(249 250 251); }
          .border-b { border-bottom-width: 1px; }
          .h-11 { height: 2.75rem; }
          .px-4 { padding-left: 1rem; padding-right: 1rem; }
          .p-4 { padding: 1rem; }
          .text-left { text-align: left; }
          .align-middle { vertical-align: middle; }
          .font-medium { font-weight: 500; }
          .uppercase { text-transform: uppercase; }
          .tracking-wide { letter-spacing: 0.025em; }
          table { border-collapse: collapse; }
          tr { border-color: rgb(229 231 235); }
          body { margin: 0; padding: 0; }
        </style>
        <div style="padding: 20px; font-family: system-ui, -apple-system, sans-serif;">
          <div class="w-full" style="overflow: auto;">
            <table class="w-full caption-bottom text-sm text-gray-900">
              <thead>
                <tr class="border-b bg-gray-50">
                  <th class="h-11 px-4 text-left align-middle text-xs font-medium uppercase tracking-wide text-gray-500 bg-gray-50 border-b">
                    Name
                  </th>
                  <th class="h-11 px-4 text-left align-middle text-xs font-medium uppercase tracking-wide text-gray-500 bg-gray-50 border-b">
                    Status
                  </th>
                  <th class="h-11 px-4 text-left align-middle text-xs font-medium uppercase tracking-wide text-gray-500 bg-gray-50 border-b">
                    Date
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr class="border-b">
                  <td class="p-4 align-middle text-sm text-gray-700">Action One</td>
                  <td class="p-4 align-middle text-sm text-gray-700">Active</td>
                  <td class="p-4 align-middle text-sm text-gray-700">2025-12-11</td>
                </tr>
                <tr class="border-b">
                  <td class="p-4 align-middle text-sm text-gray-700">Action Two</td>
                  <td class="p-4 align-middle text-sm text-gray-700">Pending</td>
                  <td class="p-4 align-middle text-sm text-gray-700">2025-12-10</td>
                </tr>
                <tr>
                  <td class="p-4 align-middle text-sm text-gray-700">Action Three</td>
                  <td class="p-4 align-middle text-sm text-gray-700">Completed</td>
                  <td class="p-4 align-middle text-sm text-gray-700">2025-12-09</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      `);

      await expect(page).toHaveScreenshot(`table-${viewport.name}-viewport.png`);
    });
  }

  test('Table with many columns renders correctly with horizontal scroll', async ({ page }) => {
    await page.setContent(`
      <style>
        .w-full { width: 100%; }
        .caption-bottom { caption-side: bottom; }
        .text-sm { font-size: 0.875rem; line-height: 1.25rem; }
        .text-xs { font-size: 0.75rem; line-height: 1rem; }
        .text-gray-900 { color: rgb(17 24 39); }
        .text-gray-500 { color: rgb(107 114 128); }
        .text-gray-700 { color: rgb(55 65 81); }
        .bg-gray-50 { background-color: rgb(249 250 251); }
        .border-b { border-bottom-width: 1px; }
        .h-11 { height: 2.75rem; }
        .px-4 { padding-left: 1rem; padding-right: 1rem; }
        .p-4 { padding: 1rem; }
        .text-left { text-align: left; }
        .align-middle { vertical-align: middle; }
        .font-medium { font-weight: 500; }
        .uppercase { text-transform: uppercase; }
        .tracking-wide { letter-spacing: 0.025em; }
        table { border-collapse: collapse; }
        tr { border-color: rgb(229 231 235); }
      </style>
      <div style="padding: 20px; font-family: system-ui, -apple-system, sans-serif;">
        <div class="w-full" style="overflow: auto; max-width: 800px;">
          <table class="w-full caption-bottom text-sm text-gray-900">
            <thead>
              <tr class="border-b bg-gray-50">
                <th class="h-11 px-4 text-left align-middle text-xs font-medium uppercase tracking-wide text-gray-500 bg-gray-50 border-b">ID</th>
                <th class="h-11 px-4 text-left align-middle text-xs font-medium uppercase tracking-wide text-gray-500 bg-gray-50 border-b">Name</th>
                <th class="h-11 px-4 text-left align-middle text-xs font-medium uppercase tracking-wide text-gray-500 bg-gray-50 border-b">Email</th>
                <th class="h-11 px-4 text-left align-middle text-xs font-medium uppercase tracking-wide text-gray-500 bg-gray-50 border-b">Status</th>
                <th class="h-11 px-4 text-left align-middle text-xs font-medium uppercase tracking-wide text-gray-500 bg-gray-50 border-b">Date</th>
                <th class="h-11 px-4 text-left align-middle text-xs font-medium uppercase tracking-wide text-gray-500 bg-gray-50 border-b">Category</th>
                <th class="h-11 px-4 text-left align-middle text-xs font-medium uppercase tracking-wide text-gray-500 bg-gray-50 border-b">Priority</th>
              </tr>
            </thead>
            <tbody>
              <tr class="border-b">
                <td class="p-4 align-middle text-sm text-gray-700">001</td>
                <td class="p-4 align-middle text-sm text-gray-700">Action One</td>
                <td class="p-4 align-middle text-sm text-gray-700">action1@example.com</td>
                <td class="p-4 align-middle text-sm text-gray-700">Active</td>
                <td class="p-4 align-middle text-sm text-gray-700">2025-12-11</td>
                <td class="p-4 align-middle text-sm text-gray-700">Development</td>
                <td class="p-4 align-middle text-sm text-gray-700">High</td>
              </tr>
              <tr>
                <td class="p-4 align-middle text-sm text-gray-700">002</td>
                <td class="p-4 align-middle text-sm text-gray-700">Action Two</td>
                <td class="p-4 align-middle text-sm text-gray-700">action2@example.com</td>
                <td class="p-4 align-middle text-sm text-gray-700">Pending</td>
                <td class="p-4 align-middle text-sm text-gray-700">2025-12-10</td>
                <td class="p-4 align-middle text-sm text-gray-700">Testing</td>
                <td class="p-4 align-middle text-sm text-gray-700">Medium</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    `);

    await expect(page).toHaveScreenshot('table-many-columns.png');
  });

  test('Table with long content in cells renders correctly', async ({ page }) => {
    await page.setContent(`
      <style>
        .w-full { width: 100%; }
        .caption-bottom { caption-side: bottom; }
        .text-sm { font-size: 0.875rem; line-height: 1.25rem; }
        .text-xs { font-size: 0.75rem; line-height: 1rem; }
        .text-gray-900 { color: rgb(17 24 39); }
        .text-gray-500 { color: rgb(107 114 128); }
        .text-gray-700 { color: rgb(55 65 81); }
        .bg-gray-50 { background-color: rgb(249 250 251); }
        .border-b { border-bottom-width: 1px; }
        .h-11 { height: 2.75rem; }
        .px-4 { padding-left: 1rem; padding-right: 1rem; }
        .p-4 { padding: 1rem; }
        .text-left { text-align: left; }
        .align-middle { vertical-align: middle; }
        .font-medium { font-weight: 500; }
        .uppercase { text-transform: uppercase; }
        .tracking-wide { letter-spacing: 0.025em; }
        table { border-collapse: collapse; }
        tr { border-color: rgb(229 231 235); }
      </style>
      <div style="padding: 20px; font-family: system-ui, -apple-system, sans-serif;">
        <div class="w-full" style="overflow: auto;">
          <table class="w-full caption-bottom text-sm text-gray-900">
            <thead>
              <tr class="border-b bg-gray-50">
                <th class="h-11 px-4 text-left align-middle text-xs font-medium uppercase tracking-wide text-gray-500 bg-gray-50 border-b">
                  Name
                </th>
                <th class="h-11 px-4 text-left align-middle text-xs font-medium uppercase tracking-wide text-gray-500 bg-gray-50 border-b">
                  Description
                </th>
                <th class="h-11 px-4 text-left align-middle text-xs font-medium uppercase tracking-wide text-gray-500 bg-gray-50 border-b">
                  Status
                </th>
              </tr>
            </thead>
            <tbody>
              <tr class="border-b">
                <td class="p-4 align-middle text-sm text-gray-700">Action One</td>
                <td class="p-4 align-middle text-sm text-gray-700">This is a very long description that demonstrates how the table handles longer content in cells. It should wrap appropriately and maintain proper spacing.</td>
                <td class="p-4 align-middle text-sm text-gray-700">Active</td>
              </tr>
              <tr>
                <td class="p-4 align-middle text-sm text-gray-700">Action Two</td>
                <td class="p-4 align-middle text-sm text-gray-700">Short description</td>
                <td class="p-4 align-middle text-sm text-gray-700">Pending</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    `);

    await expect(page).toHaveScreenshot('table-long-content.png');
  });
});
