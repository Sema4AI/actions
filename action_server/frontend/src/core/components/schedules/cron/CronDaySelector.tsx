import { cn } from '@/shared/utils/cn';

interface CronDaySelectorProps {
  selectedDays: number[];
  onChange: (days: number[]) => void;
}

const DAYS = Array.from({ length: 31 }, (_, i) => i + 1);

export function CronDaySelector({ selectedDays, onChange }: CronDaySelectorProps) {
  const toggleDay = (day: number) => {
    if (selectedDays.includes(day)) {
      onChange(selectedDays.filter((d) => d !== day));
    } else {
      onChange([...selectedDays, day].sort((a, b) => a - b));
    }
  };

  const selectAll = () => {
    onChange(DAYS);
  };

  const clearAll = () => {
    onChange([]);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-card-foreground">
          Day of Month
          {selectedDays.length > 0 && (
            <span className="ml-2 text-xs text-muted-foreground">
              ({selectedDays.length} selected)
            </span>
          )}
        </label>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={selectAll}
            className="text-xs text-primary hover:underline"
          >
            Select all
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
        {DAYS.map((day) => {
          const isSelected = selectedDays.includes(day);
          return (
            <button
              key={day}
              type="button"
              onClick={() => toggleDay(day)}
              className={cn(
                'flex h-10 items-center justify-center rounded-md border text-sm font-medium',
                'transition-all duration-150 active:scale-95',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                isSelected
                  ? 'border-primary bg-primary text-primary-foreground shadow-sm'
                  : 'border-border bg-background text-foreground hover:border-primary/50 hover:bg-accent'
              )}
            >
              {day}
            </button>
          );
        })}
      </div>

      <p className="text-xs text-muted-foreground">
        Select days of the month (1-31). Note: Not all months have 31 days.
      </p>
    </div>
  );
}
