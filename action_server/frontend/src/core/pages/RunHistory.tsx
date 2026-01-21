import { useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { Button } from '@/core/components/ui/Button';
import { Input } from '@/core/components/ui/Input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/core/components/ui/Table';
import { Badge } from '@/core/components/ui/Badge';
import { Loading } from '@/core/components/ui/Loading';
import { ErrorBanner } from '@/core/components/ui/ErrorBanner';
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from '@/core/components/ui/DropdownMenu';
import { Select, SelectItem } from '@/core/components/ui/Select';
import { useActionServerContext } from '@/shared/context/actionServerContext';
import { Run, RunStatus } from '@/shared/types';
import { cn } from '@/shared/utils/cn';
import { baseUrl, refreshRuns } from '@/shared/api-client';

// Status styles are now handled by Badge component variants

const statusLabel: Record<RunStatus, string> = {
  [RunStatus.NOT_RUN]: 'Not run',
  [RunStatus.RUNNING]: 'Running',
  [RunStatus.PASSED]: 'Passed',
  [RunStatus.FAILED]: 'Failed',
  [RunStatus.CANCELLED]: 'Cancelled',
};

const formatDuration = (run: Run) => {
  if (!run.run_time) {
    return '—';
  }
  if (run.run_time < 1) {
    return `${Math.round(run.run_time * 1000)} ms`;
  }
  return `${run.run_time.toFixed(2)} s`;
};

// Icon components for run types
const ActionIcon = () => (
  <svg className="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
  </svg>
);

const RobotIcon = () => (
  <svg className="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="11" width="18" height="10" rx="2" />
    <circle cx="12" cy="5" r="2" />
    <path d="M12 7v4" />
    <line x1="8" y1="16" x2="8" y2="16" />
    <line x1="16" y1="16" x2="16" y2="16" />
  </svg>
);

export const RunHistoryPage = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { loadedRuns, loadedActions } = useActionServerContext();
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await refreshRuns();
    } finally {
      // Short delay to show feedback
      setTimeout(() => setIsRefreshing(false), 300);
    }
  };

  const actionLookup = useMemo(() => {
    const map = new Map<string, string>();
    loadedActions.data?.forEach((pkg) => {
      pkg.actions.forEach((action) => {
        map.set(action.id, `${pkg.name} / ${action.name}`);
      });
    });
    return map;
  }, [loadedActions.data]);

  const currentSearch = searchParams.get('search') || '';
  const filteredRuns = useMemo(() => {
    if (!loadedRuns.data) {
      return [];
    }
    let runs = [...loadedRuns.data];
    runs.sort((a, b) => b.numbered_id - a.numbered_id);
    
    // Filter by type
    if (typeFilter !== 'all') {
      runs = runs.filter((run) => (run.run_type || 'action') === typeFilter);
    }
    
    if (!currentSearch.trim()) {
      return runs;
    }
    const lowered = currentSearch.toLowerCase();
    return runs.filter((run) => {
      const runType = run.run_type || 'action';
      if (runType === 'robot') {
        return (
          run.robot_task_name?.toLowerCase().includes(lowered) ||
          run.robot_package_path?.toLowerCase().includes(lowered) ||
          run.id.toLowerCase().includes(lowered)
        );
      }
      const label = actionLookup.get(run.action_id) || '';
      return label.toLowerCase().includes(lowered) || run.id.toLowerCase().includes(lowered);
    });
  }, [actionLookup, currentSearch, loadedRuns.data, typeFilter]);

  // Get run name/label based on type
  const getRunLabel = (run: Run) => {
    const runType = run.run_type || 'action';
    if (runType === 'robot') {
      return run.robot_task_name || 'Unknown Task';
    }
    return actionLookup.get(run.action_id) || run.action_id;
  };

  // Get run subtitle based on type
  const getRunSubtitle = (run: Run) => {
    const runType = run.run_type || 'action';
    if (runType === 'robot') {
      return run.robot_package_path || '';
    }
    return run.id;
  };

  const handleViewDetails = (run: Run) => {
    navigate(`/logs/${run.id}`);
  };

  const handleDownloadLogs = (run: Run) => {
    // Create a temporary anchor element to trigger the download
    const link = document.createElement('a');
    link.href = `${baseUrl}/api/runs/${run.id}/log.html`;
    link.download = `run-${run.numbered_id}-log.html`;
    link.target = '_blank';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (loadedRuns.isPending) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loading text="Loading run history…" />
      </div>
    );
  }

  if (loadedRuns.errorMessage) {
    return (
      <div className="p-6">
        <ErrorBanner message={`Unable to load run history: ${loadedRuns.errorMessage}`} />
      </div>
    );
  }

  if (filteredRuns.length === 0) {
    return (
      <div className="h-full space-y-4 p-6 animate-fadeInUp">
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border bg-muted/30 p-12 text-center min-h-[400px]">
          <div className="mb-4 rounded-full bg-primary/10 p-4">
            <svg className="h-8 w-8 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="8" x2="21" y1="6" y2="6" />
              <line x1="8" x2="21" y1="12" y2="12" />
              <line x1="8" x2="21" y1="18" y2="18" />
              <line x1="3" x2="3.01" y1="6" y2="6" />
              <line x1="3" x2="3.01" y1="12" y2="12" />
              <line x1="3" x2="3.01" y1="18" y2="18" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold text-foreground">No runs recorded yet</h2>
          <p className="mt-2 max-w-sm text-sm text-muted-foreground">
            Trigger an Action or Robot run to populate the history. Use the Actions page to test your
            automation flows.
          </p>
          <Button className="mt-6" onClick={() => navigate('/actions')}>
            Go to actions
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full space-y-6 p-6 animate-fadeInUp">
      <div className="rounded-lg border border-border bg-card shadow-sm">
        <div className="flex flex-col gap-4 border-b border-border p-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1">
            <h1 className="text-2xl font-semibold text-card-foreground">Run History</h1>
            <p className="text-sm text-muted-foreground">
              Monitor executions across all Actions and Robots. Filter by type, name, or run identifier.
            </p>
          </div>
          <div className="flex w-full gap-2 sm:w-auto">
            <Input
              value={currentSearch}
              placeholder="Filter by name or run id"
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
              value={typeFilter} 
              onValueChange={setTypeFilter} 
              className={cn(
                "w-[150px]",
                typeFilter === 'action' && "border-primary/50 ring-1 ring-primary/20",
                typeFilter === 'robot' && "border-info/50 ring-1 ring-info/20"
              )}
            >
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value="action">Actions Only</SelectItem>
              <SelectItem value="robot">Robots Only</SelectItem>
            </Select>
            <Button variant="ghost" onClick={() => {
              setSearchParams({});
              setTypeFilter('all');
            }}>
              Reset
            </Button>
            <Button 
              variant="ghost" 
              onClick={handleRefresh}
              disabled={isRefreshing}
              title="Refresh runs"
            >
              <svg 
                className={cn("h-4 w-4", isRefreshing && "animate-spin")} 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor" 
                strokeWidth="2"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </Button>
          </div>
        </div>

        <div className="p-6">
          <div className="rounded-md border border-border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-20">Run #</TableHead>
                  <TableHead className="w-24">Type</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Started</TableHead>
                  <TableHead className="hidden sm:table-cell">Duration</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-20 text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredRuns.map((run, index) => {
                  const runType = run.run_type || 'action';
                  const label = getRunLabel(run);
                  const subtitle = getRunSubtitle(run);
                  return (
                    <TableRow
                      key={run.id}
                      className={cn(
                        'hover:bg-muted/50 transition-all duration-200 cursor-pointer',
                        'animate-fadeInUp',
                        'motion-reduce:animate-none',
                        'relative'
                      )}
                      style={{ animationDelay: `${index * 30}ms` }}
                      onClick={() => handleViewDetails(run)}
                    >
                      <TableCell className="font-mono text-sm text-foreground">
                        <div className="flex items-center gap-2">
                          <span 
                            className={cn(
                              "w-1 h-6 rounded-full shrink-0",
                              runType === 'robot' ? 'bg-info' : 'bg-primary'
                            )}
                            aria-hidden="true"
                          />
                          {run.numbered_id}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge 
                          variant={runType === 'robot' ? 'secondary' : 'primary'}
                          className="gap-1.5"
                        >
                          {runType === 'robot' ? <RobotIcon /> : <ActionIcon />}
                          {runType === 'robot' ? 'Robot' : 'Action'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col gap-0.5">
                          <span className="font-medium text-card-foreground">{label}</span>
                          <span className="text-xs text-muted-foreground truncate max-w-[300px]">
                            {runType === 'robot' ? (
                              <span className="flex items-center gap-1">
                                <span className="text-info/70">Package:</span>
                                <span className="font-mono">{subtitle || '—'}</span>
                              </span>
                            ) : (
                              <span className="flex items-center gap-1">
                                <span className="text-primary/70">Run ID:</span>
                                <span className="font-mono">{subtitle}</span>
                              </span>
                            )}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell className="whitespace-nowrap text-sm text-muted-foreground">
                        {new Date(run.start_time).toLocaleString()}
                      </TableCell>
                      <TableCell className="hidden whitespace-nowrap text-sm text-muted-foreground sm:table-cell">
                        <span className="inline-flex items-center gap-1.5">
                          {formatDuration(run)}
                        </span>
                      </TableCell>
                      <TableCell>
                        <Badge variant={
                          run.status === RunStatus.PASSED ? 'success' :
                          run.status === RunStatus.FAILED ? 'error' :
                          run.status === RunStatus.RUNNING ? 'info' :
                          run.status === RunStatus.CANCELLED ? 'warning' : 'neutral'
                        }>
                          {statusLabel[run.status]}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon"
                                aria-label="More actions"
                                onClick={(e) => e.stopPropagation()}
                              >
                                <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                                  <circle cx="5" cy="12" r="2" />
                                  <circle cx="12" cy="12" r="2" />
                                  <circle cx="19" cy="12" r="2" />
                                </svg>
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem onClick={(e) => {
                                e.stopPropagation();
                                handleViewDetails(run);
                              }}>
                                View Details
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={(e) => {
                                e.stopPropagation();
                                handleDownloadLogs(run);
                              }}>
                                Download Logs
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        </div>
      </div>
    </div>
  );
};
