/**
 * Component Type Contracts for Community UI Enhancement
 * 
 * This file defines the TypeScript interfaces for all enhanced and new components.
 * It serves as the source of truth for component APIs during implementation.
 * 
 * @feature 004-community-ui-enhancement
 * @package action-server/frontend
 */

import * as React from 'react';
import * as DialogPrimitive from '@radix-ui/react-dialog';
import * as DropdownMenuPrimitive from '@radix-ui/react-dropdown-menu';

// ============================================================================
// Input Component
// ============================================================================

/**
 * Enhanced single-line text input with error state support
 * 
 * @example
 * ```tsx
 * <Input 
 *   type="text" 
 *   placeholder="Enter action name" 
 *   error={!!errors.name}
 * />
 * ```
 */
export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  /** Display error styling (red border, red focus ring) */
  error?: boolean;
}

// ============================================================================
// Textarea Component
// ============================================================================

/**
 * Enhanced multi-line text input with code/JSON support
 * 
 * @example
 * ```tsx
 * <Textarea 
 *   placeholder="Enter JSON payload" 
 *   spellCheck={false}  // Triggers monospace font
 *   error={!!errors.payload}
 * />
 * ```
 */
export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  /** Display error styling (red border, red focus ring) */
  error?: boolean;
}

// ============================================================================
// Dialog Component
// ============================================================================

/**
 * Dialog root component (wrapper for all dialog sub-components)
 * 
 * @example
 * ```tsx
 * <Dialog open={isOpen} onOpenChange={setIsOpen}>
 *   <DialogContent>
 *     <DialogHeader>
 *       <DialogTitle>Confirm Action</DialogTitle>
 *       <DialogDescription>Are you sure you want to delete this?</DialogDescription>
 *     </DialogHeader>
 *     <DialogFooter>
 *       <Button variant="outline" onClick={() => setIsOpen(false)}>Cancel</Button>
 *       <Button variant="destructive" onClick={handleDelete}>Delete</Button>
 *     </DialogFooter>
 *   </DialogContent>
 * </Dialog>
 * ```
 */
export type DialogProps = React.ComponentPropsWithoutRef<typeof DialogPrimitive.Root>;

/**
 * Dialog trigger button (opens dialog when clicked)
 */
export type DialogTriggerProps = React.ComponentPropsWithoutRef<typeof DialogPrimitive.Trigger>;

/**
 * Dialog content container (main visible dialog with backdrop)
 */
export interface DialogContentProps 
  extends React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content> {
  // Inherits all Radix Dialog.Content props:
  // - onEscapeKeyDown: (event: KeyboardEvent) => void
  // - onPointerDownOutside: (event: PointerDownOutsideEvent) => void
  // - forceMount: boolean
}

/**
 * Dialog header section (contains title and description)
 */
export type DialogHeaderProps = React.HTMLAttributes<HTMLDivElement>;

/**
 * Dialog footer section (contains action buttons)
 */
export type DialogFooterProps = React.HTMLAttributes<HTMLDivElement>;

/**
 * Dialog title (required for accessibility)
 */
export type DialogTitleProps = React.ComponentPropsWithoutRef<typeof DialogPrimitive.Title>;

/**
 * Dialog description (optional, provides context)
 */
export type DialogDescriptionProps = React.ComponentPropsWithoutRef<typeof DialogPrimitive.Description>;

// ============================================================================
// Table Component
// ============================================================================

/**
 * Table root component
 * 
 * @example
 * ```tsx
 * <Table>
 *   <TableHeader>
 *     <TableRow>
 *       <TableHead>Name</TableHead>
 *       <TableHead>Status</TableHead>
 *     </TableRow>
 *   </TableHeader>
 *   <TableBody>
 *     <TableRow clickable onClick={() => navigate(`/actions/${id}`)}>
 *       <TableCell>{name}</TableCell>
 *       <TableCell><Badge variant="success">Running</Badge></TableCell>
 *     </TableRow>
 *   </TableBody>
 * </Table>
 * ```
 */
export interface TableProps extends React.HTMLAttributes<HTMLTableElement> {
  // No custom props - uses standard table element
}

/**
 * Table header container (<thead> element)
 */
export type TableHeaderProps = React.HTMLAttributes<HTMLTableSectionElement>;

/**
 * Table body container (<tbody> element)
 */
export type TableBodyProps = React.HTMLAttributes<HTMLTableSectionElement>;

/**
 * Table row with hover and selected states
 */
