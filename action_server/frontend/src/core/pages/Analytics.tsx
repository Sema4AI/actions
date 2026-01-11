import { useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  Legend,
} from 'recharts';

import { Loading } from '@/core/components/ui/Loading';
import { ErrorBanner } from '@/core/components/ui/ErrorBanner';
import { Badge } from '@/core/components/ui/Badge';
import { cn } from '@/shared/utils/cn';
import {
  useAnalyticsSummary,
  useRunsByDay,
  useRunsByAction,
} from '@/queries/analytics';

// Icon Props type
interface IconProps {
  className?: string;
}

// Base SVG Icon wrapper
function SvgIcon({
  className,
  size = "16",
  children
}: IconProps & {
  size?: string;
  children: React.ReactNode;
}): JSX.Element {
  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {children}
    </svg>
  );
}

// Icon components
function ChartIcon({ className }: IconProps): JSX.Element {
  return (
    <SvgIcon className={className} size="24">
      <line x1="12" y1="20" x2="12" y2="10" />
      <line x1="18" y1="20" x2="18" y2="4" />
      <line x1="6" y1="20" x2="6" y2="16" />
    </SvgIcon>
  );
}

function TrendUpIcon({ className }: IconProps): JSX.Element {
  return (
    <SvgIcon className={className}>
      <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" />
      <polyline points="16 7 22 7 22 13" />
    </SvgIcon>
  );
}

function ClockIcon({ className }: IconProps): JSX.Element {
  return (
    <SvgIcon className={className}>
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </SvgIcon>
  );
}

function CheckCircleIcon({ className }: IconProps): JSX.Element {
  return (
    <SvgIcon className={className}>
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <polyline points="22 4 12 14.01 9 11.01" />
    </SvgIcon>
  );
}

function ActivityIcon({ className }: IconProps): JSX.Element {
  return (
    <SvgIcon className={className}>
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
    </SvgIcon>
  );
}

// Summary Card Props
interface SummaryCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ComponentType<IconProps>;
  trend?: 'up' | 'down' | 'neutral';
}

// Summary Card Component
function SummaryCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
}: SummaryCardProps): JSX.Element {
  return (
    <div className="rounded-lg border border-border bg-card p-6 shadow-sm transition-all duration-200 hover:shadow-md">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-muted-foreground">{title}</span>
        <div className="rounded-full bg-primary/10 p-2">
          <Icon className="h-4 w-4 text-primary" />
        </div>
      </div>
      <div className="mt-3 flex items-baseline gap-2">
        <span className="text-3xl font-bold text-card-foreground">{value}</span>
        {trend && (
          <TrendUpIcon
            className={cn(
              'h-4 w-4',
              trend === 'up' && 'text-green-500',
              trend === 'down' && 'rotate-180 text-red-500',
              trend === 'neutral' && 'text-muted-foreground'
            )}
          />
        )}
      </div>
      {subtitle && (
        <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>
      )}
    </div>
  );
}

// Format duration helper
function formatDuration(ms: number): string {
  if (ms < 1000) {
    return `${Math.round(ms)}ms`;
  }
  return `${(ms / 1000).toFixed(2)}s`;
}

// Calculate success rate
function calculateSuccessRate(passed: number, failed: number): string {
  const total = passed + failed;
  if (total === 0) return '0';
  return ((passed / total) * 100).toFixed(1);
}

// Get trend indicator based on success rate
function getTrend(successRate: number): 'up' | 'down' | 'neutral' {
  if (successRate >= 90) {
    return 'up';
  }
  if (successRate >= 70) {
    return 'neutral';
  }
  return 'down';
}

// Get badge variant based on success rate
function getBadgeVariant(successRate: number): 'success' | 'warning' | 'error' {
  if (successRate >= 90) {
    return 'success';
  }
  if (successRate >= 70) {
    return 'warning';
  }
  return 'error';
}

