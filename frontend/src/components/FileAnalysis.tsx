import { FileTextIcon, DatabaseIcon } from 'lucide-react';

interface FileAnalysisProps {
  totalCharacters: number;
  estimatedChunks: number;
  fileName: string;
}

export const FileAnalysis = ({
  totalCharacters,
  estimatedChunks,
  fileName
}: FileAnalysisProps) => {
  const formatNumber = (num: number) => {
    return num.toLocaleString();
  };

  const formatFileSize = (chars: number) => {
    if (chars < 1000) return `${chars} chars`;
    if (chars < 1000000) return `${(chars / 1000).toFixed(1)}K chars`;
    return `${(chars / 1000000).toFixed(1)}M chars`;
  };

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium text-light-text dark:text-catppuccin-text mb-3 flex items-center">
        <FileTextIcon className="w-4 h-4 mr-2 text-catppuccin-blue" />
        File Analysis
      </h3>
      
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm text-light-subtext1 dark:text-catppuccin-subtext1">File:</span>
          <span className="text-sm font-mono text-light-text dark:text-catppuccin-text truncate max-w-48" title={fileName}>
            {fileName}
          </span>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-sm text-light-subtext1 dark:text-catppuccin-subtext1">Total Characters:</span>
          <span className="text-sm font-semibold text-catppuccin-blue">
            {formatFileSize(totalCharacters)}
          </span>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-sm text-light-subtext1 dark:text-catppuccin-subtext1 flex items-center">
            <DatabaseIcon className="w-3 h-3 mr-1 text-catppuccin-green" />
            Processing Chunks:
          </span>
          <span className="text-sm font-semibold text-catppuccin-green">
            {formatNumber(estimatedChunks)} chunks
          </span>
        </div>
        
        {estimatedChunks > 1 && (
          <div className="text-xs text-light-subtext0 dark:text-catppuccin-subtext0 bg-catppuccin-yellow/10 border border-catppuccin-yellow/20 rounded p-2">
            💡 Large files are processed in chunks for better reliability and progress tracking
          </div>
        )}
      </div>
    </div>
  );
};