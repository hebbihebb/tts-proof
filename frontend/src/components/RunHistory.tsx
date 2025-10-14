import React, { useEffect, useState } from 'react';
import { History, RefreshCcw, Download, FolderOpen, Trash2, AlertTriangle, BarChart3, FileDiff } from 'lucide-react';
import { apiService, RunSummary } from '../services/api';
import { Button } from './Button';

type LogKind = 'info' | 'warning' | 'error' | 'success';

interface RunHistoryProps {
  onViewArtifacts: (runId: string) => void;
  onViewReport: (runId: string) => void;
  onViewDiff: (runId: string) => void;
  onLog?: (message: string, kind?: LogKind) => void;
  activeRunId?: string | null;
}

const formatBytes = (value?: number | null): string => {
  if (!value || value <= 0) return '—';
  const units = ['B', 'KB', 'MB', 'GB'];
  const index = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1);
  const num = value / Math.pow(1024, index);
  return `${num.toFixed(num >= 10 || index === 0 ? 0 : 1)} ${units[index]}`;
};

const formatDate = (iso: string): string => {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return iso;
  }
  return date.toLocaleString();
};

const getStatusStyles = (status: string): string => {
  const normalized = status.toLowerCase();
  if (normalized.includes('error') || normalized === 'failed') {
    return 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-100';
  }
  if (normalized === 'completed' || normalized === 'success') {
    return 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-100';
  }
  if (normalized === 'processing' || normalized === 'running') {
    return 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-100';
  }
  return 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-200';
};

export const RunHistory: React.FC<RunHistoryProps> = ({
  onViewArtifacts,
  onViewReport,
  onViewDiff,
  onLog,
  activeRunId,
}) => {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  const fetchRuns = async () => {
    try {
      setIsRefreshing(true);
      setError(null);
      const history = await apiService.listRuns();
      setRuns(history);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load run history';
      setError(message);
      onLog?.(`Run history failed: ${message}`, 'error');
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, []);

  const handleDownloadArchive = async (runId: string) => {
    try {
      const blob = await apiService.downloadRunArchive(runId);
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `${runId}_artifacts.zip`;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      window.URL.revokeObjectURL(url);
      onLog?.(`Downloaded archive for ${runId}`, 'success');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to download archive';
      onLog?.(`Archive download failed for ${runId}: ${message}`, 'error');
    }
  };

  const handleDelete = async (runId: string) => {
    try {
      await apiService.deleteRun(runId);
      onLog?.(`Deleted run ${runId}`, 'warning');
      fetchRuns();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete run';
      onLog?.(`Delete failed for ${runId}: ${message}`, 'error');
    }
  };

  return (
    <section className="mt-8">
      <div className="bg-light-mantle dark:bg-catppuccin-mantle rounded-lg shadow-lg border border-light-surface0 dark:border-catppuccin-surface0">
        <div className="flex items-center justify-between border-b border-light-surface1 dark:border-catppuccin-surface1 px-5 py-4">
          <div className="flex items-center gap-2">
            <History className="h-5 w-5 text-light-text dark:text-catppuccin-subtext1" />
            <h2 className="text-lg font-semibold text-light-text dark:text-catppuccin-text">Run History</h2>
            <span className="text-xs text-gray-500 dark:text-gray-400">{runs.length} runs</span>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={fetchRuns} isLoading={isRefreshing} icon={<RefreshCcw className="h-4 w-4" />}>Refresh</Button>
          </div>
        </div>

        {error && (
          <div className="flex items-center gap-2 bg-yellow-100 px-4 py-2 text-sm text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-100">
            <AlertTriangle className="h-4 w-4" />
            <span>{error}</span>
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-900/60">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Run ID</th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Status</th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Created</th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Completed</th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Artifacts</th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Size</th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-800 bg-white dark:bg-gray-950">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-4 py-6 text-center text-sm text-gray-500 dark:text-gray-400">
                    Loading run history...
                  </td>
                </tr>
              ) : runs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-6 text-center text-sm text-gray-500 dark:text-gray-400">
                    No runs recorded yet. Process a file to populate run history.
                  </td>
                </tr>
              ) : (
                runs.map((run) => (
                  <tr key={run.run_id} className={run.run_id === activeRunId ? 'bg-blue-50 dark:bg-blue-900/20' : ''}>
                    <td className="px-4 py-3 text-sm font-mono text-blue-700 dark:text-blue-200 break-all">{run.run_id}</td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${getStatusStyles(run.status)}`}>
                        {run.status}
                      </span>
                      {run.has_rejected && (
                        <span className="ml-2 rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-700 dark:bg-amber-900/40 dark:text-amber-100">
                          Rejected
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{formatDate(run.created_at)}</td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{run.completed_at ? formatDate(run.completed_at) : '—'}</td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{run.artifact_count}</td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{formatBytes(run.total_size)}</td>
                    <td className="px-4 py-3 text-sm">
                      <div className="flex flex-wrap gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-xs"
                          icon={<FolderOpen className="h-3.5 w-3.5" />}
                          onClick={() => {
                            onViewArtifacts(run.run_id);
                            onLog?.(`Opening artifact browser for ${run.run_id}`, 'info');
                          }}
                        >
                          Artifacts
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-xs"
                          icon={<BarChart3 className="h-3.5 w-3.5" />}
                          onClick={() => {
                            onViewReport(run.run_id);
                            onLog?.(`Viewing report for ${run.run_id}`, 'info');
                          }}
                        >
                          Report
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-xs"
                          icon={<FileDiff className="h-3.5 w-3.5" />}
                          onClick={() => {
                            onViewDiff(run.run_id);
                            onLog?.(`Viewing diff for ${run.run_id}`, 'info');
                          }}
                        >
                          Diff
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-xs"
                          icon={<Download className="h-3.5 w-3.5" />}
                          onClick={() => handleDownloadArchive(run.run_id)}
                        >
                          Zip
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-xs text-red-600 hover:bg-red-50 dark:text-red-300 dark:hover:bg-red-900/20"
                          icon={<Trash2 className="h-3.5 w-3.5" />}
                          onClick={() => handleDelete(run.run_id)}
                        >
                          Delete
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
};
