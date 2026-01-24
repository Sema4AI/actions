import { useState, useMemo } from 'react';
import { Button } from '@/core/components/ui/Button';
import { Badge } from '@/core/components/ui/Badge';
import { cn } from '@/shared/utils/cn';
import { ScheduleExecution, ScheduleExecutionStatus } from '@/shared/types';

interface ScheduleCalendarProps {
  executions?: ScheduleExecution[];
  scheduleId?: string;
}

const DAYS_OF_WEEK = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

export function ScheduleCalendar({ executions = [] }: ScheduleCalendarProps) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDay, setSelectedDay] = useState<Date | null>(null);

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  // Get first day of month and number of days in month
  const firstDayOfMonth = new Date(year, month, 1);
  const lastDayOfMonth = new Date(year, month + 1, 0);
  const daysInMonth = lastDayOfMonth.getDate();
  const startingDayOfWeek = firstDayOfMonth.getDay();

  // Group executions by date
  const executionsByDate = useMemo(() => {
    const map = new Map<string, ScheduleExecution[]>();
    executions.forEach((exec) => {
      const date = new Date(exec.scheduled_time);
      const key = `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`;
      if (!map.has(key)) {
        map.set(key, []);
      }
      map.get(key)?.push(exec);
    });
    return map;
  }, [executions]);

  const getExecutionsForDay = (day: number): ScheduleExecution[] => {
    const key = `${year}-${month}-${day}`;
    return executionsByDate.get(key) || [];
  };

  const getDayStatus = (day: number): 'success' | 'error' | 'info' | 'neutral' => {
    const execs = getExecutionsForDay(day);
    if (execs.length === 0) return 'neutral';

    const hasFailure = execs.some((e) => e.status === ScheduleExecutionStatus.FAILED);
    const hasCompleted = execs.some((e) => e.status === ScheduleExecutionStatus.COMPLETED);
    const hasRunning = execs.some((e) => e.status === ScheduleExecutionStatus.RUNNING);

    if (hasFailure) return 'error';
    if (hasRunning) return 'info';
    if (hasCompleted) return 'success';
    return 'neutral';
  };

  const navigateMonth = (delta: number) => {
    setCurrentDate(new Date(year, month + delta, 1));
    setSelectedDay(null);
  };

  const goToToday = () => {
    setCurrentDate(new Date());
    setSelectedDay(null);
  };

  const handleDayClick = (day: number) => {
    setSelectedDay(new Date(year, month, day));
  };

  const dayExecutions = selectedDay ? getExecutionsForDay(selectedDay.getDate()) : [];

  // Generate calendar grid
  const calendarDays: (number | null)[] = [];
  for (let i = 0; i < startingDayOfWeek; i++) {
    calendarDays.push(null);
  }
  for (let day = 1; day <= daysInMonth; day++) {
    calendarDays.push(day);
  }

  return (
    <div className="space-y-4">
      {/* Calendar Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-card-foreground">
          {MONTHS[month]} {year}
        </h2>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => navigateMonth(-1)}>
            <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="15 18 9 12 15 6" />
            </svg>
          </Button>
          <Button variant="outline" size="sm" onClick={goToToday}>
            Today
          </Button>
          <Button variant="outline" size="sm" onClick={() => navigateMonth(1)}>
            <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </Button>
        </div>
      </div>

      {/* Calendar Grid */}
      <div className="rounded-lg border border-border bg-card">
        {/* Day headers */}
        <div className="grid grid-cols-7 border-b border-border">
          {DAYS_OF_WEEK.map((day) => (
            <div
              key={day}
              className="p-2 text-center text-sm font-medium text-muted-foreground"
            >
              {day}
            </div>
          ))}
        </div>

        {/* Calendar days */}
        <div className="grid grid-cols-7">
          {calendarDays.map((day, index) => {
            if (day === null) {
              return (
                <div
                  key={`empty-${index}`}
                  className="aspect-square border-b border-r border-border bg-muted/20"
                />
              );
            }

            const execs = getExecutionsForDay(day);
            const status = getDayStatus(day);
            const isToday =
              year === new Date().getFullYear() &&
              month === new Date().getMonth() &&
              day === new Date().getDate();
            const isSelected =
              selectedDay &&
              selectedDay.getFullYear() === year &&
              selectedDay.getMonth() === month &&
              selectedDay.getDate() === day;

            return (
              <button
                key={day}
                onClick={() => handleDayClick(day)}
                className={cn(
                  'aspect-square border-b border-r border-border p-2 text-left transition-colors',
                  'hover:bg-accent',
                  isSelected && 'bg-accent ring-2 ring-primary ring-inset',
                  isToday && 'font-bold'
                )}
              >
                <div className="flex h-full flex-col">
                  <span
                    className={cn(
                      'text-sm',
                      isToday && 'text-primary',
                      execs.length === 0 && 'text-muted-foreground'
                    )}
                  >
                    {day}
                  </span>
                  {execs.length > 0 && (
                    <div className="mt-auto flex items-center gap-1">
                      <div
                        className={cn(
                          'h-2 w-2 rounded-full',
                          status === 'success' && 'bg-success',
                          status === 'error' && 'bg-destructive',
                          status === 'info' && 'bg-info',
                          status === 'neutral' && 'bg-muted-foreground'
                        )}
                      />
                      <span className="text-xs text-muted-foreground">{execs.length}</span>
                    </div>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Selected Day Details */}
      {selectedDay && (
        <div className="rounded-lg border border-border bg-card p-4">
          <h3 className="mb-3 text-sm font-semibold text-card-foreground">
            Executions on {selectedDay.toLocaleDateString()}
          </h3>
          {dayExecutions.length === 0 ? (
            <p className="text-sm text-muted-foreground">No executions scheduled for this day.</p>
          ) : (
            <div className="space-y-2">
              {dayExecutions.map((exec) => (
                <div
                  key={exec.id}
                  className="flex items-center justify-between rounded-md border border-border bg-background p-3"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-card-foreground">
                        {new Date(exec.scheduled_time).toLocaleTimeString()}
                      </span>
                      <Badge
                        variant={
                          exec.status === ScheduleExecutionStatus.COMPLETED
                            ? 'success'
                            : exec.status === ScheduleExecutionStatus.FAILED
                            ? 'error'
                            : exec.status === ScheduleExecutionStatus.RUNNING
                            ? 'info'
                            : 'neutral'
                        }
                      >
                        {exec.status}
                      </Badge>
                    </div>
                    {exec.duration_ms && (
                      <p className="mt-1 text-xs text-muted-foreground">
                        Duration: {(exec.duration_ms / 1000).toFixed(2)}s
                      </p>
                    )}
                    {exec.error_message && (
                      <p className="mt-1 text-xs text-destructive">{exec.error_message}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Legend */}
      <div className="flex items-center gap-4 text-xs text-muted-foreground">
        <div className="flex items-center gap-1.5">
          <div className="h-2 w-2 rounded-full bg-success" />
          <span>Success</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="h-2 w-2 rounded-full bg-destructive" />
          <span>Failed</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="h-2 w-2 rounded-full bg-info" />
          <span>Running</span>
        </div>
      </div>
    </div>
  );
}
