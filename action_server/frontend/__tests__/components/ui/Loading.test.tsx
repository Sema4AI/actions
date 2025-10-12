import React from 'react';
import { render } from '../../utils/test-utils';
import { describe, it, expect, vi } from 'vitest';

import { Loading } from '@/core/components/ui/Loading';

describe('Loading component', () => {
  it('renders spinner and optional text', () => {
    const { getByText, container } = render(<Loading text="Loading actions..." />);
    expect(getByText('Loading actions...')).toBeTruthy();
    // Spinner is an element with the animate-spin class
    expect(container.querySelector('.animate-spin')).toBeTruthy();
  });

  it('shows retry button and calls onRetry when timeout prop is used', async () => {
    const onRetry = vi.fn();
    const { getByRole } = render(<Loading timeout onRetry={onRetry} />);
    const btn = getByRole('button', { name: /retry/i });
    expect(btn).toBeTruthy();
    await btn.click();
    expect(onRetry).toHaveBeenCalled();
  });
});
