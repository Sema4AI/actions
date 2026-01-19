import { useState, useMemo } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { Loading } from '@/core/components/ui/Loading';
import { ErrorBanner } from '@/core/components/ui/ErrorBanner';
import { Button } from '@/core/components/ui/Button';
import { Badge } from '@/core/components/ui/Badge';
import { Input } from '@/core/components/ui/Input';
import { Select, SelectItem } from '@/core/components/ui/Select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/core/components/ui/Dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/core/components/ui/Table';
import { cn } from '@/shared/utils/cn';
import {
  useWorkItems,
  useWorkItemStats,
  useCreateWorkItem,
  useDeleteWorkItem,
  downloadWorkItemFile,
  type WorkItemState,
  type WorkItemResponse,
} from '@/queries/workItems';

// Icon Props type
interface IconProps {
  className?: string;
}

// Base SVG Icon wrapper
function SvgIcon({
  className,
  size = '16',
  children,
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
function QueueIcon({ className }: IconProps): JSX.Element {
  return (
    <SvgIcon className={className} size="24">
      <line x1="8" x2="21" y1="6" y2="6" />
      <line x1="8" x2="21" y1="12" y2="12" />
      <line x1="8" x2="21" y1="18" y2="18" />
      <line x1="3" x2="3.01" y1="6" y2="6" />
      <line x1="3" x2="3.01" y1="12" y2="12" />
      <line x1="3" x2="3.01" y1="18" y2="18" />
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

function RefreshIcon({ className }: IconProps): JSX.Element {
  return (
    <SvgIcon className={className}>
      <path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8" />
      <path d="M21 3v5h-5" />
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

function PlayIcon({ className }: IconProps): JSX.Element {
  return (
    <SvgIcon className={className}>
      <polygon points="5 3 19 12 5 21 5 3" />
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

function XIcon({ className }: IconProps): JSX.Element {
  return (
    <SvgIcon className={className}>
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </SvgIcon>
  );
}

function FileAttachmentIcon({ className }: IconProps): JSX.Element {
  return (
    <SvgIcon className={className}>
      <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48" />
    </SvgIcon>
  );
}

function DownloadIcon({ className }: IconProps): JSX.Element {
  return (
    <SvgIcon className={className}>
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </SvgIcon>
  );
}

function CopyIcon({ className }: IconProps): JSX.Element {
  return (
    <SvgIcon className={className}>
      <rect width="14" height="14" x="8" y="8" rx="2" ry="2" />
      <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" />
    </SvgIcon>
  );
}

function MoreIcon({ className }: IconProps): JSX.Element {
  return (
    <SvgIcon className={className}>
      <circle cx="12" cy="12" r="1" fill="currentColor" />
      <circle cx="19" cy="12" r="1" fill="currentColor" />
      <circle cx="5" cy="12" r="1" fill="currentColor" />
    </SvgIcon>
  );
}

// State icon component
const StateIcon = ({ state }: { state: WorkItemState }) => {
  switch (state) {
    case 'PENDING':
      return <ClockIcon className="h-3 w-3" />;
    case 'IN_PROGRESS':
      return <PlayIcon className="h-3 w-3" />;
    case 'DONE':
      return <CheckIcon className="h-3 w-3" />;
    case 'FAILED':
      return <XIcon className="h-3 w-3" />;
  }
};

// Get badge variant for work item state
const getStateBadgeVariant = (state: WorkItemState) => {
  switch (state) {
    case 'PENDING':
      return 'warning';
    case 'IN_PROGRESS':
      return 'info';
    case 'DONE':
      return 'success';
    case 'FAILED':
      return 'error';
  }
};

// Stat Card Component
interface StatCardProps {
  label: string;
  value: number;
  percentage: string;
  state: WorkItemState;
}

function StatCard({ label, value, percentage, state }: StatCardProps): JSX.Element {
  const borderColorClass = {
    PENDING: 'border-l-warning',
    IN_PROGRESS: 'border-l-info',
    DONE: 'border-l-success',
    FAILED: 'border-l-destructive',
  }[state];

  return (
    <div
      className={cn(
        'rounded-lg border border-border bg-card p-4',
        'transition-all duration-200 hover:shadow-md hover:scale-[1.02]',
        'motion-reduce:hover:scale-100',
        'border-l-4',
        borderColorClass
      )}
    >
      <div className="flex items-center gap-2 mb-2">
        <StateIcon state={state} />
        <span className="text-xs text-muted-foreground uppercase tracking-wide">{label}</span>
      </div>
      <div className="text-3xl font-bold text-card-foreground">{value}</div>
      <div className="text-xs text-muted-foreground font-mono mt-1">{percentage}</div>
    </div>
  );
}

// Create Item Dialog Component
interface CreateItemDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  defaultQueueName?: string;
}

function CreateItemDialog({ open, onOpenChange, defaultQueueName }: CreateItemDialogProps): JSX.Element {
  const [queueName, setQueueName] = useState(defaultQueueName || '');
  const [payloadText, setPayloadText] = useState('{\n  \n}');
  const [validationError, setValidationError] = useState<string | null>(null);
  const createMutation = useCreateWorkItem();

  const handleClose = () => {
    setQueueName(defaultQueueName || '');
    setPayloadText('{\n  \n}');
    setValidationError(null);
    onOpenChange(false);
  };

  const validateAndCreate = () => {
    setValidationError(null);

    if (!queueName.trim()) {
      setValidationError('Queue name is required');
      return;
    }

    try {
      const payload = JSON.parse(payloadText);
      createMutation.mutate(
        { queue_name: queueName, payload },
        {
          onSuccess: () => {
            handleClose();
          },
          onError: (error) => {
            setValidationError(error.message);
          },
        }
      );
    } catch (e) {
      setValidationError('Invalid JSON: ' + (e as Error).message);
    }
  };

  const isValid = queueName.trim().length > 0 && payloadText.trim().length > 0;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] w-[90vw]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <div className="rounded-md bg-primary/10 p-1.5">
              <PlusIcon className="h-4 w-4 text-primary" />
            </div>
            Create Work Item
          </DialogTitle>
          <DialogDescription>
            Add a new work item to the queue with a JSON payload
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-card-foreground">Queue Name</label>
            <Input
              value={queueName}
              onChange={(e) => setQueueName(e.target.value)}
              placeholder="e.g., email-processing"
              readOnly={!!defaultQueueName}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-card-foreground">Payload (JSON)</label>
            <textarea
              value={payloadText}
              onChange={(e) => {
                setPayloadText(e.target.value);
                setValidationError(null);
              }}
              placeholder='{"key": "value"}'
              className={cn(
                'w-full px-3 py-2 rounded-lg border bg-background text-sm font-mono',
                'placeholder:text-muted-foreground min-h-[200px]',
                'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
                'focus:ring-offset-background transition-all resize-y'
              )}
            />
          </div>

          {validationError && (
            <div className="rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3">
              <p className="text-sm text-destructive">{validationError}</p>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose}>
            Cancel
          </Button>
          <Button onClick={validateAndCreate} disabled={!isValid || createMutation.isPending}>
            {createMutation.isPending ? (
              <>
                <span className="animate-spin mr-2">⟳</span>
                Creating...
              </>
            ) : (
              <>
                <PlusIcon className="h-4 w-4 mr-1" />
                Create
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Item Detail Dialog Component
interface ItemDetailDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  item: WorkItemResponse | null;
}

function ItemDetailDialog({ open, onOpenChange, item }: ItemDetailDialogProps): JSX.Element {
  const deleteMutation = useDeleteWorkItem();

  if (!item) return <></>;

  const handleDelete = () => {
    if (confirm('Are you sure you want to delete this work item?')) {
      deleteMutation.mutate(item.id, {
        onSuccess: () => {
          onOpenChange(false);
        },
      });
    }
  };

  const handleDownloadFile = async (fileName: string) => {
    try {
      await downloadWorkItemFile(item.id, fileName);
    } catch (error) {
      alert('Failed to download file: ' + (error as Error).message);
    }
  };

  const handleCopyPayload = () => {
    const payloadText = JSON.stringify(item.payload, null, 2);
    navigator.clipboard.writeText(payloadText);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[700px] w-[90vw] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <div className="rounded-md bg-primary/10 p-1.5">
              <QueueIcon className="h-4 w-4 text-primary" />
            </div>
            <span className="font-mono text-base">Work Item: {item.id.substring(0, 8)}</span>
            <Badge variant={getStateBadgeVariant(item.state)} className="gap-1.5">
              <StateIcon state={item.state} />
              {item.state}
            </Badge>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Metadata Section */}
          <div className="space-y-2">
            <div className="text-sm">
              <span className="text-muted-foreground">Queue:</span>{' '}
              <span className="font-medium text-card-foreground">{item.queue_name}</span>
            </div>
            <div className="text-sm">
              <span className="text-muted-foreground">Created:</span>{' '}
              <span className="text-card-foreground">{new Date(item.created_at).toLocaleString()}</span>
            </div>
            <div className="text-sm">
              <span className="text-muted-foreground">Updated:</span>{' '}
              <span className="text-card-foreground">{new Date(item.updated_at).toLocaleString()}</span>
            </div>
            {item.parent_id && (
              <div className="text-sm">
                <span className="text-muted-foreground">Parent:</span>{' '}
                <span className="font-mono text-xs text-primary">{item.parent_id}</span>
              </div>
            )}
          </div>

          {/* Payload Section */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-card-foreground">Payload</span>
              <Button variant="ghost" size="sm" onClick={handleCopyPayload}>
                <CopyIcon className="h-3 w-3 mr-1" />
                Copy
              </Button>
            </div>
            <pre className="p-3 rounded-md bg-muted/50 text-xs overflow-auto max-h-96 font-mono text-card-foreground border border-border">
              {JSON.stringify(item.payload, null, 2)}
            </pre>
          </div>

          {/* Error Section */}
          {item.state === 'FAILED' && (item.error_code || item.error_message) && (
            <div className="space-y-2">
              <span className="text-sm font-semibold text-card-foreground">Error Details</span>
              <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4">
                {item.error_code && (
                  <div className="text-sm mb-2">
                    <span className="font-medium text-destructive">Code:</span>{' '}
                    <span className="font-mono text-xs text-destructive">{item.error_code}</span>
                  </div>
                )}
                {item.error_message && (
                  <div className="text-sm">
                    <span className="font-medium text-destructive">Message:</span>
                    <pre className="mt-1 text-xs text-destructive whitespace-pre-wrap font-mono">
                      {item.error_message}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Files Section */}
          {item.files && item.files.length > 0 && (
            <div className="space-y-2">
              <span className="text-sm font-semibold text-card-foreground">Attachments</span>
              <div className="rounded-lg border border-border bg-muted/30 divide-y divide-border">
                {item.files.map((fileName) => (
                  <div key={fileName} className="flex items-center justify-between p-3">
                    <div className="flex items-center gap-2">
                      <FileAttachmentIcon className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm text-card-foreground font-mono">{fileName}</span>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDownloadFile(fileName)}
                    >
                      <DownloadIcon className="h-3 w-3 mr-1" />
                      Download
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="destructive" onClick={handleDelete} disabled={deleteMutation.isPending}>
            {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
          </Button>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Main WorkItems Page
export function WorkItemsPage(): JSX.Element {
  const [selectedQueue, setSelectedQueue] = useState<string>('all');
  const [stateFilter, setStateFilter] = useState<WorkItemState | 'all'>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedItem, setSelectedItem] = useState<WorkItemResponse | null>(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  const { data: itemsData, isLoading, error, refetch } = useWorkItems(
    selectedQueue !== 'all' ? selectedQueue : undefined,
    stateFilter,
    100
  );
  const { data: statsData } = useWorkItemStats(
    selectedQueue !== 'all' ? selectedQueue : undefined
  );

  // Extract unique queue names
  const queueNames = useMemo(() => {
    if (!itemsData?.items) return ['all'];
    const names = new Set(itemsData.items.map((item) => item.queue_name));
    return ['all', ...Array.from(names)];
  }, [itemsData]);

  // Filter items by search query
  const filteredItems = useMemo(() => {
    if (!itemsData?.items) return [];
    if (!searchQuery.trim()) return itemsData.items;

    const lowered = searchQuery.toLowerCase();
    return itemsData.items.filter(
      (item) =>
        item.id.toLowerCase().includes(lowered) ||
        JSON.stringify(item.payload).toLowerCase().includes(lowered)
    );
  }, [itemsData, searchQuery]);

  const handleRowClick = (item: WorkItemResponse) => {
    setSelectedItem(item);
    setDetailDialogOpen(true);
  };

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loading text="Loading work items..." />
      </div>
    );
  }

  if (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    const isNotInstalled = errorMessage.includes('not installed');

    if (isNotInstalled) {
      return (
        <div className="h-full space-y-4 p-6 animate-fadeInUp">
          <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border bg-muted/30 p-12 text-center min-h-[400px]">
            <div className="mb-4 rounded-full bg-warning/10 p-4">
              <QueueIcon className="h-8 w-8 text-warning" />
            </div>
            <h2 className="text-lg font-semibold text-foreground">Work Items Not Available</h2>
            <p className="mt-2 max-w-md text-sm text-muted-foreground">
              The <code className="px-1.5 py-0.5 rounded bg-muted font-mono text-xs">actions-work-items</code> package
              is not installed in your action package environment.
            </p>
            <p className="mt-4 max-w-md text-sm text-muted-foreground">
              Add it to your <code className="px-1.5 py-0.5 rounded bg-muted font-mono text-xs">package.yaml</code> dependencies:
            </p>
            <pre className="mt-3 p-4 rounded-lg bg-muted/50 border border-border font-mono text-xs text-left">
{`dependencies:
  conda-forge:
    - python=3.11
  pypi:
    - actions-work-items`}
            </pre>
          </div>
        </div>
      );
    }

    return (
      <div className="p-6">
        <ErrorBanner
          message={`Unable to load work items: ${errorMessage}`}
        />
      </div>
    );
  }

  // Empty state
  if (!itemsData?.items || itemsData.items.length === 0) {
    return (
      <div className="h-full space-y-4 p-6 animate-fadeInUp">
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border bg-muted/30 p-12 text-center min-h-[400px]">
          <div className="mb-4 rounded-full bg-primary/10 p-4">
            <QueueIcon className="h-8 w-8 text-primary" />
          </div>
          <h2 className="text-lg font-semibold text-foreground">No work items yet</h2>
          <p className="mt-2 max-w-sm text-sm text-muted-foreground">
            Start automating workflows by creating your first work item
          </p>
          <Button className="mt-6" onClick={() => setCreateDialogOpen(true)}>
            <PlusIcon className="h-4 w-4 mr-2" />
            Create First Item
          </Button>
        </div>

        <CreateItemDialog
          open={createDialogOpen}
          onOpenChange={setCreateDialogOpen}
          defaultQueueName={selectedQueue !== 'all' ? selectedQueue : undefined}
        />
      </div>
    );
  }

  return (
    <div className="h-full space-y-6 p-6 animate-fadeInUp">
      {/* Page Header */}
      <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="rounded-full bg-primary/10 p-2">
              <QueueIcon className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h1 className="text-2xl font-semibold text-card-foreground">Work Items</h1>
              <p className="text-sm text-muted-foreground">
                Queue-based automation work item management
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Select value={selectedQueue} onValueChange={setSelectedQueue} className="w-[180px]">
              {queueNames.map((name) => (
                <SelectItem key={name} value={name}>
                  {name === 'all' ? 'All Queues' : name}
                </SelectItem>
              ))}
            </Select>
            <Button onClick={() => setCreateDialogOpen(true)}>
              <PlusIcon className="h-4 w-4 mr-2" />
              Create Item
            </Button>
          </div>
        </div>

        {/* Stats Overview */}
        {statsData && (
          <div className="mt-4 text-xs text-muted-foreground">
            {selectedQueue === 'all' ? 'All Queues' : statsData.queue_name}: {statsData.total}{' '}
            items ({statsData.pending} pending, {statsData.in_progress} active,{' '}
            {statsData.done} done, {statsData.failed} failed)
          </div>
        )}
      </div>

      {/* Stats Bar */}
      {statsData && (
        <div className="grid gap-4 grid-cols-2 sm:grid-cols-4">
          <StatCard
            label="PENDING"
            value={statsData.pending}
            percentage={`${((statsData.pending / statsData.total) * 100).toFixed(1)}%`}
            state="PENDING"
          />
          <StatCard
            label="IN PROGRESS"
            value={statsData.in_progress}
            percentage={`${((statsData.in_progress / statsData.total) * 100).toFixed(1)}%`}
            state="IN_PROGRESS"
          />
          <StatCard
            label="DONE"
            value={statsData.done}
            percentage={`${((statsData.done / statsData.total) * 100).toFixed(1)}%`}
            state="DONE"
          />
          <StatCard
            label="FAILED"
            value={statsData.failed}
            percentage={`${((statsData.failed / statsData.total) * 100).toFixed(1)}%`}
            state="FAILED"
          />
        </div>
      )}

      {/* Items Table */}
      <div className="rounded-lg border border-border bg-card shadow-sm">
        <div className="flex flex-col gap-4 border-b border-border p-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex gap-2">
            <Select
              value={stateFilter}
              onValueChange={(value) => setStateFilter(value as WorkItemState | 'all')}
              className="w-[150px]"
            >
              <SelectItem value="all">All States</SelectItem>
              <SelectItem value="PENDING">Pending</SelectItem>
              <SelectItem value="IN_PROGRESS">In Progress</SelectItem>
              <SelectItem value="DONE">Done</SelectItem>
              <SelectItem value="FAILED">Failed</SelectItem>
            </Select>
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by ID or payload..."
              className="w-[250px]"
            />
          </div>
          <Button variant="ghost" size="sm" onClick={() => refetch()}>
            <RefreshIcon className="h-4 w-4 mr-1" />
            Refresh
          </Button>
        </div>

        <div className="p-4">
          <div className="rounded-md border border-border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[140px]">ID</TableHead>
                  <TableHead>State</TableHead>
                  <TableHead className="hidden sm:table-cell">Payload Preview</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="w-20"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredItems.map((item, index) => (
                  <TableRow
                    key={item.id}
                    className={cn(
                      'cursor-pointer hover:bg-muted/50 transition-all duration-200',
                      'animate-fadeInUp motion-reduce:animate-none'
                    )}
                    style={{ animationDelay: `${index * 30}ms` }}
                    onClick={() => handleRowClick(item)}
                  >
                    <TableCell className="font-mono text-xs text-foreground">
                      {item.id.substring(0, 12)}...
                    </TableCell>
                    <TableCell>
                      <Badge variant={getStateBadgeVariant(item.state)} className="gap-1.5">
                        <StateIcon state={item.state} />
                        {item.state}
                      </Badge>
                    </TableCell>
                    <TableCell className="hidden sm:table-cell">
                      <span className="text-xs text-muted-foreground font-mono truncate max-w-[300px] block">
                        {JSON.stringify(item.payload).substring(0, 80)}
                        {JSON.stringify(item.payload).length > 80 ? '...' : ''}
                      </span>
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      <time
                        dateTime={item.created_at}
                        title={new Date(item.created_at).toLocaleString()}
                      >
                        {formatDistanceToNow(new Date(item.created_at), { addSuffix: true })}
                      </time>
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRowClick(item);
                        }}
                        aria-label="View details"
                      >
                        <MoreIcon className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      </div>

      {/* Dialogs */}
      <CreateItemDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        defaultQueueName={selectedQueue !== 'all' ? selectedQueue : undefined}
      />
      <ItemDetailDialog
        open={detailDialogOpen}
        onOpenChange={setDetailDialogOpen}
        item={selectedItem}
      />
    </div>
  );
}

export default WorkItemsPage;
