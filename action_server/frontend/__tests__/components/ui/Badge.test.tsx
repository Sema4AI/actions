import React from 'react';
import { render } from '../../utils/test-utils';
import { describe, it, expect } from 'vitest';

import { Badge } from '@/core/components/ui/Badge';

describe('Badge', () => {
  it('renders the default (neutral) variant when no variant is provided', () => {
    const { getByText } = render(<Badge>Neutral</Badge>);
    expect(getByText('Neutral')).toBeTruthy();
  });

  it('applies success variant styling when variant="success"', () => {
    const { container } = render(<Badge variant="success">OK</Badge>);
    const el = container.firstChild as HTMLElement | null;
    expect(el).toBeTruthy();
    // Variant classes are expected to include a green background for success
    expect(el?.className).toMatch(/bg-green-100/);
  });
});
