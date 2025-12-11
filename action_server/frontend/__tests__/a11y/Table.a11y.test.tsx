import React from 'react';
import { render, userEvent } from '../utils/test-utils';
import { describe, it, expect, vi } from 'vitest';
import { runAxe } from './setup';

import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
  TableCaption,
} from '@/core/components/ui/Table';

describe('Table accessibility', () => {
  it('has no axe violations in basic state', async () => {
    const { container } = render(
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Email</TableHead>
            <TableHead>Role</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell>John Doe</TableCell>
            <TableCell>john@example.com</TableCell>
            <TableCell>Admin</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Jane Smith</TableCell>
            <TableCell>jane@example.com</TableCell>
            <TableCell>User</TableCell>
          </TableRow>
        </TableBody>
      </Table>,
    );

    const results = await runAxe(container);
    expect(results).toHaveNoViolations();
  });

  it('has no axe violations with caption', async () => {
    const { container } = render(
      <Table>
        <TableCaption>List of team members</TableCaption>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Email</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell>John Doe</TableCell>
            <TableCell>john@example.com</TableCell>
          </TableRow>
        </TableBody>
      </Table>,
    );

    const results = await runAxe(container);
    expect(results).toHaveNoViolations();
  });

  it('has no axe violations with aria-label', async () => {
    const { container } = render(
      <Table aria-label="Team members table">
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Email</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell>John Doe</TableCell>
            <TableCell>john@example.com</TableCell>
          </TableRow>
        </TableBody>
      </Table>,
    );

    const results = await runAxe(container);
    expect(results).toHaveNoViolations();
  });

  it('has no axe violations with selected rows', async () => {
    const { container } = render(
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Email</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow selected>
            <TableCell>John Doe</TableCell>
            <TableCell>john@example.com</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Jane Smith</TableCell>
            <TableCell>jane@example.com</TableCell>
          </TableRow>
        </TableBody>
      </Table>,
    );

    const results = await runAxe(container);
    expect(results).toHaveNoViolations();
  });

  it('uses semantic HTML for table structure', () => {
    const { container } = render(
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Column 1</TableHead>
            <TableHead>Column 2</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell>Cell 1</TableCell>
            <TableCell>Cell 2</TableCell>
          </TableRow>
        </TableBody>
      </Table>,
    );

    // Verify semantic HTML structure
    const table = container.querySelector('table');
    expect(table).toBeTruthy();

    const thead = container.querySelector('thead');
    expect(thead).toBeTruthy();

    const tbody = container.querySelector('tbody');
    expect(tbody).toBeTruthy();

    const th = container.querySelectorAll('th');
    expect(th.length).toBe(2);

    const td = container.querySelectorAll('td');
    expect(td.length).toBe(2);
  });

  it('supports scope attribute on table headers', () => {
    const { container } = render(
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead scope="col">Name</TableHead>
            <TableHead scope="col">Email</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell>John Doe</TableCell>
            <TableCell>john@example.com</TableCell>
          </TableRow>
        </TableBody>
      </Table>,
    );

    const headers = container.querySelectorAll('th[scope="col"]');
    expect(headers.length).toBe(2);
  });

  it('supports aria-label on Table component', () => {
    const { container } = render(
      <Table aria-label="User data table">
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell>John Doe</TableCell>
          </TableRow>
        </TableBody>
      </Table>,
    );

    const table = container.querySelector('table');
    expect(table?.getAttribute('aria-label')).toBe('User data table');
  });

  it('supports keyboard navigation for clickable rows', async () => {
    const handleClick = vi.fn();
    const handleKeyDown = vi.fn((e: React.KeyboardEvent) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        handleClick();
      }
    });

    const { getByRole } = render(
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow
            clickable
            onClick={handleClick}
            onKeyDown={handleKeyDown}
            tabIndex={0}
            role="button"
          >
            <TableCell>John Doe</TableCell>
          </TableRow>
        </TableBody>
      </Table>,
    );

    const row = getByRole('button');
    expect(row).toBeTruthy();

    // Test Enter key
    row.focus();
    await userEvent.keyboard('{Enter}');
    expect(handleClick).toHaveBeenCalledTimes(1);

    // Test Space key
    await userEvent.keyboard(' ');
    expect(handleClick).toHaveBeenCalledTimes(2);
  });

  it('applies clickable cursor style for clickable rows', () => {
    const { container } = render(
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow clickable>
            <TableCell>John Doe</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Jane Smith</TableCell>
          </TableRow>
        </TableBody>
      </Table>,
    );

    const rows = container.querySelectorAll('tbody tr');
    expect(rows[0].className).toContain('cursor-pointer');
    expect(rows[1].className).not.toContain('cursor-pointer');
  });

  it('announces row selection state with data-state attribute', () => {
    const { container } = render(
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow selected>
            <TableCell>John Doe</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Jane Smith</TableCell>
          </TableRow>
        </TableBody>
      </Table>,
    );

    const rows = container.querySelectorAll('tbody tr');
    expect(rows[0].getAttribute('data-state')).toBe('selected');
    expect(rows[1].getAttribute('data-state')).toBeNull();
  });

  it('supports aria-selected for row selection', () => {
    const { container } = render(
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow selected aria-selected="true">
            <TableCell>John Doe</TableCell>
          </TableRow>
          <TableRow aria-selected="false">
            <TableCell>Jane Smith</TableCell>
          </TableRow>
        </TableBody>
      </Table>,
    );

    const rows = container.querySelectorAll('tbody tr');
    expect(rows[0].getAttribute('aria-selected')).toBe('true');
    expect(rows[1].getAttribute('aria-selected')).toBe('false');
  });

  it('has no axe violations with complex table structure', async () => {
    const { container } = render(
      <Table aria-label="Complex data table">
        <TableCaption>Detailed user information</TableCaption>
        <TableHeader>
          <TableRow>
            <TableHead scope="col">ID</TableHead>
            <TableHead scope="col">Name</TableHead>
            <TableHead scope="col">Email</TableHead>
            <TableHead scope="col">Role</TableHead>
            <TableHead scope="col">Status</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow selected aria-selected="true" data-testid="row-1">
            <TableCell>1</TableCell>
            <TableCell>John Doe</TableCell>
            <TableCell>john@example.com</TableCell>
            <TableCell>Admin</TableCell>
            <TableCell>Active</TableCell>
          </TableRow>
          <TableRow clickable tabIndex={0} data-testid="row-2">
            <TableCell>2</TableCell>
            <TableCell>Jane Smith</TableCell>
            <TableCell>jane@example.com</TableCell>
            <TableCell>User</TableCell>
            <TableCell>Active</TableCell>
          </TableRow>
          <TableRow data-testid="row-3">
            <TableCell>3</TableCell>
            <TableCell>Bob Johnson</TableCell>
            <TableCell>bob@example.com</TableCell>
            <TableCell>User</TableCell>
            <TableCell>Inactive</TableCell>
          </TableRow>
        </TableBody>
      </Table>,
    );

    const results = await runAxe(container);
    expect(results).toHaveNoViolations();
  });

  it('maintains accessibility with empty table body', async () => {
    const { container } = render(
      <Table aria-label="Empty table">
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Email</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {/* Empty body */}
        </TableBody>
      </Table>,
    );

    const results = await runAxe(container);
    expect(results).toHaveNoViolations();
  });

  it('supports custom ARIA attributes', () => {
    const { container } = render(
      <Table
        aria-label="Custom table"
        aria-describedby="table-description"
        role="table"
      >
        <TableHeader>
          <TableRow role="row">
            <TableHead role="columnheader">Name</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow role="row">
            <TableCell role="cell">John Doe</TableCell>
          </TableRow>
        </TableBody>
      </Table>,
    );

    const table = container.querySelector('table');
    expect(table?.getAttribute('aria-label')).toBe('Custom table');
    expect(table?.getAttribute('aria-describedby')).toBe('table-description');
    expect(table?.getAttribute('role')).toBe('table');

    const th = container.querySelector('th');
    expect(th?.getAttribute('role')).toBe('columnheader');

    const td = container.querySelector('td');
    expect(td?.getAttribute('role')).toBe('cell');
  });

  it('handles keyboard focus correctly for clickable rows', async () => {
    const handleClick = vi.fn();

    const { container } = render(
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow clickable tabIndex={0} onClick={handleClick}>
            <TableCell>Row 1</TableCell>
          </TableRow>
          <TableRow clickable tabIndex={0} onClick={handleClick}>
            <TableCell>Row 2</TableCell>
          </TableRow>
          <TableRow clickable tabIndex={0} onClick={handleClick}>
            <TableCell>Row 3</TableCell>
          </TableRow>
        </TableBody>
      </Table>,
    );

    const rows = container.querySelectorAll('tbody tr');

    // Verify all rows are keyboard focusable
    rows.forEach((row) => {
      expect(row.getAttribute('tabIndex')).toBe('0');
    });

    // Test that clicking works
    await userEvent.click(rows[0]);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
