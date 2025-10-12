import * as React from 'react';
import { Button } from './Button';
import { cn } from '@/shared/utils/cn';

export interface ErrorBannerProps extends React.HTMLAttributes<HTMLDivElement> {
  message: string;
  onDismiss?: () => void;
}

const ErrorBanner = React.forwardRef<HTMLDivElement, ErrorBannerProps>(({ className, message, onDismiss, ...props }, ref) => {
  return (
    <div ref={ref} className={cn('bg-red-50 border border-red-200 rounded-md p-4 flex items-start gap-3', className)} {...props}>
      <svg className="h-5 w-5 text-red-600" viewBox="0 0 24 24" fill="none" aria-hidden>
        <path d="M12 9v4" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
        <path d="M12 17h.01" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth={2} /></svg>

      <p className="text-sm text-red-700 flex-1">{message}</p>

      {onDismiss && (
        <button onClick={onDismiss} aria-label="Dismiss" className="text-red-500 hover:bg-red-100 rounded-md p-1"> 
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
