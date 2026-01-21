import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
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
import { refreshRuns } from '@/shared/api-client';
import { useLocalStorage } from '@/shared/hooks/useLocalStorage';
import { Action, ActionPackage, Run, RunStatus, ServerConfig } from '@/shared/types';
import { formDataToPayload, propertiesToFormData } from '@/shared/utils/formData';
import { prettyPrint, downloadAsJson, copyToClipboard } from '@/shared/utils/helpers';
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

// Copy button component
const CopyButton = ({ 
  value, 
  label = 'Copy',
  size = 'sm',
  variant = 'ghost',
}: { 
  value: string; 
  label?: string;
  size?: 'sm' | 'default';
  variant?: 'ghost' | 'outline' | 'secondary';
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    const success = await copyToClipboard(value);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <Button
      type="button"
      variant={variant}
      size={size}
      onClick={handleCopy}
      className="gap-1.5"
    >
      {copied ? (
        <>
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          Copied!
        </>
      ) : (
        <>
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          {label}
        </>
      )}
    </Button>
  );
};

// Code block with copy button
const CodeBlock = ({ 
  value, 
  title,
  maxHeight = 'max-h-64',
  showCopy = true,
  showExport = false,
  exportFilename,
}: { 
  value: string; 
  title?: string;
  maxHeight?: string;
  showCopy?: boolean;
  showExport?: boolean;
  exportFilename?: string;
}) => {
  return (
    <div className="relative group">
      {title && (
        <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground mb-2">
          {title}
        </h3>
      )}
      <div className="relative">
        <pre className={cn(
          'overflow-auto rounded-md border border-border bg-muted/50 p-4 text-sm text-foreground font-mono',
          maxHeight,
        )}>
          {value}
        </pre>
        {(showCopy || showExport) && (
          <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-150">
            {showCopy && <CopyButton value={value} label="" size="sm" variant="secondary" />}
            {showExport && exportFilename && (
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => downloadAsJson(value, exportFilename)}
                className="gap-1"
              >
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

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
          Reload to ensure the UI is using the latest schema and resources.
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
  
  // Track if component has mounted to prevent re-animation on selection changes
  const hasMounted = useRef(false);
  useEffect(() => {
    hasMounted.current = true;
  }, []);

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
    return runs.slice(0, 5);
  }, [loadedRuns.data, selectedActionId]);

  // Auto-select first action on load
  useEffect(() => {
    if (!selectedActionId && actions.length > 0) {
      setSelectedActionId(actions[0].id);
    }
  }, [actions, selectedActionId]);

  const openRunDialog = useCallback(
    (action: Action) => {
      // Set the selected action first
      setSelectedActionId(action.id);
      
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
        try {
          parsedPayload = JSON.parse(runPayload || '{}');
          setJsonPayloadError(null);
        } catch (err) {
          setJsonPayloadError('Invalid JSON payload. Please fix any syntax issues and try again.');
          return;
        }
      } else {
        const properties = parseInputSchema(selectedAction);
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
        
        // Immediately refresh runs list so the new run appears without waiting for WebSocket
        refreshRuns().catch(() => {
          // Silently ignore - WebSocket will eventually update the list
        });
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
        Loading actions...
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
      <div className="h-full space-y-6 p-8 animate-fadeInUp motion-reduce:animate-none">
        <VersionMismatchBanner serverConfig={loadedServerConfig.data} />
        <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-muted/30 p-16 text-center min-h-[400px]">
          <div className="mb-6 rounded-full bg-primary/10 p-6">
            <ActionsIcon className="h-10 w-10 text-primary" />
          </div>
          <h2 className="text-xl font-semibold text-foreground">No actions available yet</h2>
          <p className="mt-3 max-w-md text-base text-muted-foreground">
            Install an action package or create one to start running automated workflows.
          </p>
          <Button className="mt-8" size="lg" onClick={() => navigate('/runs')}>
            Review run history
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full space-y-6 p-8 animate-fadeInUp motion-reduce:animate-none">
      <VersionMismatchBanner serverConfig={loadedServerConfig.data} />

      <div className="rounded-xl border border-border bg-card shadow-sm">
        <div className="flex flex-col gap-4 border-b border-border p-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1">
            <h1 className="text-2xl font-semibold text-card-foreground">Action Packages</h1>
            <p className="text-base text-muted-foreground">
              Click an action to run it, or select to view details.
            </p>
          </div>
          <div className="text-base text-muted-foreground whitespace-nowrap">
            {loadedActions.data?.length || 0} packages &bull; {actions.length} enabled actions
          </div>
        </div>

        <div className="grid gap-8 p-6 lg:grid-cols-[3fr,2fr]">
          {/* Actions Table - Left Side */}
          <div className="rounded-lg border border-border overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/50">
                  <TableHead className="text-sm">Action</TableHead>
                  <TableHead className="text-sm">Package</TableHead>
                  <TableHead className="text-sm">Location</TableHead>
                  <TableHead className="text-sm w-[100px]">Runs</TableHead>
                  <TableHead className="w-[80px]"></TableHead>
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
                        'cursor-pointer transition-colors duration-150 h-14',
                        'hover:bg-muted/50',
                        isSelected && 'bg-primary/10 hover:bg-primary/15 border-l-2 border-l-primary',
                        // Only animate on initial mount
                        !hasMounted.current && 'animate-fadeInUp motion-reduce:animate-none',
                      )}
                      style={!hasMounted.current ? getStaggerDelay(index) : undefined}
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
                      <TableCell className="font-medium text-card-foreground text-base">{action.name}</TableCell>
                      <TableCell>{renderPackageBadge(pkg)}</TableCell>
                      <TableCell className="text-sm text-muted-foreground font-mono">
                        {action.file}:{action.lineno}
                      </TableCell>
                      <TableCell>
                        <span className="inline-flex items-center justify-center rounded-md bg-muted px-2.5 py-1 text-sm text-muted-foreground font-medium min-w-[2.5rem]">
                          {runs.length}
                        </span>
                      </TableCell>
                      <TableCell>
                        {/* Inline Run Button - Modal First UX */}
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={(e) => {
                            e.stopPropagation();
                            openRunDialog(action);
                          }}
                          className="h-9 w-9 p-0"
                          title="Run action"
                        >
                          <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M6.3 2.841A1.5 1.5 0 004 4.11v11.78a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
                          </svg>
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>

          {/* Detail Panel - Right Side (Simplified: just info + recent runs + collapsible docs) */}
          <div className="space-y-5">
            {selectedAction && selectedPackage ? (
              <>
                {/* Action Info Card */}
                <div className="p-5 rounded-lg border border-border bg-gradient-to-br from-card to-muted/20 shadow-sm">
                  <div className="flex flex-wrap items-center gap-3 mb-3">
                    <h2 className="text-xl font-semibold text-card-foreground">
                      {selectedAction.name}
                    </h2>
                    {renderPackageBadge(selectedPackage)}
                  </div>
                  <p className="text-base text-muted-foreground leading-relaxed mb-5">
                    {selectedAction.docs
                      ? selectedAction.docs.split('\n')[0]
                      : 'No description available.'}
                  </p>
                  <div className="flex flex-wrap items-center gap-3">
                    <Button size="lg" onClick={() => openRunDialog(selectedAction)} disabled={!selectedAction.enabled}>
                      <svg className="h-5 w-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M6.3 2.841A1.5 1.5 0 004 4.11v11.78a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
                      </svg>
                      Run action
                    </Button>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm" className="h-10 w-10 p-0" aria-label="More options">
                          <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 16 16">
                            <circle cx="8" cy="2" r="1.5" />
                            <circle cx="8" cy="8" r="1.5" />
                            <circle cx="8" cy="14" r="1.5" />
                          </svg>
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => navigate(`/runs?search=${selectedAction.name}`)}>
                          View all runs
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem destructive onClick={() => openDeleteDialog(selectedAction)}>
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>

                {/* Recent Runs */}
                <div className="p-5 rounded-lg border border-border bg-card">
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground mb-4">
                    Recent runs
                  </h3>
                  {recentRuns.length === 0 ? (
                    <p className="text-base text-muted-foreground">No runs yet.</p>
                  ) : (
                    <ul className="space-y-2">
                      {recentRuns.map((run) => (
                        <li
                          key={run.id}
                          className="flex items-center justify-between px-4 py-3 rounded-md border border-border bg-muted/30 cursor-pointer hover:bg-muted/50 transition-colors duration-150"
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
                            <p className="text-base font-medium text-card-foreground">
                              {new Date(run.start_time).toLocaleString()}
                            </p>
                            <p className="text-sm text-muted-foreground font-mono">#{run.numbered_id}</p>
                          </div>
                          {renderStatusBadge(run.status)}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                {/* Documentation - Collapsible */}
                <details className="rounded-lg border border-border bg-card group">
                  <summary className="p-5 cursor-pointer hover:bg-muted/50 transition-colors duration-150 list-none flex items-center justify-between">
                    <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                      Documentation
                    </h3>
                    <svg className="h-5 w-5 text-muted-foreground transition-transform duration-150 group-open:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </summary>
                  <div className="p-5 pt-0 space-y-4 border-t border-border">
                    <CodeBlock
                      title="Description"
                      value={selectedAction.docs || 'No documentation available.'}
                      showCopy
                    />
                    <CodeBlock
                      title="Input Schema"
                      value={prettyPrint(selectedAction.input_schema)}
                      showCopy
                    />
                    <CodeBlock
                      title="Output Schema"
                      value={prettyPrint(selectedAction.output_schema)}
                      showCopy
                    />
                  </div>
                </details>
              </>
            ) : (
              <div className="flex h-full items-center justify-center rounded-md border border-dashed border-border bg-muted/50 p-12 text-sm text-muted-foreground min-h-[200px]">
                Select an action to view details
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Run Action Dialog - Modal First UX */}
      <Dialog open={isRunDialogOpen} onOpenChange={setRunDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {selectedAction ? `Run ${selectedAction.name}` : 'Run action'}
            </DialogTitle>
            <DialogDescription>
              Update the payload and submit to run the action. The result will display below when available.
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
                  if (!useAdvancedMode && selectedAction) {
                    const properties = parseInputSchema(selectedAction);
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
                        {param.required && <span className="text-destructive ml-1">*</span>}
                      </label>
                      {param.description && (
                        <p className="text-xs text-muted-foreground">{param.description}</p>
                      )}
                      {param.type === 'array' || param.type === 'object' ? (
                        <Textarea
                          id={`param-${param.name}`}
                          value={formValues[param.name] || ''}
                          placeholder={param.type === 'array' ? '["item1", "item2"]' : '{"key": "value"}'}
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
                          type={param.type === 'number' || param.type === 'integer' ? 'number' : 'text'}
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
                <Loading text="Running action..." />
              </div>
            )}

            {runResult && (
              <div className="rounded-md border border-border bg-muted/50 p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                    Run result
                  </h3>
                  <div className="flex items-center gap-2">
                    <CopyButton value={runResult.response} label="Copy" size="sm" variant="outline" />
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => downloadAsJson(runResult.response, `run-${runResult.runId}`)}
                      className="gap-1.5"
                    >
                      <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                      Export JSON
                    </Button>
                  </div>
                </div>
                <p className="text-xs text-muted-foreground font-mono">
                  Run ID: {runResult.runId}
                </p>
                <pre className="max-h-96 overflow-auto rounded-md border border-border bg-card p-3 text-xs text-foreground whitespace-pre-wrap break-words font-mono">
                  {runResult.response}
                </pre>
              </div>
            )}

            <DialogFooter>
              <Button type="button" variant="ghost" onClick={() => setRunDialogOpen(false)}>
                Close
              </Button>
              <Button type="submit" disabled={isRunning || !selectedAction}>
                {isRunning ? 'Running...' : 'Run action'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
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
