import React, { useEffect, useRef } from 'react';
interface LogEntry {
  id: string;
  message: string;
  timestamp: Date;
  type: 'info' | 'warning' | 'error' | 'success';
}
interface LogAreaProps {
  logs: LogEntry[];
}
export const LogArea: React.FC<LogAreaProps> = ({
  logs
}) => {
  const logEndRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    // Scroll to bottom when logs change
    logEndRef.current?.scrollIntoView({
      behavior: 'smooth'
    });
  }, [logs]);
  const getLogTypeStyles = (type: LogEntry['type']) => {
    switch (type) {
      case 'error':
        return 'text-red-600 dark:text-red-400';
      case 'warning':
        return 'text-amber-600 dark:text-amber-400';
      case 'success':
        return 'text-green-600 dark:text-green-400';
      default:
        return 'text-gray-700 dark:text-gray-300';
    }
  };
  return <div className="w-full h-full bg-gray-50 dark:bg-dark-background border border-gray-200 dark:border-dark-border rounded-lg overflow-hidden">
      <div className="p-2 bg-gray-100 dark:bg-dark-card border-b border-gray-200 dark:border-dark-border">
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
          Process Log
        </h3>
      </div>
      <div className="p-3 h-[calc(100%-32px)] overflow-y-auto font-mono text-sm">
        {logs.length === 0 ? <p className="text-gray-500 dark:text-gray-400 italic">
            No logs yet. Start processing to see output here.
          </p> : logs.map(log => <div key={log.id} className="mb-1.5">
              <span className="text-gray-500 dark:text-gray-500">
                {log.timestamp.toLocaleTimeString()}
              </span>{' '}
              <span className={getLogTypeStyles(log.type)}>{log.message}</span>
            </div>)}
        <div ref={logEndRef} />
      </div>
    </div>;
};