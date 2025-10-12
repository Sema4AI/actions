import * as React from 'react';
import { cn } from '@/shared/utils/cn';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'success' | 'error' | 'warning' | 'info' | 'neutral';
}

const VARIANT_CLASSES: Record<NonNullable<BadgeProps['variant']>, string> = {
  success: 'bg-green-100 text-green-700 border border-green-200',
  error: 'bg-red-100 text-red-700 border border-red-200',
  warning: 'bg-yellow-100 text-yellow-700 border border-yellow-200',
  info: 'bg-blue-100 text-blue-700 border border-blue-200',
  neutral: 'bg-gray-100 text-gray-700 border border-gray-200',
};

const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(({ className, variant = 'neutral', children, ...props }, ref) => {
  return (
    <span
      ref={ref}
      className={cn('inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium', VARIANT_CLASSES[variant], className)}
      {...props}
    >
      {children}
    </span>
  );
});

Badge.displayName = 'Badge';

export { Badge };
