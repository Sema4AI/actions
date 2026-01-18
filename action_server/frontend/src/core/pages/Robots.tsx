import { useState, useCallback, useRef } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Loading } from '@/core/components/ui/Loading';
import { ErrorBanner } from '@/core/components/ui/ErrorBanner';
import { Button } from '@/core/components/ui/Button';
import { Badge } from '@/core/components/ui/Badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/core/components/ui/Dialog';
import { cn } from '@/shared/utils/cn';
import { useRobotCatalog } from '@/queries/robots';
import type { RobotPackageDetailAPI, RobotTaskInfoAPI } from '@/shared/types';

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
function RobotIcon({ className }: IconProps): JSX.Element {
  return (
    <SvgIcon className={className} size="24">
      <rect x="3" y="11" width="18" height="10" rx="2" />
      <circle cx="12" cy="5" r="2" />
      <path d="M12 7v4" />
      <circle cx="8" cy="16" r="1" fill="currentColor" />
      <circle cx="16" cy="16" r="1" fill="currentColor" />
    </SvgIcon>
  );
}

function FolderIcon({ className }: IconProps): JSX.Element {
  return (
    <SvgIcon className={className}>
      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
    </SvgIcon>
  );
}

function PlayIcon({ className }: IconProps): JSX.Element {
  return (
    <SvgIcon className={className}>
      <polygon points="5 3 19 12 5 21 5 3" />
    </SvgIcon>
  );
}

function TaskIcon({ className }: IconProps): JSX.Element {
  return (
    <SvgIcon className={className}>
      <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
      <rect x="8" y="2" width="8" height="4" rx="1" ry="1" />
    </SvgIcon>
  );
}

function PlusIcon({ className }: IconProps): JSX.Element {
  return (
    <SvgIcon className={className}>
      <line x1="12" y1="5" x2="12" y2="19" />
      <line x1="5" y1="12" x2="19" y2="12" />
    </SvgIcon>
  );
}

function UploadIcon({ className }: IconProps): JSX.Element {
  return (
    <SvgIcon className={className}>
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="17 8 12 3 7 8" />
      <line x1="12" y1="3" x2="12" y2="15" />
    </SvgIcon>
  );
}

function LinkIcon({ className }: IconProps): JSX.Element {
  return (
    <SvgIcon className={className}>
      <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
      <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
    </SvgIcon>
  );
}

function FileIcon({ className }: IconProps): JSX.Element {
  return (
    <SvgIcon className={className}>
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
    </SvgIcon>
  );
}

function XIcon({ className }: IconProps): JSX.Element {
  return (
    <SvgIcon className={className}>
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </SvgIcon>
  );
}

function CheckIcon({ className }: IconProps): JSX.Element {
  return (
    <SvgIcon className={className}>
      <polyline points="20 6 9 17 4 12" />
    </SvgIcon>
  );
}

// Robot Task Component
interface RobotTaskProps {
  task: RobotTaskInfoAPI;
  robotPath: string;
  onRun?: (taskName: string) => void;
}

function RobotTask({ task, robotPath, onRun }: RobotTaskProps): JSX.Element {
  return (
    <div className="flex items-center justify-between rounded-md border border-border/50 bg-muted/30 p-3">
      <div className="flex items-center gap-3">
        <div className="rounded-md bg-primary/10 p-1.5">
          <TaskIcon className="h-4 w-4 text-primary" />
        </div>
        <div>
          <div className="font-medium text-sm text-card-foreground">{task.name}</div>
          {task.docs && (
            <div className="text-xs text-muted-foreground line-clamp-1">{task.docs}</div>
          )}
        </div>
      </div>
      {onRun && (
        <Button
          variant="outline"
          size="sm"
          onClick={() => onRun(task.name)}
        >
          <PlayIcon className="h-3 w-3 mr-1" />
          Run
        </Button>
      )}
    </div>
  );
}

// Run Task Dialog Component
interface RunTaskDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  robotPath: string;
  taskName: string;
  robotName: string;
}

