import * as React from 'react';

import { cn } from '@/shared/utils/cn';

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  /** Display error styling (red border, red focus ring) */
  error?: boolean;
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(({ className, error = false, ...props }, ref) => {
  const isCode = props.spellCheck === false;
  const errorClass = error ? 'border-red-500 hover:border-red-500' : 'border-gray-300 hover:border-gray-400';
  const focusRing = error ? 'focus-visible:ring-red-500' : 'focus-visible:ring-blue-500';

  return (
    <textarea
      ref={ref}
      aria-invalid={error ? true : undefined}
      className={cn(
        'w-full rounded-md px-3 py-2 text-sm transition-colors duration-200 motion-reduce:transition-none',
        'min-h-[80px] resize-y',
        'bg-white placeholder:text-gray-400 focus-visible:outline-none focus-visible:ring-2',
        'focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
        errorClass,
        focusRing,
        isCode && 'font-mono',
        className,
      )}
      {...props}
    />
  );
});
Textarea.displayName = 'Textarea';

export { Textarea };
