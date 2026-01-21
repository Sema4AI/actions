import React from 'react';
import { render } from '../../utils/test-utils';
import { describe, it, expect } from 'vitest';

import { renderStatusBadge } from '@/core/pages/Actions';
import { RunStatus } from '@/shared/types';

describe('Actions page status helpers', () => {
  it('renders a Badge for a passed status', () => {
    const { getByText, container } = render(renderStatusBadge(RunStatus.PASSED));
    expect(getByText('Passed')).toBeTruthy();
    const el = container.firstChild as HTMLElement | null;
    // Badge uses semantic color tokens
    expect(el?.className).toContain('bg-success/10');
    expect(el?.className).toContain('text-success');
  });
});
