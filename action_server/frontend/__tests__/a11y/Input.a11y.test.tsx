import React from 'react';
import { render } from '../utils/test-utils';
import { describe, it, expect } from 'vitest';
import { Input } from '@/core/components/ui/Input';
import { runAxe } from '../a11y/setup';

describe('Input accessibility', () => {
  it('has no axe violations in basic state', async () => {
    const { container } = render(<Input placeholder="A11y Input" />);
    const results = await runAxe(container);
    expect(results).toHaveNoViolations();
  });
});
