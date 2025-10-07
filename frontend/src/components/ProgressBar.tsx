import React from 'react';
interface ProgressBarProps {
  progress: number; // 0 to 100
  status: string;
  isProcessing: boolean;
}
export const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  status,
  isProcessing
}) => {
  return <div className="w-full">
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {isProcessing ? 'Processing' : 'Ready'}
        </span>
        <span className="text-sm text-gray-500 dark:text-gray-400">
          {progress}%
        </span>
      </div>
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5 overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-300 ${isProcessing ? 'bg-primary-500 animate-pulse' : progress === 100 ? 'bg-green-500' : 'bg-primary-500'}`} style={{
        width: `${progress}%`
      }}></div>
      </div>
      <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">{status}</p>
    </div>;
};