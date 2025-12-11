import { test, expect } from '@playwright/test';

test.describe('DropdownMenu Visual Regression', () => {
  test('captures menu open state', async ({ page }) => {
    await page.setContent(`
      <!DOCTYPE html>
      <html>
        <head>
          <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
          <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
          <style>
            body {
              font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
              padding: 50px;
              background: #f9f9f9;
            }
            .dropdown-trigger {
              padding: 8px 16px;
              background: #3b82f6;
              color: white;
              border: none;
              border-radius: 6px;
              cursor: pointer;
              font-size: 14px;
            }
            .dropdown-content {
              min-width: 10rem;
              overflow: hidden;
              border-radius: 6px;
              border: 1px solid #e5e7eb;
              background: white;
              padding: 4px;
              box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
              margin-top: 8px;
            }
            .dropdown-item {
              display: flex;
              align-items: center;
              padding: 8px;
              font-size: 14px;
              border-radius: 4px;
              cursor: pointer;
              outline: none;
            }
            .dropdown-item:hover {
              background: #f3f4f6;
              color: #111827;
            }
            .dropdown-separator {
              height: 1px;
              background: #e5e7eb;
              margin: 4px -4px;
            }
            .dropdown-label {
              padding: 6px 8px;
              font-size: 14px;
              font-weight: 600;
              color: #6b7280;
            }
          </style>
        </head>
        <body>
          <button class="dropdown-trigger">Options</button>
          <div class="dropdown-content">
            <div class="dropdown-label">My Account</div>
            <div class="dropdown-item">Profile</div>
            <div class="dropdown-item">Settings</div>
            <div class="dropdown-separator"></div>
            <div class="dropdown-item">Help</div>
            <div class="dropdown-item">Sign out</div>
          </div>
        </body>
      </html>
    `);

    await expect(page).toHaveScreenshot('dropdown-menu-open.png');
  });

  test('captures item hover styling', async ({ page }) => {
    await page.setContent(`
      <!DOCTYPE html>
      <html>
        <head>
          <style>
            body {
              font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
              padding: 50px;
              background: #f9f9f9;
            }
            .dropdown-content {
              min-width: 10rem;
              overflow: hidden;
              border-radius: 6px;
              border: 1px solid #e5e7eb;
              background: white;
              padding: 4px;
              box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            }
            .dropdown-item {
              display: flex;
              align-items: center;
              padding: 8px;
              font-size: 14px;
              border-radius: 4px;
              cursor: pointer;
              outline: none;
            }
            .dropdown-item.hover {
              background: #f3f4f6;
              color: #111827;
            }
          </style>
        </head>
        <body>
          <div class="dropdown-content">
            <div class="dropdown-item">Profile</div>
            <div class="dropdown-item hover">Settings</div>
            <div class="dropdown-item">Help</div>
          </div>
        </body>
      </html>
    `);

    const hoveredItem = page.locator('.dropdown-item.hover');
    await hoveredItem.scrollIntoViewIfNeeded();

    await expect(page).toHaveScreenshot('dropdown-menu-item-hover.png');
  });

  test('captures destructive item styling (red text)', async ({ page }) => {
    await page.setContent(`
      <!DOCTYPE html>
      <html>
        <head>
          <style>
            body {
              font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
              padding: 50px;
              background: #f9f9f9;
            }
            .dropdown-content {
              min-width: 10rem;
              overflow: hidden;
              border-radius: 6px;
              border: 1px solid #e5e7eb;
              background: white;
              padding: 4px;
              box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            }
            .dropdown-item {
              display: flex;
              align-items: center;
              padding: 8px;
              font-size: 14px;
              border-radius: 4px;
              cursor: pointer;
              outline: none;
            }
            .dropdown-item.destructive {
              color: #dc2626;
            }
            .dropdown-item.destructive:hover {
              background: #fee2e2;
              color: #991b1b;
            }
            .dropdown-separator {
              height: 1px;
              background: #e5e7eb;
              margin: 4px -4px;
            }
          </style>
        </head>
        <body>
          <div class="dropdown-content">
            <div class="dropdown-item">Edit</div>
            <div class="dropdown-item">Duplicate</div>
            <div class="dropdown-separator"></div>
            <div class="dropdown-item destructive">Delete</div>
            <div class="dropdown-item destructive">Remove permanently</div>
          </div>
        </body>
      </html>
    `);

    await expect(page).toHaveScreenshot('dropdown-menu-destructive-items.png');
  });

  test('captures destructive item hover styling', async ({ page }) => {
    await page.setContent(`
      <!DOCTYPE html>
      <html>
        <head>
          <style>
            body {
              font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
              padding: 50px;
              background: #f9f9f9;
            }
            .dropdown-content {
              min-width: 10rem;
              overflow: hidden;
              border-radius: 6px;
              border: 1px solid #e5e7eb;
              background: white;
              padding: 4px;
              box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            }
            .dropdown-item {
              display: flex;
              align-items: center;
              padding: 8px;
              font-size: 14px;
              border-radius: 4px;
              cursor: pointer;
              outline: none;
            }
            .dropdown-item.destructive {
              color: #dc2626;
            }
            .dropdown-item.destructive.hover {
              background: #fee2e2;
              color: #991b1b;
            }
            .dropdown-separator {
              height: 1px;
              background: #e5e7eb;
              margin: 4px -4px;
            }
          </style>
        </head>
        <body>
          <div class="dropdown-content">
            <div class="dropdown-item">Edit</div>
            <div class="dropdown-item">Duplicate</div>
            <div class="dropdown-separator"></div>
            <div class="dropdown-item destructive hover">Delete</div>
          </div>
        </body>
      </html>
    `);

    await expect(page).toHaveScreenshot('dropdown-menu-destructive-hover.png');
  });

  test('captures separator styling', async ({ page }) => {
    await page.setContent(`
      <!DOCTYPE html>
      <html>
        <head>
          <style>
            body {
              font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
              padding: 50px;
              background: #f9f9f9;
            }
            .dropdown-content {
              min-width: 10rem;
              overflow: hidden;
              border-radius: 6px;
              border: 1px solid #e5e7eb;
              background: white;
              padding: 4px;
              box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            }
            .dropdown-item {
              display: flex;
              align-items: center;
              padding: 8px;
              font-size: 14px;
              border-radius: 4px;
              cursor: pointer;
              outline: none;
            }
            .dropdown-separator {
              height: 1px;
              background: #e5e7eb;
              margin: 4px -4px;
            }
            .dropdown-label {
              padding: 6px 8px;
              font-size: 14px;
              font-weight: 600;
              color: #6b7280;
            }
          </style>
        </head>
        <body>
          <div class="dropdown-content">
            <div class="dropdown-label">Account</div>
            <div class="dropdown-item">Profile</div>
            <div class="dropdown-item">Billing</div>
            <div class="dropdown-separator"></div>
            <div class="dropdown-label">Support</div>
            <div class="dropdown-item">Help Center</div>
            <div class="dropdown-item">Contact Us</div>
            <div class="dropdown-separator"></div>
            <div class="dropdown-item">Sign out</div>
          </div>
        </body>
      </html>
    `);

    await expect(page).toHaveScreenshot('dropdown-menu-separators.png');
  });

  test('captures disabled item styling', async ({ page }) => {
    await page.setContent(`
      <!DOCTYPE html>
      <html>
        <head>
          <style>
            body {
              font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
              padding: 50px;
              background: #f9f9f9;
            }
            .dropdown-content {
              min-width: 10rem;
              overflow: hidden;
              border-radius: 6px;
              border: 1px solid #e5e7eb;
              background: white;
              padding: 4px;
              box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            }
            .dropdown-item {
              display: flex;
              align-items: center;
              padding: 8px;
              font-size: 14px;
              border-radius: 4px;
              cursor: pointer;
              outline: none;
            }
            .dropdown-item:hover {
              background: #f3f4f6;
            }
            .dropdown-item.disabled {
              opacity: 0.5;
              pointer-events: none;
              cursor: not-allowed;
            }
          </style>
        </head>
        <body>
          <div class="dropdown-content">
            <div class="dropdown-item">New File</div>
            <div class="dropdown-item">Open</div>
            <div class="dropdown-item disabled">Save (no changes)</div>
            <div class="dropdown-item">Save As...</div>
          </div>
        </body>
      </html>
    `);

    await expect(page).toHaveScreenshot('dropdown-menu-disabled-item.png');
  });

  test('captures checkbox menu items', async ({ page }) => {
    await page.setContent(`
      <!DOCTYPE html>
      <html>
        <head>
          <style>
            body {
              font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
              padding: 50px;
              background: #f9f9f9;
            }
            .dropdown-content {
              min-width: 10rem;
              overflow: hidden;
              border-radius: 6px;
              border: 1px solid #e5e7eb;
              background: white;
              padding: 4px;
              box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            }
            .dropdown-item {
              position: relative;
              display: flex;
              align-items: center;
              padding: 8px 8px 8px 32px;
              font-size: 14px;
              border-radius: 4px;
              cursor: pointer;
              outline: none;
            }
            .dropdown-item:hover {
              background: #f3f4f6;
            }
            .dropdown-item .checkbox {
              position: absolute;
              left: 8px;
              display: flex;
              align-items: center;
              justify-content: center;
              height: 14px;
              width: 14px;
            }
            .dropdown-label {
              padding: 6px 8px;
              font-size: 14px;
              font-weight: 600;
              color: #6b7280;
            }
          </style>
        </head>
        <body>
          <div class="dropdown-content">
            <div class="dropdown-label">View Options</div>
            <div class="dropdown-item">
              <span class="checkbox">✓</span>
              Show Sidebar
            </div>
            <div class="dropdown-item">
              <span class="checkbox">✓</span>
              Show Toolbar
            </div>
            <div class="dropdown-item">
              <span class="checkbox"></span>
              Show Status Bar
            </div>
          </div>
        </body>
      </html>
    `);

    await expect(page).toHaveScreenshot('dropdown-menu-checkbox-items.png');
  });

  test('captures radio menu items', async ({ page }) => {
    await page.setContent(`
      <!DOCTYPE html>
      <html>
        <head>
          <style>
            body {
              font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
              padding: 50px;
              background: #f9f9f9;
            }
            .dropdown-content {
              min-width: 10rem;
              overflow: hidden;
              border-radius: 6px;
              border: 1px solid #e5e7eb;
              background: white;
              padding: 4px;
              box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            }
            .dropdown-item {
              position: relative;
              display: flex;
              align-items: center;
              padding: 8px 8px 8px 32px;
              font-size: 14px;
              border-radius: 4px;
              cursor: pointer;
              outline: none;
            }
            .dropdown-item:hover {
              background: #f3f4f6;
            }
            .dropdown-item .radio {
              position: absolute;
              left: 8px;
              display: flex;
              align-items: center;
              justify-content: center;
              height: 14px;
              width: 14px;
            }
            .dropdown-label {
              padding: 6px 8px;
              font-size: 14px;
              font-weight: 600;
              color: #6b7280;
            }
          </style>
        </head>
        <body>
          <div class="dropdown-content">
            <div class="dropdown-label">Text Size</div>
            <div class="dropdown-item">
              <span class="radio"></span>
              Small
            </div>
            <div class="dropdown-item">
              <span class="radio">•</span>
              Medium
            </div>
            <div class="dropdown-item">
              <span class="radio"></span>
              Large
            </div>
          </div>
        </body>
      </html>
    `);

    await expect(page).toHaveScreenshot('dropdown-menu-radio-items.png');
  });

  test('captures submenu styling', async ({ page }) => {
    await page.setContent(`
      <!DOCTYPE html>
      <html>
        <head>
          <style>
            body {
              font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
              padding: 50px;
              background: #f9f9f9;
            }
            .dropdown-content {
              min-width: 10rem;
              overflow: hidden;
              border-radius: 6px;
              border: 1px solid #e5e7eb;
              background: white;
              padding: 4px;
              box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            }
            .dropdown-item {
              display: flex;
              align-items: center;
              justify-content: space-between;
              padding: 8px;
              font-size: 14px;
              border-radius: 4px;
              cursor: pointer;
              outline: none;
            }
            .dropdown-item:hover {
              background: #f3f4f6;
            }
            .dropdown-item.has-submenu::after {
              content: '›';
              margin-left: auto;
              padding-left: 16px;
              color: #6b7280;
            }
            .submenu {
              position: absolute;
              left: 100%;
              top: 0;
              margin-left: 4px;
            }
          </style>
        </head>
        <body>
          <div style="position: relative; display: inline-block;">
            <div class="dropdown-content">
              <div class="dropdown-item">New File</div>
              <div class="dropdown-item has-submenu">Export</div>
              <div class="dropdown-item">Share</div>
            </div>
            <div class="dropdown-content submenu">
              <div class="dropdown-item">Export as PDF</div>
              <div class="dropdown-item">Export as HTML</div>
              <div class="dropdown-item">Export as Markdown</div>
            </div>
          </div>
        </body>
      </html>
    `);

    await expect(page).toHaveScreenshot('dropdown-menu-submenu.png');
  });

  test('captures menu with shortcuts', async ({ page }) => {
    await page.setContent(`
      <!DOCTYPE html>
      <html>
        <head>
          <style>
            body {
              font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
              padding: 50px;
              background: #f9f9f9;
            }
            .dropdown-content {
              min-width: 12rem;
              overflow: hidden;
              border-radius: 6px;
              border: 1px solid #e5e7eb;
              background: white;
              padding: 4px;
              box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            }
            .dropdown-item {
              display: flex;
              align-items: center;
              justify-content: space-between;
              padding: 8px;
              font-size: 14px;
              border-radius: 4px;
              cursor: pointer;
              outline: none;
            }
            .dropdown-item:hover {
              background: #f3f4f6;
            }
            .shortcut {
              margin-left: auto;
              padding-left: 16px;
              font-size: 12px;
              letter-spacing: 0.05em;
              color: #9ca3af;
            }
            .dropdown-separator {
              height: 1px;
              background: #e5e7eb;
              margin: 4px -4px;
            }
          </style>
        </head>
        <body>
          <div class="dropdown-content">
            <div class="dropdown-item">
              <span>New File</span>
              <span class="shortcut">⌘N</span>
            </div>
            <div class="dropdown-item">
              <span>Open</span>
              <span class="shortcut">⌘O</span>
            </div>
            <div class="dropdown-item">
              <span>Save</span>
              <span class="shortcut">⌘S</span>
            </div>
            <div class="dropdown-separator"></div>
            <div class="dropdown-item">
              <span>Print</span>
              <span class="shortcut">⌘P</span>
            </div>
          </div>
        </body>
      </html>
    `);

    await expect(page).toHaveScreenshot('dropdown-menu-shortcuts.png');
  });
});
