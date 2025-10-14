import React, { useEffect, useMemo, useState } from 'react';
import { X, Download, RefreshCcw, FileText, FileArchive, AlertTriangle } from 'lucide-react';
import { apiService, ArtifactInfo } from '../services/api';
import { Button } from './Button';

type LogKind = 'info' | 'warning' | 'error' | 'success';

interface ArtifactBrowserProps {
  runId: string;
  onClose: () => void;
  onLog?: (message: string, kind?: LogKind) => void;
}

const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / Math.pow(1024, index);
  return `${value.toFixed(value >= 10 || index === 0 ? 0 : 1)} ${units[index]}`;
};

const formatTimestamp = (iso: string): string => {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return iso;
  }
  return `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
};

export const ArtifactBrowser: React.FC<ArtifactBrowserProps> = ({ runId, onClose, onLog }) => {
  const [artifacts, setArtifacts] = useState<ArtifactInfo[]>([]);
  const [totalSize, setTotalSize] = useState<number>(0);
  const [selectedName, setSelectedName] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isDownloading, setIsDownloading] = useState<boolean>(false);

  const selectedArtifact = useMemo(() => artifacts.find((item) => item.name === selectedName) || null, [artifacts, selectedName]);

  const inferMediaLabel = (info: ArtifactInfo | null) => {
    if (!info) return '';
    const extension = info.name.split('.').pop();
    if (!extension) return info.media_type;
    return `${info.media_type} • .${extension}`;
  };

  const loadArtifacts = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.listRunArtifacts(runId);
      setArtifacts(response.artifacts);
      setTotalSize(response.total_size);
      if (!selectedName && response.artifacts.length > 0) {
        setSelectedName(response.artifacts[0].name);
      } else if (selectedName && !response.artifacts.some((item) => item.name === selectedName)) {
        setSelectedName(response.artifacts[0]?.name ?? null);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load artifacts';
      setError(message);
      onLog?.(`Artifact load failed: ${message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setSelectedName(null);
    setArtifacts([]);
    setTotalSize(0);
    loadArtifacts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runId]);

  const handleDownloadSelected = async () => {
    if (!selectedArtifact) return;
    try {
      setIsDownloading(true);
      const blob = await apiService.downloadRunArtifact(runId, selectedArtifact.name);
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `${runId}_${selectedArtifact.name}`;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      window.URL.revokeObjectURL(url);
      onLog?.(`Downloaded ${selectedArtifact.name}`, 'success');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Download failed';
      onLog?.(`Download failed: ${message}`, 'error');
    } finally {
      setIsDownloading(false);
    }
  };

  const handleDownloadArchive = async () => {
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
      onLog?.('Downloaded run archive', 'success');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Archive download failed';
      onLog?.(`Archive download failed: ${message}`, 'error');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="flex h-[80vh] w-full max-w-6xl flex-col rounded-lg bg-white shadow-xl dark:bg-gray-900">
        <div className="flex items-center justify-between border-b border-gray-200 px-5 py-4 dark:border-gray-700">
          <div>
            <h2 className="text-xl font-semibold text-light-text dark:text-catppuccin-text">Artifacts</h2>
            <p className="text-xs text-gray-500 dark:text-gray-400">Run ID: {runId}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">Total Size: {formatBytes(totalSize)}</p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={loadArtifacts} isLoading={loading} icon={<RefreshCcw className="h-4 w-4" />}>Refresh</Button>
            <Button variant="outline" size="sm" onClick={handleDownloadArchive} icon={<FileArchive className="h-4 w-4" />}>Download All</Button>
            <button onClick={onClose} className="rounded p-2 hover:bg-gray-100 dark:hover:bg-gray-800">
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {error && (
          <div className="flex items-center gap-2 bg-yellow-100 px-4 py-2 text-sm text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-100">
            <AlertTriangle className="h-4 w-4" />
            <span>{error}</span>
          </div>
        )}

        <div className="flex flex-1 overflow-hidden">
          <div className="w-full max-w-xs border-r border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-950">
            <div className="flex items-center justify-between px-4 py-3">
              <span className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Files</span>
              <span className="text-xs text-gray-500 dark:text-gray-400">{artifacts.length}</span>
            </div>
            <div className="h-full overflow-auto">
              {loading ? (
                <div className="p-4 text-sm text-gray-500 dark:text-gray-400">Loading artifacts...</div>
              ) : artifacts.length === 0 ? (
                <div className="p-4 text-sm text-gray-500 dark:text-gray-400">No artifacts recorded for this run.</div>
              ) : (
                artifacts.map((artifact) => {
                  const isActive = artifact.name === selectedName;
                  return (
                    <button
                      key={artifact.name}
                      onClick={() => setSelectedName(artifact.name)}
                      className={`flex w-full flex-col items-start px-4 py-3 text-left text-sm transition-colors ${isActive ? 'bg-blue-100 text-blue-900 dark:bg-blue-900/40 dark:text-blue-100' : 'hover:bg-gray-100 dark:hover:bg-gray-800'}`}
                    >
                      <div className="flex w-full items-center justify-between">
                        <div className="flex items-center gap-2">
                          <FileText className="h-4 w-4" />
                          <span className="font-medium break-all">{artifact.name}</span>
                        </div>
                        <span className="text-xs text-gray-500 dark:text-gray-400">{formatBytes(artifact.size_bytes)}</span>
                      </div>
                      <span className="mt-1 text-xs text-gray-500 dark:text-gray-400">{formatTimestamp(artifact.modified_at)}</span>
                    </button>
                  );
                })
              )}
            </div>
          </div>

          <div className="flex flex-1 flex-col">
            <div className="flex items-center justify-between border-b border-gray-200 px-5 py-3 dark:border-gray-800">
              <div>
                <h3 className="text-sm font-semibold text-light-text dark:text-catppuccin-text">Preview</h3>
                {selectedArtifact && (
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {inferMediaLabel(selectedArtifact)} • {formatBytes(selectedArtifact.size_bytes)}
                  </p>
                )}
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleDownloadSelected}
                  disabled={!selectedArtifact}
                  isLoading={isDownloading}
                  icon={<Download className="h-4 w-4" />}
                >
                  Download
                </Button>
              </div>
            </div>

            <div className="flex-1 overflow-auto px-5 py-4">
              {loading ? (
                <div className="text-sm text-gray-500 dark:text-gray-400">Loading preview...</div>
              ) : !selectedArtifact ? (
                <div className="text-sm text-gray-500 dark:text-gray-400">Select an artifact to preview it.</div>
              ) : selectedArtifact.preview ? (
                <pre className="whitespace-pre-wrap break-words rounded bg-gray-100 p-4 text-xs text-gray-700 dark:bg-gray-900 dark:text-gray-200">
                  {selectedArtifact.preview}
                </pre>
              ) : (
                <div className="text-sm text-gray-500 dark:text-gray-400">
                  Preview unavailable. The file may be binary or exceeds the inline preview limit.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
