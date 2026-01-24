import { useState, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Button } from '@/core/components/ui/Button';
import { Input } from '@/core/components/ui/Input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/core/components/ui/Table';
import { Badge } from '@/core/components/ui/Badge';
import { Loading } from '@/core/components/ui/Loading';
import { ErrorBanner } from '@/core/components/ui/ErrorBanner';
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from '@/core/components/ui/DropdownMenu';
import { Select, SelectItem } from '@/core/components/ui/Select';
import { ScheduleForm } from '@/core/components/schedules/ScheduleForm';
import {
  useSchedules,
  useScheduleStats,
  useToggleSchedule,
  useTriggerSchedule,
  useDeleteSchedule,
} from '@/queries/schedules';
import { Schedule } from '@/shared/types';
import { cn } from '@/shared/utils/cn';

// Icons
const ClockIcon = ({ className }: { className?: string }) => (
  <svg className={className} width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <polyline points="12 6 12 12 16 14" />
  </svg>
);

const PlayIcon = ({ className }: { className?: string }) => (
  <svg className={className} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="5 3 19 12 5 21 5 3" />
  </svg>
);

const PauseIcon = ({ className }: { className?: string }) => (
  <svg className={className} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="6" y="4" width="4" height="16" />
    <rect x="14" y="4" width="4" height="16" />
  </svg>
);

const formatSchedule = (schedule: Schedule): string => {
  if (schedule.schedule_type === 'interval' && schedule.interval_seconds) {
    const seconds = schedule.interval_seconds;
    if (seconds < 60) return `Every ${seconds}s`;
    if (seconds < 3600) return `Every ${Math.floor(seconds / 60)}m`;
    if (seconds < 86400) return `Every ${Math.floor(seconds / 3600)}h`;
    return `Every ${Math.floor(seconds / 86400)}d`;
  }
  if (schedule.schedule_type === 'cron') {
    return schedule.cron_expression || 'Cron';
  }
  if (schedule.schedule_type === 'weekday' && schedule.weekday_config_json) {
    try {
      const config = JSON.parse(schedule.weekday_config_json);
      return `${config.days.length} days @ ${config.time}`;
    } catch {
      return 'Weekday';
    }
  }
  if (schedule.schedule_type === 'once') {
    return 'One-time';
  }
  return schedule.schedule_type;
};

function SummaryCard({
  title,
  value,
  icon: Icon,
  variant = 'neutral',
}: {
  title: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  variant?: 'success' | 'error' | 'warning' | 'info' | 'neutral';
}) {
  return (
    <div className="rounded-lg border border-border bg-card p-6 shadow-sm transition-all duration-200 hover:shadow-md">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-muted-foreground">{title}</span>
        <div className={cn(
          "rounded-full p-2",
          variant === 'success' && 'bg-success/10',
          variant === 'error' && 'bg-destructive/10',
          variant === 'info' && 'bg-info/10',
          variant === 'neutral' && 'bg-primary/10',
        )}>
          <Icon className={cn(
            "h-4 w-4",
            variant === 'success' && 'text-success',
            variant === 'error' && 'text-destructive',
            variant === 'info' && 'text-info',
            variant === 'neutral' && 'text-primary',
          )} />
        </div>
      </div>
      <div className="mt-3">
        <span className="text-3xl font-bold text-card-foreground">{value}</span>
      </div>
    </div>
  );
}

