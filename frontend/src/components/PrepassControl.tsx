import React, { useState } from 'react';
import { Button } from './Button';
import { Upload, Play, FileText, CheckCircle, XCircle } from 'lucide-react';
import { apiService } from '../services/api';

interface PrepassControlProps {
  onPrepassComplete: (report: any) => void;
  onPrepassClear: () => void;
  prepassReport: any;
  usePrepass: boolean;
  onUsePrepassChange: (use: boolean) => void;
  isRunningPrepass: boolean;
  onRunningPrepassChange: (running: boolean) => void;
  content: string;
  modelId: string;
  endpoint: string;
  chunkSize: number;
  onLog: (message: string, type: 'info' | 'success' | 'warning' | 'error') => void;
}

export const PrepassControl: React.FC<PrepassControlProps> = ({
  onPrepassComplete,
  onPrepassClear,
  prepassReport,
  usePrepass,
  onUsePrepassChange,
  isRunningPrepass,
  onRunningPrepassChange,
  content,
  modelId,
  endpoint,
  chunkSize,
  onLog
}) => {
  const [isDragOver, setIsDragOver] = useState(false);

  const handleRunPrepass = async () => {
    if (!content) {
      onLog('No content available for prepass detection', 'warning');
      return;
    }

    onRunningPrepassChange(true);
    onLog('Starting prepass TTS problem detection...', 'info');

    try {
      const result = await apiService.runPrepass({
        content,
        model_name: modelId,
        api_base: endpoint,
        chunk_size: chunkSize
      });

      onPrepassComplete(result.report);
      onLog(`Prepass complete: Found ${result.summary.unique_problems} unique problems in ${result.summary.chunks_processed} chunks`, 'success');
      
      if (result.summary.sample_problems.length > 0) {
        onLog(`Sample problems: ${result.summary.sample_problems.slice(0, 3).join(', ')}`, 'info');
      }
    } catch (error) {
      onLog(`Prepass failed: ${error}`, 'error');
    } finally {
      onRunningPrepassChange(false);
    }
  };

  const handleFileUpload = async (file: File) => {
    if (!file.name.endsWith('.json')) {
      onLog('Please upload a JSON prepass report file', 'warning');
      return;
    }

    onLog('Uploading prepass report...', 'info');

    try {
      const result = await apiService.uploadPrepassReport(file);
      onPrepassComplete(result.report);
      onLog(`Prepass report loaded: ${result.summary.unique_problems} problems from ${result.summary.source}`, 'success');
    } catch (error) {
      onLog(`Failed to upload prepass report: ${error}`, 'error');
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileUpload(file);
    }
  };

  const getStatusIcon = () => {
    if (isRunningPrepass) {
      return <Play className="animate-spin h-4 w-4 text-blue-500" />;
    }
    if (prepassReport) {
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    }
    return <XCircle className="h-4 w-4 text-gray-400" />;
  };

  const getStatusText = () => {
    if (isRunningPrepass) {
      return 'Running prepass...';
    }
    if (prepassReport) {
      const problems = prepassReport.summary?.unique_problem_words?.length || 0;
      return `Prepass ready (${problems} problems found)`;
    }
    return 'No prepass data';
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 text-sm">
          {getStatusIcon()}
          <span className="font-medium">{getStatusText()}</span>
        </div>
        
        {prepassReport && (
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={usePrepass}
              onChange={(e) => onUsePrepassChange(e.target.checked)}
              className="rounded border-gray-300 dark:border-gray-600"
            />
            <span>Use prepass in grammar correction</span>
          </label>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        <Button
          onClick={handleRunPrepass}
          disabled={isRunningPrepass || !content}
          variant="secondary"
          size="sm"
        >
          <Play className="h-4 w-4 mr-1" />
          Run Prepass
        </Button>

        <div
          className={`relative ${isDragOver ? 'bg-blue-50 dark:bg-blue-900/20' : ''}`}
          onDrop={handleDrop}
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragOver(true);
          }}
          onDragLeave={() => setIsDragOver(false)}
        >
          <input
            type="file"
            accept=".json"
            onChange={handleFileSelect}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            id="prepass-upload"
          />
          <Button
            variant="secondary"
            size="sm"
            className={isDragOver ? 'border-blue-500 border-dashed' : ''}
          >
            <Upload className="h-4 w-4 mr-1" />
            Upload Report
          </Button>
        </div>

        {prepassReport && (
          <Button
            onClick={onPrepassClear}
            variant="secondary"
            size="sm"
          >
            <XCircle className="h-4 w-4 mr-1" />
            Clear
          </Button>
        )}
      </div>

      {prepassReport && (
        <div className="text-xs text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 p-2 rounded">
          <div className="flex items-center gap-1 mb-1">
            <FileText className="h-3 w-3" />
            <span className="font-medium">Prepass Report Summary</span>
          </div>
          <div className="grid grid-cols-2 gap-x-3 gap-y-0.5">
            <div>Source: {prepassReport.source.substring(0, 20)}...</div>
            <div>Problems: {prepassReport.summary?.unique_problem_words?.length || 0}</div>
            <div>Chunks: {prepassReport.chunks?.length || 0}</div>
            <div>Created: {new Date(prepassReport.created_at).toLocaleString()}</div>
          </div>
        </div>
      )}
    </div>
  );
};