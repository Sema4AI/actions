# Quickstart: Using Enhanced Community UI Components

**Feature**: Community UI Enhancement Implementation  
**Audience**: Frontend developers working in `action_server/frontend`  
**Date**: 2025-10-12

## Overview

This guide demonstrates how to use the enhanced community tier UI components in your pages and forms. All components follow the shadcn/ui pattern: they're copy-pasted into `src/core/components/ui/` and fully customizable via Tailwind classes.

---

## Getting Started

### Import Components

```typescript
// Enhanced components
import { Input } from '@/core/components/ui/Input';
import { Textarea } from '@/core/components/ui/Textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/core/components/ui/Dialog';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/core/components/ui/Table';
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator } from '@/core/components/ui/DropdownMenu';

// New components
import { Badge } from '@/core/components/ui/Badge';
import { Loading } from '@/core/components/ui/Loading';
import { ErrorBanner } from '@/core/components/ui/ErrorBanner';

// Already styled
import { Button } from '@/core/components/ui/Button';
```

---

## Component Examples

### 1. Input & Textarea

**Basic Usage**:
```tsx
import { Input } from '@/core/components/ui/Input';

function ActionForm() {
  const [name, setName] = useState('');
  
  return (
    <div className="space-y-4">
      <div>
        <label htmlFor="action-name" className="block text-sm font-medium text-gray-700 mb-1">
          Action Name
        </label>
        <Input 
          id="action-name"
          type="text"
          placeholder="Enter action name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      </div>
    </div>
  );
}
```

**With Error State**:
```tsx
import { Input } from '@/core/components/ui/Input';

function ActionForm() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState<string | null>(null);
  
  const validateEmail = (value: string) => {
    if (!value.includes('@')) {
      setError('Invalid email address');
    } else {
      setError(null);
    }
  };
  
  return (
    <div>
      <Input 
        type="email"
        placeholder="user@example.com"
        value={email}
        onChange={(e) => {
          setEmail(e.target.value);
          validateEmail(e.target.value);
        }}
        error={!!error}  // Triggers red border and red focus ring
      />
      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
    </div>
  );
}
```

**Textarea for JSON**:
```tsx
import { Textarea } from '@/core/components/ui/Textarea';

function PayloadEditor() {
  const [payload, setPayload] = useState('{}');
  
  return (
    <Textarea 
      placeholder="Enter JSON payload"
      spellCheck={false}  // Triggers monospace font automatically
      value={payload}
      onChange={(e) => setPayload(e.target.value)}
      rows={10}
      maxLength={10000}  // Enforces 10k character limit
    />
  );
}
```

---

### 2. Dialog

**Confirmation Dialog**:
```tsx
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/core/components/ui/Dialog';
import { Button } from '@/core/components/ui/Button';

function DeleteActionButton({ actionId }: { actionId: string }) {
  const [isOpen, setIsOpen] = useState(false);
  
  const handleDelete = async () => {
    await deleteAction(actionId);
    setIsOpen(false);
  };
  
  return (
    <>
      <Button variant="destructive" onClick={() => setIsOpen(true)}>
        Delete
      </Button>
      
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Action</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this action? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDelete}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
```

**Form Dialog**:
```tsx
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/core/components/ui/Dialog';
import { Input } from '@/core/components/ui/Input';
import { Textarea } from '@/core/components/ui/Textarea';
import { Button } from '@/core/components/ui/Button';

function EditActionDialog({ action, onSave }: { action: Action; onSave: (updated: Action) => void }) {
  const [isOpen, setIsOpen] = useState(false);
  const [name, setName] = useState(action.name);
  const [description, setDescription] = useState(action.description);
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({ ...action, name, description });
    setIsOpen(false);
  };
  
  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Edit Action</DialogTitle>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
              Name
            </label>
            <Input 
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>
          
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <Textarea 
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={4}
            />
          </div>
          
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setIsOpen(false)}>
              Cancel
            </Button>
            <Button type="submit">
              Save Changes
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
```

---

### 3. Table

**Basic Table with Status Badges**:
```tsx
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/core/components/ui/Table';
import { Badge } from '@/core/components/ui/Badge';

function ActionsTable({ actions }: { actions: Action[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Last Run</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      
      <TableBody>
        {actions.map((action) => (
          <TableRow key={action.id}>
            <TableCell className="font-medium">{action.name}</TableCell>
            <TableCell>
              <Badge variant={action.status === 'success' ? 'success' : 'error'}>
                {action.status}
              </Badge>
            </TableCell>
            <TableCell className="text-gray-600">
              {formatDistanceToNow(action.lastRun, { addSuffix: true })}
            </TableCell>
            <TableCell>
              <Button variant="outline" size="sm">Run</Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
```

