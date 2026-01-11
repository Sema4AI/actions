import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { Badge } from '@/core/components/ui/Badge';
import { Button } from '@/core/components/ui/Button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/core/components/ui/Dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/core/components/ui/DropdownMenu';
import { ErrorBanner } from '@/core/components/ui/ErrorBanner';
import { Input } from '@/core/components/ui/Input';
import { Loading } from '@/core/components/ui/Loading';
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
import { getStaggerDelay, animationClasses } from '@/shared/utils/animations';
import { ActionsIcon } from '@/shared/components/Icons';

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

// statusBadgeStyles is superseded by Badge variants — mapping now lives in renderStatusBadge

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

type SchemaProperty = {
  name: string;
  type: string;
  description?: string;
  required: boolean;
  default?: unknown;
};

const parseInputSchema = (action: Action): SchemaProperty[] => {
  try {
    if (!action.input_schema) {
      return [];
    }
    const schema = JSON.parse(action.input_schema) as OpenAPIV3_1.SchemaObject;
    const properties = schema.properties || {};
    const required = schema.required || [];

    return Object.entries(properties).map(([name, prop]) => {
      const propSchema = prop as OpenAPIV3_1.SchemaObject;
      return {
        name,
        type: propSchema.type as string || 'string',
        description: propSchema.description,
        required: required.includes(name),
        default: propSchema.default,
      };
    });
  } catch {
    return [];
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

export const renderStatusBadge = (status: RunStatus) => {
  // Map run status to badge variants for consistent visual semantics
  const map: Record<RunStatus, 'success' | 'error' | 'warning' | 'info' | 'neutral'> = {
    [RunStatus.NOT_RUN]: 'neutral',
    [RunStatus.RUNNING]: 'info',
    [RunStatus.PASSED]: 'success',
    [RunStatus.FAILED]: 'error',
    [RunStatus.CANCELLED]: 'warning',
  };
  const variant = map[status] ?? 'neutral';

  return <Badge variant={variant}>{statusLabel[status]}</Badge>;
};

const renderPackageBadge = (pkg: ActionPackage | undefined) => {
  if (!pkg) {
    return null;
  }
  return (
    <span className="inline-flex items-center rounded-full bg-muted px-2 py-1 text-xs font-medium text-muted-foreground">
      {pkg.name}
    </span>
  );
};

const documentationSection = (action: Action) => (
  <div className="space-y-4">
    <div>
      <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
        Documentation
      </h3>
      <pre className="mt-2 max-h-64 overflow-auto rounded-md border border-border bg-muted/50 p-4 text-sm text-foreground">
        {action.docs || 'No documentation available for this action yet.'}
      </pre>
    </div>
    <div>
      <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">Input Schema</h3>
      <pre className="mt-2 max-h-64 overflow-auto rounded-md border border-border bg-muted/50 p-4 text-sm text-foreground">
        {prettyPrint(action.input_schema)}
      </pre>
    </div>
    <div>
      <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
        Output Schema
      </h3>
      <pre className="mt-2 max-h-64 overflow-auto rounded-md border border-border bg-muted/50 p-4 text-sm text-foreground">
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
    <div className="flex items-start justify-between rounded-md border border-yellow-500/30 bg-yellow-500/10 p-4">
      <div>
        <p className="text-sm font-medium text-yellow-600 dark:text-yellow-400">
          Action Server backend version changed!
        </p>
        <p className="mt-1 text-sm text-yellow-700 dark:text-yellow-300/80">
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
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [actionToDelete, setActionToDelete] = useState<Action | null>(null);
  const [runPayload, setRunPayload] = useState<string>('{}');
  const [runResult, setRunResult] = useState<RunResult | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [jsonPayloadError, setJsonPayloadError] = useState<string | null>(null);
  const [contactEmail, setContactEmail] = useState<string>('');
  const [contactEmailError, setContactEmailError] = useState<string | null>(null);
  const [apiKey, setApiKey] = useLocalStorage<string>('action-server-api-key', '');
  const [useAdvancedMode, setUseAdvancedMode] = useState(false);
  const [formValues, setFormValues] = useState<Record<string, string>>({});
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
      setUseAdvancedMode(false);

      // Initialize form values with defaults
      const properties = parseInputSchema(action);
      const initialValues: Record<string, string> = {};
      properties.forEach((prop) => {
        if (prop.default !== undefined) {
          initialValues[prop.name] = String(prop.default);
        } else {
          initialValues[prop.name] = '';
        }
      });
      setFormValues(initialValues);

      setRunDialogOpen(true);
    },
    [setRunDialogOpen],
  );

  const openDeleteDialog = useCallback(
    (action: Action) => {
      setActionToDelete(action);
      setDeleteDialogOpen(true);
    },
    [],
  );

  const handleDelete = useCallback(
    async () => {
      if (!actionToDelete) {
        return;
      }
      // TODO: Implement actual delete API call
      // Example: await deleteAction(actionToDelete.id);
      console.log('Delete action:', actionToDelete.name);
      setDeleteDialogOpen(false);
      setActionToDelete(null);
    },
    [actionToDelete],
  );

  const handleRunSubmit = useCallback(
    async (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      if (!selectedAction || !selectedPackage) {
        return;
      }
      let parsedPayload: unknown;

      if (useAdvancedMode) {
        // Use JSON payload from textarea
        try {
          parsedPayload = JSON.parse(runPayload || '{}');
          setJsonPayloadError(null);
        } catch (err) {
          setJsonPayloadError('Invalid JSON payload. Please fix any syntax issues and try again.');
          return;
        }
      } else {
        // Build payload from form values
        const properties = parseInputSchema(selectedAction);
        const payload: Record<string, unknown> = {};

        properties.forEach((prop) => {
          const value = formValues[prop.name];
          if (value !== undefined && value !== '') {
            // Convert value based on type
            if (prop.type === 'number' || prop.type === 'integer') {
              payload[prop.name] = Number(value);
            } else if (prop.type === 'boolean') {
              payload[prop.name] = value === 'true';
            } else if (prop.type === 'array' || prop.type === 'object') {
              try {
                payload[prop.name] = JSON.parse(value);
              } catch {
                payload[prop.name] = value;
              }
            } else {
              payload[prop.name] = value;
            }
          }
        });

        parsedPayload = payload;
        setJsonPayloadError(null);
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
    [apiKey, runAction, runPayload, selectedAction, selectedPackage, useAdvancedMode, formValues],
  );

  if (loadedActions.isPending) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
        Loading actions…
      </div>
    );
  }

  if (loadedActions.errorMessage) {
    return (
      <div className="rounded-md border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
        Unable to load action packages: {loadedActions.errorMessage}
      </div>
    );
  }

  if (actions.length === 0) {
    return (
      <div className="h-full space-y-4 p-6 animate-fadeInUp">
        <VersionMismatchBanner serverConfig={loadedServerConfig.data} />
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border bg-muted/30 p-12 text-center min-h-[400px]">
          <div className="mb-4 rounded-full bg-primary/10 p-4">
            <ActionsIcon className="h-8 w-8 text-primary" />
          </div>
          <h2 className="text-lg font-semibold text-foreground">No actions available yet</h2>
          <p className="mt-2 max-w-sm text-sm text-muted-foreground">
            Install an action package or create one to start running automated workflows.
          </p>
          <Button className="mt-6" onClick={() => navigate('/runs')}>
            Review run history
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full space-y-6 p-6 animate-fadeInUp">
      <VersionMismatchBanner serverConfig={loadedServerConfig.data} />

      <div className="rounded-lg border border-border bg-card shadow-sm">
        <div className="flex flex-col gap-4 border-b border-border p-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1">
            <h1 className="text-2xl font-semibold text-card-foreground">Action Packages</h1>
            <p className="text-sm text-muted-foreground">
              Actions available on this Action Server instance. Select one to inspect its schema or
              execute it with custom parameters.
            </p>
          </div>
          <div className="text-sm text-muted-foreground whitespace-nowrap">
            {loadedActions.data?.length || 0} packages • {actions.length} enabled actions
          </div>
        </div>

        <div className="grid gap-6 p-6 lg:grid-cols-[2fr,3fr]">
          <div className="rounded-md border border-border">
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/50">
                  <TableHead>Action</TableHead>
                  <TableHead>Package</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Runs</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {actions.map((action, index) => {
                  const pkg = findPackageForAction(loadedActions.data, action.id);
                  const runs = getRunsForAction(loadedRuns.data, action.id);
                  const isSelected = selectedActionId === action.id;
                  return (
                    <TableRow
                      key={action.id}
                      className={cn(
                        // Base styles
                        'cursor-pointer',
                        // Colors and states
                        'hover:bg-muted/50',
                        isSelected && 'bg-primary/10 hover:bg-primary/15 border-l-2 border-l-primary',
                        // Animations
                        animationClasses.transitionWithMotionSafe,
                        animationClasses.fadeInWithMotionSafe,
                      )}
                      style={getStaggerDelay(index)}
                      onClick={() => setSelectedActionId(action.id)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          setSelectedActionId(action.id);
                        }
                      }}
                      aria-selected={isSelected}
                    >
                      <TableCell className="font-medium text-card-foreground">{action.name}</TableCell>
                      <TableCell>{renderPackageBadge(pkg)}</TableCell>
                      <TableCell className="text-xs text-muted-foreground font-mono">
                        {action.file}:{action.lineno}
                      </TableCell>
                      <TableCell>
                        <span className="inline-flex items-center justify-center rounded-md bg-muted px-2 py-1 text-xs text-muted-foreground font-medium min-w-[2rem]">
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
                <div
                  className={cn(
                    // Layout
                    'flex flex-col gap-4 p-6',
                    // Style
                    'rounded-md border border-border bg-gradient-to-br from-card to-muted/20 shadow-sm',
                    // Hover effects
                    'hover:shadow-md hover:border-border/60',
                    // Animations
                    'transition-all duration-300',
                    animationClasses.fadeInWithMotionSafe,
                  )}
                >
                  <div>
                    <div className="flex flex-wrap items-center gap-3">
                      <h2 className="text-xl font-semibold text-card-foreground">
                        {selectedAction.name}
                      </h2>
                      {!selectedAction.enabled && (
                        <Badge variant="warning">
                          Not available
                        </Badge>
                      )}
                      {renderPackageBadge(selectedPackage)}
                    </div>
                    <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                      {selectedAction.docs
                        ? selectedAction.docs.split('\n')[0]
                        : 'This action does not provide description text yet.'}
                    </p>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <Button onClick={() => openRunDialog(selectedAction)} disabled={!selectedAction.enabled}>
                      Run action
                    </Button>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0" aria-label="Open action menu">
                          <span className="sr-only">Open action menu</span>
                          <svg
                            className="h-4 w-4"
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 16 16"
                            fill="currentColor"
                            aria-hidden="true"
                          >
                            <circle cx="8" cy="2" r="1.5" />
                            <circle cx="8" cy="8" r="1.5" />
                            <circle cx="8" cy="14" r="1.5" />
                          </svg>
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => openRunDialog(selectedAction)}>
                          Run action
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => navigate(`/runs?search=${selectedAction.name}`)}>
                          View logs
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem destructive onClick={() => openDeleteDialog(selectedAction)}>
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>

                <div
                  className={cn(
                    // Layout & style
                    'p-6 rounded-md border border-border bg-card shadow-sm',
                    // Hover effects
                    'hover:shadow-md hover:border-border/60',
                    // Animations
                    'transition-all duration-300',
                    animationClasses.fadeInWithMotionSafe,
                  )}
                  style={{ animationDelay: '100ms' }}
                >
                  <h3 className="section-header">
                    Recent runs
                  </h3>
                  {recentRuns.length === 0 ? (
                    <p className="mt-3 text-sm text-muted-foreground">
                      This action has not been executed yet.
                    </p>
                  ) : (
                    <ul className="mt-3 space-y-2 text-sm">
                      {recentRuns.map((run, index) => (
                        <li
                          key={run.id}
                          className={cn(
                            // Layout
                            'flex items-center justify-between px-3 py-2.5',
                            // Style
                            'rounded-md border border-border bg-muted/30 cursor-pointer',
                            // Hover effects
                            'hover:bg-muted/50 hover:border-border/60',
                            // Animations
                            animationClasses.fadeInWithMotionSafe,
                            'transition-all duration-200',
                          )}
                          style={getStaggerDelay(index + 1, 50)}
                          onClick={() => navigate(`/logs/${run.id}`)}
                          role="button"
                          tabIndex={0}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                              e.preventDefault();
                              navigate(`/logs/${run.id}`);
                            }
                          }}
                        >
                          <div>
                            <p className="font-medium text-card-foreground">
                              {new Date(run.start_time).toLocaleString()}
                            </p>
                            <p className="text-xs text-muted-foreground font-mono">Run #{run.numbered_id}</p>
                          </div>
                          {renderStatusBadge(run.status)}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                <div
                  className={cn(
                    'rounded-md border border-border bg-card p-6 shadow-sm',
                    'transition-all duration-300',
                    'hover:shadow-md hover:border-border/60',
                    'animate-fadeInUp',
                    'motion-reduce:transform-none motion-reduce:transition-none motion-reduce:animate-none',
                  )}
                  style={{ animationDelay: '200ms' }}
                >
                  {documentationSection(selectedAction)}
                </div>
              </>
            ) : (
              <div className="flex h-full items-center justify-center rounded-md border border-dashed border-border bg-muted/50 p-12 text-sm text-muted-foreground">
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
            {loadedServerConfig.data?.auth_enabled && (
              <div className="grid gap-2">
                <label htmlFor="api-key" className="text-sm font-medium text-foreground">
                  API Key
                </label>
                <Input
                  id="api-key"
                  value={apiKey}
                  placeholder="Bearer key required for authentication"
                  onChange={(event) => setApiKey(event.target.value)}
                />
              </div>
            )}

            <div className="grid gap-2">
              <label htmlFor="contact-email" className="text-sm font-medium text-foreground">
                Contact email (optional)
              </label>
              <Input
                id="contact-email"
                value={contactEmail}
                error={!!contactEmailError}
                placeholder="owner@example.com"
                onChange={(event) => {
                  const value = event.target.value;
                  setContactEmail(value);
                  if (value && !/^\S+@\S+\.\S+$/.test(value)) {
                    setContactEmailError('Invalid email address');
                  } else {
                    setContactEmailError(null);
                  }
                }}
              />
              {contactEmailError && (
                <p className="mt-1 text-sm text-destructive">{contactEmailError}</p>
              )}
            </div>

            <div className="flex items-center justify-between border-t border-border pt-4">
              <h3 className="text-sm font-semibold text-foreground">Action Parameters</h3>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => {
                  setUseAdvancedMode(!useAdvancedMode);
                  if (!useAdvancedMode) {
                    // Switching to advanced mode - sync form values to JSON
                    const properties = parseInputSchema(selectedAction!);
                    const payload: Record<string, unknown> = {};
                    properties.forEach((prop) => {
                      const value = formValues[prop.name];
                      if (value !== undefined && value !== '') {
                        if (prop.type === 'number' || prop.type === 'integer') {
                          payload[prop.name] = Number(value);
                        } else if (prop.type === 'boolean') {
                          payload[prop.name] = value === 'true';
                        } else if (prop.type === 'array' || prop.type === 'object') {
                          try {
                            payload[prop.name] = JSON.parse(value);
                          } catch {
                            payload[prop.name] = value;
                          }
                        } else {
                          payload[prop.name] = value;
                        }
                      }
                    });
                    setRunPayload(JSON.stringify(payload, null, 2));
                  }
                }}
              >
                {useAdvancedMode ? 'Use Form Mode' : 'Use JSON Mode'}
              </Button>
            </div>

            {useAdvancedMode ? (
              <div className="grid gap-2">
                <label htmlFor="payload" className="text-sm font-medium text-foreground">
                  Payload (JSON)
                </label>
                <Textarea
                  id="payload"
                  spellCheck={false}
                  value={runPayload}
                  error={!!jsonPayloadError}
                  onChange={(event) => {
                    setRunPayload(event.target.value);
                    if (jsonPayloadError) {
                      setJsonPayloadError(null);
                    }
                  }}
                />
                <p className="text-xs text-muted-foreground">
                  The payload must be valid JSON matching the action input schema.
                </p>
                {jsonPayloadError && (
                  <p className="mt-2 text-sm text-destructive">{jsonPayloadError}</p>
                )}
              </div>
            ) : (
              <div className="space-y-4">
                {selectedAction && parseInputSchema(selectedAction).length > 0 ? (
                  parseInputSchema(selectedAction).map((param) => (
                    <div key={param.name} className="grid gap-2">
                      <label htmlFor={`param-${param.name}`} className="text-sm font-medium text-foreground">
                        {param.name}
                        {param.required && <span className="text-red-500 ml-1">*</span>}
                      </label>
                      {param.description && (
                        <p className="text-xs text-muted-foreground">{param.description}</p>
                      )}
                      {param.type === 'array' || param.type === 'object' ? (
                        <Textarea
                          id={`param-${param.name}`}
                          value={formValues[param.name] || ''}
                          placeholder={
                            param.type === 'array'
                              ? '["item1", "item2"]'
                              : '{"key": "value"}'
                          }
                          required={param.required}
                          onChange={(event) => {
                            setFormValues({
                              ...formValues,
                              [param.name]: event.target.value,
                            });
                          }}
                        />
                      ) : (
                        <Input
                          id={`param-${param.name}`}
                          type={
                            param.type === 'number' || param.type === 'integer'
                              ? 'number'
                              : 'text'
                          }
                          value={formValues[param.name] || ''}
                          placeholder={`Enter ${param.name}`}
                          required={param.required}
                          onChange={(event) => {
                            setFormValues({
                              ...formValues,
                              [param.name]: event.target.value,
                            });
                          }}
                        />
                      )}
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground">
                    This action does not require any parameters.
                  </p>
                )}
              </div>
            )}

            {runError && (
              <div className="mb-3">
                <ErrorBanner message={String(runError)} onDismiss={() => setRunError(null)} />
              </div>
            )}

            {isRunning && (
              <div className="rounded-md border border-border bg-muted/50 p-4">
                <Loading text="Running action…" />
              </div>
            )}
            {runResult && (
              <div className="rounded-md border border-border bg-muted/50 p-4">
                <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                  Run result
                </h3>
                <div className="mt-2 text-sm text-foreground">
                  <p>
                    Run ID: {runResult.runId}
                  </p>
                  <pre className="mt-3 max-h-64 overflow-auto rounded-md border border-border bg-card p-3 text-xs text-foreground">
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

      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Action</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{actionToDelete?.name}"? This cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDelete}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};
