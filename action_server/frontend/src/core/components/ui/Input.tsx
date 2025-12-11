import * as React from 'react';

import { cn } from '@/shared/utils/cn';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  /** Display error styling (red border, red focus ring) */
  error?: boolean;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = 'text', error = false, ...props }, ref) => {
    const errorClass = error ? 'border-red-500 hover:border-red-500' : 'border-gray-300 hover:border-gray-400';
    const focusRing = error ? 'focus-visible:ring-red-500' : 'focus-visible:ring-blue-500';

    return (
      <input
        type={type}
        aria-invalid={error ? true : undefined}
        className={cn(
          'flex h-10 w-full rounded-md px-3 py-2 text-sm transition-colors duration-200 motion-reduce:transition-none',
          'bg-white placeholder:text-gray-400',
          'focus-visible:outline-none focus-visible:ring-2',
          'focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
          errorClass,
          focusRing,
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
