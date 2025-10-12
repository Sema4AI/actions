import React from 'react';
import { render, userEvent } from '../utils/test-utils';
import { describe, it, expect } from 'vitest';
import { runAxe } from './setup';

import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@/core/components/ui/DropdownMenu';

describe('DropdownMenu accessibility', () => {
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
});
