import { cn } from '@/shared/utils/cn';

interface CronMonthSelectorProps {
  selectedMonths: number[];
  onChange: (months: number[]) => void;
}

const MONTHS = [
  { value: 1, label: 'Jan' },
  { value: 2, label: 'Feb' },
  { value: 3, label: 'Mar' },
  { value: 4, label: 'Apr' },
  { value: 5, label: 'May' },
  { value: 6, label: 'Jun' },
  { value: 7, label: 'Jul' },
  { value: 8, label: 'Aug' },
  { value: 9, label: 'Sep' },
  { value: 10, label: 'Oct' },
  { value: 11, label: 'Nov' },
  { value: 12, label: 'Dec' },
];

export function CronMonthSelector({ selectedMonths, onChange }: CronMonthSelectorProps) {
  const toggleMonth = (month: number) => {
    if (selectedMonths.includes(month)) {
      onChange(selectedMonths.filter((m) => m !== month));
    } else {
      onChange([...selectedMonths, month].sort((a, b) => a - b));
    }
  };

  const selectAll = () => {
    onChange(MONTHS.map((m) => m.value));
  };

  const clearAll = () => {
    onChange([]);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-card-foreground">
          Months
          {selectedMonths.length > 0 && (
            <span className="ml-2 text-xs text-muted-foreground">
              ({selectedMonths.length} selected)
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

      <div className="grid grid-cols-4 gap-2">
        {MONTHS.map(({ value, label }) => {
          const isSelected = selectedMonths.includes(value);
          return (
            <button
              key={value}
              type="button"
              onClick={() => toggleMonth(value)}
              className={cn(
                'flex h-12 items-center justify-center rounded-md border text-sm font-medium',
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
        Select the months when the schedule should run.
      </p>
    </div>
  );
}
