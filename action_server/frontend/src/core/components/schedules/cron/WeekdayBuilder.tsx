import { Input } from '@/core/components/ui/Input';
import { cn } from '@/shared/utils/cn';

interface WeekdayBuilderProps {
  weekdayConfig?: { days: number[]; time: string };
  onChange: (config: { days: number[]; time: string } | undefined) => void;
}

const WEEKDAYS = [
  { value: 0, label: 'Sun' },
  { value: 1, label: 'Mon' },
  { value: 2, label: 'Tue' },
  { value: 3, label: 'Wed' },
  { value: 4, label: 'Thu' },
  { value: 5, label: 'Fri' },
  { value: 6, label: 'Sat' },
];

export function WeekdayBuilder({ weekdayConfig, onChange }: WeekdayBuilderProps) {
  const selectedDays = weekdayConfig?.days ?? [];
  const time = weekdayConfig?.time ?? '09:00';

  const toggleDay = (day: number) => {
    const newDays = selectedDays.includes(day)
      ? selectedDays.filter((d) => d !== day)
      : [...selectedDays, day].sort((a, b) => a - b);

    if (newDays.length === 0) {
      onChange(undefined);
    } else {
      onChange({ days: newDays, time });
    }
  };

  const handleTimeChange = (newTime: string) => {
    if (selectedDays.length === 0) {
      return;
    }
    onChange({ days: selectedDays, time: newTime });
  };

  const selectWeekdays = () => {
    onChange({ days: [1, 2, 3, 4, 5], time });
  };

  const selectWeekend = () => {
    onChange({ days: [0, 6], time });
  };

  return (
    <div className="space-y-4">
      <div>
        <div className="flex items-center justify-between mb-3">
          <label className="text-sm font-medium text-card-foreground">
            Days of Week
            {selectedDays.length > 0 && (
              <span className="ml-2 text-xs text-muted-foreground">
                ({selectedDays.length} selected)
              </span>
            )}
          </label>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={selectWeekdays}
              className="text-xs text-primary hover:underline"
            >
              Weekdays
            </button>
            <span className="text-xs text-muted-foreground">|</span>
            <button
              type="button"
              onClick={selectWeekend}
              className="text-xs text-primary hover:underline"
            >
              Weekend
            </button>
          </div>
        </div>

        <div className="grid grid-cols-7 gap-2">
          {WEEKDAYS.map(({ value, label }) => {
            const isSelected = selectedDays.includes(value);
            return (
              <button
                key={value}
                type="button"
                onClick={() => toggleDay(value)}
                className={cn(
                  'flex h-14 items-center justify-center rounded-md border text-sm font-medium',
                  'transition-all duration-150 active:scale-95',
                  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                  isSelected
                    ? 'border-primary bg-primary text-primary-foreground shadow-sm'
                    : 'border-border bg-background text-foreground hover:border-primary/50 hover:bg-accent'
                )}
              >
                {label}
              </button>
            );
          })}
        </div>
      </div>

      <div>
        <label htmlFor="weekday-time" className="block text-sm font-medium text-card-foreground mb-2">
          Time (HH:MM)
        </label>
        <Input
          id="weekday-time"
          type="time"
          value={time}
          onChange={(e) => handleTimeChange(e.target.value)}
          className="w-40"
          disabled={selectedDays.length === 0}
        />
      </div>

      <div className="rounded-md border border-border bg-muted/30 p-3">
        <p className="text-xs text-muted-foreground">
          Common times:
        </p>
        <div className="mt-2 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => handleTimeChange('09:00')}
            className="rounded-md bg-background px-2 py-1 text-xs text-card-foreground hover:bg-accent"
            disabled={selectedDays.length === 0}
          >
            9:00 AM
          </button>
          <button
            type="button"
            onClick={() => handleTimeChange('12:00')}
            className="rounded-md bg-background px-2 py-1 text-xs text-card-foreground hover:bg-accent"
            disabled={selectedDays.length === 0}
          >
            12:00 PM
          </button>
          <button
            type="button"
            onClick={() => handleTimeChange('17:00')}
            className="rounded-md bg-background px-2 py-1 text-xs text-card-foreground hover:bg-accent"
            disabled={selectedDays.length === 0}
          >
            5:00 PM
          </button>
          <button
            type="button"
            onClick={() => handleTimeChange('00:00')}
            className="rounded-md bg-background px-2 py-1 text-xs text-card-foreground hover:bg-accent"
            disabled={selectedDays.length === 0}
          >
            Midnight
          </button>
        </div>
      </div>
    </div>
  );
}