export function AnalyticsPage(): JSX.Element {
  const {
    data: summary,
    isLoading: summaryLoading,
    error: summaryError,
  } = useAnalyticsSummary();
  const {
    data: runsByDay,
    isLoading: runsByDayLoading,
    error: runsByDayError,
  } = useRunsByDay(30);
  const {
    data: runsByAction,
    isLoading: runsByActionLoading,
    error: runsByActionError,
  } = useRunsByAction();

  const isLoading = summaryLoading || runsByDayLoading || runsByActionLoading;
  const error = summaryError || runsByDayError || runsByActionError;

  // Prepare chart data
  const chartData = useMemo(() => {
    if (!runsByDay) return [];
    return runsByDay.map((item) => ({
      ...item,
      // Format date for display
      displayDate: new Date(item.date).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      }),
    }));
  }, [runsByDay]);

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loading text="Loading analytics..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <ErrorBanner
          message={`Unable to load analytics: ${error instanceof Error ? error.message : 'Unknown error'}`}
        />
      </div>
    );
  }

  if (!summary || summary.total_runs === 0) {
    return (
      <div className="h-full space-y-4 p-6 animate-fadeInUp">
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border bg-muted/30 p-12 text-center min-h-[400px]">
          <div className="mb-4 rounded-full bg-primary/10 p-4">
            <ChartIcon className="h-8 w-8 text-primary" />
          </div>
          <h2 className="text-lg font-semibold text-foreground">
            No analytics data yet
          </h2>
          <p className="mt-2 max-w-sm text-sm text-muted-foreground">
            Run some actions to generate analytics data. Statistics will appear
            here once runs are recorded.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full space-y-6 p-6 animate-fadeInUp">
      {/* Header */}
      <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="rounded-full bg-primary/10 p-2">
            <ChartIcon className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold text-card-foreground">
              Analytics
            </h1>
            <p className="text-sm text-muted-foreground">
              Monitor action execution metrics and performance trends
            </p>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <SummaryCard
          title="Total Runs"
          value={summary.total_runs.toLocaleString()}
          subtitle="All time"
          icon={ActivityIcon}
        />
        <SummaryCard
          title="Success Rate"
          value={`${summary.success_rate}%`}
          subtitle="Passed / Completed"
          icon={CheckCircleIcon}
          trend={getTrend(summary.success_rate)}
        />
        <SummaryCard
          title="Avg Duration"
          value={formatDuration(summary.avg_duration_ms)}
          subtitle="Per completed run"
          icon={ClockIcon}
        />
        <SummaryCard
          title="Runs Today"
          value={summary.runs_today.toLocaleString()}
          subtitle="Since midnight"
          icon={TrendUpIcon}
        />
      </div>

      {/* Charts Section */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Runs Over Time Chart */}
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-card-foreground">
            Runs Over Time
          </h2>
          <p className="mb-4 text-sm text-muted-foreground">
            Daily run counts for the last 30 days
          </p>
          {chartData.length > 0 ? (
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    className="stroke-border"
                  />
                  <XAxis
                    dataKey="displayDate"
                    tick={{ fontSize: 12 }}
                    className="text-muted-foreground"
                  />
                  <YAxis tick={{ fontSize: 12 }} className="text-muted-foreground" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px',
                    }}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="passed"
                    name="Passed"
                    stroke="hsl(142, 76%, 36%)"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="failed"
                    name="Failed"
                    stroke="hsl(0, 84%, 60%)"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="flex h-[300px] items-center justify-center text-muted-foreground">
              No data available
            </div>
          )}
        </div>

        {/* Runs by Action Chart */}
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-card-foreground">
            Runs by Action
          </h2>
          <p className="mb-4 text-sm text-muted-foreground">
            Top actions by execution count
          </p>
          {runsByAction && runsByAction.length > 0 ? (
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={runsByAction.slice(0, 10)}
                  layout="vertical"
                  margin={{ left: 20 }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    className="stroke-border"
                    horizontal={true}
                    vertical={false}
                  />
                  <XAxis type="number" tick={{ fontSize: 12 }} />
                  <YAxis
                    type="category"
                    dataKey="action_name"
                    tick={{ fontSize: 11 }}
                    width={120}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px',
                    }}
                    formatter={(value: number, name: string) => [
                      value,
                      name === 'passed' ? 'Passed' : 'Failed',
                    ]}
                  />
                  <Legend />
                  <Bar
                    dataKey="passed"
                    name="Passed"
                    stackId="a"
                    fill="hsl(142, 76%, 36%)"
                    radius={[0, 0, 0, 0]}
                  />
                  <Bar
                    dataKey="failed"
                    name="Failed"
                    stackId="a"
                    fill="hsl(0, 84%, 60%)"
                    radius={[0, 4, 4, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="flex h-[300px] items-center justify-center text-muted-foreground">
              No data available
            </div>
          )}
        </div>
      </div>

      {/* Action Performance Table */}
      {runsByAction && runsByAction.length > 0 && (
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-card-foreground">
            Action Performance
          </h2>
          <p className="mb-4 text-sm text-muted-foreground">
            Detailed performance metrics per action
          </p>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="py-3 text-left text-sm font-medium text-muted-foreground">
                    Action
                  </th>
                  <th className="py-3 text-left text-sm font-medium text-muted-foreground">
                    Package
                  </th>
                  <th className="py-3 text-right text-sm font-medium text-muted-foreground">
                    Total Runs
                  </th>
                  <th className="py-3 text-right text-sm font-medium text-muted-foreground">
                    Success Rate
                  </th>
                  <th className="py-3 text-right text-sm font-medium text-muted-foreground">
                    Avg Duration
                  </th>
                </tr>
              </thead>
              <tbody>
                {runsByAction.map((action, index) => {
                  const successRate = calculateSuccessRate(action.passed, action.failed);
                  const successRateValue = parseFloat(successRate);
                  const badgeVariant = getBadgeVariant(successRateValue);

                  return (
                    <tr
                      key={`${action.package_name}-${action.action_name}`}
                      className={cn(
                        'border-b border-border/50 transition-colors hover:bg-muted/50',
                        'animate-fadeInUp'
                      )}
                      style={{ animationDelay: `${index * 30}ms` }}
                    >
                      <td className="py-3 font-medium text-card-foreground">
                        {action.action_name}
                      </td>
                      <td className="py-3 text-muted-foreground">
                        {action.package_name}
                      </td>
                      <td className="py-3 text-right font-mono text-sm">
                        {action.total.toLocaleString()}
                      </td>
                      <td className="py-3 text-right">
                        <Badge variant={badgeVariant}>
                          {successRate}%
                        </Badge>
                      </td>
                      <td className="py-3 text-right font-mono text-sm text-muted-foreground">
                        {formatDuration(action.avg_duration_ms)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default AnalyticsPage;