export interface TableRowProps extends React.HTMLAttributes<HTMLTableRowElement> {
  /** Highlight row with blue background (for selected state) */
  selected?: boolean;
  /** Make row clickable (shows pointer cursor, applies hover state) */
  clickable?: boolean;
}

/**
 * Table header cell (<th> element)
 */
export type TableHeadProps = React.ThHTMLAttributes<HTMLTableCellElement>;

/**
 * Table data cell (<td> element)
 */
export type TableCellProps = React.TdHTMLAttributes<HTMLTableCellElement>;

// ============================================================================
// DropdownMenu Component
// ============================================================================

/**
 * DropdownMenu root component (wrapper for menu sub-components)
 * 
 * @example
 * ```tsx
 * <DropdownMenu>
 *   <DropdownMenuTrigger asChild>
 *     <Button variant="outline">Options</Button>
 *   </DropdownMenuTrigger>
 *   <DropdownMenuContent>
 *     <DropdownMenuItem onClick={handleEdit}>Edit</DropdownMenuItem>
 *     <DropdownMenuSeparator />
 *     <DropdownMenuItem destructive onClick={handleDelete}>Delete</DropdownMenuItem>
 *   </DropdownMenuContent>
 * </DropdownMenu>
 * ```
 */
export type DropdownMenuProps = React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Root>;

/**
 * DropdownMenu trigger button (opens menu when clicked)
 */
export type DropdownMenuTriggerProps = React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Trigger>;

/**
 * DropdownMenu content container (visible menu)
 */
export interface DropdownMenuContentProps 
  extends React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Content> {
  // Inherits Radix props:
  // - sideOffset: number (distance from trigger)
  // - align: 'start' | 'center' | 'end' (alignment to trigger)
}

/**
 * DropdownMenu item (single menu option)
 */
export interface DropdownMenuItemProps 
  extends React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Item> {
  /** Show destructive styling (red text/icon for dangerous actions) */
  destructive?: boolean;
}

/**
 * DropdownMenu separator (horizontal divider)
 */
export type DropdownMenuSeparatorProps = React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Separator>;

// ============================================================================
// Badge Component (New)
// ============================================================================

/**
 * Status badge with semantic color variants
 * 
 * @example
 * ```tsx
 * <Badge variant="success">Completed</Badge>
 * <Badge variant="error">Failed</Badge>
 * <Badge variant="info">Running</Badge>
 * ```
 */
export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  /** Semantic variant for status representation */
  variant?: 'success' | 'error' | 'warning' | 'info' | 'neutral';
}

// ============================================================================
// Loading Component (New)
// ============================================================================

/**
 * Loading indicator with timeout state support
 * 
 * @example
 * ```tsx
 * // Normal loading
 * <Loading text="Loading actions..." />
 * 
 * // Timeout state (after 30 seconds)
 * <Loading timeout onRetry={() => refetch()} />
 * ```
 */
export interface LoadingProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Optional loading message (displayed next to spinner) */
  text?: string;
  /** Show timeout state instead of spinner (after 30s) */
  timeout?: boolean;
  /** Callback when retry button is clicked (only shown when timeout=true) */
  onRetry?: () => void;
}

// ============================================================================
// ErrorBanner Component (New)
// ============================================================================

/**
 * Dismissible error message banner
 * 
 * @example
 * ```tsx
 * <ErrorBanner 
 *   message="Failed to load actions. Please try again."
 *   onDismiss={() => setError(null)}
 * />
 * ```
 */
export interface ErrorBannerProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Error message to display (required) */
  message: string;
  /** Callback when dismiss button is clicked (optional - hides dismiss if not provided) */
  onDismiss?: () => void;
}

// ============================================================================
// Component Exports
// ============================================================================

/**
 * Union type of all component props for generic handling
 */
export type ComponentProps = 
  | InputProps
  | TextareaProps
  | DialogProps
  | DialogContentProps
  | TableProps
  | TableRowProps
  | DropdownMenuProps
  | DropdownMenuItemProps
  | BadgeProps
  | LoadingProps
  | ErrorBannerProps;

/**
 * Variant types for components with multiple visual states
 */
export type BadgeVariant = BadgeProps['variant'];
export type ButtonVariant = 'default' | 'secondary' | 'outline' | 'ghost' | 'destructive'; // From existing Button component

/**
 * Component state types for testing
 */
export type InputState = 'base' | 'hover' | 'focus' | 'disabled' | 'error';
export type DialogState = 'closed' | 'opening' | 'open' | 'closing';
export type TableRowState = 'base' | 'hover' | 'selected';
