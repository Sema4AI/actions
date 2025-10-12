import React from 'react';
import { render } from '../../utils/test-utils';
import { describe, it, expect, vi } from 'vitest';

import { ErrorBanner } from '@/core/components/ui/ErrorBanner';

describe('ErrorBanner', () => {
  it('renders the provided message', () => {
    const { getByText } = render(<ErrorBanner message="Something went wrong" />);
    expect(getByText('Something went wrong')).toBeTruthy();
  });

  it('calls onDismiss when dismiss button clicked', async () => {
    const onDismiss = vi.fn();
    const { getByRole } = render(<ErrorBanner message="Error" onDismiss={onDismiss} />);
    const btn = getByRole('button');
    await btn.click();
    expect(onDismiss).toHaveBeenCalled();
  });
});
