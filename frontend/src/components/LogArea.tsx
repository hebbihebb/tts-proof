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
        return 'text-catppuccin-red dark:text-catppuccin-red';
      case 'warning':
        return 'text-catppuccin-yellow dark:text-catppuccin-yellow';
      case 'success':
        return 'text-catppuccin-green dark:text-catppuccin-green';
      default:
        return 'text-light-text dark:text-catppuccin-text';
    }
  };
  return <div className="w-full h-full bg-light-mantle dark:bg-catppuccin-mantle border border-light-surface0 dark:border-catppuccin-surface0 rounded-lg overflow-hidden">
      <div className="px-2 py-1.5 bg-light-crust dark:bg-catppuccin-crust border-b border-light-surface0 dark:border-catppuccin-surface0">
        <h3 className="text-sm font-medium text-light-text dark:text-catppuccin-text">
          Process Log
        </h3>
      </div>
      <div className="p-2 h-[calc(100%-30px)] overflow-y-auto font-mono text-sm">
        {logs.length === 0 ? <p className="text-light-subtext1 dark:text-catppuccin-subtext1 italic">
            No logs yet. Start processing to see output here.
          </p> : logs.map(log => <div key={log.id} className="mb-1.5">
              <span className="text-light-subtext0 dark:text-catppuccin-subtext0">
                {log.timestamp.toLocaleTimeString()}
              </span>{' '}
              <span className={getLogTypeStyles(log.type)}>{log.message}</span>
            </div>)}
        <div ref={logEndRef} />
      </div>
    </div>;
};