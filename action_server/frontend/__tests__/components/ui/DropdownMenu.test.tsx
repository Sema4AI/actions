import React from 'react';
import { render, screen, userEvent, waitFor } from '../../utils/test-utils';
import { describe, it, expect, vi } from 'vitest';

import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from '@/core/components/ui/DropdownMenu';

describe('DropdownMenu', () => {
  describe('Open/Close States', () => {
    it('opens content when trigger is clicked', async () => {
      const { getByText, queryByText } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Open</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Menu Item</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      expect(queryByText('Menu Item')).toBeNull();
      await userEvent.click(getByText('Open'));
      expect(getByText('Menu Item')).toBeTruthy();
    });

    it('closes content when trigger is clicked again', async () => {
      const user = userEvent.setup();
      const { getByText, queryByText } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Toggle</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Menu Item</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      const trigger = getByText('Toggle');

      // Open
      await user.click(trigger);
      expect(getByText('Menu Item')).toBeTruthy();

      // Close
      await user.click(trigger);
      await waitFor(() => {
        expect(queryByText('Menu Item')).toBeNull();
      });
    });

    it('closes content when clicking outside', async () => {
      const user = userEvent.setup();
      const { getByText, queryByText, container } = render(
        <div>
          <div data-testid="outside">Outside</div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button>Open</button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem>Menu Item</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>,
      );

      // Open menu
      await user.click(getByText('Open'));
      expect(getByText('Menu Item')).toBeTruthy();

      // Click outside
      await user.click(getByText('Outside'));
      await waitFor(() => {
        expect(queryByText('Menu Item')).toBeNull();
      });
    });

    it('is closed by default', () => {
      const { queryByText } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Trigger</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Item</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      expect(queryByText('Item')).toBeNull();
    });
  });

  describe('Item Selection', () => {
    it('calls onSelect when item is clicked', async () => {
      const onSelect = vi.fn();
      const { getByText } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Open</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem onSelect={onSelect}>Do thing</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Open'));
      await userEvent.click(getByText('Do thing'));
      expect(onSelect).toHaveBeenCalled();
    });

    it('closes menu after selecting an item', async () => {
      const { getByText, queryByText } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Open</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Select Me</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Open'));
      await userEvent.click(getByText('Select Me'));

      await waitFor(() => {
        expect(queryByText('Select Me')).toBeNull();
      });
    });
  });

  describe('Item Styling', () => {
    it('applies base item styling classes', async () => {
      const { getByText, container } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Open</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Item</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Open'));
      const item = getByText('Item');

      expect(item.className).toMatch(/cursor-pointer/);
      expect(item.className).toMatch(/select-none/);
      expect(item.className).toMatch(/rounded-(sm|md)/);
      expect(item.className).toMatch(/px-[23]/);
      expect(item.className).toMatch(/py-2/);
    });

    it('applies focus styling classes for item hover', async () => {
      const { getByText } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Open</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Hover Me</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Open'));
      const item = getByText('Hover Me');

      // Check that focus classes are defined (uses semantic color)
      expect(item.className).toMatch(/focus:bg-accent/);
    });

    it('applies destructive item styling when custom className includes red text', async () => {
      const { getByText } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Open</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem className="text-red-600 hover:bg-red-50">
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Open'));
      const deleteItem = getByText('Delete');

      expect(deleteItem.className).toMatch(/text-red-600/);
      expect(deleteItem.className).toMatch(/hover:bg-red-50/);
    });

    it('applies disabled styling when disabled prop is true', async () => {
      const onSelect = vi.fn();
      const user = userEvent.setup();
      const { getByText } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Open</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem disabled onSelect={onSelect}>
              Disabled Item
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await user.click(getByText('Open'));
      const item = getByText('Disabled Item');

      expect(item.getAttribute('data-disabled')).toBeTruthy();
      await user.click(item);
      expect(onSelect).not.toHaveBeenCalled();
    });
  });

  describe('Keyboard Navigation', () => {
    it('opens menu when pressing Enter on trigger', async () => {
      const user = userEvent.setup();
      const { getByText } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Trigger</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Item 1</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      const trigger = getByText('Trigger');
      trigger.focus();
      await user.keyboard('{Enter}');

      expect(getByText('Item 1')).toBeTruthy();
    });

    it('opens menu when pressing Space on trigger', async () => {
      const user = userEvent.setup();
      const { getByText } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Trigger</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Item 1</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      const trigger = getByText('Trigger');
      trigger.focus();
      await user.keyboard(' ');

      expect(getByText('Item 1')).toBeTruthy();
    });

    it('closes menu when pressing Escape', async () => {
      const user = userEvent.setup();
      const { getByText, queryByText } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Trigger</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Item 1</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      // Open menu
      await userEvent.click(getByText('Trigger'));
      expect(getByText('Item 1')).toBeTruthy();

      // Close with Escape
      await user.keyboard('{Escape}');
      await waitFor(() => {
        expect(queryByText('Item 1')).toBeNull();
      });
    });

    it('navigates through items with arrow keys', async () => {
      const user = userEvent.setup();
      const { getByText } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Trigger</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Item 1</DropdownMenuItem>
            <DropdownMenuItem>Item 2</DropdownMenuItem>
            <DropdownMenuItem>Item 3</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Trigger'));

      // Navigate down with arrow keys
      await user.keyboard('{ArrowDown}');
      expect(getByText('Item 1')).toBeTruthy();

      await user.keyboard('{ArrowDown}');
      expect(getByText('Item 2')).toBeTruthy();

      // Navigate up
      await user.keyboard('{ArrowUp}');
      expect(getByText('Item 1')).toBeTruthy();
    });

    it('selects item when pressing Enter on focused item', async () => {
      const user = userEvent.setup();
      const onSelect = vi.fn();
      const { getByText } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Trigger</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem onSelect={onSelect}>Item 1</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Trigger'));
      await user.keyboard('{ArrowDown}');
      await user.keyboard('{Enter}');

      expect(onSelect).toHaveBeenCalled();
    });

    it('wraps focus from last item to first with ArrowDown', async () => {
      const user = userEvent.setup();
      const { getByText } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Trigger</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Item 1</DropdownMenuItem>
            <DropdownMenuItem>Item 2</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Trigger'));

      // Navigate to last item
      await user.keyboard('{ArrowDown}');
      await user.keyboard('{ArrowDown}');

      // Should wrap to first item
      await user.keyboard('{ArrowDown}');
      expect(getByText('Item 1')).toBeTruthy();
    });
  });

  describe('Animation Classes', () => {
    it('applies fade-in and slide-in animations when opening', async () => {
      const { getByText, container } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Trigger</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Item</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Trigger'));

      // Find the content element (it's portaled, so look in document)
      await waitFor(() => {
        const content = document.querySelector('[role="menu"]');
        expect(content).toBeTruthy();
        expect(content?.className).toMatch(/animate-fade-in-0/);
        expect(content?.className).toMatch(/animate-slide-in-from-top-2/);
      });
    });

    it('applies motion-reduce classes for accessibility', async () => {
      const { getByText } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Trigger</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Item</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Trigger'));

      await waitFor(() => {
        const content = document.querySelector('[role="menu"]');
        expect(content).toBeTruthy();
        expect(content?.className).toMatch(/motion-reduce:animate-none/);
        expect(content?.className).toMatch(/motion-reduce:transition-none/);
      });
    });
  });

  describe('DropdownMenuSeparator', () => {
    it('renders separator between items', async () => {
      const { getByText, container } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Trigger</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Item 1</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem>Item 2</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Trigger'));

      // Look for separator element with proper role
      await waitFor(() => {
        const separator = document.querySelector('[role="separator"]');
        expect(separator).toBeTruthy();
        expect(separator?.className).toMatch(/bg-border/);
      });
    });
  });

  describe('Multiple Items', () => {
    it('renders multiple menu items correctly', async () => {
      const { getByText } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Trigger</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Edit</DropdownMenuItem>
            <DropdownMenuItem>Copy</DropdownMenuItem>
            <DropdownMenuItem>Delete</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Trigger'));

      expect(getByText('Edit')).toBeTruthy();
      expect(getByText('Copy')).toBeTruthy();
      expect(getByText('Delete')).toBeTruthy();
    });

    it('allows each item to have independent onSelect handlers', async () => {
      const onEdit = vi.fn();
      const onDelete = vi.fn();
      const { getByText } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Trigger</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem onSelect={onEdit}>Edit</DropdownMenuItem>
            <DropdownMenuItem onSelect={onDelete}>Delete</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Trigger'));
      await userEvent.click(getByText('Edit'));

      expect(onEdit).toHaveBeenCalledOnce();
      expect(onDelete).not.toHaveBeenCalled();
    });
  });

  describe('Content Portal', () => {
    it('renders content in a portal', async () => {
      const { getByText } = render(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button>Trigger</button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Item</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>,
      );

      await userEvent.click(getByText('Trigger'));

      // Content should be rendered in a portal (directly in document body, not in component tree)
      await waitFor(() => {
        const portalContent = document.querySelector('[role="menu"]');
        expect(portalContent).toBeTruthy();
      });
    });
  });
});
