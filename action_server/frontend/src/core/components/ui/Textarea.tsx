import * as React from 'react';

import { cn } from '@/shared/utils/cn';

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  /** Display error styling (red border, red focus ring) */
  error?: boolean;
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(({ className, error = false, ...props }, ref) => {
  const isCode = props.spellCheck === false;
  const errorClass = error ? 'border-destructive hover:border-destructive' : 'border-input hover:border-input/80';
  const focusRing = error ? 'focus-visible:ring-destructive' : 'focus-visible:ring-ring';

  return (
    <textarea
      ref={ref}
      aria-invalid={error ? true : undefined}
      className={cn(
        // Layout
        'w-full min-h-[80px] resize-y px-3 py-2',
        // Typography
        'text-sm',
        isCode && 'font-mono',
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
      {...props}
    />
  );
});
Textarea.displayName = 'Textarea';

export { Textarea };
