import { Cpu, Sparkles } from 'lucide-react';

interface BlessedModelPickersProps {
  detectorModel: string;
  fixerModel: string;
  blessedModels: { detector: string[]; fixer: string[] };
  onDetectorChange: (model: string) => void;
  onFixerChange: (model: string) => void;
  disabled?: boolean;
}

export const BlessedModelPickers = ({
  detectorModel,
  fixerModel,
  blessedModels,
  onDetectorChange,
  onFixerChange,
  disabled = false
}: BlessedModelPickersProps) => {
  return (
    <div className="space-y-4">
      <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
        Model Selection
      </h3>
      
      {/* Detector Model */}
      <div className="space-y-2">
        <label className="flex items-center gap-2 text-sm font-medium text-gray-600 dark:text-gray-400">
          <Cpu className="w-4 h-4" />
          Detector Model (Phase 6)
        </label>
        <select
          value={detectorModel}
          onChange={(e) => onDetectorChange(e.target.value)}
          disabled={disabled || blessedModels.detector.length === 0}
          className={`
            w-full px-3 py-2 rounded-lg border text-sm
            bg-white dark:bg-gray-800
            border-gray-300 dark:border-gray-600
            text-gray-900 dark:text-gray-100
            focus:ring-2 focus:ring-blue-500 focus:border-blue-500
            disabled:opacity-50 disabled:cursor-not-allowed
          `}
        >
          {blessedModels.detector.length === 0 ? (
            <option value="">Loading models...</option>
          ) : (
            blessedModels.detector.map((model) => (
              <option key={model} value={model}>
                {model}
              </option>
            ))
          )}
        </select>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Small model for TTS problem detection
        </p>
      </div>
      
      {/* Fixer Model */}
      <div className="space-y-2">
        <label className="flex items-center gap-2 text-sm font-medium text-gray-600 dark:text-gray-400">
          <Sparkles className="w-4 h-4" />
          Fixer Model (Phase 8)
        </label>
        <select
          value={fixerModel}
          onChange={(e) => onFixerChange(e.target.value)}
          disabled={disabled || blessedModels.fixer.length === 0}
          className={`
            w-full px-3 py-2 rounded-lg border text-sm
            bg-white dark:bg-gray-800
            border-gray-300 dark:border-gray-600
            text-gray-900 dark:text-gray-100
            focus:ring-2 focus:ring-blue-500 focus:border-blue-500
            disabled:opacity-50 disabled:cursor-not-allowed
          `}
        >
          {blessedModels.fixer.length === 0 ? (
            <option value="">Loading models...</option>
          ) : (
            blessedModels.fixer.map((model) => (
              <option key={model} value={model}>
                {model}
              </option>
            ))
          )}
        </select>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Larger model for final text polishing
        </p>
      </div>
      
      <div className="mt-3 p-2 bg-blue-50 dark:bg-blue-900/20 rounded text-xs text-blue-700 dark:text-blue-300">
        <strong>Blessed models</strong> are validated for quality and performance in the TTS-Proof pipeline.
      </div>
    </div>
  );
};
