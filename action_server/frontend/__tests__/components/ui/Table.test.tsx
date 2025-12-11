import React from 'react';
import { render, screen } from '../../utils/test-utils';
import { describe, it, expect } from 'vitest';

import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from '@/core/components/ui/Table';

describe('Table component — visual and interaction contracts', () => {
  describe('Header styling', () => {
    it('applies bg-gray-50, border-b, and font-medium to header cells', () => {
      const { getByText } = render(
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Value</TableHead>
            </TableRow>
          </TableHeader>
        </Table>,
      );

      const nameHead = getByText('Name');
      expect(nameHead.className).toContain('bg-gray-50');
      expect(nameHead.className).toContain('border-b');
      expect(nameHead.className).toContain('font-medium');
    });

    it('applies uppercase and tracking-wide to header text', () => {
      const { getByText } = render(
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Header</TableHead>
            </TableRow>
          </TableHeader>
        </Table>,
      );

      const header = getByText('Header');
      expect(header.className).toContain('uppercase');
      expect(header.className).toContain('tracking-wide');
    });

    it('applies text-gray-500 color to header text', () => {
      const { getByText } = render(
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Column</TableHead>
            </TableRow>
          </TableHeader>
        </Table>,
      );

      const header = getByText('Column');
      expect(header.className).toContain('text-gray-500');
    });
  });

  describe('Row hover states', () => {
    it('applies hover:bg-gray-50 to table rows', () => {
      const { getByText } = render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Regular row</TableCell>
            </TableRow>
          </TableBody>
        </Table>,
      );

      const row = getByText('Regular row').closest('tr') as HTMLElement;
      expect(row).toBeTruthy();
      expect(row.className).toContain('hover:bg-gray-50');
    });

    it('applies transition-colors to table rows for smooth hover effect', () => {
      const { getByText } = render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Transition row</TableCell>
            </TableRow>
          </TableBody>
        </Table>,
      );

      const row = getByText('Transition row').closest('tr') as HTMLElement;
      expect(row).toBeTruthy();
      expect(row.className).toContain('transition-colors');
    });
  });

  describe('Selected row state', () => {
    it('applies bg-blue-50 when selected prop is true', () => {
      const { getByText } = render(
        <Table>
          <TableBody>
            <TableRow selected>
              <TableCell>Selected row</TableCell>
            </TableRow>
          </TableBody>
        </Table>,
      );

      const selected = getByText('Selected row').closest('tr') as HTMLElement;
      expect(selected).toBeTruthy();
      expect(selected.className).toContain('bg-blue-50');
    });

    it('sets data-state="selected" when selected prop is true', () => {
      const { getByText } = render(
        <Table>
          <TableBody>
            <TableRow selected>
              <TableCell>Selected row</TableCell>
            </TableRow>
          </TableBody>
        </Table>,
      );

      const row = getByText('Selected row').closest('tr') as HTMLElement;
      expect(row).toBeTruthy();
      expect(row.getAttribute('data-state')).toBe('selected');
    });

    it('does not set data-state when selected is false', () => {
      const { getByText } = render(
        <Table>
          <TableBody>
            <TableRow selected={false}>
              <TableCell>Not selected</TableCell>
            </TableRow>
          </TableBody>
        </Table>,
      );

      const row = getByText('Not selected').closest('tr') as HTMLElement;
      expect(row).toBeTruthy();
      expect(row.getAttribute('data-state')).toBeNull();
    });

    it('maintains hover state on selected rows', () => {
      const { getByText } = render(
        <Table>
          <TableBody>
            <TableRow selected>
              <TableCell>Selected with hover</TableCell>
            </TableRow>
          </TableBody>
        </Table>,
      );

      const row = getByText('Selected with hover').closest('tr') as HTMLElement;
      expect(row).toBeTruthy();
      expect(row.className).toContain('bg-blue-50');
      expect(row.className).toContain('hover:bg-gray-50');
    });
  });

  describe('Clickable cursor', () => {
    it('applies cursor-pointer when clickable prop is true', () => {
      const { getByText } = render(
        <Table>
          <TableBody>
            <TableRow clickable>
              <TableCell>Clickable row</TableCell>
            </TableRow>
          </TableBody>
        </Table>,
      );

      const el = getByText('Clickable row').closest('tr') as HTMLElement;
      expect(el).toBeTruthy();
      expect(el.className).toContain('cursor-pointer');
    });

    it('does not apply cursor-pointer when clickable prop is false', () => {
      const { getByText } = render(
        <Table>
          <TableBody>
            <TableRow clickable={false}>
              <TableCell>Not clickable</TableCell>
            </TableRow>
          </TableBody>
        </Table>,
      );

      const el = getByText('Not clickable').closest('tr') as HTMLElement;
      expect(el).toBeTruthy();
      expect(el.className).not.toContain('cursor-pointer');
    });

    it('applies cursor-pointer on selected and clickable rows', () => {
      const { getByText } = render(
        <Table>
          <TableBody>
            <TableRow selected clickable>
              <TableCell>Selected and clickable</TableCell>
            </TableRow>
          </TableBody>
        </Table>,
      );

      const row = getByText('Selected and clickable').closest('tr') as HTMLElement;
      expect(row).toBeTruthy();
      expect(row.className).toContain('cursor-pointer');
      expect(row.className).toContain('bg-blue-50');
    });
  });

  describe('Last row border removal', () => {
    it('applies last:border-0 class to rows', () => {
      const { getByText } = render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>First</TableCell>
            </TableRow>
            <TableRow>
              <TableCell>Last</TableCell>
            </TableRow>
          </TableBody>
        </Table>,
      );

      const lastRow = getByText('Last').closest('tr') as HTMLElement;
      expect(lastRow).toBeTruthy();
      expect(lastRow.className).toMatch(/last:border-0|border-0/);
    });

    it('applies border-b to non-last rows', () => {
      const { getByText } = render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>First</TableCell>
            </TableRow>
            <TableRow>
              <TableCell>Second</TableCell>
            </TableRow>
          </TableBody>
        </Table>,
      );

      const firstRow = getByText('First').closest('tr') as HTMLElement;
      expect(firstRow).toBeTruthy();
      expect(firstRow.className).toContain('border-b');
    });
  });

  describe('Semantic HTML structure', () => {
    it('renders thead element for TableHeader', () => {
      const { container } = render(
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Header</TableHead>
            </TableRow>
          </TableHeader>
        </Table>,
      );

      const thead = container.querySelector('thead');
      expect(thead).toBeTruthy();
    });

    it('renders tbody element for TableBody', () => {
      const { container } = render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Cell</TableCell>
            </TableRow>
          </TableBody>
        </Table>,
      );

      const tbody = container.querySelector('tbody');
      expect(tbody).toBeTruthy();
    });

    it('renders th elements for TableHead', () => {
      const { getByText } = render(
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Column Header</TableHead>
            </TableRow>
          </TableHeader>
        </Table>,
      );

      const header = getByText('Column Header');
      expect(header.tagName).toBe('TH');
    });

    it('renders td elements for TableCell', () => {
      const { getByText } = render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Cell Content</TableCell>
            </TableRow>
          </TableBody>
        </Table>,
      );

      const cell = getByText('Cell Content');
      expect(cell.tagName).toBe('TD');
    });

    it('renders a complete table structure', () => {
      const { container } = render(
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow>
              <TableCell>Item 1</TableCell>
              <TableCell>Active</TableCell>
            </TableRow>
            <TableRow>
              <TableCell>Item 2</TableCell>
              <TableCell>Inactive</TableCell>
            </TableRow>
          </TableBody>
        </Table>,
      );

      const table = container.querySelector('table');
      const thead = container.querySelector('thead');
      const tbody = container.querySelector('tbody');
      const ths = container.querySelectorAll('th');
      const tds = container.querySelectorAll('td');

      expect(table).toBeTruthy();
      expect(thead).toBeTruthy();
      expect(tbody).toBeTruthy();
      expect(ths.length).toBe(2);
      expect(tds.length).toBe(4);
    });
  });

  describe('Table base styles', () => {
    it('applies w-full to table', () => {
      const { container } = render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Content</TableCell>
            </TableRow>
          </TableBody>
        </Table>,
      );

      const table = container.querySelector('table');
      expect(table).toBeTruthy();
      expect(table?.className).toContain('w-full');
    });

    it('applies text-sm to table', () => {
      const { container } = render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Content</TableCell>
            </TableRow>
          </TableBody>
        </Table>,
      );

      const table = container.querySelector('table');
      expect(table).toBeTruthy();
      expect(table?.className).toContain('text-sm');
    });

    it('wraps table in overflow-auto container', () => {
      const { container } = render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Content</TableCell>
            </TableRow>
          </TableBody>
        </Table>,
      );

      const wrapper = container.querySelector('.overflow-auto');
      expect(wrapper).toBeTruthy();
    });
  });

  describe('Cell styling', () => {
    it('applies text-gray-700 to table cells', () => {
      const { getByText } = render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Data</TableCell>
            </TableRow>
          </TableBody>
        </Table>,
      );

      const cell = getByText('Data');
      expect(cell.className).toContain('text-gray-700');
    });

    it('applies proper padding to cells', () => {
      const { getByText } = render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Padded cell</TableCell>
            </TableRow>
          </TableBody>
        </Table>,
      );

      const cell = getByText('Padded cell');
      expect(cell.className).toContain('p-4');
    });

    it('applies proper padding to header cells', () => {
      const { getByText } = render(
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Header</TableHead>
            </TableRow>
          </TableHeader>
        </Table>,
      );

      const header = getByText('Header');
      expect(header.className).toContain('px-4');
    });
  });

  describe('Component exports', () => {
    it('exports all required table components', () => {
      expect(Table).toBeDefined();
      expect(TableHeader).toBeDefined();
      expect(TableBody).toBeDefined();
      expect(TableRow).toBeDefined();
      expect(TableHead).toBeDefined();
      expect(TableCell).toBeDefined();
    });

    it('all components have display names', () => {
      expect(Table.displayName).toBe('Table');
      expect(TableHeader.displayName).toBe('TableHeader');
      expect(TableBody.displayName).toBe('TableBody');
      expect(TableRow.displayName).toBe('TableRow');
      expect(TableHead.displayName).toBe('TableHead');
      expect(TableCell.displayName).toBe('TableCell');
    });
  });
});