function RunTaskDialog({ open, onOpenChange, robotPath, taskName, robotName }: RunTaskDialogProps): JSX.Element {
  const [runId, setRunId] = useState<string | null>(null);
  const [status, setStatus] = useState<'idle' | 'starting' | 'running' | 'completed' | 'failed'>('idle');
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const runMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch('/api/robots/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          robot_package_path: robotPath,
          task_name: taskName,
          inputs: {},
          use_secrets: false,
        }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.message || 'Failed to start task');
      }

      return response.json();
    },
    onSuccess: (data) => {
      setRunId(data.run_id);
      setStatus('running');
      // Create new abort controller for this polling session
      abortControllerRef.current = new AbortController();
      pollRunStatus(data.run_id, abortControllerRef.current.signal);
    },
    onError: (err: Error) => {
      setStatus('failed');
      setError(err.message);
    },
  });

  // RunStatus values from backend: NOT_RUN=0, RUNNING=1, PASSED=2, FAILED=3, CANCELLED=4
  const RUN_STATUS = {
    NOT_RUN: 0,
    RUNNING: 1,
    PASSED: 2,
    FAILED: 3,
    CANCELLED: 4,
  };

  const pollRunStatus = async (id: string, abortSignal: AbortSignal) => {
    const maxAttempts = 120; // 2 minutes with 1s intervals
    let attempts = 0;

    const poll = async () => {
      // Check if polling was cancelled
      if (abortSignal.aborted) {
        return;
      }

      try {
        const response = await fetch(`/api/runs/${id}`);
        if (!response.ok) {
          throw new Error('Failed to fetch run status');
        }
        const run = await response.json();

        // Backend returns integer status values
        if (run.status === RUN_STATUS.PASSED) {
          setStatus('completed');
          setResult(run.result || 'Task completed successfully');
        } else if (run.status === RUN_STATUS.FAILED || run.status === RUN_STATUS.CANCELLED) {
          setStatus('failed');
          setError(run.error_message || 'Task failed');
        } else if (attempts < maxAttempts && !abortSignal.aborted) {
          attempts++;
          setTimeout(poll, 1000);
        } else if (!abortSignal.aborted) {
          setStatus('failed');
          setError('Task timed out');
        }
      } catch (err) {
        if (!abortSignal.aborted) {
          setStatus('failed');
          setError(err instanceof Error ? err.message : 'Unknown error');
        }
      }
    };

    poll();
  };

  const handleRun = () => {
    setStatus('starting');
    setError(null);
    setResult(null);
    runMutation.mutate();
  };

  const handleClose = () => {
    // Abort any ongoing polling
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setStatus('idle');
    setRunId(null);
    setResult(null);
    setError(null);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] w-[90vw]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <div className="rounded-md bg-primary/10 p-1.5">
              <PlayIcon className="h-4 w-4 text-primary" />
            </div>
            Run Task: {taskName}
          </DialogTitle>
          <DialogDescription>
            Execute task from {robotName}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Status Display */}
          {status === 'idle' && (
            <div className="rounded-lg border border-border bg-muted/30 p-4 text-center">
              <TaskIcon className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                Click "Run Task" to execute <strong>{taskName}</strong>
              </p>
            </div>
          )}

          {(status === 'starting' || status === 'running') && (
            <div className="rounded-lg border border-primary/30 bg-primary/5 p-4 text-center">
              <div className="animate-spin h-8 w-8 mx-auto mb-2 border-2 border-primary border-t-transparent rounded-full" />
              <p className="text-sm text-primary font-medium">
                {status === 'starting' ? 'Starting task...' : 'Task running...'}
              </p>
              {runId && (
                <p className="text-xs text-muted-foreground mt-1">Run ID: {runId}</p>
              )}
            </div>
          )}

          {status === 'completed' && (
            <div className="rounded-lg border border-success/30 bg-success/5 p-4">
              <div className="flex items-center gap-2 mb-2">
                <CheckIcon className="h-5 w-5 text-success flex-shrink-0" />
                <span className="font-medium text-success">Task Completed</span>
              </div>
              {result && (
                <pre className="text-xs bg-muted/50 rounded p-2 overflow-auto max-h-64 text-card-foreground whitespace-pre-wrap break-all font-mono">
                  {(() => {
                    try {
                      // Parse the JSON result
                      const parsed = typeof result === 'string' ? JSON.parse(result) : result;
                      // Extract output and strip ANSI escape codes
                      const output = parsed.output || parsed.result || JSON.stringify(parsed, null, 2);
                      // Strip ANSI escape codes (e.g., \u001b[96m)
                      return String(output).replace(/\u001b\[[0-9;]*m/g, '').trim();
                    } catch {
                      // If parsing fails, just strip ANSI codes from the raw string
                      return String(result).replace(/\u001b\[[0-9;]*m/g, '').trim();
                    }
                  })()}
                </pre>
              )}
            </div>
          )}

          {status === 'failed' && (
            <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4">
              <div className="flex items-center gap-2 mb-2">
                <XIcon className="h-5 w-5 text-destructive flex-shrink-0" />
                <span className="font-medium text-destructive">Task Failed</span>
              </div>
              {error && (
                <pre className="text-xs bg-muted/50 rounded p-2 overflow-auto max-h-64 text-destructive whitespace-pre-wrap break-all font-mono">
                  {String(error).replace(/\u001b\[[0-9;]*m/g, '').trim()}
                </pre>
              )}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose}>
            {status === 'completed' || status === 'failed' ? 'Close' : 'Cancel'}
          </Button>
          {(status === 'idle' || status === 'completed' || status === 'failed') && (
            <Button onClick={handleRun} disabled={runMutation.isPending}>
              <PlayIcon className="h-4 w-4 mr-1" />
              {status === 'idle' ? 'Run Task' : 'Run Again'}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Robot Package Card Component
interface RobotPackageCardProps {
  robot: RobotPackageDetailAPI;
}

function RobotPackageCard({ robot }: RobotPackageCardProps): JSX.Element {
  const [runDialogOpen, setRunDialogOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState<string | null>(null);

  const handleRunTask = (taskName: string) => {
    setSelectedTask(taskName);
    setRunDialogOpen(true);
  };

  return (
    <>
      <div className="rounded-lg border border-border bg-card shadow-sm transition-all duration-200 hover:shadow-md">
        {/* Header */}
        <div className="border-b border-border/50 p-4">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="rounded-full bg-primary/10 p-2">
                <RobotIcon className="h-5 w-5 text-primary" />
              </div>
              <div>
                <h3 className="font-semibold text-card-foreground">{robot.name}</h3>
                {robot.description && (
                  <p className="text-sm text-muted-foreground mt-0.5">{robot.description}</p>
                )}
              </div>
            </div>
            <Badge variant="outline">
              {robot.tasks?.length || 0} tasks
            </Badge>
          </div>
        </div>

        {/* Path */}
        <div className="border-b border-border/50 px-4 py-2 bg-muted/20">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <FolderIcon className="h-3 w-3" />
            <code className="font-mono truncate">{robot.path}</code>
          </div>
        </div>

        {/* Tasks */}
        <div className="p-4">
          {robot.tasks && robot.tasks.length > 0 ? (
            <div className="space-y-2">
              {robot.tasks.map((task) => (
                <RobotTask
                  key={task.name}
                  task={task}
                  robotPath={robot.path}
                  onRun={handleRunTask}
                />
              ))}
            </div>
          ) : (
            <div className="text-sm text-muted-foreground text-center py-4">
              No tasks defined
            </div>
          )}
        </div>
      </div>

      {selectedTask && (
        <RunTaskDialog
          open={runDialogOpen}
          onOpenChange={setRunDialogOpen}
          robotPath={robot.path}
          taskName={selectedTask}
          robotName={robot.name}
        />
      )}
    </>
  );
}

// Import Mode Type
type ImportMode = 'upload' | 'url';

// Import Robot Dialog Component
interface ImportRobotDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function ImportRobotDialog({ open, onOpenChange }: ImportRobotDialogProps): JSX.Element {
  const [mode, setMode] = useState<ImportMode>('upload');
  const [url, setUrl] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const importMutation = useMutation({
    mutationFn: async (data: { file?: File; url?: string }) => {
      const formData = new FormData();
      if (data.file) {
        formData.append('file', data.file);
      } else if (data.url) {
        formData.append('url', data.url);
      }

      const response = await fetch('/api/robots/import', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.message || 'Failed to import robot');
      }

      const result = await response.json();

      // API returns {success: false, message: "..."} for validation errors
      if (!result.success) {
        throw new Error(result.message || 'Import failed');
      }

      return result;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['robotCatalog'] });
      handleClose();
    },
    onError: (err: Error) => {
      setError(err.message);
    },
  });

  const handleClose = () => {
    setSelectedFile(null);
    setUrl('');
    setError(null);
    setMode('upload');
    onOpenChange(false);
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    setError(null);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      if (file.name.endsWith('.zip')) {
        setSelectedFile(file);
      } else {
        setError('Please upload a .zip file');
      }
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    const files = e.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (file.name.endsWith('.zip')) {
        setSelectedFile(file);
      } else {
        setError('Please upload a .zip file');
      }
    }
  };

  const handleImport = () => {
    setError(null);
    if (mode === 'upload' && selectedFile) {
      importMutation.mutate({ file: selectedFile });
    } else if (mode === 'url' && url.trim()) {
      importMutation.mutate({ url: url.trim() });
    }
  };

  const isValid = mode === 'upload' ? !!selectedFile : url.trim().length > 0;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[520px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <div className="rounded-md bg-primary/10 p-1.5">
              <PlusIcon className="h-4 w-4 text-primary" />
            </div>
            Import Robot Package
          </DialogTitle>
          <DialogDescription>
            Add a robot package by uploading a .zip file or importing from a URL.
          </DialogDescription>
        </DialogHeader>

        {/* Mode Tabs */}
        <div className="flex gap-1 p-1 bg-muted/50 rounded-lg">
          <button
            onClick={() => { setMode('upload'); setError(null); }}
            className={cn(
              'flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-md text-sm font-medium transition-all',
              mode === 'upload'
                ? 'bg-card text-card-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
            )}
          >
            <UploadIcon className="h-4 w-4" />
            Upload File
          </button>
          <button
            onClick={() => { setMode('url'); setError(null); }}
            className={cn(
              'flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-md text-sm font-medium transition-all',
              mode === 'url'
                ? 'bg-card text-card-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
            )}
          >
            <LinkIcon className="h-4 w-4" />
            From URL
          </button>
        </div>

        {/* Upload Mode */}
        {mode === 'upload' && (
          <div className="space-y-4">
            {/* Drop Zone */}
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={cn(
                'relative flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 cursor-pointer transition-all',
                isDragging
                  ? 'border-primary bg-primary/5 scale-[1.02]'
                  : 'border-border hover:border-primary/50 hover:bg-muted/30',
                selectedFile && 'border-success bg-success/5'
              )}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".zip"
                onChange={handleFileSelect}
                className="hidden"
              />

              {selectedFile ? (
                <>
                  <div className="rounded-full bg-success/10 p-3 mb-3">
                    <CheckIcon className="h-6 w-6 text-success" />
                  </div>
                  <div className="flex items-center gap-2 text-sm font-medium text-card-foreground">
                    <FileIcon className="h-4 w-4" />
                    {selectedFile.name}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedFile(null);
                    }}
                    className="absolute top-2 right-2 p-1 rounded-md hover:bg-muted/50 text-muted-foreground hover:text-foreground transition-colors"
                  >
                    <XIcon className="h-4 w-4" />
                  </button>
                </>
              ) : (
                <>
                  <div className={cn(
                    'rounded-full p-3 mb-3 transition-colors',
                    isDragging ? 'bg-primary/20' : 'bg-muted/50'
                  )}>
                    <UploadIcon className={cn(
                      'h-6 w-6 transition-colors',
                      isDragging ? 'text-primary' : 'text-muted-foreground'
                    )} />
                  </div>
                  <p className="text-sm font-medium text-card-foreground">
                    {isDragging ? 'Drop your file here' : 'Drag & drop your robot package'}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    or click to browse • .zip files only
                  </p>
                </>
              )}
            </div>
          </div>
        )}

        {/* URL Mode */}
        {mode === 'url' && (
          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-card-foreground">
                Repository or Package URL
              </label>
              <input
                type="url"
                value={url}
                onChange={(e) => { setUrl(e.target.value); setError(null); }}
                placeholder="https://github.com/org/robot-package or .zip URL"
                className={cn(
                  'w-full px-3 py-2.5 rounded-lg border bg-background text-sm',
                  'placeholder:text-muted-foreground',
                  'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:ring-offset-background',
                  'transition-all'
                )}
              />
              <p className="text-xs text-muted-foreground">
                Supports GitHub repositories or direct links to .zip packages
              </p>
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3">
            <p className="text-sm text-destructive">{error}</p>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={handleClose}>
            Cancel
          </Button>
          <Button
            onClick={handleImport}
            disabled={!isValid || importMutation.isPending}
          >
            {importMutation.isPending ? (
              <>
                <span className="animate-spin mr-2">⟳</span>
                Importing...
              </>
            ) : (
              <>
                <PlusIcon className="h-4 w-4 mr-1" />
                Import Robot
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Main Robots Page
export function RobotsPage(): JSX.Element {
  const { data, isLoading, error } = useRobotCatalog();
  const [importDialogOpen, setImportDialogOpen] = useState(false);

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loading text="Loading robots..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <ErrorBanner
          message={`Unable to load robots: ${error instanceof Error ? error.message : 'Unknown error'}`}
        />
      </div>
    );
  }

  if (!data || !data.robots || data.robots.length === 0) {
    return (
      <div className="h-full space-y-4 p-6 animate-fadeInUp">
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border bg-muted/30 p-12 text-center min-h-[400px]">
          <div className="mb-4 rounded-full bg-primary/10 p-4">
            <RobotIcon className="h-8 w-8 text-primary" />
          </div>
          <h2 className="text-lg font-semibold text-foreground">
            No robots found
          </h2>
          <p className="mt-2 max-w-sm text-sm text-muted-foreground">
            Import a robot package to get started with automation workflows.
          </p>
          <Button
            className="mt-6"
            onClick={() => setImportDialogOpen(true)}
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            Import Robot
          </Button>
        </div>

        <ImportRobotDialog
          open={importDialogOpen}
          onOpenChange={setImportDialogOpen}
        />
      </div>
    );
  }

  return (
    <div className="h-full space-y-6 p-6 animate-fadeInUp">
      {/* Header */}
      <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="rounded-full bg-primary/10 p-2">
              <RobotIcon className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h1 className="text-2xl font-semibold text-card-foreground">
                Robots
              </h1>
              <p className="text-sm text-muted-foreground">
                Manage and run robot automation packages
              </p>
            </div>
          </div>
          <Button onClick={() => setImportDialogOpen(true)}>
            <PlusIcon className="h-4 w-4 mr-2" />
            Import Robot
          </Button>
        </div>
      </div>

      {/* Robot Cards Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {data.robots.map((robot, index) => (
          <div
            key={robot.name + robot.path}
            className="animate-fadeInUp"
            style={{ animationDelay: `${index * 50}ms` }}
          >
            <RobotPackageCard robot={robot} />
          </div>
        ))}
      </div>

      <ImportRobotDialog
        open={importDialogOpen}
        onOpenChange={setImportDialogOpen}
      />
    </div>
  );
}

export default RobotsPage;
