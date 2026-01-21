import { useEffect, useMemo, useState, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { Button } from '@/core/components/ui/Button';
import { Loading } from '@/core/components/ui/Loading';
import { ErrorBanner } from '@/core/components/ui/ErrorBanner';
import { useActionServerContext } from '@/shared/context/actionServerContext';
import { baseUrl, collectRunArtifacts } from '@/shared/api-client';
import { AsyncLoaded, Run, RunStatus } from '@/shared/types';
import { Badge } from '@/core/components/ui/Badge';
import { cn } from '@/shared/utils/cn';
import { copyToClipboard } from '@/shared/utils/helpers';

const OUTPUT_ARTIFACT_NAME = '__action_server_output.txt';

// Parse and colorize console output with ANSI-like styling
const colorizeOutput = (text: string): React.ReactNode[] => {
  const lines = text.split('\n');
  
  return lines.map((line, index) => {
    // Determine line styling based on content patterns
    let className = 'text-foreground';
    let lineStyle: React.CSSProperties = {};
    
    // PASS/SUCCESS patterns - bright green
    if (/\bPASS\b|\bPASSED\b|\bsuccess\b|\bSuccess\b|\bSUCCESS\b|\bcompleted\b|\bCompleted\b/i.test(line)) {
      className = 'text-emerald-400 font-medium';
    }
    // FAIL/ERROR patterns - bright red
    else if (/\bFAIL\b|\bFAILED\b|\berror\b|\bError\b|\bERROR\b|\bexception\b|\bException\b|\btraceback\b|\bTraceback\b/i.test(line)) {
      className = 'text-red-400 font-medium';
    }
    // Warning patterns - yellow/amber
    else if (/\bwarn\b|\bWarning\b|\bWARNING\b/i.test(line)) {
      className = 'text-amber-400 font-medium';
    }
    // Running/executing lines - cyan/blue
    else if (/Running:|Executing:|Starting:|Loading:|Collecting/i.test(line)) {
      className = 'text-cyan-400';
    }
    // Log/output path lines - purple/violet
    else if (/Log \(html\):|Output:|Result:|log\.html/i.test(line)) {
      className = 'text-violet-400';
    }
    // Separator lines (====, ----, etc.) - dimmed
    else if (/^[=\-*_]{3,}/.test(line.trim()) || /[=\-]{10,}/.test(line)) {
      className = 'text-muted-foreground/60';
    }
    // Pre-loading/module lines - blue
    else if (/Pre-loading|module:|import|from:/i.test(line)) {
      className = 'text-blue-400';
    }
    // Status lines with brackets like [96m, [0m (ANSI codes) - strip and color
    else if (/\[\d+m/.test(line)) {
      // This has ANSI codes, let's handle it
      const cleanLine = line.replace(/\[\d+m/g, '');
      if (/PASS/i.test(cleanLine)) {
        className = 'text-emerald-400 font-medium';
      } else if (/FAIL/i.test(cleanLine)) {
        className = 'text-red-400 font-medium';
      } else {
        className = 'text-cyan-400';
      }
    }
    // Timestamps/metadata - subtle
    else if (/^\d{4}-\d{2}-\d{2}/.test(line) || /^\[.*?\]/.test(line.trim())) {
      className = 'text-muted-foreground';
    }
    // Stack trace lines - dimmed red
    else if (/^\s+(at |File |in |from |line \d)/.test(line)) {
      className = 'text-red-300/70';
    }
    // File paths - subtle violet
    else if (/\/[a-zA-Z0-9_\-./]+\.(py|txt|json|yaml|html|log)/.test(line)) {
      className = 'text-violet-300/80';
    }
    // Empty lines - small spacing
    else if (line.trim() === '') {
      return <div key={index} className="h-1" />;
    }
    
    // Clean ANSI codes from display
    const displayLine = line.replace(/\[\d+m/g, '');
    
    return (
      <div key={index} className={cn('py-0.5 leading-relaxed', className)} style={lineStyle}>
        {displayLine || '\u00A0'}
      </div>
    );
  });
};

// Copy button component
const CopyButton = ({ value }: { value: string }) => {
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
      variant="ghost"
      size="sm"
      onClick={handleCopy}
      className="gap-1.5"
    >
      {copied ? (
        <>
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          Copied!
        </>
      ) : (
        <>
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          Copy
        </>
      )}
    </Button>
  );
};

// Status badge helper
const renderStatusBadge = (status: RunStatus) => {
  const statusLabel: Record<RunStatus, string> = {
    [RunStatus.NOT_RUN]: 'Not run',
    [RunStatus.RUNNING]: 'Running',
    [RunStatus.PASSED]: 'Passed',
    [RunStatus.FAILED]: 'Failed',
    [RunStatus.CANCELLED]: 'Cancelled',
  };
  
  const map: Record<RunStatus, 'success' | 'error' | 'warning' | 'info' | 'neutral'> = {
    [RunStatus.NOT_RUN]: 'neutral',
    [RunStatus.RUNNING]: 'info',
    [RunStatus.PASSED]: 'success',
    [RunStatus.FAILED]: 'error',
    [RunStatus.CANCELLED]: 'warning',
  };
  
  return <Badge variant={map[status] ?? 'neutral'}>{statusLabel[status]}</Badge>;
};

export const LogsPage = () => {
  const navigate = useNavigate();
  const { runId } = useParams<{ runId: string }>();
  const { loadedRuns } = useActionServerContext();
  const [artifactsState, setArtifactsState] = useState<AsyncLoaded<Record<string, string>>>({
    isPending: true,
    data: {},
  });
  const [activeTab, setActiveTab] = useState<'console' | 'fullLog'>('console');
  const iframeRef = useRef<HTMLIFrameElement>(null);

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
      <div className="flex h-full items-center justify-center text-base text-muted-foreground">
        Select a run from the history to inspect logs.
      </div>
    );
  }

  if (loadedRuns.isPending) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loading text="Loading run details..." />
      </div>
    );
  }

  if (!run) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="max-w-md rounded-lg p-8 text-center">
          <ErrorBanner message={`Run ${runId} was not found in the local cache.`} />
          <div className="mt-6">
            <Button variant="secondary" size="lg" onClick={() => navigate('/runs')}>
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

  const logHtmlUrl = `${baseUrl}/api/runs/${runId}/log.html`;

  return (
    <div className="h-full flex flex-col p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Run Details</h1>
          <p className="mt-1 text-base text-muted-foreground">
            Inspect the execution output and detailed logs.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="ghost" onClick={() => navigate('/runs')}>
            Back to run history
          </Button>
        </div>
      </div>

      {/* Run Info Card */}
      <div className="rounded-xl border border-border bg-card shadow-sm p-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div>
              <h2 className="text-xl font-semibold text-card-foreground">Run #{run.numbered_id}</h2>
              <p className="text-base text-muted-foreground mt-1">
                {new Date(run.start_time).toLocaleString()}
              </p>
            </div>
            {renderStatusBadge(run.status)}
          </div>
          <div className="text-sm text-muted-foreground font-mono">
            {run.id}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 border-b border-border">
        <button
          onClick={() => setActiveTab('console')}
          className={cn(
            'px-4 py-3 text-base font-medium transition-colors duration-150',
            'border-b-2 -mb-px',
            activeTab === 'console'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
          )}
        >
          Console Output
        </button>
        <button
          onClick={() => setActiveTab('fullLog')}
          className={cn(
            'px-4 py-3 text-base font-medium transition-colors duration-150',
            'border-b-2 -mb-px',
            activeTab === 'fullLog'
              ? 'border-primary text-primary'
              : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
          )}
        >
          Full Log (HTML)
        </button>
      </div>

      {/* Content Area */}
      <div className="flex-1 min-h-0">
        {activeTab === 'console' ? (
          <div className="h-full rounded-xl border border-border bg-card shadow-sm flex flex-col">
            <div className="flex items-center justify-between border-b border-border px-5 py-3">
              <span className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
                Console Output
              </span>
              <CopyButton value={logContent} />
            </div>
            <div className="flex-1 overflow-auto p-5">
              {artifactsState.isPending ? (
                <div className="text-base text-muted-foreground">Loading log output...</div>
              ) : (
                <div className="font-mono text-sm leading-relaxed">
                  {colorizeOutput(logContent)}
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="h-full rounded-xl border border-border bg-card shadow-sm overflow-hidden flex flex-col">
            <div className="flex items-center justify-between border-b border-border px-5 py-3">
              <span className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
                Full Execution Log
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => window.open(logHtmlUrl, '_blank')}
                className="gap-1.5"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
                Open in new tab
              </Button>
            </div>
            <div className="flex-1 bg-white dark:bg-gray-900 rounded-b-xl overflow-hidden">
              <iframe
                ref={iframeRef}
                src={logHtmlUrl}
                className="w-full h-full border-0"
                title="Run Log"
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
