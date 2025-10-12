import { test, expect } from '@playwright/test';

test('Input base renders visually', async ({ page }) => {
  await page.setContent(`<input placeholder="Input Visual" class="border-gray-300" />`);
  const input = page.getByPlaceholder('Input Visual');
  await input.focus();
  await expect(page).toHaveScreenshot('input-base.png'); // Baseline to be added by author
});

test('Textarea base renders visually', async ({ page }) => {
  await page.setContent(`<textarea placeholder="Textarea Visual" class="min-h-[80px]" />`);
  await expect(page).toHaveScreenshot('textarea-base.png'); // Baseline to be added by author
});
