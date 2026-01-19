# Work Items Management Page - Design Specification

## Overview
The Work Items page provides queue-based work item management for automation workflows. Users can view queue statistics, browse items by state, inspect details including payloads and errors, and create new work items.

## Component Hierarchy

```
WorkItemsPage
├── PageHeader (Card)
│   ├── TitleSection
│   │   ├── QueueIcon
│   │   ├── Title + Description
│   │   └── QueueStatsOverview (inline summary)
│   └── ActionSection
│       ├── QueueSelector (Select dropdown)
│       └── CreateItemButton (Button)
│
├── StatsBar (Card with grid)
│   ├── StatCard (PENDING)
│   ├── StatCard (IN_PROGRESS)
│   ├── StatCard (DONE)
│   └── StatCard (FAILED)
│
├── ItemsTable (Card with Table)
│   ├── TableHeader
│   │   ├── FilterControls
│   │   │   ├── StateFilter (Select)
│   │   │   ├── SearchInput (Input)
│   │   │   └── RefreshButton (Button)
│   │   └── ColumnHeaders
│   │       ├── ID
│   │       ├── State
│   │       ├── Payload Preview
│   │       ├── Created
│   │       └── Actions
│   └── TableBody
│       └── WorkItemRow[] (clickable)
│           ├── ID (monospace)
│           ├── StateBadge (Badge)
│           ├── PayloadPreview (truncated JSON)
│           ├── RelativeTime (with tooltip)
│           └── ActionsMenu (DropdownMenu)
│
├── ItemDetailPanel (Dialog)
│   ├── DialogHeader
│   │   ├── ItemIcon + ID
│   │   ├── StateBadge
│   │   └── CloseButton
│   ├── DialogContent
│   │   ├── MetadataSection
│   │   │   ├── Queue Name
│   │   │   ├── Created/Updated Timestamps
│   │   │   └── Parent Link (if exists)
│   │   ├── PayloadSection
│   │   │   ├── Label: "Payload"
│   │   │   └── JSONViewer (formatted, copyable)
│   │   ├── ErrorSection (conditional: state === FAILED)
│   │   │   ├── Label: "Error Details"
│   │   │   ├── ErrorCode
│   │   │   └── ErrorMessage
│   │   └── FilesSection (conditional: files.length > 0)
│   │       ├── Label: "Attachments"
│   │       └── FileList[] (name + download link)
│   └── DialogFooter
│       ├── DeleteButton (destructive)
│       └── CloseButton
│
└── CreateItemDialog (Dialog)
    ├── DialogHeader
    │   ├── PlusIcon + "Create Work Item"
    │   └── Description
    ├── DialogContent
    │   ├── QueueInput (Input - read-only if queue selected)
    │   ├── PayloadEditor (Textarea with JSON validation)
    │   └── ValidationMessage (conditional)
    └── DialogFooter
        ├── CancelButton
        └── CreateButton (disabled until valid)
```

## Layout Wireframe

