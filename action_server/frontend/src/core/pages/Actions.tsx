import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { Button } from '@/core/components/ui/Button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/core/components/ui/Dialog';
import { Input } from '@/core/components/ui/Input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/core/components/ui/Table';
import { Textarea } from '@/core/components/ui/Textarea';
import type { OpenAPIV3_1 } from 'openapi-types';
import { useActionRunMutation } from '~/queries/actions';
import { useActionServerContext } from '@/shared/context/actionServerContext';
import { useLocalStorage } from '@/shared/hooks/useLocalStorage';
import { Action, ActionPackage, Run, RunStatus, ServerConfig } from '@/shared/types';
import { formDataToPayload, propertiesToFormData } from '@/shared/utils/formData';
import { prettyPrint } from '@/shared/utils/helpers';
import { cn } from '@/shared/utils/cn';

type RunResult = {
  runId: string;
  response: string;
};

const statusLabel: Record<RunStatus, string> = {
  [RunStatus.NOT_RUN]: 'Not run',
  [RunStatus.RUNNING]: 'Running',
  [RunStatus.PASSED]: 'Passed',
  [RunStatus.FAILED]: 'Failed',
  [RunStatus.CANCELLED]: 'Cancelled',
};

const statusBadgeStyles: Record<RunStatus, string> = {
  [RunStatus.NOT_RUN]: 'bg-gray-100 text-gray-600',
  [RunStatus.RUNNING]: 'bg-blue-100 text-blue-700',
  [RunStatus.PASSED]: 'bg-green-100 text-green-700',
  [RunStatus.FAILED]: 'bg-red-100 text-red-700',
  [RunStatus.CANCELLED]: 'bg-yellow-100 text-yellow-700',
};

declare global {
  interface Window {
    __ACTION_SERVER_VERSION__?: string;
  }
}

const buildInitialPayload = (action: Action): string => {
  try {
    if (!action.input_schema) {
      return '{}';
    }
    const schema = JSON.parse(action.input_schema) as OpenAPIV3_1.BaseSchemaObject;
    const formData = propertiesToFormData(schema);
    const payload = formDataToPayload(formData);
    return JSON.stringify(payload, null, 2);
  } catch {
    return '{}';
  }
};

const findPackageForAction = (
  packages: ActionPackage[] | undefined,
  actionId: string | null,
): ActionPackage | undefined => {
  if (!packages || !actionId) {
    return undefined;
  }
  return packages.find((pkg) => pkg.actions.some((action) => action.id === actionId));
};

const getRunsForAction = (runs: Run[] | undefined, actionId: string | null): Run[] => {
  if (!runs || !actionId) {
    return [];
  }
  return runs.filter((run) => run.action_id === actionId);
};

const renderStatusBadge = (status: RunStatus) => {
  return (
    <span className={cn('inline-flex items-center rounded-full px-2 py-1 text-xs font-medium', statusBadgeStyles[status])}>
      {statusLabel[status]}
    </span>
  );
};

const renderPackageBadge = (pkg: ActionPackage | undefined) => {
  if (!pkg) {
    return null;
  }
  return (
    <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-1 text-xs font-medium text-gray-600">
      {pkg.name}
    </span>
  );
};

const documentationSection = (action: Action) => (
  <div className="space-y-4">
    <div>
      <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-500">
        Documentation
      </h3>
      <pre className="mt-2 max-h-64 overflow-auto rounded-md border border-gray-200 bg-gray-50 p-4 text-sm text-gray-700">
        {action.docs || 'No documentation available for this action yet.'}
      </pre>
    </div>
    <div>
      <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-500">Input Schema</h3>
      <pre className="mt-2 max-h-64 overflow-auto rounded-md border border-gray-200 bg-gray-50 p-4 text-sm text-gray-700">
        {prettyPrint(action.input_schema)}
      </pre>
    </div>
    <div>
      <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-500">
        Output Schema
      </h3>
      <pre className="mt-2 max-h-64 overflow-auto rounded-md border border-gray-200 bg-gray-50 p-4 text-sm text-gray-700">
        {prettyPrint(action.output_schema)}
      </pre>
    </div>
  </div>
);

const VersionMismatchBanner = ({ serverConfig }: { serverConfig: ServerConfig | undefined }) => {
  const [dismissed, setDismissed] = useState(false);
  const [knownVersion, setKnownVersion] = useState<string | undefined>(
    window.__ACTION_SERVER_VERSION__,
  );

  useEffect(() => {
    if (!knownVersion && serverConfig?.version) {
      setKnownVersion(serverConfig.version);
    }
  }, [knownVersion, serverConfig?.version]);

  if (!serverConfig?.version || !knownVersion || dismissed) {
    return null;
  }

  if (serverConfig.version === knownVersion) {
    return null;
  }

  return (
    <div className="flex items-start justify-between rounded-md border border-yellow-300 bg-yellow-50 p-4">
      <div>
        <p className="text-sm font-medium text-yellow-800">
          Action Server backend version changed!
        </p>
        <p className="mt-1 text-sm text-yellow-700">
          Reload to ensure the UI is using the latest schema and resources. If you&apos;re in the
          middle of editing request data you can ignore this warning, but the current session may be
          unstable.
        </p>
      </div>
      <div className="flex items-center gap-2">
        <Button
          variant="secondary"
          onClick={() => window.location.reload()}
          className="whitespace-nowrap"
        >
          Reload now
        </Button>
        <Button
          variant="ghost"
          onClick={() => {
            setKnownVersion(serverConfig.version);
            setDismissed(true);
          }}
        >
          Ignore
        </Button>
      </div>
    </div>
  );
};

