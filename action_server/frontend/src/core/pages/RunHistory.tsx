import { useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { Button } from '@/core/components/ui/Button';
import { Input } from '@/core/components/ui/Input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/core/components/ui/Table';
import { Badge } from '@/core/components/ui/Badge';
import { Loading } from '@/core/components/ui/Loading';
import { ErrorBanner } from '@/core/components/ui/ErrorBanner';
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from '@/core/components/ui/DropdownMenu';
import { useActionServerContext } from '@/shared/context/actionServerContext';
import { Run, RunStatus } from '@/shared/types';
import { cn } from '@/shared/utils/cn';

const statusStyles: Record<RunStatus, string> = {
  [RunStatus.NOT_RUN]: 'bg-gray-100 text-gray-600',
  [RunStatus.RUNNING]: 'bg-blue-100 text-blue-700',
  [RunStatus.PASSED]: 'bg-green-100 text-green-700',
  [RunStatus.FAILED]: 'bg-red-100 text-red-700',
  [RunStatus.CANCELLED]: 'bg-yellow-100 text-yellow-700',
};

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

export const RunHistoryPage = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { loadedRuns, loadedActions } = useActionServerContext();

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
    const runs = [...loadedRuns.data];
    runs.sort((a, b) => b.numbered_id - a.numbered_id);
    if (!currentSearch.trim()) {
      return runs;
    }
    const lowered = currentSearch.toLowerCase();
    return runs.filter((run) => {
      const label = actionLookup.get(run.action_id) || '';
      return label.toLowerCase().includes(lowered) || run.id.toLowerCase().includes(lowered);
    });
  }, [actionLookup, currentSearch, loadedRuns.data]);

  const handleViewDetails = (run: Run) => {
    navigate(`/logs/${run.id}`);
  };

  const handleDownloadLogs = (run: Run) => {
    // TODO: Implement log download functionality
    console.log('Download logs for run:', run.id);
  };

  if (loadedRuns.isPending) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-gray-600">
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
      <div className="space-y-4">
        <div className="flex flex-col items-center justify-center rounded-md border border-dashed border-gray-300 bg-gray-50 p-12 text-center">
          <h2 className="text-lg font-semibold text-gray-700">No runs recorded yet</h2>
          <p className="mt-2 text-sm text-gray-500">
            Trigger an action run to populate the history. Use the Actions page to test your
            automation flows.
          </p>
          <Button className="mt-4" onClick={() => navigate('/actions')}>
            Go to actions
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="flex flex-col gap-4 border-b border-gray-200 p-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">Run History</h1>
            <p className="mt-1 text-sm text-gray-600">
              Monitor the latest executions across all action packages. Use the filters to narrow by
              action or run identifier.
            </p>
          </div>
          <div className="flex w-full gap-2 sm:w-auto">
            <Input
              value={currentSearch}
              placeholder="Filter by action or run id"
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
            <Button variant="ghost" onClick={() => setSearchParams({})}>
              Reset
            </Button>
          </div>
        </div>

        <div className="p-6">
          <div className="rounded-md border border-gray-200">
            <Table>
              <TableHeader>
                <TableRow className="bg-gray-50">
                  <TableHead className="w-20">Run #</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead>Started</TableHead>
                  <TableHead className="hidden sm:table-cell">Duration</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-20 text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredRuns.map((run) => {
                  const label = actionLookup.get(run.action_id) || run.action_id;
                  return (
                    <TableRow key={run.id}>
                      <TableCell className="font-mono text-sm text-gray-700">
                        {run.numbered_id}
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col">
                          <span className="font-medium text-gray-900">{label}</span>
                          <span className="text-xs text-gray-500">{run.id}</span>
                        </div>
                      </TableCell>
                      <TableCell className="whitespace-nowrap text-sm text-gray-600">
                        {new Date(run.start_time).toLocaleString()}
                      </TableCell>
                      <TableCell className="hidden whitespace-nowrap text-sm text-gray-600 sm:table-cell">
                        {formatDuration(run)}
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
                              <Button variant="ghost" size="icon" aria-label="More actions">
                                <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                                  <circle cx="5" cy="12" r="2" />
                                  <circle cx="12" cy="12" r="2" />
                                  <circle cx="19" cy="12" r="2" />
                                </svg>
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem onClick={() => handleViewDetails(run)}>
                                View Details
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => handleDownloadLogs(run)}>
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