```
┌─────────────────────────────────────────────────────────────────────┐
│ ╔═══════════════════════════════════════════════════════════════╗   │
│ ║  🗂️  Work Items                                 [Queue: All ▾] ║   │
│ ║     Queue-based automation work item management    [+ Create] ║   │
│ ║                                                                ║   │
│ ║  📊 All Queues: 24 items (8 pending, 2 active, 12 done, 2 failed)║
│ ╚═══════════════════════════════════════════════════════════════╝   │
│                                                                       │
│ ┌───────────┬───────────┬───────────┬───────────┐                   │
│ │ ⏳ PENDING│ ▶️ ACTIVE │ ✓ DONE   │ ✗ FAILED │                   │
│ │     8     │     2     │    12     │     2     │                   │
│ │  (33.3%)  │  (8.3%)   │  (50.0%)  │  (8.3%)   │                   │
│ └───────────┴───────────┴───────────┴───────────┘                   │
│                                                                       │
│ ╔═══════════════════════════════════════════════════════════════╗   │
│ ║ [State: All ▾]  [🔍 Search by ID or payload...]  [↻ Refresh] ║   │
│ ╟─────────┬──────────┬────────────────────┬──────────┬─────────╢   │
│ ║ ID      │ State    │ Payload Preview    │ Created  │ Actions ║   │
│ ╟─────────┼──────────┼────────────────────┼──────────┼─────────╢   │
│ ║ wi-0023 │ PENDING  │ {"user": "john"... │ 2m ago   │ [⋮]    ║   │
│ ║ wi-0022 │ ACTIVE   │ {"task": "proce... │ 5m ago   │ [⋮]    ║   │
│ ║ wi-0021 │ DONE     │ {"result": true... │ 10m ago  │ [⋮]    ║   │
│ ║ wi-0020 │ FAILED   │ {"order_id": 12... │ 15m ago  │ [⋮]    ║   │
│ ║ ...     │ ...      │ ...                │ ...      │ [⋮]    ║   │
│ ╚═════════╧══════════╧════════════════════╧══════════╧═════════╝   │
│                                                                       │
│ [Pagination: ← 1 2 3 4 5 →]                        Showing 1-10 of 24│
└───────────────────────────────────────────────────────────────────────┘

CLICK ITEM → DETAIL PANEL OPENS:

┌─────────────────────────────────────────────┐
│ 📄 Work Item: wi-0020        [FAILED]   [×] │
├─────────────────────────────────────────────┤
│                                             │
│ Queue: email-processing                     │
│ Created: 2026-01-18 14:23:15               │
│ Updated: 2026-01-18 14:23:47               │
│ Parent: wi-0015 (view)                     │
│                                             │
│ ┌─ Payload ─────────────────────────────┐  │
│ │ {                                      │  │
│ │   "order_id": 12345,                   │  │
│ │   "email": "customer@example.com",     │  │
│ │   "action": "send_confirmation"        │  │
│ │ }                                      │  │
│ │                          [📋 Copy]    │  │
│ └────────────────────────────────────────┘  │
│                                             │
│ ┌─ Error Details ───────────────────────┐  │
│ │ Code: SMTP_CONNECTION_FAILED           │  │
│ │                                        │  │
│ │ Message: Unable to connect to SMTP     │  │
│ │ server at smtp.example.com:587.        │  │
│ │ Connection timeout after 30s.          │  │
│ └────────────────────────────────────────┘  │
│                                             │
│ ┌─ Attachments ─────────────────────────┐  │
│ │ 📎 order_data.json        [↓ Download] │  │
│ │ 📎 template.html          [↓ Download] │  │
│ └────────────────────────────────────────┘  │
│                                             │
├─────────────────────────────────────────────┤
│                    [🗑️ Delete]    [Close]  │
└─────────────────────────────────────────────┘
```

## State Management Approach

### Data Fetching Strategy
```typescript
// React Query for server state management
const { data: queues } = useQuery(['workItemQueues'], fetchQueues);
const { data: stats } = useQuery(['workItemStats', selectedQueue],
  () => fetchQueueStats(selectedQueue));
const { data: items, refetch } = useQuery(
  ['workItems', selectedQueue, stateFilter, page],
  () => fetchWorkItems({
    queue: selectedQueue,
    state: stateFilter,
    page,
    limit: 25
  }),
  { refetchInterval: 5000 } // Auto-refresh every 5s
);
```

### Local UI State
```typescript
// Component state
const [selectedQueue, setSelectedQueue] = useState<string>('all');
const [stateFilter, setStateFilter] = useState<WorkItemState | 'all'>('all');
const [searchQuery, setSearchQuery] = useState<string>('');
const [selectedItem, setSelectedItem] = useState<WorkItem | null>(null);
const [detailDialogOpen, setDetailDialogOpen] = useState(false);
const [createDialogOpen, setCreateDialogOpen] = useState(false);
const [page, setPage] = useState(1);
```

### Mutations
```typescript
const createMutation = useMutation({
  mutationFn: createWorkItem,
  onSuccess: () => {
    queryClient.invalidateQueries(['workItems']);
    queryClient.invalidateQueries(['workItemStats']);
    setCreateDialogOpen(false);
  }
});

const deleteMutation = useMutation({
  mutationFn: deleteWorkItem,
  onSuccess: () => {
    queryClient.invalidateQueries(['workItems']);
    queryClient.invalidateQueries(['workItemStats']);
    setDetailDialogOpen(false);
  }
});
```

## Interaction Patterns

### 1. Queue Selection
- **Trigger**: User clicks queue selector dropdown
- **Behavior**:
  - Dropdown opens showing "All Queues" + list of unique queue names
  - Selection updates `selectedQueue` state
  - Triggers refetch of stats and items
  - Updates URL with `?queue=<name>` for shareable links

### 2. State Filtering
- **Trigger**: User selects state filter
- **Behavior**:
  - Filter applied client-side if items < 100, server-side otherwise
  - Badge colors update table scan-ability
  - Persists in URL: `?queue=<name>&state=<state>`

