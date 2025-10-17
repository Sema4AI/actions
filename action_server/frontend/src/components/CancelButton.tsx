import { FC, useMemo } from 'react';
import { Button, Tooltip } from '@sema4ai/components';
import { IconStop } from '@sema4ai/icons';
import { cancelRun } from '@/shared/api-client';
import { RunStatus } from '@/shared/types';

type Props = {
  runId?: string;
  disabled?: boolean;
  status: RunStatus;
  requestId?: string;
};

export const CancelButton: FC<Props> = ({ runId, disabled, status, requestId }) => {
  // Either runId or requestId must be provided.
  if (!runId && !requestId) {
    throw new Error('Either runId or requestId must be provided.');
  }

  const button = useMemo(
    () => (
      <Tooltip text="Cancel Run">
        <Button
          icon={IconStop}
          variant="secondary"
          size="small"
          disabled={disabled}
          onClick={() => cancelRun(runId, requestId)}
          aria-label="Cancel run"
          label="Cancel run"
          align="primary"
        >
          Cancel Run
        </Button>
      </Tooltip>
    ),
    [runId, requestId, disabled],
  );

  if (status !== RunStatus.RUNNING && status !== RunStatus.NOT_RUN) {
    return undefined;
  }
  return button;
};
