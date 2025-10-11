import { Loader2 } from 'lucide-react';

interface ProgressBarProps {
  progress: number; // 0 to 100
  status: string;
  isProcessing: boolean;
}

export const ProgressBar = ({
  progress,
  status,
  isProcessing
}: ProgressBarProps) => {
  return (
    <div className="w-full">
      <div className="flex justify-between items-center mb-2">
        <div className="flex items-center gap-2">
          {isProcessing && (
            <Loader2 className="animate-spin h-4 w-4 text-catppuccin-mauve" />
          )}
          <span className="text-sm font-medium text-light-text dark:text-catppuccin-text">
            {isProcessing ? 'Processing' : 'Ready'}
          </span>
        </div>
        <span className="text-sm text-light-subtext1 dark:text-catppuccin-subtext1">
          {progress}%
        </span>
      </div>
      <div className="w-full bg-light-surface1 dark:bg-catppuccin-surface1 rounded-full h-2.5 overflow-hidden shadow-inner">
        <div 
          className={`h-full rounded-full transition-all duration-500 ${
            isProcessing 
              ? 'bg-gradient-to-r from-catppuccin-mauve to-catppuccin-blue animate-pulse shadow-sm' 
              : progress === 100 
                ? 'bg-gradient-to-r from-catppuccin-green to-catppuccin-teal shadow-sm' 
                : 'bg-gradient-to-r from-catppuccin-mauve to-catppuccin-blue shadow-sm'
          }`} 
          style={{ width: `${progress}%` }}
        />
      </div>
      <p className="mt-2 text-sm text-light-subtext1 dark:text-catppuccin-subtext1">{status}</p>
    </div>
  );
};