import { useState, useEffect } from 'react';
import { cn } from '@/shared/utils/cn';
import { Input } from '@/core/components/ui/Input';
import { CronMinuteSelector } from './CronMinuteSelector';
import { CronHourSelector } from './CronHourSelector';
import { CronDaySelector } from './CronDaySelector';
import { CronMonthSelector } from './CronMonthSelector';
import { CronWeekdaySelector } from './CronWeekdaySelector';
import { IntervalBuilder } from './IntervalBuilder';
import { WeekdayBuilder } from './WeekdayBuilder';
import { CronPreview } from './CronPreview';

type ScheduleType = 'cron' | 'interval' | 'weekday' | 'once';

interface VisualCronBuilderProps {
  scheduleType: ScheduleType;
  onScheduleTypeChange: (type: ScheduleType) => void;
  cronExpression?: string;
  intervalSeconds?: number;
  weekdayConfig?: { days: number[]; time: string };
  onceAt?: string;
  timezone: string;
  onCronChange: (expression: string | undefined) => void;
  onIntervalChange: (seconds: number | undefined) => void;
  onWeekdayConfigChange: (config: { days: number[]; time: string } | undefined) => void;
  onOnceAtChange: (datetime: string | undefined) => void;
}

export function VisualCronBuilder({
  scheduleType,
  onScheduleTypeChange,
  cronExpression,
  intervalSeconds,
  weekdayConfig,
  onceAt,
  timezone,
  onCronChange,
  onIntervalChange,
  onWeekdayConfigChange,
  onOnceAtChange,
}: VisualCronBuilderProps) {
  // Cron builder state
  const [selectedMinutes, setSelectedMinutes] = useState<number[]>([0]);
  const [selectedHours, setSelectedHours] = useState<number[]>([0]);
  const [selectedDays, setSelectedDays] = useState<number[]>([]);
  const [selectedMonths, setSelectedMonths] = useState<number[]>([]);
  const [selectedWeekdays, setSelectedWeekdays] = useState<number[]>([]);

  // Update cron expression when selections change
  useEffect(() => {
    if (scheduleType !== 'cron') return;

    // Build cron expression from selections
    const minute = selectedMinutes.length > 0 ? selectedMinutes.join(',') : '*';
    const hour = selectedHours.length > 0 ? selectedHours.join(',') : '*';
    const dayOfMonth = selectedDays.length > 0 ? selectedDays.join(',') : '*';
    const month = selectedMonths.length > 0 ? selectedMonths.join(',') : '*';
    const dayOfWeek = selectedWeekdays.length > 0 ? selectedWeekdays.join(',') : '*';

    const expression = `${minute} ${hour} ${dayOfMonth} ${month} ${dayOfWeek}`;
    onCronChange(expression);
  }, [selectedMinutes, selectedHours, selectedDays, selectedMonths, selectedWeekdays, scheduleType, onCronChange]);

  const scheduleTypes = [
    { value: 'cron' as const, label: 'Cron Expression', icon: '⚙️' },
    { value: 'interval' as const, label: 'Interval', icon: '🔁' },
    { value: 'weekday' as const, label: 'Weekday', icon: '📅' },
    { value: 'once' as const, label: 'One-time', icon: '1️⃣' },
  ];

  return (
    <div className="space-y-6">
      {/* Schedule Type Tabs */}
      <div className="flex gap-2 border-b border-border">
        {scheduleTypes.map((type) => (
          <button
            key={type.value}
            type="button"
            onClick={() => onScheduleTypeChange(type.value)}
            className={cn(
              'flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors',
              'border-b-2 -mb-px',
              scheduleType === type.value
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            )}
          >
            <span>{type.icon}</span>
            <span>{type.label}</span>
          </button>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Builder Section */}
        <div className="space-y-6">
          {scheduleType === 'cron' && (
            <>
              <CronMinuteSelector
                selectedMinutes={selectedMinutes}
                onChange={setSelectedMinutes}
              />
              <CronHourSelector
                selectedHours={selectedHours}
                onChange={setSelectedHours}
              />
              <CronDaySelector
                selectedDays={selectedDays}
                onChange={setSelectedDays}
              />
              <CronMonthSelector
                selectedMonths={selectedMonths}
                onChange={setSelectedMonths}
              />
              <CronWeekdaySelector
                selectedWeekdays={selectedWeekdays}
                onChange={setSelectedWeekdays}
              />
              {/* Raw cron expression */}
              <div>
                <label htmlFor="raw-cron" className="block text-sm font-medium text-card-foreground mb-2">
                  Raw Cron Expression
                </label>
                <Input
                  id="raw-cron"
                  type="text"
                  value={cronExpression || ''}
                  onChange={(e) => onCronChange(e.target.value || undefined)}
                  placeholder="* * * * *"
                  className="font-mono"
                />
                <p className="mt-1 text-xs text-muted-foreground">
                  Format: minute hour day month weekday
                </p>
              </div>
            </>
          )}

          {scheduleType === 'interval' && (
            <IntervalBuilder
              intervalSeconds={intervalSeconds}
              onChange={onIntervalChange}
            />
          )}

          {scheduleType === 'weekday' && (
            <WeekdayBuilder
              weekdayConfig={weekdayConfig}
              onChange={onWeekdayConfigChange}
            />
          )}

          {scheduleType === 'once' && (
            <div>
              <label htmlFor="once-at" className="block text-sm font-medium text-card-foreground mb-2">
                Date and Time
              </label>
              <Input
                id="once-at"
                type="datetime-local"
                value={onceAt || ''}
                onChange={(e) => onOnceAtChange(e.target.value || undefined)}
              />
              <p className="mt-1 text-xs text-muted-foreground">
                Schedule will run once at the specified date and time.
              </p>
            </div>
          )}
        </div>

        {/* Preview Section */}
        <div>
          <h3 className="mb-4 text-sm font-semibold text-card-foreground">Schedule Preview</h3>
          <CronPreview
            scheduleType={scheduleType}
            cronExpression={cronExpression}
            intervalSeconds={intervalSeconds}
            weekdayConfig={weekdayConfig}
            onceAt={onceAt}
            timezone={timezone}
          />
        </div>
      </div>
    </div>
  );
}
