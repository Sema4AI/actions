import React from 'react';
import { render } from '../../utils/test-utils';
import { describe, it, expect } from 'vitest';

import { Button } from '@/core/components/ui/Button';
import { Input } from '@/core/components/ui/Input';
import { Table, TableBody, TableRow, TableCell } from '@/core/components/ui/Table';

describe('Micro-interaction Animations', () => {
  describe('Transition Duration Requirements', () => {
    it('Button has transition-all with explicit duration-150 for interactive feedback', () => {
      const { container } = render(<Button>Test Button</Button>);
      const button = container.querySelector('button');
      // Button uses transition-all to support scale animation on active state
      expect(button?.className).toContain('transition-all');
      expect(button?.className).toContain('duration-150');
      expect(button?.className).toContain('active:scale-[0.98]');
    });

    it('Input has transition-colors with explicit duration-200', () => {
      const { container } = render(<Input placeholder="test" />);
      const input = container.querySelector('input');
      expect(input?.className).toContain('transition-colors');
      expect(input?.className).toContain('duration-200');
    });

    it('TableRow has transition-colors for hover states', () => {
      const { container } = render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Test</TableCell>
            </TableRow>
          </TableBody>
        </Table>,
      );
      const row = container.querySelector('tr');
      expect(row?.className).toContain('transition-colors');
    });
  });

  describe('GPU-Accelerated Properties', () => {
    it('Components use appropriate transitions for their interaction patterns', () => {
      const { container: buttonContainer } = render(<Button>Test</Button>);
      const { container: inputContainer } = render(<Input />);
      const { container: rowContainer } = render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Test</TableCell>
            </TableRow>
          </TableBody>
        </Table>,
      );

      // Button uses transition-all to support scale animation on press
      expect(buttonContainer.querySelector('button')?.className).toContain('transition-all');
      // Input and TableRow use transition-colors for color changes only
      expect(inputContainer.querySelector('input')?.className).toContain('transition-colors');
      expect(rowContainer.querySelector('tr')?.className).toContain('transition-colors');
    });
  });

  describe('Hover State Transitions', () => {
    it('Button applies hover:bg-* classes that work with transitions', () => {
      const { container } = render(<Button>Hover Me</Button>);
      const button = container.querySelector('button');
      const classes = button?.className || '';

      // Check for hover state class and transition (uses transition-all for scale support)
      expect(classes).toContain('transition-all');
      expect(classes).toMatch(/hover:bg-/);
    });

    it('Button variants all have hover states with transitions', () => {
      const variants = ['default', 'secondary', 'outline', 'ghost', 'destructive'] as const;

      variants.forEach((variant) => {
        const { container } = render(<Button variant={variant}>Test</Button>);
        const button = container.querySelector('button');
        const classes = button?.className || '';

        expect(classes).toContain('transition-all');
        expect(classes).toMatch(/hover:bg-/);
      });
    });

    it('Input has hover:border-* transition', () => {
      const { container } = render(<Input />);
      const input = container.querySelector('input');
      const classes = input?.className || '';

      expect(classes).toContain('transition-colors');
      expect(classes).toMatch(/hover:border-/);
    });

    it('TableRow has hover:bg-* class with transition-colors', () => {
      const { container } = render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Test</TableCell>
            </TableRow>
          </TableBody>
        </Table>,
      );
      const row = container.querySelector('tr');
      const classes = row?.className || '';

      expect(classes).toContain('transition-colors');
      expect(classes).toContain('hover:bg-muted/50');
    });
  });

  describe('Motion Reduce Support', () => {
    it('respects prefers-reduced-motion for animations', () => {
      // Components should still render correctly when prefers-reduced-motion is active
      const { container: buttonContainer } = render(<Button>Test</Button>);
      const { container: inputContainer } = render(<Input />);

      expect(buttonContainer.querySelector('button')).toBeTruthy();
      expect(inputContainer.querySelector('input')).toBeTruthy();

      // The actual motion-reduce behavior is handled by Tailwind CSS at the stylesheet level
      // We verify that components don't break when prefers-reduced-motion is active
    });
  });

  describe('Focus State Transitions', () => {
    it('Button has focus-visible:ring with transition support', () => {
      const { container } = render(<Button>Focus Me</Button>);
      const button = container.querySelector('button');
      const classes = button?.className || '';

      expect(classes).toContain('focus-visible:outline-none');
      expect(classes).toContain('focus-visible:ring-2');
      expect(classes).toContain('focus-visible:ring-ring');
      // Button uses transition-all for interactive feedback (scale on press)
      expect(classes).toContain('transition-all');
    });

    it('Input has focus-visible:ring with transition-colors', () => {
      const { container } = render(<Input />);
      const input = container.querySelector('input');
      const classes = input?.className || '';

      expect(classes).toContain('focus-visible:outline-none');
      expect(classes).toContain('focus-visible:ring-2');
      expect(classes).toContain('transition-colors');
    });

    it('Input error state has destructive focus ring', () => {
      const { container } = render(<Input error />);
      const input = container.querySelector('input');
      const classes = input?.className || '';

      expect(classes).toContain('focus-visible:ring-destructive');
      expect(classes).toContain('transition-colors');
    });
  });

  describe('Animation Property Validation', () => {
    it('Button uses transition-all for interactive scale feedback', () => {
      // Button intentionally uses transition-all to support active:scale animation
      const { container: buttonContainer } = render(<Button>Test</Button>);
      const button = buttonContainer.querySelector('button');

      // Button should use transition-all for scale animation on press
      expect(button?.className).toContain('transition-all');
      expect(button?.className).toContain('active:scale-[0.98]');
      // Should respect reduced motion
      expect(button?.className).toContain('motion-reduce:transition-none');
      expect(button?.className).toContain('motion-reduce:active:scale-100');
    });

    it('Input uses transition-colors for safe color-only transitions', () => {
      const { container: inputContainer } = render(<Input />);
      const input = inputContainer.querySelector('input');

      // Input should use transition-colors, not transition-all
      expect(input?.className).not.toContain('transition-all');
      expect(input?.className).toContain('transition-colors');
    });

    it('Table row transitions only affect colors, not layout', () => {
      const { container } = render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Test</TableCell>
            </TableRow>
          </TableBody>
        </Table>,
      );

      const row = container.querySelector('tr');
      expect(row?.className).toContain('transition-colors');
      expect(row?.className).not.toContain('transition-all');
    });
  });

  describe('Disabled State Handling', () => {
    it('Button disabled state has opacity transition', () => {
      const { container } = render(<Button disabled>Disabled</Button>);
      const button = container.querySelector('button');
      const classes = button?.className || '';

      expect(classes).toContain('disabled:opacity-50');
      expect(classes).toContain('disabled:pointer-events-none');
      // Button uses transition-all for interactive feedback
      expect(classes).toContain('transition-all');
    });

    it('Input disabled state has opacity transition', () => {
      const { container } = render(<Input disabled />);
      const input = container.querySelector('input');
      const classes = input?.className || '';

      expect(classes).toContain('disabled:opacity-50');
      expect(classes).toContain('disabled:cursor-not-allowed');
      expect(classes).toContain('transition-colors');
    });
  });

  describe('Selected State Transitions', () => {
    it('TableRow selected state uses colors, not transforms', () => {
      const { container } = render(
        <Table>
          <TableBody>
            <TableRow selected>
              <TableCell>Selected</TableCell>
            </TableRow>
          </TableBody>
        </Table>,
      );

      const row = container.querySelector('tr');
      const classes = row?.className || '';

      expect(classes).toContain('bg-primary/8');
      expect(classes).toContain('transition-colors');
      expect(row?.getAttribute('data-state')).toBe('selected');
    });

    it('TableRow clickable state maintains transitions', () => {
      const { container } = render(
        <Table>
          <TableBody>
            <TableRow clickable>
              <TableCell>Clickable</TableCell>
            </TableRow>
          </TableBody>
        </Table>,
      );

      const row = container.querySelector('tr');
      const classes = row?.className || '';

      expect(classes).toContain('cursor-pointer');
      expect(classes).toContain('transition-colors');
      expect(classes).toContain('hover:bg-muted/50');
    });
  });

  describe('Component Variant Consistency', () => {
    it('All Button variants have consistent transition classes', () => {
      const variants = ['default', 'secondary', 'outline', 'ghost', 'destructive'] as const;
      const sizes = ['default', 'sm', 'lg', 'icon'] as const;

      variants.forEach((variant) => {
        sizes.forEach((size) => {
          const { container } = render(
            <Button variant={variant} size={size}>
              Test
            </Button>,
          );
          const button = container.querySelector('button');
          // Button uses transition-all for interactive scale feedback
          expect(button?.className).toContain('transition-all');
          expect(button?.className).toContain('active:scale-[0.98]');
        });
      });
    });

    it('Input with and without error state both have transitions', () => {
      const { container: normalContainer } = render(<Input />);
      const { container: errorContainer } = render(<Input error />);

      const normalInput = normalContainer.querySelector('input');
      const errorInput = errorContainer.querySelector('input');

      expect(normalInput?.className).toContain('transition-colors');
      expect(normalInput?.className).toContain('duration-200');

      expect(errorInput?.className).toContain('transition-colors');
      expect(errorInput?.className).toContain('duration-200');
    });
  });

  describe('Animation Performance Best Practices', () => {
    it('Input avoids animating box-shadow directly', () => {
      const { container: inputContainer } = render(<Input />);
      const input = inputContainer.querySelector('input');

      // Input should not have transition-shadow or transition-all
      expect(input?.className).not.toMatch(/transition-shadow/);
      expect(input?.className).not.toContain('transition-all');
    });

    it('Button uses transition-all with reduced motion support', () => {
      const { container: buttonContainer } = render(<Button>Test</Button>);
      const button = buttonContainer.querySelector('button');

      // Button intentionally uses transition-all for scale animation
      expect(button?.className).toContain('transition-all');
      // But respects reduced motion preference
      expect(button?.className).toContain('motion-reduce:transition-none');
    });

    it('Focus rings appear with proper focus-visible support', () => {
      const { container } = render(<Button>Focus Test</Button>);
      const button = container.querySelector('button');
      const classes = button?.className || '';

      // Focus ring should use focus-visible
      expect(classes).toContain('focus-visible:ring-2');
      expect(classes).toContain('focus-visible:outline-none');
    });

    it('Button hover states work with transition-all', () => {
      const { container } = render(<Button>Hover Test</Button>);
      const button = container.querySelector('button');
      const classes = button?.className || '';

      // Button uses transition-all for both color and scale transitions
      expect(classes).toContain('transition-all');
      expect(classes).toMatch(/hover:bg-/);
      expect(classes).toContain('active:scale-[0.98]');
    });
  });

  describe('Transition Duration Validation', () => {
    it('All transition durations are ≤200ms or use default', () => {
      // Button uses transition-all with explicit duration-150
      const { container: buttonContainer } = render(<Button>Test</Button>);
      const button = buttonContainer.querySelector('button');
      expect(button?.className).toContain('transition-all');
      expect(button?.className).toContain('duration-150');
      expect(button?.className).not.toMatch(/duration-(300|500|700|1000)/);

      // Input explicitly uses duration-200
      const { container: inputContainer } = render(<Input />);
      const input = inputContainer.querySelector('input');
      expect(input?.className).toContain('duration-200');

      // TableRow uses default (150ms)
      const { container: rowContainer } = render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Test</TableCell>
            </TableRow>
          </TableBody>
        </Table>,
      );
      const row = rowContainer.querySelector('tr');
      expect(row?.className).toContain('transition-colors');
      expect(row?.className).not.toMatch(/duration-(300|500|700|1000)/);
    });
  });
});