**Clickable Rows with Selection**:
```tsx
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/core/components/ui/Table';

function RunHistoryTable({ runs }: { runs: Run[] }) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const navigate = useNavigate();
  
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Run ID</TableHead>
          <TableHead>Duration</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      
      <TableBody>
        {runs.map((run) => (
          <TableRow 
            key={run.id}
            clickable  // Shows pointer cursor
            selected={selectedId === run.id}  // Highlights with blue background
            onClick={() => {
              setSelectedId(run.id);
              navigate(`/runs/${run.id}`);
            }}
          >
            <TableCell className="font-mono text-sm">{run.id}</TableCell>
            <TableCell>{run.duration}ms</TableCell>
            <TableCell>
              <Badge variant={run.status === 'success' ? 'success' : 'error'}>
                {run.status}
              </Badge>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
```

**Empty State**:
```tsx
function ActionsTable({ actions }: { actions: Action[] }) {
  if (actions.length === 0) {
    return (
      <div className="border-dashed border-2 border-gray-300 bg-gray-50 rounded-lg p-12 text-center">
        <h3 className="text-lg font-semibold text-gray-700">No actions yet</h3>
        <p className="text-sm text-gray-500 mt-2 max-w-md mx-auto">
          Get started by creating your first action.
        </p>
        <Button className="mt-6" onClick={() => navigate('/actions/new')}>
          Create Action
        </Button>
      </div>
    );
  }
  
  return <Table>{/* ... */}</Table>;
}
```

---

### 4. DropdownMenu

**Action Menu (Edit, Delete)**:
```tsx
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator } from '@/core/components/ui/DropdownMenu';
import { Button } from '@/core/components/ui/Button';

function ActionRowMenu({ action }: { action: Action }) {
  const handleEdit = () => {
    navigate(`/actions/${action.id}/edit`);
  };
  
  const handleDelete = () => {
    // Open confirmation dialog
  };
  
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon">
          <svg className="h-4 w-4" /* Three dots icon */>...</svg>
        </Button>
      </DropdownMenuTrigger>
      
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={handleEdit}>
          <svg className="mr-2 h-4 w-4">...</svg>
          Edit
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => window.open(`/actions/${action.id}/logs`)}>
          <svg className="mr-2 h-4 w-4">...</svg>
          View Logs
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem destructive onClick={handleDelete}>
          <svg className="mr-2 h-4 w-4">...</svg>
          Delete
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
```

---

### 5. Loading & Error States

**Loading Spinner**:
```tsx
import { Loading } from '@/core/components/ui/Loading';

function ActionsPage() {
  const { data, isLoading, error } = useQuery({ queryKey: ['actions'], queryFn: fetchActions });
  
  if (isLoading) {
    return <Loading text="Loading actions..." />;
  }
  
  return <ActionsTable actions={data} />;
}
```

**Timeout State**:
```tsx
import { Loading } from '@/core/components/ui/Loading';

function ActionsPage() {
  const [isTimeout, setIsTimeout] = useState(false);
  const { refetch } = useQuery({ 
    queryKey: ['actions'], 
    queryFn: fetchActions,
    onError: () => setTimeout(() => setIsTimeout(true), 30000),  // 30 seconds
  });
  
  if (isTimeout) {
    return <Loading timeout onRetry={() => { setIsTimeout(false); refetch(); }} />;
  }
  
  return <Loading text="Loading actions..." />;
}
```

**Error Banner**:
```tsx
import { ErrorBanner } from '@/core/components/ui/ErrorBanner';

function ActionsPage() {
  const [error, setError] = useState<string | null>(null);
  const { data, isError, error: queryError } = useQuery({ 
    queryKey: ['actions'], 
    queryFn: fetchActions,
    onError: (err) => setError(err.message),
  });
  
  return (
    <div className="space-y-4">
      {error && (
        <ErrorBanner 
          message={error}
          onDismiss={() => setError(null)}
        />
      )}
      
      <ActionsTable actions={data || []} />
    </div>
  );
}
```

---

### 6. Badge Component

**Status Indicators**:
```tsx
import { Badge } from '@/core/components/ui/Badge';

function ActionStatus({ status }: { status: 'success' | 'error' | 'running' | 'pending' }) {
  const variantMap = {
    success: 'success' as const,
    error: 'error' as const,
    running: 'info' as const,
    pending: 'warning' as const,
  };
  
  return (
    <Badge variant={variantMap[status]}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </Badge>
  );
}
```

**With Icons**:
```tsx
function ActionStatus({ status }: { status: string }) {
  return (
    <Badge variant="success" className="inline-flex items-center gap-1">
      <svg className="h-3 w-3" /* Check icon */>...</svg>
      {status}
    </Badge>
  );
}
```

---

## Accessibility Best Practices

### Keyboard Navigation

All components support keyboard navigation out of the box:

- **Input/Textarea**: Tab to focus, type to edit, Shift+Tab to go back
- **Dialog**: Escape to close, Tab cycles through interactive elements (focus trap)
- **DropdownMenu**: Arrow keys to navigate items, Enter to select, Escape to close
- **Table**: Tab through clickable rows and cells

### Screen Reader Support

All components include proper ARIA attributes:

