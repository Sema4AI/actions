import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { Button } from '@/core/components/ui/Button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/core/components/ui/Table';
import { useActionServerContext } from '@/shared/context/actionServerContext';
import { baseUrl, fetchRunArtifactsList } from '@/shared/api-client';
import { ArtifactInfo, AsyncLoaded } from '@/shared/types';

const formatBytes = (size: number) => {
  if (!size) {
    return '0 B';
  }
  const units = ['B', 'KB', 'MB', 'GB'];
  const index = Math.min(Math.floor(Math.log(size) / Math.log(1024)), units.length - 1);
  const value = size / 1024 ** index;
  return `${value.toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
};

export const ArtifactsPage = () => {
  const navigate = useNavigate();
  const { runId } = useParams<{ runId: string }>();
  const { loadedRuns } = useActionServerContext();
  const [artifactState, setArtifactState] = useState<AsyncLoaded<ArtifactInfo[]>>({
    isPending: true,
    data: undefined,
  });

  const run = useMemo(() => {
    return loadedRuns.data?.find((item) => item.id === runId);
  }, [loadedRuns.data, runId]);

  useEffect(() => {
    if (!runId) {
      return;
    }
    fetchRunArtifactsList(runId, setArtifactState);
  }, [runId]);

  if (!runId) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
        Select a run from the history to inspect artifacts.
      </div>
    );
  }

  if (loadedRuns.isPending) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
        Loading run metadata…
      </div>
    );
  }

  if (!run) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="max-w-md rounded-md border border-destructive/20 bg-destructive/5 p-6 text-center text-sm text-destructive">
          Run <span className="font-mono font-semibold">{runId}</span> could not be found.
          <div className="mt-4">
            <Button variant="secondary" onClick={() => navigate('/runs')}>
              Back to run history
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Artifacts</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Download generated files or reports produced during the run execution.
          </p>
        </div>
        <Button variant="ghost" onClick={() => navigate('/runs')}>
          Back to run history
        </Button>
      </div>

      <div className="rounded-lg border border-border bg-card shadow-sm">
        <div className="border-b border-border p-4 text-sm text-muted-foreground">
          <span className="font-medium text-card-foreground">Run #{run.numbered_id}</span>
          <span className="mx-2 text-muted-foreground/50">•</span>
          {new Date(run.start_time).toLocaleString()}
        </div>
        <div className="p-6">
          {artifactState.isPending ? (
            <div className="text-sm text-muted-foreground">Loading artifact list…</div>
          ) : artifactState.errorMessage ? (
            <div className="mb-4">
              <ErrorBanner message={`Unable to load artifacts: ${artifactState.errorMessage}`} />
            </div>
          ) : !artifactState.data || artifactState.data.length === 0 ? (
            <div className="rounded-md border border-dashed border-border bg-muted/50 p-12 text-center text-sm text-muted-foreground">
              This run did not produce artifacts.
            </div>
          ) : (
            <div className="rounded-md border border-border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead className="w-40 text-right">Size</TableHead>
                    <TableHead className="w-32 text-right">Download</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {artifactState.data.map((artifact) => (
                    <TableRow key={artifact.name} className="hover:bg-muted/50 transition-colors">
                      <TableCell className="font-mono text-sm text-foreground">
                        {artifact.name}
                      </TableCell>
                      <TableCell className="text-right text-sm text-muted-foreground">
                        {formatBytes(artifact.size_in_bytes)}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button asChild size="sm" variant="ghost">
                          <a
                            href={`${baseUrl}/api/runs/${runId}/artifacts/${encodeURIComponent(artifact.name)}`}
                            target="_blank"
                            rel="noreferrer"
                          >
                            Download
                          </a>
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
