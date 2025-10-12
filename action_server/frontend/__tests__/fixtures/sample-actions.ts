import { formatISO } from 'date-fns';

export const sampleActions = [
  {
    id: 'action-1',
    name: 'Send welcome email',
    status: 'success',
    lastRun: formatISO(new Date(Date.now() - 1000 * 60 * 60)),
  },
  {
    id: 'action-2',
    name: 'Generate report',
    status: 'error',
    lastRun: formatISO(new Date(Date.now() - 1000 * 60 * 60 * 24)),
  },
];
