import { useEffect } from 'react';
import { usePreviewRuns, useValidateCron } from '@/queries/schedules';
import { Badge } from '@/core/components/ui/Badge';
import { Loading } from '@/core/components/ui/Loading';
import { cn } from '@/shared/utils/cn';

interface CronPreviewProps {
  scheduleType: 'cron' | 'interval' | 'weekday' | 'once';
  cronExpression?: string;
  intervalSeconds?: number;
  weekdayConfig?: { days: number[]; time: string };
  onceAt?: string;
  timezone: string;
}

const WEEKDAY_NAMES = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

export function CronPreview({
  scheduleType,
  cronExpression,
  intervalSeconds,
  weekdayConfig,
  onceAt,
  timezone,
}: CronPreviewProps) {
  const { mutate: validateCron, data: validation, isPending: validating } = useValidateCron();
  const { mutate: previewRuns, data: preview, isPending: previewing } = usePreviewRuns();

  useEffect(() => {
    if (scheduleType === 'cron' && cronExpression) {
      validateCron(cronExpression);
    }
  }, [cronExpression, scheduleType, validateCron]);

  useEffect(() => {
    const params: {
      schedule_type: string;
      cron_expression?: string;
      interval_seconds?: number;
      weekday_config?: { days: number[]; time: string };
      once_at?: string;
      timezone: string;
      count?: number;
    } = {
      schedule_type: scheduleType,
      timezone,
      count: 5,
    };

    if (scheduleType === 'cron' && cronExpression) {
      params.cron_expression = cronExpression;
    } else if (scheduleType === 'interval' && intervalSeconds) {
      params.interval_seconds = intervalSeconds;
    } else if (scheduleType === 'weekday' && weekdayConfig) {
      params.weekday_config = weekdayConfig;
    } else if (scheduleType === 'once' && onceAt) {
      params.once_at = onceAt;
    }

    if (
      (scheduleType === 'cron' && cronExpression) ||
      (scheduleType === 'interval' && intervalSeconds) ||
      (scheduleType === 'weekday' && weekdayConfig) ||
      (scheduleType === 'once' && onceAt)
    ) {
      previewRuns(params);
    }
  }, [scheduleType, cronExpression, intervalSeconds, weekdayConfig, onceAt, timezone, previewRuns]);

  const getHumanReadable = () => {
    if (scheduleType === 'cron' && validation?.description) {
      return validation.description;
    }
    if (scheduleType === 'interval' && intervalSeconds) {
      if (intervalSeconds < 60) {
        return `Every ${intervalSeconds} seconds`;
      }
      if (intervalSeconds < 3600) {
        return `Every ${Math.floor(intervalSeconds / 60)} minutes`;
      }
      return `Every ${Math.floor(intervalSeconds / 3600)} hours`;
    }
    if (scheduleType === 'weekday' && weekdayConfig) {
      const days = weekdayConfig.days.map((d) => WEEKDAY_NAMES[d]).join(', ');
      return `Every ${days} at ${weekdayConfig.time}`;
    }
    if (scheduleType === 'once' && onceAt) {
      return `Once at ${new Date(onceAt).toLocaleString()}`;
    }
    return 'Configure schedule to see preview';
  };

  const isValid =
    scheduleType === 'cron' ? validation?.valid ?? false :
    scheduleType === 'interval' ? !!intervalSeconds :
    scheduleType === 'weekday' ? !!(weekdayConfig?.days?.length && weekdayConfig?.time) :
    scheduleType === 'once' ? !!onceAt : false;

  return (
    <div className="space-y-4">
      {/* Human-readable description */}
      <div className="rounded-lg border border-border bg-muted/30 p-4">
        <div className="flex items-start gap-3">
          <div className={cn(
            "mt-0.5 rounded-full p-1.5",
            isValid ? "bg-success/10" : "bg-muted"
          )}>
            {isValid ? (
              <svg className="h-4 w-4 text-success" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            ) : (
              <svg className="h-4 w-4 text-muted-foreground" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
            )}
          </div>
          <div className="flex-1 space-y-1">
            <p className="text-sm font-medium text-card-foreground">
              {validating || previewing ? 'Validating...' : getHumanReadable()}
            </p>
            {scheduleType === 'cron' && validation && !validation.valid && (
              <p className="text-xs text-destructive">{validation.error}</p>
            )}
            <p className="text-xs text-muted-foreground">Timezone: {timezone}</p>
          </div>
        </div>
      </div>

      {/* Next run times */}
      {preview && preview.next_runs && preview.next_runs.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-card-foreground">Next 5 scheduled runs:</h4>
          <div className="space-y-1.5">
            {preview.next_runs.map((runTime, index) => (
              <div
                key={index}
                className={cn(
                  "flex items-center gap-2 rounded-md border border-border bg-card p-2.5",
                  "animate-fadeInUp"
                )}
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <Badge variant={index === 0 ? 'info' : 'neutral'} className="text-xs">
                  {index === 0 ? 'Next' : `+${index}`}
                </Badge>
                <span className="font-mono text-sm text-card-foreground">
                  {new Date(runTime).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {(validating || previewing) && (
        <div className="flex items-center justify-center py-4">
          <Loading text="Loading preview..." />
        </div>
      )}
    </div>
  );
}