### 3. Search
- **Trigger**: User types in search input (debounced 300ms)
- **Behavior**:
  - Searches: ID (exact match prefix), payload JSON (substring)
  - Visual feedback: matching terms highlighted (optional enhancement)
  - Clear button appears when search active

### 4. Item Row Click
- **Trigger**: User clicks any table row
- **Behavior**:
  - Row highlights with scale-up animation
  - Detail dialog slides in from right
  - Focus trapped in dialog (accessibility)
  - ESC key closes dialog

### 5. Item Actions Menu
- **Trigger**: User clicks 3-dot menu in row
- **Behavior**:
  - Menu appears aligned to button
  - Options:
    - "View Details" - Opens detail dialog
    - "Copy ID" - Copies ID to clipboard with toast
    - "Delete" - Shows confirmation then deletes
  - Prevents row click propagation

### 6. Create Item
- **Trigger**: User clicks "+ Create Item" button
- **Behavior**:
  - Modal dialog opens
  - Queue pre-filled if filtered by queue
  - JSON editor with syntax validation
  - Real-time validation feedback
  - Submit disabled until valid
  - Success: Toast notification + table refresh

### 7. Auto-refresh
- **Behavior**:
  - Items table refreshes every 5 seconds
  - Stats update on each refresh
  - Non-disruptive: maintains scroll position
  - Pauses when detail dialog open
  - Visual indicator: subtle pulse on refresh button

### 8. Error Handling
- Network errors: Red banner at top with retry button
- Validation errors: Inline red text below input
- Delete confirmation: "Are you sure?" dialog
- Empty states: Friendly illustration + CTA

## Color & Styling Specifications

### State Colors (from Badge component)
```typescript
const STATE_VARIANTS: Record<WorkItemState, BadgeVariant> = {
  PENDING: 'warning',    // Yellow/amber - bg-warning/10 text-warning
  IN_PROGRESS: 'info',   // Blue/cyan - bg-info/10 text-info
  DONE: 'success',       // Green - bg-success/10 text-success
  FAILED: 'error'        // Red - bg-destructive/10 text-destructive
};
```

### Stat Cards
```css
/* Stat Card Layout */
.stat-card {
  @apply rounded-lg border border-border bg-card p-4;
  @apply transition-all duration-200 hover:shadow-md hover:scale-[1.02];
  @apply motion-reduce:hover:scale-100;
}

/* State-specific accents */
.stat-card.pending {
  @apply border-l-4 border-l-warning;
}
.stat-card.in-progress {
  @apply border-l-4 border-l-info;
}
.stat-card.done {
  @apply border-l-4 border-l-success;
}
.stat-card.failed {
  @apply border-l-4 border-l-destructive;
}

/* Stat content */
.stat-value {
  @apply text-3xl font-bold text-card-foreground;
}
.stat-label {
  @apply text-sm text-muted-foreground uppercase tracking-wide;
}
.stat-percentage {
  @apply text-xs text-muted-foreground font-mono;
}
```

### Icons
```typescript
// Use inline SVG icons matching existing pattern (see Robots.tsx)
const QueueIcon = () => (
  <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="8" x2="21" y1="6" y2="6" />
    <line x1="8" x2="21" y1="12" y2="12" />
    <line x1="8" x2="21" y1="18" y2="18" />
    <line x1="3" x2="3.01" y1="6" y2="6" />
    <line x1="3" x2="3.01" y1="12" y2="12" />
    <line x1="3" x2="3.01" y1="18" y2="18" />
  </svg>
);

const FileAttachmentIcon = () => (
  <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48" />
  </svg>
);
```

### Typography
- **Page Title**: `text-2xl font-semibold text-card-foreground`
- **Section Headers**: `text-lg font-semibold text-card-foreground`
- **Body Text**: `text-sm text-card-foreground`
- **Muted Text**: `text-sm text-muted-foreground`
- **Monospace** (IDs, JSON): `font-mono text-sm`
- **Timestamps**: `text-xs text-muted-foreground`

### Spacing & Layout
- **Page Padding**: `p-6`
- **Card Padding**: `p-6`
- **Section Gap**: `space-y-6`
- **Grid Gap**: `gap-4` (stats), `gap-6` (main layout)
- **Border Radius**: `rounded-lg` (cards), `rounded-md` (inputs/buttons)

### Animations
```css
/* Match existing patterns from RunHistory */
.animate-fadeInUp {
  animation: fadeInUp 0.3s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Stagger animations for table rows */
tr.animate-fadeInUp {
  animation-delay: calc(var(--row-index) * 30ms);
}
```

