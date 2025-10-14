import { FileSelector } from './FileSelector';
import { PreviewWindow } from './PreviewWindow';
import { FileAnalysis } from './FileAnalysis';

interface InputPanelProps {
  file: File | null;
  onFileSelect: (file: File | null) => void;
  originalText: string;
  processedText: string;
  estimatedChunks: number;
  chunkSize: number;
  onClearPreview: () => void;
}

export function InputPanel({
  file,
  onFileSelect,
  originalText,
  processedText,
  estimatedChunks,
  chunkSize,
  onClearPreview,
}: InputPanelProps) {
  const fileName = file?.name ?? 'No file selected';
  const totalCharacters = originalText ? originalText.length : 0;

  return (
    <section className="bg-light-crust dark:bg-catppuccin-crust border border-light-surface1 dark:border-catppuccin-surface1 rounded-xl p-5 space-y-5 shadow-sm">
      <header className="space-y-1">
        <h2 className="text-lg font-semibold text-light-text dark:text-catppuccin-text">Input</h2>
        <p className="text-sm text-gray-600 dark:text-gray-400">Drop Markdown files or paste text to prepare a run.</p>
      </header>

      <FileSelector onFileSelect={onFileSelect} />

      {originalText && (
        <div className="grid gap-4 lg:grid-cols-[minmax(0,18rem)_minmax(0,1fr)]">
          <div className="space-y-4">
            <FileAnalysis
              totalCharacters={totalCharacters}
              estimatedChunks={estimatedChunks}
              fileName={fileName}
            />
            <div className="text-xs text-gray-600 dark:text-gray-400">
              Chunk size: {chunkSize.toLocaleString()} characters
            </div>
          </div>
          <PreviewWindow
            originalText={originalText}
            processedText={processedText}
            onDelete={onClearPreview}
          />
        </div>
      )}
    </section>
  );
}
