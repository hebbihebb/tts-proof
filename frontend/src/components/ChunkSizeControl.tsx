import { SettingsIcon } from 'lucide-react';

interface ChunkSizeControlProps {
  chunkSize: number;
  onChunkSizeChange: (size: number) => void;
  disabled?: boolean;
}

export const ChunkSizeControl = ({
  chunkSize,
  onChunkSizeChange,
  disabled = false
}: ChunkSizeControlProps) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value);
    if (!isNaN(value) && value > 0) {
      onChunkSizeChange(value);
    }
  };

  const presets = [
    { label: 'Small (4K)', value: 4000 },
    { label: 'Default (8K)', value: 8000 },
    { label: 'Large (12K)', value: 12000 },
    { label: 'Extra Large (16K)', value: 16000 }
  ];

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium text-light-text dark:text-catppuccin-text mb-3 flex items-center">
        <SettingsIcon className="w-4 h-4 mr-2 text-catppuccin-mauve" />
        Chunk Size
      </h3>
      
      <div className="space-y-3">
        <div className="flex items-center space-x-2">
          <input
            type="number"
            min="1000"
            max="32000"
            step="1000"
            value={chunkSize}
            onChange={handleChange}
            disabled={disabled}
            className="flex-1 px-3 py-2 border border-light-surface1 dark:border-catppuccin-surface1 rounded-md 
                     bg-light-crust dark:bg-catppuccin-crust text-light-text dark:text-catppuccin-text
                     focus:ring-2 focus:ring-catppuccin-mauve focus:border-catppuccin-mauve
                     disabled:opacity-50 disabled:cursor-not-allowed text-sm
                     transition-colors duration-200"
            placeholder="8000"
          />
          <span className="text-xs text-light-subtext1 dark:text-catppuccin-subtext1 whitespace-nowrap">
            characters
          </span>
        </div>

        <div className="grid grid-cols-2 gap-1">
          {presets.map((preset) => (
            <button
              key={preset.value}
              onClick={() => onChunkSizeChange(preset.value)}
              disabled={disabled}
              className={`px-2 py-1 text-xs rounded border transition-colors duration-200
                ${chunkSize === preset.value
                  ? 'bg-catppuccin-mauve/20 border-catppuccin-mauve text-catppuccin-mauve'
                  : 'bg-light-crust dark:bg-catppuccin-crust border-light-surface1 dark:border-catppuccin-surface1 text-light-subtext1 dark:text-catppuccin-subtext1 hover:bg-light-surface0 dark:hover:bg-catppuccin-surface0'
                }
                disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {preset.label}
            </button>
          ))}
        </div>

        <div className="text-xs text-light-subtext0 dark:text-catppuccin-subtext0 bg-catppuccin-blue/10 border border-catppuccin-blue/20 rounded p-2">
          💡 Smaller chunks = more API calls but better progress tracking. Larger chunks = fewer calls but less granular progress.
        </div>
      </div>
    </div>
  );
};