## Accessibility Considerations

### Keyboard Navigation
- **Tab Order**: Header actions → Filters → Table rows → Pagination
- **Table Navigation**: Arrow keys move between cells (optional enhancement)
- **Dialog Focus**: Auto-focus first input, trap focus within dialog
- **ESC Key**: Closes dialogs and menus
- **Enter Key**:
  - On row: Opens detail dialog
  - In search: Applies filter
  - In create form: Submits (if valid)

### Screen Reader Support
```tsx
// ARIA labels and roles
<button aria-label="Create new work item">
  <PlusIcon aria-hidden="true" />
  <span>Create</span>
</button>

<Table role="table" aria-label="Work items table">
  <TableRow
    role="row"
    aria-label={`Work item ${item.id}, state ${item.state}`}
    onClick={handleRowClick}
  >
    ...
  </TableRow>
</Table>

<Badge
  variant={stateVariant}
  aria-label={`Status: ${item.state}`}
>
  {item.state}
</Badge>

// Live regions for updates
<div aria-live="polite" aria-atomic="true" className="sr-only">
  {itemsUpdatedAnnouncement}
</div>
```

### Visual Accessibility
- **Color Contrast**: All text meets WCAG AA (4.5:1 minimum)
- **Color Independence**: State conveyed by icon + text, not just color
- **Focus Indicators**: Visible 2px ring on all interactive elements
- **Motion Reduction**: `motion-reduce:transition-none` on all animations
- **Text Sizing**: Respects user font-size preferences (rem-based)

### Status Indicators
```tsx
// Multi-modal status communication
<Badge variant={stateVariant}>
  <StateIcon aria-hidden="true" />
  <span>{item.state}</span>
</Badge>

// State icons
const StateIcon = ({ state }: { state: WorkItemState }) => {
  switch (state) {
    case 'PENDING': return <ClockIcon />;
    case 'IN_PROGRESS': return <PlayIcon />;
    case 'DONE': return <CheckIcon />;
    case 'FAILED': return <XIcon />;
  }
};
```

### Error States
- **Form Validation**: `aria-invalid` and `aria-describedby` link errors
- **Error Banners**: `role="alert"` for immediate announcement
- **Retry Actions**: Clearly labeled and keyboard accessible

## Progressive Enhancement

### Loading States
```tsx
// Skeleton placeholders
{isLoading && <TableSkeleton rows={10} />}

// Optimistic updates
const handleDelete = (item: WorkItem) => {
  // Optimistically remove from UI
  queryClient.setQueryData(['workItems'], (old) =>
    old?.filter(i => i.id !== item.id)
  );
  // Execute deletion
  deleteMutation.mutate(item.id, {
    onError: () => {
      // Rollback on error
      queryClient.invalidateQueries(['workItems']);
    }
  });
};
```

### Empty States
```tsx
// No items in queue
<div className="text-center p-12">
  <QueueIcon className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
  <h3 className="text-lg font-semibold">No items in this queue</h3>
  <p className="text-sm text-muted-foreground mt-2">
    Work items will appear here once created
  </p>
  <Button className="mt-4" onClick={() => setCreateDialogOpen(true)}>
    Create First Item
  </Button>
</div>

// No queues at all
<div className="text-center p-12">
  <QueueIcon className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
  <h3 className="text-lg font-semibold">No work items yet</h3>
  <p className="text-sm text-muted-foreground mt-2">
    Start automating workflows by creating your first work item
  </p>
</div>
```

### Responsive Design
```css
/* Mobile-first approach */
/* Base (mobile): Stack stats vertically, hide less critical columns */
.stats-grid {
  @apply grid grid-cols-2 gap-3;
}

.table-cell-payload {
  @apply hidden sm:table-cell;
}

/* Tablet (640px+): 4-column stats, show payload preview */
@media (min-width: 640px) {
  .stats-grid {
    @apply grid-cols-4;
  }
}

/* Desktop (1024px+): Wider detail panel */
.detail-dialog {
  @apply w-[90vw] sm:max-w-[600px] lg:max-w-[800px];
}
```

## Performance Considerations

### Virtualization
- For queues with > 100 items, implement virtual scrolling
- Use `react-virtual` or `@tanstack/react-virtual`
- Render only visible rows + buffer

### Pagination
- Default: 25 items per page
- Options: 10, 25, 50, 100
- Server-side pagination for large datasets
- URL state: `?page=2&limit=25`

