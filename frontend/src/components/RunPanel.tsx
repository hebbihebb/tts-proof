import { Button } from './Button';
import { ProgressBar } from './ProgressBar';
import { LogArea } from './LogArea';

interface RunPanelProps {
  isProcessing: boolean;
  progress: number;
  status: string;
  onRunPipeline: () => void;
  onCancelPipeline: () => void;
  logs: Array<{
    id: string;
    message: string;
    timestamp: Date;
    type: 'info' | 'warning' | 'error' | 'success';
  }>;
  activePresetName: string;
  serverSummary: string;
}

export function RunPanel({
  isProcessing,
  progress,
  status,
  onRunPipeline,
  onCancelPipeline,
  logs,
  activePresetName,
  serverSummary,
}: RunPanelProps) {
  return (
    <section className="bg-light-crust dark:bg-catppuccin-crust border border-light-surface1 dark:border-catppuccin-surface1 rounded-xl p-5 space-y-5 shadow-sm">
      <header className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-light-text dark:text-catppuccin-text">Run</h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Ready on {serverSummary} • Preset <span className="font-semibold text-light-text dark:text-catppuccin-text">{activePresetName}</span>
          </p>
        </div>
        <div className="flex gap-2 flex-wrap">
          {isProcessing ? (
            <Button variant="outline" onClick={onCancelPipeline}>
              Cancel run
            </Button>
          ) : (
            <Button onClick={onRunPipeline}>
              Run pipeline
            </Button>
          )}
        </div>
      </header>

      <ProgressBar progress={progress} status={status} isProcessing={isProcessing} />

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,18rem)]">
        <LogArea logs={logs} />
        <div className="rounded-lg border border-light-surface1 dark:border-catppuccin-surface1 bg-light-mantle dark:bg-catppuccin-mantle p-3 text-sm text-gray-600 dark:text-gray-400 space-y-2">
          <p>Pipeline runs stream updates here in real time. Keep the browser window open to maintain the connection.</p>
          <p className="text-xs">Artifacts and detailed reports remain available in the history list below.</p>
        </div>
      </div>
    </section>
  );
}
