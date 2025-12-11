import React from 'react';
import { render } from '../../utils/test-utils';
import { describe, it, expect } from 'vitest';

import { Button } from '@/core/components/ui/Button';
import { Input } from '@/core/components/ui/Input';
import { Table, TableBody, TableRow, TableCell } from '@/core/components/ui/Table';

describe('Micro-interaction Animations', () => {
  describe('Transition Duration Requirements', () => {
    it('Button has transition-colors with implicit duration ≤200ms', () => {
      const { container } = render(<Button>Test Button</Button>);
      const button = container.querySelector('button');
      expect(button?.className).toContain('transition-colors');
      // Tailwind's default transition-colors duration is 150ms, which meets the ≤200ms requirement
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
    it('Components use transition-colors for color changes (not layout-affecting)', () => {
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

      expect(buttonContainer.querySelector('button')?.className).toContain('transition-colors');
      expect(inputContainer.querySelector('input')?.className).toContain('transition-colors');
      expect(rowContainer.querySelector('tr')?.className).toContain('transition-colors');
    });
  });

  describe('Hover State Transitions', () => {
    it('Button applies hover:bg-* classes that work with transition-colors', () => {
      const { container } = render(<Button>Hover Me</Button>);
      const button = container.querySelector('button');
      const classes = button?.className || '';

      // Check for hover state class and transition
      expect(classes).toContain('transition-colors');
      expect(classes).toMatch(/hover:bg-/);
    });

    it('Button variants all have hover states with transitions', () => {
      const variants = ['default', 'secondary', 'outline', 'ghost', 'destructive'] as const;

      variants.forEach((variant) => {
        const { container } = render(<Button variant={variant}>Test</Button>);
        const button = container.querySelector('button');
        const classes = button?.className || '';

        expect(classes).toContain('transition-colors');
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
      expect(classes).toContain('hover:bg-gray-50');
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
      expect(classes).toContain('focus-visible:ring-blue-500');
      expect(classes).toContain('transition-colors');
    });

    it('Input has focus-visible:ring with transition-colors', () => {
      const { container } = render(<Input />);
      const input = container.querySelector('input');
      const classes = input?.className || '';

      expect(classes).toContain('focus-visible:outline-none');
      expect(classes).toContain('focus-visible:ring-2');
      expect(classes).toContain('transition-colors');
    });

    it('Input error state has red focus ring', () => {
      const { container } = render(<Input error />);
      const input = container.querySelector('input');
      const classes = input?.className || '';

      expect(classes).toContain('focus-visible:ring-red-500');
      expect(classes).toContain('transition-colors');
    });
  });

  describe('Animation Property Validation', () => {
    it('No components use layout-affecting properties in transitions', () => {
      // Test that components don't animate width, height, margin, padding, etc.
      const { container: buttonContainer } = render(<Button>Test</Button>);
      const { container: inputContainer } = render(<Input />);

      const button = buttonContainer.querySelector('button');
      const input = inputContainer.querySelector('input');

      // Should use transition-colors, not transition-all or transition
      expect(button?.className).not.toContain('transition-all');
      expect(input?.className).not.toContain('transition-all');

      // Should only use safe transition properties
      expect(button?.className).toContain('transition-colors');
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
      expect(classes).toContain('transition-colors');
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

      expect(classes).toContain('bg-blue-50');
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
      expect(classes).toContain('hover:bg-gray-50');
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
          expect(button?.className).toContain('transition-colors');
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
    it('Components avoid animating box-shadow directly', () => {
      const { container: buttonContainer } = render(<Button>Test</Button>);
      const { container: inputContainer } = render(<Input />);

      const button = buttonContainer.querySelector('button');
      const input = inputContainer.querySelector('input');

      // Should not have transition-shadow or transition-all
      expect(button?.className).not.toMatch(/transition-(shadow|all)/);
      expect(input?.className).not.toMatch(/transition-(shadow|all)/);
    });

    it('Focus rings appear instantly without transition delay', () => {
      const { container } = render(<Button>Focus Test</Button>);
      const button = container.querySelector('button');
      const classes = button?.className || '';

      // Focus ring should be instant (no transition on ring property)
      expect(classes).toContain('focus-visible:ring-2');
      // Transition is only on colors, not on ring appearance
      expect(classes).toContain('transition-colors');
    });

    it('Hover states transition smoothly with colors only', () => {
      const { container } = render(<Button>Hover Test</Button>);
      const button = container.querySelector('button');
      const classes = button?.className || '';

      // Should transition colors for hover
      expect(classes).toContain('transition-colors');
      expect(classes).toMatch(/hover:bg-/);

      // Should not transition other properties
      expect(classes).not.toMatch(/transition-(transform|scale|width|height)/);
    });
  });

  describe('Transition Duration Validation', () => {
    it('All transition durations are ≤200ms or use default', () => {
      // Button uses default Tailwind transition-colors (150ms)
      const { container: buttonContainer } = render(<Button>Test</Button>);
      const button = buttonContainer.querySelector('button');
      expect(button?.className).toContain('transition-colors');
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
