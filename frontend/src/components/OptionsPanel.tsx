import { useMemo } from 'react';
import { Button } from './Button';
import { ChunkSizeControl } from './ChunkSizeControl';
import { StepToggles } from './StepToggles';

interface OptionsPanelProps {
  acronymText: string;
  onAcronymTextChange: (value: string) => void;
  onSaveAcronyms: () => Promise<void>;
  onResetAcronyms: () => void;
  isSavingAcronyms: boolean;
  hasAcronymChanges: boolean;
  chunkSize: number;
  onChunkSizeChange: (size: number) => void;
  enabledSteps: Record<string, boolean>;
  onToggleStep: (step: string) => void;
  isProcessing: boolean;
}

export function OptionsPanel({
  acronymText,
  onAcronymTextChange,
  onSaveAcronyms,
  onResetAcronyms,
  isSavingAcronyms,
  hasAcronymChanges,
  chunkSize,
  onChunkSizeChange,
  enabledSteps,
  onToggleStep,
  isProcessing,
}: OptionsPanelProps) {
  const acronymCount = useMemo(() => {
    return acronymText
      .split(/\r?\n/)
      .map((token) => token.trim())
      .filter(Boolean).length;
  }, [acronymText]);

  return (
    <section className="bg-light-crust dark:bg-catppuccin-crust border border-light-surface1 dark:border-catppuccin-surface1 rounded-xl p-5 space-y-6 shadow-sm">
      <header className="space-y-1">
        <h2 className="text-lg font-semibold text-light-text dark:text-catppuccin-text">Options</h2>
        <p className="text-sm text-gray-600 dark:text-gray-400">Tune chunking, pipeline steps, and acronym handling.</p>
      </header>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <ChunkSizeControl
            chunkSize={chunkSize}
            onChunkSizeChange={onChunkSizeChange}
            disabled={isProcessing}
          />
          <StepToggles
            enabledSteps={enabledSteps}
            onToggleStep={onToggleStep}
            disabled={isProcessing}
          />
        </div>

        <div className="space-y-5">
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-light-text dark:text-catppuccin-text">Acronym Whitelist</h3>
            <p className="text-xs text-gray-600 dark:text-gray-400">
              Preserve acronyms during hazard detection. One entry per line. Currently tracking {acronymCount} item{acronymCount === 1 ? '' : 's'}.
            </p>
            <textarea
              className="w-full h-40 rounded-lg border border-light-surface1 dark:border-catppuccin-surface1 bg-white dark:bg-catppuccin-base px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-catppuccin-mauve"
              value={acronymText}
              onChange={(event) => onAcronymTextChange(event.target.value)}
              disabled={isSavingAcronyms || isProcessing}
              spellCheck={false}
            />
            <div className="flex flex-wrap gap-2">
              <Button
                onClick={onSaveAcronyms}
                isLoading={isSavingAcronyms}
                disabled={!hasAcronymChanges || isProcessing}
              >
                Save acronyms
              </Button>
              <Button
                variant="outline"
                onClick={onResetAcronyms}
                disabled={!hasAcronymChanges || isSavingAcronyms || isProcessing}
              >
                Reset edits
              </Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
