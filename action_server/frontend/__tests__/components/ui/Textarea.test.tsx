import React from 'react';
import { render } from '../../utils/test-utils';
import { describe, it, expect } from 'vitest';
import { Textarea } from '@/core/components/ui/Textarea';

describe('Textarea component — visual states', () => {
  it('renders with minimum height class (min-h-[80px]) per spec (test-first)', () => {
    const { getByPlaceholderText } = render(<Textarea placeholder="Payload" />);
    const el = getByPlaceholderText('Payload') as HTMLTextAreaElement;
    // Expecting min-h-[80px], current component uses min-h-[120px] — test intended to fail
    expect(el.className).toContain('min-h-[80px]');
  });

  it('applies monospace font when spellCheck is false (code/JSON heuristic)', () => {
    const { getByPlaceholderText } = render(<Textarea placeholder="JSON" spellCheck={false} />);
    const el = getByPlaceholderText('JSON') as HTMLTextAreaElement;
    expect(el.className).toContain('font-mono');
  });
});
