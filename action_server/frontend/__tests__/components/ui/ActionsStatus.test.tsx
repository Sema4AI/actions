import React from 'react';
import { render } from '../../utils/test-utils';
import { describe, it, expect } from 'vitest';

import { renderStatusBadge } from '@/core/pages/Actions';
import { Badge } from '@/core/components/ui/Badge';

describe('Actions page status helpers', () => {
  it('renders a Badge for a passed status', () => {
    const { getByText, container } = render(renderStatusBadge(2));
    expect(getByText('Passed')).toBeTruthy();
    const el = container.firstChild as HTMLElement | null;
    expect(el?.className).toContain('bg-green-100');
  });
});
