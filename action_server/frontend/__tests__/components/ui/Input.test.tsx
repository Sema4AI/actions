import React from 'react';
import { render } from '../../utils/test-utils';
import { describe, it, expect } from 'vitest';
import { Input } from '@/core/components/ui/Input';

describe('Input component — visual states', () => {
  it('renders base input with expected base border class', () => {
    const { getByPlaceholderText } = render(<Input placeholder="Test input" />);
    const el = getByPlaceholderText('Test input') as HTMLInputElement;
    expect(el).not.toBeNull();
    expect(el.className).toContain('border-input');
  });

  it('applies error styles when error prop provided', () => {
    const { getByPlaceholderText } = render(<Input error placeholder="Error input" />);
    const el = getByPlaceholderText('Error input') as HTMLInputElement;
    expect(el.className).toContain('border-destructive');
    expect(el.className).toContain('focus-visible:ring-destructive');
    expect(el.getAttribute('aria-invalid')).toBe('true');
  });
});