export const ActionsPage = () => {
  const navigate = useNavigate();
  const { loadedActions, loadedRuns, loadedServerConfig } = useActionServerContext();
  const [selectedActionId, setSelectedActionId] = useState<string | null>(null);
  const [isRunDialogOpen, setRunDialogOpen] = useState(false);
  const [runPayload, setRunPayload] = useState<string>('{}');
  const [runResult, setRunResult] = useState<RunResult | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [apiKey, setApiKey] = useLocalStorage<string>('action-server-api-key', '');
  const { mutateAsync: runAction, isPending: isRunning } = useActionRunMutation();

  const actions = useMemo(() => {
    if (!loadedActions.data) {
      return [];
    }
    return loadedActions.data.flatMap((pkg) => pkg.actions).filter((action) => action.enabled);
  }, [loadedActions.data]);

  const selectedPackage = useMemo(() => {
    return findPackageForAction(loadedActions.data, selectedActionId);
  }, [loadedActions.data, selectedActionId]);

  const selectedAction = useMemo(() => {
    if (!selectedActionId || !selectedPackage) {
      return undefined;
    }
    return selectedPackage.actions.find((action) => action.id === selectedActionId);
  }, [selectedActionId, selectedPackage]);

  const recentRuns = useMemo(() => {
    const runs = getRunsForAction(loadedRuns.data, selectedActionId);
    return runs.slice(0, 10);
  }, [loadedRuns.data, selectedActionId]);

  useEffect(() => {
    if (!selectedActionId && actions.length > 0) {
      setSelectedActionId(actions[0].id);
    }
  }, [actions, selectedActionId]);

  const openRunDialog = useCallback(
    (action: Action) => {
      setRunPayload(buildInitialPayload(action));
      setRunResult(null);
      setRunError(null);
      setRunDialogOpen(true);
    },
    [setRunDialogOpen],
  );

  const handleRunSubmit = useCallback(
    async (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      if (!selectedAction || !selectedPackage) {
        return;
      }
      let parsedPayload: unknown;
      try {
        parsedPayload = JSON.parse(runPayload || '{}');
      } catch (err) {
        setRunError('Invalid JSON payload. Please fix any syntax issues and try again.');
        return;
      }

      try {
        const result = await runAction({
          actionPackageName: selectedPackage.name,
          actionName: selectedAction.name,
          args: parsedPayload as Record<string, unknown>,
          apiKey: apiKey || undefined,
        });
        setRunResult(result);
        setRunError(null);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to run action';
        setRunError(message);
      }
    },
    [apiKey, runAction, runPayload, selectedAction, selectedPackage],
  );

  if (loadedActions.isPending) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-gray-600">
        Loading actions…
      </div>
    );
  }

  if (loadedActions.errorMessage) {
    return (
      <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        Unable to load action packages: {loadedActions.errorMessage}
      </div>
    );
  }

  if (actions.length === 0) {
    return (
      <div className="space-y-4">
        <VersionMismatchBanner serverConfig={loadedServerConfig.data} />
        <div className="rounded-md border border-dashed border-gray-300 bg-gray-50 p-12 text-center">
          <h2 className="text-lg font-semibold text-gray-700">No actions available yet</h2>
          <p className="mt-2 text-sm text-gray-500">
            Install an action package or create one to start running automated workflows.
          </p>
          <Button className="mt-4" onClick={() => navigate('/runs')}>
            Review run history
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <VersionMismatchBanner serverConfig={loadedServerConfig.data} />

      <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="flex flex-col gap-4 border-b border-gray-200 p-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">Action Packages</h1>
            <p className="mt-1 text-sm text-gray-600">
              Actions available on this Action Server instance. Select one to inspect its schema or
              execute it with custom parameters.
            </p>
          </div>
          <div className="text-sm text-gray-500">
            {loadedActions.data?.length || 0} packages • {actions.length} enabled actions
          </div>
        </div>

        <div className="grid gap-6 p-6 lg:grid-cols-[2fr,3fr]">
          <div className="rounded-md border border-gray-200">
            <Table>
              <TableHeader>
                <TableRow className="bg-gray-50">
                  <TableHead>Action</TableHead>
                  <TableHead>Package</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Runs</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {actions.map((action) => {
                  const pkg = findPackageForAction(loadedActions.data, action.id);
                  const runs = getRunsForAction(loadedRuns.data, action.id);
                  const isSelected = selectedActionId === action.id;
                  return (
                    <TableRow
                      key={action.id}
                      className={cn(
                        'cursor-pointer transition-colors',
                        isSelected && 'bg-blue-50 hover:bg-blue-50',
                      )}
                      onClick={() => setSelectedActionId(action.id)}
                    >
                      <TableCell className="font-medium">{action.name}</TableCell>
                      <TableCell>{renderPackageBadge(pkg)}</TableCell>
                      <TableCell className="text-xs text-gray-500">
                        {action.file}:{action.lineno}
                      </TableCell>
                      <TableCell>
                        <span className="rounded-md bg-gray-100 px-2 py-1 text-xs text-gray-600">
                          {runs.length}
                        </span>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>

          <div className="space-y-6">
            {selectedAction && selectedPackage ? (
              <>
                <div className="flex flex-col gap-4 rounded-md border border-gray-200 bg-gray-50 p-6 shadow-sm">
                  <div>
                    <div className="flex flex-wrap items-center gap-3">
                      <h2 className="text-xl font-semibold text-gray-900">
                        {selectedAction.name}
                      </h2>
                      {!selectedAction.enabled && (
                        <span className="rounded-full bg-yellow-100 px-2 py-1 text-xs font-medium text-yellow-700">
                          Not available
                        </span>
                      )}
                      {renderPackageBadge(selectedPackage)}
                    </div>
                    <p className="mt-2 text-sm text-gray-600">
                      {selectedAction.docs
                        ? selectedAction.docs.split('\n')[0]
                        : 'This action does not provide description text yet.'}
                    </p>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <Button onClick={() => openRunDialog(selectedAction)} disabled={!selectedAction.enabled}>
                      Run action
                    </Button>
                    <Button variant="ghost" onClick={() => navigate(`/runs?search=${selectedAction.name}`)}>
                      View related runs
                    </Button>
                  </div>
                </div>

                <div className="rounded-md border border-gray-200 bg-white p-6 shadow-sm">
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-500">
                    Recent runs
                  </h3>
                  {recentRuns.length === 0 ? (
                    <p className="mt-3 text-sm text-gray-500">
                      This action has not been executed yet.
                    </p>
                  ) : (
                    <ul className="mt-3 space-y-2 text-sm text-gray-700">
                      {recentRuns.map((run) => (
                        <li
                          key={run.id}
                          className="flex items-center justify-between rounded-md border border-gray-200 bg-gray-50 px-3 py-2"
                        >
                          <div>
                            <p className="font-medium text-gray-900">
                              {new Date(run.start_time).toLocaleString()}
                            </p>
                            <p className="text-xs text-gray-500">Run #{run.numbered_id}</p>
                          </div>
                          {renderStatusBadge(run.status)}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                <div className="rounded-md border border-gray-200 bg-white p-6 shadow-sm">
                  {documentationSection(selectedAction)}
                </div>
              </>
            ) : (
              <div className="flex h-full items-center justify-center rounded-md border border-dashed border-gray-300 bg-gray-50 p-12 text-sm text-gray-500">
                Select an action to view details
              </div>
            )}
          </div>
        </div>
      </div>

      <Dialog open={isRunDialogOpen} onOpenChange={setRunDialogOpen}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>
              {selectedAction ? `Run ${selectedAction.name}` : 'Run action'}
            </DialogTitle>
            <DialogDescription>
              Update the payload and submit to run the action. The result will display below when
              available.
            </DialogDescription>
          </DialogHeader>

          <form className="space-y-4" onSubmit={handleRunSubmit}>
            <div className="grid gap-2">
              <label htmlFor="api-key" className="text-sm font-medium text-gray-700">
                API Key (optional)
              </label>
              <Input
                id="api-key"
                value={apiKey}
                placeholder="Provide an API key when required by the action"
                onChange={(event) => setApiKey(event.target.value)}
              />
            </div>

            <div className="grid gap-2">
              <label htmlFor="payload" className="text-sm font-medium text-gray-700">
                Payload (JSON)
              </label>
              <Textarea
                id="payload"
                spellCheck={false}
                value={runPayload}
                onChange={(event) => setRunPayload(event.target.value)}
              />
              <p className="text-xs text-gray-500">
                The payload must be valid JSON matching the action input schema.
              </p>
            </div>

            {runError && (
              <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                {runError}
              </div>
            )}

            {runResult && (
              <div className="rounded-md border border-gray-200 bg-gray-50 p-4">
                <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-500">
                  Run result
                </h3>
                <div className="mt-2 text-sm text-gray-700">
                  <p>
                    Run ID: {runResult.runId}
                  </p>
                  <pre className="mt-3 max-h-64 overflow-auto rounded-md border border-gray-200 bg-white p-3 text-xs text-gray-800">
                    {runResult.response}
                  </pre>
                </div>
              </div>
            )}

            <DialogFooter>
              <Button type="submit" disabled={isRunning || !selectedAction}>
                {isRunning ? 'Running…' : 'Run action'}
              </Button>
              <Button type="button" variant="ghost" onClick={() => setRunDialogOpen(false)}>
                Close
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};
