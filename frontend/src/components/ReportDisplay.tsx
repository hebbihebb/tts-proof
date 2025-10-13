import React, { useEffect, useState } from 'react';
import { X, Download, Copy, CheckCircle, AlertTriangle } from 'lucide-react';
import { apiService } from '../services/api';

interface ReportDisplayProps {
  runId: string;
  onClose: () => void;
}

export const ReportDisplay: React.FC<ReportDisplayProps> = ({ runId, onClose }) => {
  const [report, setReport] = useState<string>('Loading report...');
  const [jsonPath, setJsonPath] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchReport = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await apiService.getRunReport(runId);
        setReport(data.pretty_report);
        setJsonPath(data.json_report_path);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load report');
        setReport('Report unavailable');
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
  }, [runId]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(report);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const handleDownloadJson = async () => {
    try {
      const blob = await apiService.downloadArtifact(runId, 'report');
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${runId}_report.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Failed to download:', err);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-5xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-gray-800 border-b dark:border-gray-700 p-4 flex justify-between items-center rounded-t-lg">
          <div className="flex items-center gap-3">
            {error ? (
              <AlertTriangle className="text-yellow-500" size={24} />
            ) : (
              <CheckCircle className="text-green-500" size={24} />
            )}
            <div>
              <h2 className="text-xl font-bold dark:text-white">Pipeline Report</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">Run ID: {runId}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              className="px-3 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded flex items-center gap-2 text-sm"
              disabled={loading}
            >
              {copied ? (
                <>
                  <CheckCircle size={16} />
                  Copied!
                </>
              ) : (
                <>
                  <Copy size={16} />
                  Copy
                </>
              )}
            </button>
            {jsonPath && (
              <button
                onClick={handleDownloadJson}
                className="px-3 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded flex items-center gap-2 text-sm"
              >
                <Download size={16} />
                JSON Report
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
              <div className="text-gray-500 dark:text-gray-400">Loading report...</div>
            </div>
          ) : error ? (
            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded p-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="text-yellow-600 dark:text-yellow-400 mt-1 flex-shrink-0" size={20} />
                <div>
                  <h3 className="font-semibold text-yellow-800 dark:text-yellow-200">Report Unavailable</h3>
                  <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">{error}</p>
                </div>
              </div>
            </div>
          ) : (
            <pre className="font-mono text-sm whitespace-pre-wrap break-words bg-gray-50 dark:bg-gray-900 p-4 rounded border dark:border-gray-700 overflow-x-auto">
              {report}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
};
