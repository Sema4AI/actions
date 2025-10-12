import React from 'react';
import { render } from '../../utils/test-utils';
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
  it('applies header styling to the header cells (bg + border + font)', () => {
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
    // Expect header to use font-medium and visual separation
    expect(nameHead.className).toContain('font-medium');
    expect(nameHead.className).toMatch(/border|bg-gray-50/);
  });

  it('supports a selected prop that applies selected styling', () => {
    const { getByText } = render(
      <Table>
        <TableBody>
          <TableRow> 
            <TableCell>Row A</TableCell>
          </TableRow>
          <TableRow {...({ selected: true } as any)}>
            <TableCell>Row B</TableCell>
          </TableRow>
        </TableBody>
      </Table>,
    );

    const selected = getByText('Row B').closest('tr') as HTMLElement;
    expect(selected).toBeTruthy();
    // Selected row should have a distinct background (design: bg-blue-50)
    expect(selected.className).toContain('bg-blue-50');
  });

  it('supports a clickable prop that sets cursor-pointer on rows', () => {
    const { getByText } = render(
      <Table>
        <TableBody>
          <TableRow {...({ clickable: true } as any)}>
            <TableCell>Clickable row</TableCell>
          </TableRow>
        </TableBody>
      </Table>,
    );

    const el = getByText('Clickable row').closest('tr') as HTMLElement;
    expect(el).toBeTruthy();
    expect(el.className).toContain('cursor-pointer');
  });

  it('removes bottom border from last row', () => {
    const { getByText } = render(
      <Table>
        <TableBody>
          <TableRow>
            <TableCell>One</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Two</TableCell>
          </TableRow>
        </TableBody>
      </Table>,
    );

    const last = getByText('Two').closest('tr') as HTMLElement;
    expect(last).toBeTruthy();
    expect(last.className).toMatch(/border-0/);
  });
});
