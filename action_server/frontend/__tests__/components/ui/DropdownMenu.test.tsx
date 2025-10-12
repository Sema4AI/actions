import React from 'react';
import { render, userEvent } from '../../utils/test-utils';
import { describe, it, expect, vi } from 'vitest';

import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@/core/components/ui/DropdownMenu';

describe('DropdownMenu', () => {
  it('opens content when trigger clicked and selects item', async () => {
    const onSelect = vi.fn();
    const { getByText, queryByText } = render(
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button>Open</button>
        </DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuItem onSelect={onSelect}>Do thing</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>,
    );

    expect(queryByText('Do thing')).toBeNull();
    await userEvent.click(getByText('Open'));
    expect(getByText('Do thing')).toBeTruthy();
    await userEvent.click(getByText('Do thing'));
    expect(onSelect).toHaveBeenCalled();
  });
});
