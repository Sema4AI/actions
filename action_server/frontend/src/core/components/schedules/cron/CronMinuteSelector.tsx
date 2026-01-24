import { cn } from '@/shared/utils/cn';

interface CronMinuteSelectorProps {
  selectedMinutes: number[];
  onChange: (minutes: number[]) => void;
}

const MINUTE_OPTIONS = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55];

export function CronMinuteSelector({ selectedMinutes, onChange }: CronMinuteSelectorProps) {
  const toggleMinute = (minute: number) => {
    if (selectedMinutes.includes(minute)) {
      onChange(selectedMinutes.filter((m) => m !== minute));
    } else {
      onChange([...selectedMinutes, minute].sort((a, b) => a - b));
    }
  };

  const selectAll = () => {
    onChange(MINUTE_OPTIONS);
  };

  const clearAll = () => {
    onChange([]);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-card-foreground">
          Minutes
          {selectedMinutes.length > 0 && (
            <span className="ml-2 text-xs text-muted-foreground">
              ({selectedMinutes.length} selected)
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

      <div className="grid grid-cols-6 gap-2">
        {MINUTE_OPTIONS.map((minute) => {
          const isSelected = selectedMinutes.includes(minute);
          return (
            <button
              key={minute}
              type="button"
              onClick={() => toggleMinute(minute)}
              className={cn(
                'flex h-12 items-center justify-center rounded-md border text-sm font-medium',
                'transition-all duration-150 active:scale-95',
                'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                isSelected
                  ? 'border-primary bg-primary text-primary-foreground shadow-sm'
                  : 'border-border bg-background text-foreground hover:border-primary/50 hover:bg-accent'
              )}
            >
              :{minute.toString().padStart(2, '0')}
            </button>
          );
        })}
      </div>

      <p className="text-xs text-muted-foreground">
        Select the minutes when the schedule should run. For example, selecting :00, :15, :30, :45
        will run every 15 minutes.
      </p>
    </div>
  );
}
