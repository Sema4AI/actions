import React from 'react';
import { render } from '../utils/test-utils';
import { describe, it, expect } from 'vitest';
import { Textarea } from '@/core/components/ui/Textarea';
import { runAxe } from '../a11y/setup';

describe('Textarea accessibility', () => {
  it('has no axe violations in basic state', async () => {
    const { container } = render(<Textarea placeholder="A11y Textarea" />);
    const results = await runAxe(container);
    expect(results).toHaveNoViolations();
  });
});
