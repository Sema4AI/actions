import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { Button } from '@/core/components/ui/Button';
import { Loading } from '@/core/components/ui/Loading';
import { ErrorBanner } from '@/core/components/ui/ErrorBanner';
import { useActionServerContext } from '@/shared/context/actionServerContext';
import { baseUrl, collectRunArtifacts } from '@/shared/api-client';
import { AsyncLoaded, Run } from '@/shared/types';

const OUTPUT_ARTIFACT_NAME = '__action_server_output.txt';

export const LogsPage = () => {
  const navigate = useNavigate();
  const { runId } = useParams<{ runId: string }>();
  const { loadedRuns } = useActionServerContext();
  const [artifactsState, setArtifactsState] = useState<AsyncLoaded<Record<string, string>>>({
    isPending: true,
    data: {},
  });

  const run = useMemo<Run | undefined>(() => {
    return loadedRuns.data?.find((item) => item.id === runId);
  }, [loadedRuns.data, runId]);

  useEffect(() => {
    if (!runId) {
      return;
    }
    collectRunArtifacts(runId, setArtifactsState, {
      artifact_names: [OUTPUT_ARTIFACT_NAME],
    });
  }, [runId]);

  if (!runId) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
        Select a run from the history to inspect logs.
      </div>
    );
  }

  if (loadedRuns.isPending) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loading text="Loading run details…" />
      </div>
    );
  }

  if (!run) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="max-w-md rounded-md p-6 text-center">
          <ErrorBanner message={`Run ${runId} was not found in the local cache.`} />
          <div className="mt-4">
            <Button variant="secondary" onClick={() => navigate('/runs')}>
              Back to run history
            </Button>
          </div>
        </div>
      </div>
    );
  }

  const logContent =
    artifactsState.data?.[OUTPUT_ARTIFACT_NAME] ||
    artifactsState.errorMessage ||
    'Log output not available for this run.';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Logs</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Inspect the streamed console output captured during the run.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" onClick={() => navigate('/runs')}>
            Back to run history
          </Button>
          <Button
            asChild
            variant="secondary"
          >
            <a href={`${baseUrl}/api/runs/${runId}/log.html`} target="_blank" rel="noreferrer">
              Open full log
            </a>
          </Button>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-card shadow-sm">
        <div className="border-b border-border p-4 text-sm text-muted-foreground">
          <span className="font-medium text-card-foreground">Run #{run.numbered_id}</span>
          <span className="mx-2 text-muted-foreground/50">•</span>
          {new Date(run.start_time).toLocaleString()}
        </div>
        <div className="max-h-[70vh] overflow-auto p-4">
          {artifactsState.isPending ? (
            <div className="text-sm text-muted-foreground">Loading log output…</div>
          ) : (
            <pre className="whitespace-pre-wrap font-mono text-sm leading-relaxed text-foreground">
              {logContent}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
};
