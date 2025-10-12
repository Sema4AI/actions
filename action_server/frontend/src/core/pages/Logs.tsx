import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { Button } from '@/core/components/ui/Button';
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
      <div className="flex h-full items-center justify-center text-sm text-gray-600">
        Select a run from the history to inspect logs.
      </div>
    );
  }

  if (loadedRuns.isPending) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-gray-600">
        <Loading text="Loading run details…" />
      </div>
    );
  }

  if (!run) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="max-w-md rounded-md border border-red-200 bg-red-50 p-6 text-center text-sm text-red-700">
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
          <h1 className="text-2xl font-semibold text-gray-900">Logs</h1>
          <p className="mt-1 text-sm text-gray-600">
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

      <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="border-b border-gray-200 p-4 text-sm text-gray-600">
          <span className="font-medium text-gray-900">Run #{run.numbered_id}</span>
          <span className="mx-2 text-gray-400">•</span>
          {new Date(run.start_time).toLocaleString()}
        </div>
        <div className="max-h-[70vh] overflow-auto p-4">
          {artifactsState.isPending ? (
            <div className="text-sm text-gray-600">Loading log output…</div>
          ) : (
            <pre className="whitespace-pre-wrap font-mono text-sm leading-relaxed text-gray-900">
              {logContent}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
};