```tsx
// Dialog - requires title for screen readers
<Dialog>
  <DialogContent>
    <DialogTitle>Confirm Delete</DialogTitle>  {/* Announced as dialog title */}
    <DialogDescription>This action cannot be undone.</DialogDescription>
  </DialogContent>
</Dialog>

// Form inputs - use labels for context
<label htmlFor="action-name" className="sr-only">Action Name</label>
<Input id="action-name" placeholder="Action Name" />

// Tables - use semantic HTML
<Table>
  <TableHeader>  {/* <thead> */}
    <TableRow>
      <TableHead scope="col">Name</TableHead>  {/* <th> with scope */}
    </TableRow>
  </TableHeader>
</Table>
```

### Reduced Motion

All animations respect `prefers-reduced-motion`:

```tsx
// Automatically handled by Tailwind classes
<DialogContent className="motion-reduce:transition-none motion-reduce:animate-none">
  {/* Animations disabled if user prefers reduced motion */}
</DialogContent>
```

---

## Styling Customization

All components accept `className` prop for custom styling:

```tsx
// Override default styles
<Input className="border-purple-500 focus:ring-purple-500" />

// Add additional spacing
<Dialog>
  <DialogContent className="max-w-2xl">  {/* Wider dialog */}
    <DialogHeader className="pb-6">  {/* More spacing below header */}
      <DialogTitle>Large Form</DialogTitle>
    </DialogHeader>
  </DialogContent>
</Dialog>

// Custom button in table
<TableCell>
  <Button variant="outline" size="sm" className="text-purple-600 border-purple-600">
    Custom Action
  </Button>
</TableCell>
```

---

## Performance Tips

### Large Tables

For tables with 100-500 rows:

```tsx
// Use React.memo for row components
const TableRowMemo = React.memo(({ action }: { action: Action }) => (
  <TableRow>
    <TableCell>{action.name}</TableCell>
    {/* ... */}
  </TableRow>
));

function LargeActionsTable({ actions }: { actions: Action[] }) {
  return (
    <Table>
      <TableHeader>{/* ... */}</TableHeader>
      <TableBody>
        {actions.map(action => (
          <TableRowMemo key={action.id} action={action} />
        ))}
      </TableBody>
    </Table>
  );
}
```

### Dialog State Management

Avoid re-rendering entire page when dialog opens:

```tsx
// Bad: Page re-renders when dialog state changes
function Page() {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const expensiveData = useMemo(() => computeData(), []);  // Recomputes on dialog state change!
  
  return (
    <>
      <ExpensiveComponent data={expensiveData} />
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>{/* ... */}</Dialog>
    </>
  );
}

// Good: Dialog state isolated in separate component
function DeleteButton({ actionId }: { actionId: string }) {
  const [isOpen, setIsOpen] = useState(false);
  
  return (
    <>
      <Button onClick={() => setIsOpen(true)}>Delete</Button>
      <DeleteDialog actionId={actionId} open={isOpen} onOpenChange={setIsOpen} />
    </>
  );
}
```

---

## Testing

### Component Tests

```tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Input } from '@/core/components/ui/Input';

describe('Input', () => {
  it('should show error styling when error prop is true', () => {
    render(<Input error />);
    const input = screen.getByRole('textbox');
    expect(input).toHaveClass('border-red-500');
  });
  
  it('should call onChange when user types', async () => {
    const handleChange = vi.fn();
    render(<Input onChange={handleChange} />);
    
    await userEvent.type(screen.getByRole('textbox'), 'test');
    expect(handleChange).toHaveBeenCalledTimes(4);  // Once per character
  });
});
```

### Accessibility Tests

```tsx
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { Dialog, DialogContent, DialogTitle } from '@/core/components/ui/Dialog';

expect.extend(toHaveNoViolations);

it('should have no accessibility violations', async () => {
  const { container } = render(
    <Dialog open>
      <DialogContent>
        <DialogTitle>Test Dialog</DialogTitle>
      </DialogContent>
    </Dialog>
  );
  
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

---

## Migration Guide

If you have existing components using basic styling, here's how to migrate:

### Before (Basic Input)
```tsx
<input 
  type="text"
  className="border border-gray-300 rounded px-3 py-2"
  placeholder="Action name"
/>
```

### After (Enhanced Input)
```tsx
<Input 
  type="text"
  placeholder="Action name"
  // All styling built-in (hover, focus, error states)
/>
```

### Before (Basic Dialog)
```tsx
{isOpen && (
  <div className="fixed inset-0 bg-black/50 flex items-center justify-center">
    <div className="bg-white rounded-lg p-6">
      <h2>Confirm</h2>
      <p>Are you sure?</p>
      <button onClick={handleConfirm}>Yes</button>
    </div>
  </div>
)}
```

### After (Enhanced Dialog)
```tsx
<Dialog open={isOpen} onOpenChange={setIsOpen}>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Confirm</DialogTitle>
      <DialogDescription>Are you sure?</DialogDescription>
    </DialogHeader>
    <DialogFooter>
      <Button onClick={handleConfirm}>Yes</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

---

## Next Steps

1. **Browse Components**: Explore `src/core/components/ui/` for all available components
2. **Check Examples**: See `src/core/pages/Actions.tsx` for real-world usage
3. **Run Tests**: `npm run test` to see component tests in action
4. **Contribute**: Follow the Constitution's Test-First principle when adding components

For questions or issues, refer to the [data-model.md](./data-model.md) for component contracts.
