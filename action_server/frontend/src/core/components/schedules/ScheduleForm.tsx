import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/core/components/ui/Dialog';
import { Button } from '@/core/components/ui/Button';
import { Input } from '@/core/components/ui/Input';
import { Select, SelectItem } from '@/core/components/ui/Select';
import { Badge } from '@/core/components/ui/Badge';
import { Loading } from '@/core/components/ui/Loading';
import { VisualCronBuilder } from './cron/VisualCronBuilder';
import { useActionServerContext } from '@/shared/context/actionServerContext';
import { useCreateSchedule, useUpdateSchedule, useTimezones } from '@/queries/schedules';
import { Schedule, CreateScheduleRequest, ScheduleType } from '@/shared/types';
import { cn } from '@/shared/utils/cn';

interface ScheduleFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  schedule?: Schedule;
}

export function ScheduleForm({ open, onOpenChange, schedule }: ScheduleFormProps) {
  const { loadedActions } = useActionServerContext();
  const { data: timezones } = useTimezones();
  const createSchedule = useCreateSchedule();
  const updateSchedule = useUpdateSchedule();

  const isEdit = !!schedule;

  // Form state
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [actionId, setActionId] = useState<string>('');
  const [actionInputs, setActionInputs] = useState<Record<string, unknown>>({});
  const [inputsJson, setInputsJson] = useState<string>('{}');
  const [inputsError, setInputsError] = useState<string>('');
  const [scheduleType, setScheduleType] = useState<ScheduleType>('interval');
  const [cronExpression, setCronExpression] = useState<string>();
  const [intervalSeconds, setIntervalSeconds] = useState<number>();
  const [weekdayConfig, setWeekdayConfig] = useState<{ days: number[]; time: string }>();
  const [onceAt, setOnceAt] = useState<string>();
  const [timezone, setTimezone] = useState('UTC');
  const [enabled, setEnabled] = useState(true);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Advanced settings
  const [skipIfRunning, setSkipIfRunning] = useState(true);
  const [maxConcurrent, setMaxConcurrent] = useState(1);
  const [timeoutSeconds, setTimeoutSeconds] = useState(3600);
  const [retryEnabled, setRetryEnabled] = useState(false);
  const [retryMaxAttempts, setRetryMaxAttempts] = useState(3);
  const [retryDelaySeconds, setRetryDelaySeconds] = useState(60);
  const [notifyOnFailure, setNotifyOnFailure] = useState(false);

  // Load schedule data if editing
  useEffect(() => {
    if (schedule) {
      setName(schedule.name);
      setDescription(schedule.description || '');
      setActionId(schedule.action_id || '');
      // Load action inputs
      const inputs = schedule.inputs || {};
      setActionInputs(inputs);
      setInputsJson(JSON.stringify(inputs, null, 2));
      setInputsError('');
      setScheduleType(schedule.schedule_type);
      setCronExpression(schedule.cron_expression);
      setIntervalSeconds(schedule.interval_seconds);
      if (schedule.weekday_config) {
        setWeekdayConfig(schedule.weekday_config);
      }
      setOnceAt(schedule.once_at);
      setTimezone(schedule.timezone);
      setEnabled(schedule.enabled);
      setSkipIfRunning(schedule.skip_if_running);
      setMaxConcurrent(schedule.max_concurrent);
      setTimeoutSeconds(schedule.timeout_seconds);
      setRetryEnabled(schedule.retry_enabled);
      setRetryMaxAttempts(schedule.retry_max_attempts);
      setRetryDelaySeconds(schedule.retry_delay_seconds);
      setNotifyOnFailure(schedule.notify_on_failure);
    }
  }, [schedule]);

  // Reset form when dialog closes
  useEffect(() => {
    if (!open) {
      setTimeout(() => {
        setName('');
        setDescription('');
        setActionId('');
        setActionInputs({});
        setInputsJson('{}');
        setInputsError('');
        setScheduleType('interval');
        setCronExpression(undefined);
        setIntervalSeconds(undefined);
        setWeekdayConfig(undefined);
        setOnceAt(undefined);
        setTimezone('UTC');
        setEnabled(true);
        setShowAdvanced(false);
        setSkipIfRunning(true);
        setMaxConcurrent(1);
        setTimeoutSeconds(3600);
        setRetryEnabled(false);
        setRetryMaxAttempts(3);
        setRetryDelaySeconds(60);
        setNotifyOnFailure(false);
      }, 200);
    }
  }, [open]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate inputs JSON before submitting
    if (inputsError) {
      return;
    }

    const data: CreateScheduleRequest = {
      name,
      description,
      action_id: actionId || undefined,
      inputs: Object.keys(actionInputs).length > 0 ? actionInputs : undefined,
      schedule_type: scheduleType,
      cron_expression: scheduleType === 'cron' ? cronExpression : undefined,
      interval_seconds: scheduleType === 'interval' ? intervalSeconds : undefined,
      weekday_config: scheduleType === 'weekday' ? weekdayConfig : undefined,
      once_at: scheduleType === 'once' ? onceAt : undefined,
      timezone,
      enabled,
      skip_if_running: skipIfRunning,
      max_concurrent: maxConcurrent,
      timeout_seconds: timeoutSeconds,
      retry_enabled: retryEnabled,
      retry_max_attempts: retryMaxAttempts,
      retry_delay_seconds: retryDelaySeconds,
      notify_on_failure: notifyOnFailure,
    };

    try {
      if (isEdit) {
        await updateSchedule.mutateAsync({ id: schedule.id, data });
      } else {
        await createSchedule.mutateAsync(data);
      }
      onOpenChange(false);
    } catch (error) {
      console.error('Failed to save schedule:', error);
    }
  };

  const isValid =
    name.trim() &&
    actionId &&
    !inputsError &&
    ((scheduleType === 'cron' && cronExpression) ||
      (scheduleType === 'interval' && intervalSeconds) ||
      (scheduleType === 'weekday' && weekdayConfig) ||
      (scheduleType === 'once' && onceAt));

  const isSaving = createSchedule.isPending || updateSchedule.isPending;

  // Get all actions for the dropdown with full action data for schema access
  const actions = loadedActions.data?.flatMap((pkg) =>
    pkg.actions.map((action) => ({
      id: action.id,
      label: `${pkg.name} / ${action.name}`,
      packageName: pkg.name,
      inputSchema: action.input_schema,
    }))
  ) ?? [];

  // Get the selected action to show its parameter schema
  const selectedAction = actions.find((a) => a.id === actionId);

  // Parse input schema for the selected action
  const inputSchemaInfo = (() => {
    if (!selectedAction?.inputSchema) return null;
    try {
      const schema = JSON.parse(selectedAction.inputSchema);
      const properties = schema.properties || {};
      const required = schema.required || [];
      return { properties, required };
    } catch {
      return null;
    }
  })();

  // Handler for JSON input changes
  const handleInputsJsonChange = (value: string) => {
    setInputsJson(value);
    try {
      const parsed = JSON.parse(value);
      setActionInputs(parsed);
      setInputsError('');
    } catch (err) {
      setInputsError('Invalid JSON');
    }
  };

  // Reset inputs when action changes (unless editing existing schedule)
  useEffect(() => {
    if (!isEdit && actionId) {
      setActionInputs({});
      setInputsJson('{}');
      setInputsError('');
    }
  }, [actionId, isEdit]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEdit ? 'Edit Schedule' : 'Create New Schedule'}</DialogTitle>
          <DialogDescription>
            {isEdit
              ? 'Update the schedule configuration.'
              : 'Configure a schedule to automatically run an action at specified times.'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <div className="space-y-4">
            <div>
              <label htmlFor="schedule-name" className="block text-sm font-medium text-card-foreground mb-2">
                Schedule Name *
              </label>
              <Input
                id="schedule-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Daily data sync"
                required
              />
            </div>

            <div>
              <label htmlFor="schedule-description" className="block text-sm font-medium text-card-foreground mb-2">
                Description
              </label>
              <Input
                id="schedule-description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Syncs data from external API every day"
              />
            </div>

            <div>
              <label htmlFor="schedule-action" className="block text-sm font-medium text-card-foreground mb-2">
                Target Action *
              </label>
              <Select value={actionId} onValueChange={setActionId} required>
                <SelectItem value="">Select an action...</SelectItem>
                {actions.map((action) => (
                  <SelectItem key={action.id} value={action.id}>
                    {action.label}
                  </SelectItem>
                ))}
              </Select>
            </div>

            {/* Action Parameters - shown when action is selected */}
            {actionId && (
              <div className="rounded-lg border border-border bg-muted/30 p-4">
                <label
                  htmlFor="action-inputs"
                  className="block text-sm font-medium text-card-foreground mb-2"
                >
                  Action Parameters (JSON)
                </label>

                {/* Show expected parameters if schema available */}
                {inputSchemaInfo && Object.keys(inputSchemaInfo.properties).length > 0 && (
                  <div className="mb-3 text-xs text-muted-foreground">
                    <span className="font-medium">Expected parameters:</span>
                    <ul className="mt-1 space-y-1 ml-4">
                      {Object.entries(inputSchemaInfo.properties).map(([key, prop]: [string, any]) => (
                        <li key={key}>
                          <code className="bg-muted px-1 rounded">{key}</code>
                          {inputSchemaInfo.required.includes(key) && (
                            <span className="text-destructive ml-1">*</span>
                          )}
                          {prop.type && (
                            <span className="text-muted-foreground ml-1">({prop.type})</span>
                          )}
                          {prop.description && (
                            <span className="text-muted-foreground ml-1">- {prop.description}</span>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {inputSchemaInfo && Object.keys(inputSchemaInfo.properties).length === 0 && (
                  <p className="mb-3 text-xs text-muted-foreground">
                    This action has no input parameters.
                  </p>
                )}

                <textarea
                  id="action-inputs"
                  value={inputsJson}
                  onChange={(e) => handleInputsJsonChange(e.target.value)}
                  className={cn(
                    'w-full h-32 px-3 py-2 font-mono text-sm',
                    'bg-background border rounded-md',
                    'focus:outline-none focus:ring-2 focus:ring-ring',
                    inputsError ? 'border-destructive' : 'border-input'
                  )}
                  placeholder='{"key": "value"}'
                  spellCheck={false}
                />
                {inputsError && (
                  <p className="mt-1 text-xs text-destructive">{inputsError}</p>
                )}
              </div>
            )}

            <div>
              <label htmlFor="schedule-timezone" className="block text-sm font-medium text-card-foreground mb-2">
                Timezone
              </label>
              <Select value={timezone} onValueChange={setTimezone}>
                {timezones?.map((tz) => (
                  <SelectItem key={tz} value={tz}>
                    {tz}
                  </SelectItem>
                ))}
              </Select>
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="schedule-enabled"
                checked={enabled}
                onChange={(e) => setEnabled(e.target.checked)}
                className="h-4 w-4 rounded border-border"
              />
              <label htmlFor="schedule-enabled" className="text-sm text-card-foreground">
                Enable schedule immediately
              </label>
            </div>
          </div>

          {/* Schedule Configuration */}
          <div>
            <h3 className="mb-4 text-base font-semibold text-card-foreground">Schedule Configuration</h3>
            <VisualCronBuilder
              scheduleType={scheduleType}
              onScheduleTypeChange={setScheduleType}
              cronExpression={cronExpression}
              intervalSeconds={intervalSeconds}
              weekdayConfig={weekdayConfig}
              onceAt={onceAt}
              timezone={timezone}
              onCronChange={setCronExpression}
              onIntervalChange={setIntervalSeconds}
              onWeekdayConfigChange={setWeekdayConfig}
              onOnceAtChange={setOnceAt}
            />
          </div>

          {/* Advanced Settings */}
          <div>
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className={cn(
                "flex items-center gap-2 text-sm font-medium text-card-foreground",
                "hover:text-primary transition-colors"
              )}
            >
              <svg
                className={cn("h-4 w-4 transition-transform", showAdvanced && "rotate-90")}
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <polyline points="9 18 15 12 9 6" />
              </svg>
              Advanced Settings
            </button>

            {showAdvanced && (
              <div className="mt-4 space-y-4 rounded-lg border border-border bg-muted/30 p-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label htmlFor="max-concurrent" className="block text-sm font-medium text-card-foreground mb-2">
                      Max Concurrent Runs
                    </label>
                    <Input
                      id="max-concurrent"
                      type="number"
                      min="1"
                      value={maxConcurrent}
                      onChange={(e) => setMaxConcurrent(parseInt(e.target.value, 10))}
                    />
                  </div>

                  <div>
                    <label htmlFor="timeout" className="block text-sm font-medium text-card-foreground mb-2">
                      Timeout (seconds)
                    </label>
                    <Input
                      id="timeout"
                      type="number"
                      min="1"
                      value={timeoutSeconds}
                      onChange={(e) => setTimeoutSeconds(parseInt(e.target.value, 10))}
                    />
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="skip-if-running"
                    checked={skipIfRunning}
                    onChange={(e) => setSkipIfRunning(e.target.checked)}
                    className="h-4 w-4 rounded border-border"
                  />
                  <label htmlFor="skip-if-running" className="text-sm text-card-foreground">
                    Skip if already running
                  </label>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="retry-enabled"
                      checked={retryEnabled}
                      onChange={(e) => setRetryEnabled(e.target.checked)}
                      className="h-4 w-4 rounded border-border"
                    />
                    <label htmlFor="retry-enabled" className="text-sm text-card-foreground">
                      Enable retry on failure
                    </label>
                  </div>

                  {retryEnabled && (
                    <div className="ml-6 grid gap-4 sm:grid-cols-2">
                      <div>
                        <label htmlFor="retry-attempts" className="block text-sm font-medium text-card-foreground mb-2">
                          Max Retry Attempts
                        </label>
                        <Input
                          id="retry-attempts"
                          type="number"
                          min="1"
                          value={retryMaxAttempts}
                          onChange={(e) => setRetryMaxAttempts(parseInt(e.target.value, 10))}
                        />
                      </div>

                      <div>
                        <label htmlFor="retry-delay" className="block text-sm font-medium text-card-foreground mb-2">
                          Retry Delay (seconds)
                        </label>
                        <Input
                          id="retry-delay"
                          type="number"
                          min="1"
                          value={retryDelaySeconds}
                          onChange={(e) => setRetryDelaySeconds(parseInt(e.target.value, 10))}
                        />
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="notify-on-failure"
                    checked={notifyOnFailure}
                    onChange={(e) => setNotifyOnFailure(e.target.checked)}
                    className="h-4 w-4 rounded border-border"
                  />
                  <label htmlFor="notify-on-failure" className="text-sm text-card-foreground">
                    Notify on failure
                  </label>
                </div>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={isSaving}>
              Cancel
            </Button>
            <Button type="submit" disabled={!isValid || isSaving}>
              {isSaving ? (
                <>
                  <Loading text="" />
                  Saving...
                </>
              ) : (
                <>{isEdit ? 'Update' : 'Create'} Schedule</>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
