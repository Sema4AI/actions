import * as React from 'react';

import { cn } from '@/shared/utils/cn';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  /** Display error styling (red border, red focus ring) */
  error?: boolean;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = 'text', error = false, ...props }, ref) => {
    const errorClass = error ? 'border-destructive hover:border-destructive' : 'border-input hover:border-input/80';
    const focusRing = error ? 'focus-visible:ring-destructive' : 'focus-visible:ring-ring';

    return (
      <input
        type={type}
        aria-invalid={error ? true : undefined}
        className={cn(
          // Layout
          'flex h-10 w-full px-3 py-2',
          // Typography
          'text-sm',
          // Style
          'rounded-md border',
          // Colors
          'bg-background text-foreground placeholder:text-muted-foreground',
          errorClass,
          // Focus states
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-background',
          focusRing,
          // Disabled states
          'disabled:cursor-not-allowed disabled:opacity-50',
          // Animations
          'transition-colors duration-200',
          'motion-reduce:transition-none',
          className,
        )}
        ref={ref}
        {...props}
      />
    );
  },
);
Input.displayName = 'Input';

export { Input };