export function SchedulesPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [formOpen, setFormOpen] = useState(false);
  const [editingSchedule, setEditingSchedule] = useState<Schedule | undefined>();

  const currentSearch = searchParams.get('search') || '';

  const { data: schedules, isLoading, error } = useSchedules({
    enabled: statusFilter === 'all' ? undefined : statusFilter === 'enabled',
  });
  const { data: stats } = useScheduleStats();
  const toggleSchedule = useToggleSchedule();
  const triggerSchedule = useTriggerSchedule();
  const deleteSchedule = useDeleteSchedule();

  const filteredSchedules = useMemo(() => {
    if (!schedules) return [];
    let filtered = [...schedules];

    if (currentSearch.trim()) {
      const lowered = currentSearch.toLowerCase();
      filtered = filtered.filter((s) =>
        s.name.toLowerCase().includes(lowered) ||
        s.description?.toLowerCase().includes(lowered)
      );
    }

    filtered.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

    return filtered;
  }, [schedules, currentSearch]);

  const handleEdit = (schedule: Schedule) => {
    setEditingSchedule(schedule);
    setFormOpen(true);
  };

  const handleDelete = async (scheduleId: string) => {
    if (!confirm('Are you sure you want to delete this schedule?')) return;
    try {
      await deleteSchedule.mutateAsync(scheduleId);
    } catch (error) {
      console.error('Failed to delete schedule:', error);
    }
  };

  const handleToggle = async (schedule: Schedule) => {
    try {
      await toggleSchedule.mutateAsync({
        scheduleId: schedule.id,
        enabled: !schedule.enabled,
      });
    } catch (error) {
      console.error('Failed to toggle schedule:', error);
    }
  };

  const handleTrigger = async (scheduleId: string) => {
    try {
      await triggerSchedule.mutateAsync(scheduleId);
    } catch (error) {
      console.error('Failed to trigger schedule:', error);
    }
  };

  const handleNewSchedule = () => {
    setEditingSchedule(undefined);
    setFormOpen(true);
  };

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loading text="Loading schedules..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <ErrorBanner message={`Unable to load schedules: ${error instanceof Error ? error.message : 'Unknown error'}`} />
      </div>
    );
  }

  if (!schedules || schedules.length === 0) {
    return (
      <div className="h-full space-y-4 p-6 animate-fadeInUp">
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border bg-muted/30 p-12 text-center min-h-[400px]">
          <div className="mb-4 rounded-full bg-primary/10 p-4">
            <ClockIcon className="h-8 w-8 text-primary" />
          </div>
          <h2 className="text-lg font-semibold text-foreground">No schedules yet</h2>
          <p className="mt-2 max-w-sm text-sm text-muted-foreground">
            Create your first schedule to automate action execution at specified times.
          </p>
          <Button className="mt-6" onClick={handleNewSchedule}>
            Create Schedule
          </Button>
        </div>
        <ScheduleForm
          open={formOpen}
          onOpenChange={setFormOpen}
          schedule={editingSchedule}
        />
      </div>
    );
  }

  return (
    <div className="h-full space-y-6 p-6 animate-fadeInUp">
      {/* Stats Cards */}
      {stats && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <SummaryCard title="Total" value={stats.total} icon={ClockIcon} variant="neutral" />
          <SummaryCard title="Enabled" value={stats.enabled} icon={PlayIcon} variant="success" />
          <SummaryCard title="Disabled" value={stats.disabled} icon={PauseIcon} variant="neutral" />
          <SummaryCard title="Running" value={stats.running} icon={ClockIcon} variant="info" />
          <SummaryCard title="Failed (24h)" value={stats.failed_24h} icon={ClockIcon} variant="error" />
        </div>
      )}

      {/* Main Card */}
      <div className="rounded-lg border border-border bg-card shadow-sm">
        <div className="flex flex-col gap-4 border-b border-border p-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1">
            <h1 className="text-2xl font-semibold text-card-foreground">Schedules</h1>
            <p className="text-sm text-muted-foreground">
              Manage automated execution schedules for your actions.
            </p>
          </div>
          <div className="flex w-full gap-2 sm:w-auto">
            <Input
              value={currentSearch}
              placeholder="Search schedules..."
              className="transition-all duration-200 focus:scale-[1.02] motion-reduce:focus:scale-100"
              onChange={(event) => {
                const value = event.target.value;
                if (!value) {
                  searchParams.delete('search');
                  setSearchParams(searchParams, { replace: true });
                } else {
                  searchParams.set('search', value);
                  setSearchParams(searchParams, { replace: true });
                }
              }}
            />
            <Select
              value={statusFilter}
              onValueChange={setStatusFilter}
              className={cn(
                "w-[140px]",
                statusFilter === 'enabled' && "border-success/50 ring-1 ring-success/20",
                statusFilter === 'disabled' && "border-muted-foreground/50 ring-1 ring-muted-foreground/20"
              )}
            >
              <SelectItem value="all">All Statuses</SelectItem>
              <SelectItem value="enabled">Enabled</SelectItem>
              <SelectItem value="disabled">Disabled</SelectItem>
            </Select>
            <Button variant="ghost" onClick={() => {
              setSearchParams({});
              setStatusFilter('all');
            }}>
              Reset
            </Button>
            <Button onClick={handleNewSchedule}>
              New Schedule
            </Button>
          </div>
        </div>

        <div className="p-6">
          <div className="rounded-md border border-border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Schedule</TableHead>
                  <TableHead>Next Run</TableHead>
                  <TableHead>Last Run</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-20 text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredSchedules.map((schedule, index) => (
                  <TableRow
                    key={schedule.id}
                    className={cn(
                      'hover:bg-muted/50 transition-all duration-200',
                      'animate-fadeInUp'
                    )}
                    style={{ animationDelay: `${index * 30}ms` }}
                  >
                    <TableCell>
                      <div className="flex flex-col gap-0.5">
                        <span className="font-medium text-card-foreground">{schedule.name}</span>
                        {schedule.description && (
                          <span className="text-xs text-muted-foreground truncate max-w-[300px]">
                            {schedule.description}
                          </span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <code className="rounded bg-muted px-2 py-1 text-xs font-mono">
                        {formatSchedule(schedule)}
                      </code>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {schedule.next_run_at
                        ? new Date(schedule.next_run_at).toLocaleString()
                        : '—'}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {schedule.last_run_at
                        ? new Date(schedule.last_run_at).toLocaleString()
                        : '—'}
                    </TableCell>
                    <TableCell>
                      <Badge variant={schedule.enabled ? 'success' : 'neutral'}>
                        {schedule.enabled ? 'Enabled' : 'Disabled'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleToggle(schedule)}
                          title={schedule.enabled ? 'Disable' : 'Enable'}
                        >
                          {schedule.enabled ? (
                            <PauseIcon className="h-4 w-4" />
                          ) : (
                            <PlayIcon className="h-4 w-4" />
                          )}
                        </Button>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" aria-label="More actions">
                              <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
                                <circle cx="5" cy="12" r="2" />
                                <circle cx="12" cy="12" r="2" />
                                <circle cx="19" cy="12" r="2" />
                              </svg>
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => handleTrigger(schedule.id)}>
                              Trigger Now
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleEdit(schedule)}>
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => handleDelete(schedule.id)}
                              className="text-destructive"
                            >
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      </div>

      <ScheduleForm
        open={formOpen}
        onOpenChange={(open) => {
          setFormOpen(open);
          if (!open) {
            setEditingSchedule(undefined);
          }
        }}
        schedule={editingSchedule}
      />
    </div>
  );
}
