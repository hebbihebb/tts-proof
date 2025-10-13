import React, { useEffect, useState } from 'react';
import { X, Download, AlertTriangle, FileText } from 'lucide-react';
import { apiService } from '../services/api';

interface DiffViewerProps {
  runId: string;
  onClose: () => void;
}

export const DiffViewer: React.FC<DiffViewerProps> = ({ runId, onClose }) => {
  const [diffText, setDiffText] = useState<string>('Loading diff...');
  const [hasMore, setHasMore] = useState(false);
  const [rejected, setRejected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDiff = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await apiService.getRunDiff(runId);
        setDiffText(data.diff_head);
        setHasMore(data.has_more);
        setRejected(data.rejected);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load diff');
        setDiffText('Diff unavailable');
      } finally {
        setLoading(false);
      }
    };

    fetchDiff();
  }, [runId]);

  const handleDownloadOutput = async () => {
    try {
      const artifactName = rejected ? 'rejected' : 'output';
      const blob = await apiService.downloadArtifact(runId, artifactName);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${runId}_${artifactName}.md`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Failed to download:', err);
    }
  };

  // Color diff lines
  const renderDiffLine = (line: string, index: number) => {
    if (line.startsWith('+++ ') || line.startsWith('--- ') || line.startsWith('@@ ')) {
      return (
        <div key={index} className="text-blue-600 dark:text-blue-400">
          {line}
        </div>
      );
    } else if (line.startsWith('+')) {
      return (
        <div key={index} className="bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300">
          {line}
        </div>
      );
    } else if (line.startsWith('-')) {
      return (
        <div key={index} className="bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300">
          {line}
        </div>
      );
    } else {
      return (
        <div key={index} className="text-gray-600 dark:text-gray-400">
          {line}
        </div>
      );
    }
  };

  const diffLines = diffText.split('\n');
  const isNoDiff = diffText.includes('No differences') || diffText.includes('identical');

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-gray-800 border-b dark:border-gray-700 p-4 flex justify-between items-center rounded-t-lg">
          <div className="flex items-center gap-3">
            <FileText className={rejected ? "text-yellow-500" : "text-blue-500"} size={24} />
            <div>
              <h2 className="text-xl font-bold dark:text-white">
                {rejected ? 'Changes (Rejected)' : 'Changes (Output)'}
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {isNoDiff ? 'No differences found' : hasMore ? 'Showing first 200 lines' : 'Unified diff'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {hasMore && (
              <button
                onClick={handleDownloadOutput}
                className="px-3 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded flex items-center gap-2 text-sm"
              >
                <Download size={16} />
                Download Full Output
              </button>
            )}
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-gray-500 dark:text-gray-400">Loading diff...</div>
            </div>
          ) : error ? (
            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded p-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="text-yellow-600 dark:text-yellow-400 mt-1 flex-shrink-0" size={20} />
                <div>
                  <h3 className="font-semibold text-yellow-800 dark:text-yellow-200">Diff Unavailable</h3>
                  <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">{error}</p>
                </div>
              </div>
            </div>
          ) : rejected ? (
            <div>
              <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded p-4 mb-4">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="text-yellow-600 dark:text-yellow-400 mt-1 flex-shrink-0" size={20} />
                  <div>
                    <h3 className="font-semibold text-yellow-800 dark:text-yellow-200">Validation Failed</h3>
                    <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
                      Output was rejected due to validation errors. Changes shown are against the rejected file.
                    </p>
                  </div>
                </div>
              </div>
              <pre className="font-mono text-xs whitespace-pre bg-gray-50 dark:bg-gray-900 p-4 rounded border dark:border-gray-700 overflow-x-auto">
                {diffLines.map((line, idx) => renderDiffLine(line, idx))}
              </pre>
            </div>
          ) : isNoDiff ? (
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded p-4">
              <div className="flex items-start gap-3">
                <FileText className="text-green-600 dark:text-green-400 mt-1 flex-shrink-0" size={20} />
                <div>
                  <h3 className="font-semibold text-green-800 dark:text-green-200">No Changes</h3>
                  <p className="text-sm text-green-700 dark:text-green-300 mt-1">
                    Input and output files are identical.
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <pre className="font-mono text-xs whitespace-pre bg-gray-50 dark:bg-gray-900 p-4 rounded border dark:border-gray-700 overflow-x-auto">
              {diffLines.map((line, idx) => renderDiffLine(line, idx))}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
};
