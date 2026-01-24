import { cn } from '@/shared/utils/cn';

interface CronWeekdaySelectorProps {
  selectedWeekdays: number[];
  onChange: (weekdays: number[]) => void;
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

export function CronWeekdaySelector({ selectedWeekdays, onChange }: CronWeekdaySelectorProps) {
  const toggleWeekday = (weekday: number) => {
    if (selectedWeekdays.includes(weekday)) {
      onChange(selectedWeekdays.filter((w) => w !== weekday));
    } else {
      onChange([...selectedWeekdays, weekday].sort((a, b) => a - b));
    }
  };

  const selectWeekdays = () => {
    onChange([1, 2, 3, 4, 5]); // Mon-Fri
  };

  const selectWeekend = () => {
    onChange([0, 6]); // Sun, Sat
  };

  const selectAll = () => {
    onChange(WEEKDAYS.map((d) => d.value));
  };

  const clearAll = () => {
    onChange([]);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-card-foreground">
          Days of Week
          {selectedWeekdays.length > 0 && (
            <span className="ml-2 text-xs text-muted-foreground">
              ({selectedWeekdays.length} selected)
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
          <span className="text-xs text-muted-foreground">|</span>
          <button
            type="button"
            onClick={selectAll}
            className="text-xs text-primary hover:underline"
          >
            All
          </button>
          <span className="text-xs text-muted-foreground">|</span>
          <button
            type="button"
            onClick={clearAll}
            className="text-xs text-muted-foreground hover:underline"
          >
            Clear
          </button>
        </div>
      </div>

      <div className="grid grid-cols-7 gap-2">
        {WEEKDAYS.map(({ value, label }) => {
          const isSelected = selectedWeekdays.includes(value);
          return (
            <button
              key={value}
              type="button"
              onClick={() => toggleWeekday(value)}
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

      <p className="text-xs text-muted-foreground">
        Select the days of the week when the schedule should run.
      </p>
    </div>
  );
}
