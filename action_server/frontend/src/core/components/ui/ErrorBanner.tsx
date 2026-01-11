import * as React from 'react';
import { Button } from './Button';
import { cn } from '@/shared/utils/cn';

export interface ErrorBannerProps extends React.HTMLAttributes<HTMLDivElement> {
  message: string;
  onDismiss?: () => void;
}

const ErrorBanner = React.forwardRef<HTMLDivElement, ErrorBannerProps>(({ className, message, onDismiss, ...props }, ref) => {
  return (
    <div
      ref={ref}
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
      className={cn(
        // Layout
        'flex items-start gap-3 p-4',
        // Style
        'rounded-md border border-destructive/20',
        // Colors
        'bg-destructive/5',
        className
      )}
      {...props}
    >
      <svg className="h-5 w-5 text-destructive" viewBox="0 0 24 24" fill="none" aria-hidden>
        <path d="M12 9v4" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
        <path d="M12 17h.01" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth={2} /></svg>

      <p className="text-sm text-destructive flex-1">{message}</p>

      {onDismiss && (
        <button
          onClick={onDismiss}
          aria-label="Dismiss"
          className={cn(
            // Layout & style
            'p-1 rounded-md',
            // Colors
            'text-destructive hover:bg-destructive/10',
            // Animations
            'transition-colors duration-200',
            'motion-reduce:transition-none'
          )}
        >
          <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" aria-hidden>
            <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      )}
    </div>
  );
});

ErrorBanner.displayName = 'ErrorBanner';

export { ErrorBanner };
