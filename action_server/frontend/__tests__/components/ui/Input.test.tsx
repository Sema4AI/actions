import React from 'react';
import { render } from '../../utils/test-utils';
import { describe, it, expect } from 'vitest';
import { Input } from '@/core/components/ui/Input';

describe('Input component — visual states', () => {
  it('renders base input with expected base border class', () => {
    const { getByPlaceholderText } = render(<Input placeholder="Test input" />);
    const el = getByPlaceholderText('Test input') as HTMLInputElement;
    expect(el).not.toBeNull();
    expect(el.className).toContain('border-gray-300');
  });

  it('applies error styles when error prop provided (test-first: should fail until implemented)', () => {
    // Intentionally using a prop that the current component does not yet declare to drive TDD
  const { getByPlaceholderText } = render(<Input error placeholder="Error input" />);
    const el = getByPlaceholderText('Error input') as HTMLInputElement;
    // These assertions will fail until the component implements the `error` prop
    expect(el.className).toContain('border-red-500');
    expect(el.className).toContain('focus-visible:ring-red-500');
  });
});