### Debouncing
- Search input: 300ms debounce
- Auto-refresh: 5s interval, paused when user active
- Filter changes: Immediate (< 100ms perceived)

### Memoization
```typescript
const filteredItems = useMemo(() => {
  if (!items) return [];
  return items.filter(item =>
    matchesStateFilter(item) && matchesSearch(item)
  );
}, [items, stateFilter, searchQuery]);

const queueOptions = useMemo(() =>
  ['all', ...Array.from(new Set(items?.map(i => i.queue_name) || []))],
  [items]
);
```

## Implementation Notes

### JSON Payload Display
```tsx
// Syntax-highlighted JSON (optional library: react-json-view)
<pre className="p-3 rounded-md bg-muted/50 text-xs overflow-auto max-h-96 font-mono">
  {JSON.stringify(item.payload, null, 2)}
</pre>

// Or custom syntax highlighting
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
<SyntaxHighlighter language="json" style={vscDarkPlus}>
  {JSON.stringify(item.payload, null, 2)}
</SyntaxHighlighter>
```

### File Downloads
```typescript
const handleDownloadFile = async (itemId: string, fileName: string) => {
  const response = await fetch(
    `/api/work-items/${itemId}/files/${fileName}`
  );
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = fileName;
  a.click();
  URL.revokeObjectURL(url);
};
```

### Relative Time Display
```typescript
import { formatDistanceToNow } from 'date-fns';

const RelativeTime = ({ timestamp }: { timestamp: string }) => (
  <time
    dateTime={timestamp}
    title={new Date(timestamp).toLocaleString()}
    className="text-xs text-muted-foreground"
  >
    {formatDistanceToNow(new Date(timestamp), { addSuffix: true })}
  </time>
);
```

## Consistency Checklist

- [ ] Uses existing `Button` component with variants
- [ ] Uses existing `Badge` component with state colors
- [ ] Uses existing `Table` components
- [ ] Uses existing `Dialog` for modals
- [ ] Uses existing `Select` for dropdowns
- [ ] Uses existing `Input` for text fields
- [ ] Matches `Robots.tsx` page header pattern
- [ ] Matches `RunHistory.tsx` table layout pattern
- [ ] Uses `cn()` utility for className composition
- [ ] Includes `Loading` component for pending states
- [ ] Includes `ErrorBanner` for error states
- [ ] Follows animation patterns (fadeInUp, stagger delays)
- [ ] Uses design tokens (colors, spacing, typography)
- [ ] Implements motion-reduce alternatives
- [ ] Includes ARIA labels and roles
- [ ] Uses inline SVG icons (not icon library)

## Future Enhancements

### Phase 2 Features
1. **Bulk Actions**: Select multiple items, batch delete/retry
2. **Advanced Filters**: Date range, custom payload queries
3. **Export**: Download items as CSV/JSON
4. **Real-time Updates**: WebSocket for live state changes
5. **Item History**: View state transitions timeline
6. **Retry Failed Items**: One-click retry with same payload
7. **Edit Payload**: Modify pending items before processing
8. **Queue Configuration**: Manage queue settings (retention, limits)

### Analytics Dashboard (Phase 3)
- Queue throughput charts
- Success/failure rate trends
- Average processing time
- Queue health alerts

---

## Design Rationale

### Why This Approach?

1. **Familiarity**: Matches existing Robots and RunHistory patterns so users instantly understand navigation
2. **Scannability**: Color-coded badges and stat cards enable at-a-glance queue health assessment
3. **Efficiency**: Most common actions (view, create) require minimal clicks
4. **Safety**: Destructive actions (delete) require confirmation
5. **Accessibility**: Built from the ground up with keyboard and screen reader users in mind
6. **Performance**: Pagination, memoization, and debouncing keep UI responsive even with large datasets
7. **Maintainability**: Uses existing component library, consistent patterns, and TypeScript for type safety

### Key Design Decisions

- **Modal vs Sidebar for Details**: Modal chosen for focus and simplicity (matches existing RunTaskDialog pattern)
- **Auto-refresh**: 5-second interval balances freshness with performance (matches typical queue monitoring needs)
- **Stat Cards vs Single Summary**: Cards provide better scannability and allow for future click-through filtering
- **Inline Payload Preview**: Helps users identify items without opening details; full view available in modal
- **Queue Selector in Header**: Top-level filtering for most common use case (viewing single queue)

This design delivers a production-ready work item management interface that feels native to the Action Server while optimizing for the specific needs of queue-based automation workflows.
