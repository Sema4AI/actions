import { Input } from '@/core/components/ui/Input';
import { Select, SelectItem } from '@/core/components/ui/Select';

interface IntervalBuilderProps {
  intervalSeconds?: number;
  onChange: (seconds: number | undefined) => void;
}

export function IntervalBuilder({ intervalSeconds, onChange }: IntervalBuilderProps) {
  const unit = intervalSeconds
    ? intervalSeconds < 60
      ? 'seconds'
      : intervalSeconds < 3600
      ? 'minutes'
      : intervalSeconds < 86400
      ? 'hours'
      : 'days'
    : 'minutes';

  const value = intervalSeconds
    ? unit === 'seconds'
      ? intervalSeconds
      : unit === 'minutes'
      ? intervalSeconds / 60
      : unit === 'hours'
      ? intervalSeconds / 3600
      : intervalSeconds / 86400
    : '';

  const handleValueChange = (val: string) => {
    const num = parseInt(val, 10);
    if (isNaN(num) || num <= 0) {
      onChange(undefined);
      return;
    }

    const multiplier =
      unit === 'seconds' ? 1 : unit === 'minutes' ? 60 : unit === 'hours' ? 3600 : 86400;
    onChange(num * multiplier);
  };

  const handleUnitChange = (newUnit: string) => {
    if (!value) return;
    const numValue = typeof value === 'number' ? value : parseInt(String(value), 10);
    if (isNaN(numValue)) return;

    const multiplier =
      newUnit === 'seconds' ? 1 : newUnit === 'minutes' ? 60 : newUnit === 'hours' ? 3600 : 86400;
    onChange(numValue * multiplier);
  };

  return (
    <div className="space-y-4">
      <label className="text-sm font-medium text-card-foreground">Interval</label>

      <div className="flex gap-3">
        <div className="flex-1">
          <Input
            type="number"
            min="1"
            placeholder="1"
            value={value}
            onChange={(e) => handleValueChange(e.target.value)}
            className="w-full"
          />
        </div>
        <div className="w-32">
          <Select value={unit} onValueChange={handleUnitChange}>
            <SelectItem value="seconds">Seconds</SelectItem>
            <SelectItem value="minutes">Minutes</SelectItem>
            <SelectItem value="hours">Hours</SelectItem>
            <SelectItem value="days">Days</SelectItem>
          </Select>
        </div>
      </div>

      <div className="rounded-md border border-border bg-muted/30 p-3">
        <p className="text-xs text-muted-foreground">
          Common intervals:
        </p>
        <div className="mt-2 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => onChange(300)}
            className="rounded-md bg-background px-2 py-1 text-xs text-card-foreground hover:bg-accent"
          >
            5 min
          </button>
          <button
            type="button"
            onClick={() => onChange(900)}
            className="rounded-md bg-background px-2 py-1 text-xs text-card-foreground hover:bg-accent"
          >
            15 min
          </button>
          <button
            type="button"
            onClick={() => onChange(1800)}
            className="rounded-md bg-background px-2 py-1 text-xs text-card-foreground hover:bg-accent"
          >
            30 min
          </button>
          <button
            type="button"
            onClick={() => onChange(3600)}
            className="rounded-md bg-background px-2 py-1 text-xs text-card-foreground hover:bg-accent"
          >
            1 hour
          </button>
          <button
            type="button"
            onClick={() => onChange(21600)}
            className="rounded-md bg-background px-2 py-1 text-xs text-card-foreground hover:bg-accent"
          >
            6 hours
          </button>
          <button
            type="button"
            onClick={() => onChange(86400)}
            className="rounded-md bg-background px-2 py-1 text-xs text-card-foreground hover:bg-accent"
          >
            1 day
          </button>
        </div>
      </div>
    </div>
  );
}
