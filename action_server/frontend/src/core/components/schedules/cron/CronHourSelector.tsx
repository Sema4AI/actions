import { cn } from '@/shared/utils/cn';

interface CronHourSelectorProps {
  selectedHours: number[];
  onChange: (hours: number[]) => void;
}

const HOURS = Array.from({ length: 24 }, (_, i) => i);

export function CronHourSelector({ selectedHours, onChange }: CronHourSelectorProps) {
  const toggleHour = (hour: number) => {
    if (selectedHours.includes(hour)) {
      onChange(selectedHours.filter((h) => h !== hour));
    } else {
      onChange([...selectedHours, hour].sort((a, b) => a - b));
    }
  };

  const selectAll = () => {
    onChange(HOURS);
  };

  const clearAll = () => {
    onChange([]);
  };

  const selectBusinessHours = () => {
    onChange([9, 10, 11, 12, 13, 14, 15, 16, 17]);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-card-foreground">
          Hours
          {selectedHours.length > 0 && (
            <span className="ml-2 text-xs text-muted-foreground">
              ({selectedHours.length} selected)
            </span>
          )}
        </label>
        <div className="flex gap-2">
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
            onClick={selectBusinessHours}
            className="text-xs text-primary hover:underline"
          >
            Business
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

      <div className="grid grid-cols-12 gap-1.5">
        {HOURS.map((hour) => {
          const isSelected = selectedHours.includes(hour);
          return (
            <button
              key={hour}
              type="button"
              onClick={() => toggleHour(hour)}
              className={cn(
                'flex h-10 items-center justify-center rounded-md border text-xs font-medium',
                'transition-all duration-150 active:scale-95',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                isSelected
                  ? 'border-primary bg-primary text-primary-foreground shadow-sm'
                  : 'border-border bg-background text-foreground hover:border-primary/50 hover:bg-accent'
              )}
              title={`${hour.toString().padStart(2, '0')}:00`}
            >
              {hour}
            </button>
          );
        })}
      </div>

      <p className="text-xs text-muted-foreground">
        Select the hours when the schedule should run. Use 24-hour format (0-23).
      </p>
    </div>
  );
}
