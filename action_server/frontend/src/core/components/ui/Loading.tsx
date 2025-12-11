import * as React from 'react';
import { Button } from './Button';
import { cn } from '@/shared/utils/cn';

export interface LoadingProps extends React.HTMLAttributes<HTMLDivElement> {
  text?: string;
  timeout?: boolean;
  onRetry?: () => void;
}

const Loading = React.forwardRef<HTMLDivElement, LoadingProps>(({ className, text, timeout = false, onRetry, ...props }, ref) => {
  if (timeout) {
    return (
      <div ref={ref} className={cn('flex flex-col items-center justify-center gap-4', className)} {...props}>
        <p className="text-sm text-gray-700 font-medium">Request timed out</p>
        <Button onClick={onRetry} variant="outline">Retry</Button>
      </div>
    );
  }

  return (
    <div ref={ref} role="status" aria-live="polite" aria-label={text || 'Loading'} className={cn('flex h-full items-center justify-center', className)} {...props}>
      <div className="h-8 w-8 animate-spin motion-reduce:animate-none rounded-full border-4 border-gray-200 border-t-blue-600" aria-hidden />
      {text && <span className="ml-3 text-sm text-gray-600">{text}</span>}
    </div>
  );
});

Loading.displayName = 'Loading';

export { Loading };
