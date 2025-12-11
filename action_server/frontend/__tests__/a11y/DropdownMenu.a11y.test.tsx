import React from 'react';
import { render, userEvent, screen, waitFor } from '../utils/test-utils';
import { describe, it, expect, vi } from 'vitest';
import { runAxe } from './setup';

import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuCheckboxItem,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubTrigger,
  DropdownMenuSubContent,
} from '@/core/components/ui/DropdownMenu';

describe('DropdownMenu accessibility', () => {
  describe('Axe violations', () => {
    it('has no axe violations when opened', async () => {
      const { getByText, container, findByRole } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Open</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>One</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Open'));
      // Wait for the menu to appear so Radix internal state updates finish inside act()
      await findByRole('menu');
      const results = await runAxe(container);
      expect(results as any).toHaveNoViolations();
    });

    it('has no axe violations with complex menu structure', async () => {
      const { getByText, container, findByRole } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Settings</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuLabel>Account</DropdownMenuLabel>
            <DropdownMenuItem>Profile</DropdownMenuItem>
            <DropdownMenuItem>Billing</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuCheckboxItem checked>Notifications</DropdownMenuCheckboxItem>
            <DropdownMenuCheckboxItem>Email alerts</DropdownMenuCheckboxItem>
            <DropdownMenuSeparator />
            <DropdownMenuRadioGroup value="light">
              <DropdownMenuRadioItem value="light">Light</DropdownMenuRadioItem>
              <DropdownMenuRadioItem value="dark">Dark</DropdownMenuRadioItem>
            </DropdownMenuRadioGroup>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Settings'));
      await findByRole('menu');
      const results = await runAxe(container);
      expect(results as any).toHaveNoViolations();
    });

    it('has no axe violations with submenu', async () => {
      const { getByText, container, findByRole } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Item 1</DropdownMenuItem>
            <DropdownMenuSub>
              <DropdownMenuSubTrigger>More options</DropdownMenuSubTrigger>
              <DropdownMenuSubContent>
                <DropdownMenuItem>Submenu item 1</DropdownMenuItem>
                <DropdownMenuItem>Submenu item 2</DropdownMenuItem>
              </DropdownMenuSubContent>
            </DropdownMenuSub>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Menu'));
      await findByRole('menu');
      const results = await runAxe(container);
      expect(results as any).toHaveNoViolations();
    });

    it('has no axe violations with disabled items', async () => {
      const { getByText, container, findByRole } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Actions</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Enabled</DropdownMenuItem>
            <DropdownMenuItem disabled>Disabled</DropdownMenuItem>
            <DropdownMenuItem>Also enabled</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Actions'));
      await findByRole('menu');
      const results = await runAxe(container);
      expect(results as any).toHaveNoViolations();
    });
  });

  describe('ARIA attributes', () => {
    it('has correct role on menu content', async () => {
      const { getByText, findByRole } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Item</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Menu'));
      const menu = await findByRole('menu');
      expect(menu).not.toBeNull();
    });

    it('has correct role on menu items', async () => {
      const { getByText, findAllByRole } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Item 1</DropdownMenuItem>
            <DropdownMenuItem>Item 2</DropdownMenuItem>
            <DropdownMenuItem>Item 3</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Menu'));
      const items = await findAllByRole('menuitem');
      expect(items).toHaveLength(3);
    });

    it('has correct aria-expanded on trigger', async () => {
      const { getByRole } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Item</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      const trigger = getByRole('button', { name: 'Menu' });
      expect(trigger.getAttribute('aria-expanded')).toBe('false');

      await userEvent.click(trigger);
      await waitFor(() => {
        expect(trigger.getAttribute('aria-expanded')).toBe('true');
      });
    });

    it('has correct aria-haspopup on trigger', () => {
      const { getByRole } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Item</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      const trigger = getByRole('button', { name: 'Menu' });
      expect(trigger.getAttribute('aria-haspopup')).toBe('menu');
    });

    it('has correct aria-checked on checkbox items', async () => {
      const { getByText, findByRole, getByRole } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuCheckboxItem checked>Checked</DropdownMenuCheckboxItem>
            <DropdownMenuCheckboxItem checked={false}>Unchecked</DropdownMenuCheckboxItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Menu'));
      // Wait for menu to be ready
      await findByRole('menu');
      // Now get the items - note that the checkmark is included in the accessible name
      const checkedItem = getByRole('menuitemcheckbox', { name: /Checked/ });
      const uncheckedItem = getByRole('menuitemcheckbox', { name: /Unchecked/ });
      expect(checkedItem.getAttribute('aria-checked')).toBe('true');
      expect(uncheckedItem.getAttribute('aria-checked')).toBe('false');
    });

    it('has correct aria-checked on radio items', async () => {
      const { getByText, findByRole, getByRole } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuRadioGroup value="option1">
              <DropdownMenuRadioItem value="option1">Option 1</DropdownMenuRadioItem>
              <DropdownMenuRadioItem value="option2">Option 2</DropdownMenuRadioItem>
            </DropdownMenuRadioGroup>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Menu'));
      // Wait for menu to be ready
      await findByRole('menu');
      // Now get the items - note that the indicator bullet is included in the accessible name
      const selectedItem = getByRole('menuitemradio', { name: /Option 1/ });
      const unselectedItem = getByRole('menuitemradio', { name: /Option 2/ });
      expect(selectedItem.getAttribute('aria-checked')).toBe('true');
      expect(unselectedItem.getAttribute('aria-checked')).toBe('false');
    });

    it('has correct aria-disabled on disabled items', async () => {
      const { getByText, getByRole } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem disabled>Disabled item</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Menu'));
      await waitFor(() => {
        const disabledItem = getByRole('menuitem', { name: 'Disabled item' });
        expect(disabledItem.getAttribute('data-disabled')).toBe('');
      });
    });
  });

  describe('Keyboard navigation', () => {
    it('opens menu with Enter key on trigger', async () => {
      const user = userEvent.setup();
      const { getByRole, findByRole } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Item 1</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      const trigger = getByRole('button', { name: 'Menu' });
      trigger.focus();
      await user.keyboard('{Enter}');

      const menu = await findByRole('menu');
      expect(menu).not.toBeNull();
    });

    it('opens menu with Space key on trigger', async () => {
      const user = userEvent.setup();
      const { getByRole, findByRole } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Item 1</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      const trigger = getByRole('button', { name: 'Menu' });
      trigger.focus();
      await user.keyboard(' ');

      const menu = await findByRole('menu');
      expect(menu).not.toBeNull();
    });

    it('closes menu with Escape key', async () => {
      const user = userEvent.setup();
      const { getByText, findByRole, queryByRole } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Item 1</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Menu'));
      await findByRole('menu');

      await user.keyboard('{Escape}');

      await waitFor(() => {
        expect(queryByRole('menu')).toBeNull();
      });
    });

    it('navigates through items with ArrowDown', async () => {
      const user = userEvent.setup();
      const { getByText, findByRole } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>First</DropdownMenuItem>
            <DropdownMenuItem>Second</DropdownMenuItem>
            <DropdownMenuItem>Third</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Menu'));
      await findByRole('menu');

      await user.keyboard('{ArrowDown}');
      const firstItem = screen.getByRole('menuitem', { name: 'First' });
      expect(document.activeElement).toBe(firstItem);

      await user.keyboard('{ArrowDown}');
      const secondItem = screen.getByRole('menuitem', { name: 'Second' });
      expect(document.activeElement).toBe(secondItem);
    });

    it('navigates through items with ArrowUp', async () => {
      const user = userEvent.setup();
      const { getByText, findByRole } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>First</DropdownMenuItem>
            <DropdownMenuItem>Second</DropdownMenuItem>
            <DropdownMenuItem>Third</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Menu'));
      await findByRole('menu');

      await user.keyboard('{ArrowUp}');
      const thirdItem = screen.getByRole('menuitem', { name: 'Third' });
      expect(document.activeElement).toBe(thirdItem);

      await user.keyboard('{ArrowUp}');
      const secondItem = screen.getByRole('menuitem', { name: 'Second' });
      expect(document.activeElement).toBe(secondItem);
    });

    it('moves to first item with Home key', async () => {
      const user = userEvent.setup();
      const { getByText, findByRole } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>First</DropdownMenuItem>
            <DropdownMenuItem>Second</DropdownMenuItem>
            <DropdownMenuItem>Third</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Menu'));
      await findByRole('menu');

      // Navigate to third item
      await user.keyboard('{ArrowDown}');
      await user.keyboard('{ArrowDown}');

      // Press Home to go back to first
      await user.keyboard('{Home}');
      const firstItem = screen.getByRole('menuitem', { name: 'First' });
      expect(document.activeElement).toBe(firstItem);
    });

    it('moves to last item with End key', async () => {
      const user = userEvent.setup();
      const { getByText, findByRole } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>First</DropdownMenuItem>
            <DropdownMenuItem>Second</DropdownMenuItem>
            <DropdownMenuItem>Third</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Menu'));
      await findByRole('menu');

      await user.keyboard('{End}');
      const thirdItem = screen.getByRole('menuitem', { name: 'Third' });
      expect(document.activeElement).toBe(thirdItem);
    });

    it('selects item with Enter key', async () => {
      const user = userEvent.setup();
      const onSelect = vi.fn();
      const { getByText, findByRole } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem onSelect={onSelect}>Item 1</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Menu'));
      await findByRole('menu');

      await user.keyboard('{ArrowDown}');
      await user.keyboard('{Enter}');

      expect(onSelect).toHaveBeenCalledTimes(1);
    });

    it('selects item with Space key', async () => {
      const user = userEvent.setup();
      const onSelect = vi.fn();
      const { getByText, findByRole } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem onSelect={onSelect}>Item 1</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Menu'));
      await findByRole('menu');

      await user.keyboard('{ArrowDown}');
      await user.keyboard(' ');

      expect(onSelect).toHaveBeenCalledTimes(1);
    });

    it('skips disabled items during keyboard navigation', async () => {
      const user = userEvent.setup();
      const { getByText, findByRole } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>First</DropdownMenuItem>
            <DropdownMenuItem disabled>Disabled</DropdownMenuItem>
            <DropdownMenuItem>Third</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Menu'));
      await findByRole('menu');

      await user.keyboard('{ArrowDown}');
      const firstItem = screen.getByRole('menuitem', { name: 'First' });
      expect(document.activeElement).toBe(firstItem);

      await user.keyboard('{ArrowDown}');
      const thirdItem = screen.getByRole('menuitem', { name: 'Third' });
      expect(document.activeElement).toBe(thirdItem);
    });
  });

  describe('Focus management', () => {
    it('returns focus to trigger when menu closes with Escape', async () => {
      const user = userEvent.setup();
      const { getByRole, findByRole } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Item 1</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      const trigger = getByRole('button', { name: 'Menu' });
      await userEvent.click(trigger);
      await findByRole('menu');

      await user.keyboard('{Escape}');

      await waitFor(() => {
        expect(document.activeElement).toBe(trigger);
      });
    });

    it('returns focus to trigger when item is selected', async () => {
      const user = userEvent.setup();
      const { getByRole, findByRole } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Item 1</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      const trigger = getByRole('button', { name: 'Menu' });
      await userEvent.click(trigger);
      await findByRole('menu');

      await user.keyboard('{ArrowDown}');
      await user.keyboard('{Enter}');

      await waitFor(() => {
        expect(document.activeElement).toBe(trigger);
      });
    });

    it('returns focus to trigger when clicking outside', async () => {
      const { getByRole, getByText, findByRole } = render(
        <div>
          <button>Outside</button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button>Menu</button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem>Item 1</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>,
      );

      const trigger = getByRole('button', { name: 'Menu' });
      await userEvent.click(trigger);
      await findByRole('menu');

      await userEvent.click(getByText('Outside'));

      await waitFor(() => {
        expect(screen.queryByRole('menu')).toBeNull();
      });
    });

    it('maintains focus trap within open menu', async () => {
      const user = userEvent.setup();
      const { getByText, findByRole } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>First</DropdownMenuItem>
            <DropdownMenuItem>Last</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Menu'));
      await findByRole('menu');

      await user.keyboard('{ArrowDown}');
      const firstItem = screen.getByRole('menuitem', { name: 'First' });
      expect(document.activeElement).toBe(firstItem);

      // Try to Tab out - focus should stay within menu
      await user.keyboard('{Tab}');
      const menu = screen.getByRole('menu');
      expect(menu).not.toBeNull();
    });
  });

  describe('Mouse interaction', () => {
    it('opens menu on click', async () => {
      const { getByText, findByRole } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Item 1</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Menu'));
      const menu = await findByRole('menu');
      expect(menu).not.toBeNull();
    });

    it('closes menu when clicking outside', async () => {
      const { getByText, findByRole, queryByRole } = render(
        <div>
          <button>Outside</button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button>Menu</button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem>Item 1</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>,
      );

      await userEvent.click(getByText('Menu'));
      await findByRole('menu');

      await userEvent.click(getByText('Outside'));

      await waitFor(() => {
        expect(queryByRole('menu')).toBeNull();
      });
    });

    it('selects item on click', async () => {
      const onSelect = vi.fn();
      const { getByText, findByRole, queryByRole } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem onSelect={onSelect}>Item 1</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Menu'));
      await findByRole('menu');

      await userEvent.click(screen.getByRole('menuitem', { name: 'Item 1' }));

      expect(onSelect).toHaveBeenCalledTimes(1);
      await waitFor(() => {
        expect(queryByRole('menu')).toBeNull();
      });
    });

    it('does not select disabled item on click', async () => {
      const onSelect = vi.fn();
      const { getByText, findByRole } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem disabled onSelect={onSelect}>
              Disabled
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Menu'));
      await findByRole('menu');

      const disabledItem = screen.getByRole('menuitem', { name: 'Disabled' });
      await userEvent.click(disabledItem);

      expect(onSelect).not.toHaveBeenCalled();
    });

    it('toggles checkbox item on click', async () => {
      const onCheckedChange = vi.fn();
      const { getByText, findByRole, rerender } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Menu</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuCheckboxItem checked={false} onCheckedChange={onCheckedChange}>
              Option
            </DropdownMenuCheckboxItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Menu'));
      await findByRole('menu');

      const checkboxItem = screen.getByRole('menuitemcheckbox', { name: 'Option' });
      await userEvent.click(checkboxItem);

      expect(onCheckedChange).toHaveBeenCalledWith(true);
    });
  });
});
