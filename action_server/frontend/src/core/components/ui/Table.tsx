import * as React from 'react';

import { cn } from '@/shared/utils/cn';

const Table = React.forwardRef<HTMLTableElement, React.HTMLAttributes<HTMLTableElement>>(
  ({ className, ...props }, ref) => (
    <div className="w-full overflow-auto">
      <table
        ref={ref}
        className={cn('w-full caption-bottom text-sm', className)}
        {...props}
      />
    </div>
  ),
);
Table.displayName = 'Table';

const TableHeader = React.forwardRef<
  HTMLTableSectionElement,
  React.HTMLAttributes<HTMLTableSectionElement>
>(({ className, ...props }, ref) => (
  // Ensure header rows receive a light background and bottom border so header cells are
  // visually distinct for screen and visual tests.
  <thead ref={ref} className={cn('[&_tr]:border-b [&_tr]:border-border [&_tr]:bg-muted/50', className)} {...props} />
));
TableHeader.displayName = 'TableHeader';

const TableBody = React.forwardRef<
  HTMLTableSectionElement,
  React.HTMLAttributes<HTMLTableSectionElement>
>(({ className, ...props }, ref) => (
  // Remove border from the last row to make table endings clean in visual tests
  <tbody ref={ref} className={cn('[&_tr:last-child]:border-0', className)} {...props} />
));
TableBody.displayName = 'TableBody';

const TableFooter = React.forwardRef<
  HTMLTableSectionElement,
  React.HTMLAttributes<HTMLTableSectionElement>
>(({ className, ...props }, ref) => (
  <tfoot ref={ref} className={cn('bg-muted font-medium text-card-foreground', className)} {...props} />
));
TableFooter.displayName = 'TableFooter';

interface TableRowProps extends React.HTMLAttributes<HTMLTableRowElement> {
  selected?: boolean;
  clickable?: boolean;
}
const TableRow = React.forwardRef<HTMLTableRowElement, TableRowProps>(({ className, selected = false, clickable = false, ...props }, ref) => (
  <tr
    ref={ref}
    data-state={selected ? 'selected' : undefined}
    className={cn(
      // Base styles
      'border-b border-border last:border-0',
      // Hover states
      'hover:bg-muted/50',
      // State variants
      selected && 'bg-primary/8',
      clickable && 'cursor-pointer',
      // Animations
      'transition-colors duration-200',
      'motion-reduce:transition-none',
      className,
    )}
    {...props}
  />
));
TableRow.displayName = 'TableRow';

interface TableHeadProps extends React.ThHTMLAttributes<HTMLTableCellElement> {}
const TableHead = React.forwardRef<HTMLTableCellElement, TableHeadProps>(({ className, ...props }, ref) => (
  <th
    ref={ref}
    className={cn(
      // Layout
      'h-11 px-4 text-left align-middle',
      // Typography
      'text-xs font-medium uppercase tracking-wide',
      // Colors & style
      'text-muted-foreground bg-muted/50 border-b border-border',
      className,
    )}
    {...props}
  />
));
TableHead.displayName = 'TableHead';

const TableCell = React.forwardRef<HTMLTableCellElement, React.TdHTMLAttributes<HTMLTableCellElement>>(
  ({ className, ...props }, ref) => (
    <td
      ref={ref}
      className={cn('p-4 align-middle text-sm text-card-foreground', className)}
      {...props}
    />
  ),
);
TableCell.displayName = 'TableCell';

const TableCaption = React.forwardRef<
  HTMLTableCaptionElement,
  React.HTMLAttributes<HTMLTableCaptionElement>
>(({ className, ...props }, ref) => (
  <caption ref={ref} className={cn('mt-4 text-sm text-muted-foreground', className)} {...props} />
));
TableCaption.displayName = 'TableCaption';

export {
  Table,
  TableHeader,
  TableBody,
  TableFooter,
  TableRow,
  TableHead,
  TableCell,
  TableCaption,
};

const TableEmptyState = ({ className, children }: { className?: string; children?: React.ReactNode }) => (
  <div className={cn('flex items-center justify-center p-12 text-center text-sm text-muted-foreground', className)}>
    {children}
  </div>
);

export { TableEmptyState };
