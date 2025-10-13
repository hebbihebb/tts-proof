import { CheckSquare, Square } from 'lucide-react';

interface StepTogglesProps {
  enabledSteps: Record<string, boolean>;
  onToggleStep: (step: string) => void;
  disabled?: boolean;
}

interface StepInfo {
  key: string;
  label: string;
  description: string;
  phase: string;
}

const PIPELINE_STEPS: StepInfo[] = [
  {
    key: 'prepass-basic',
    label: 'Unicode Normalization',
    description: 'Fix spacing, hyphenation, control characters',
    phase: 'Phase 2'
  },
  {
    key: 'prepass-advanced',
    label: 'Advanced Normalization',
    description: 'Casing, punctuation, ellipsis standardization',
    phase: 'Phase 2+'
  },
  {
    key: 'scrubber',
    label: 'Content Scrubbing',
    description: 'Remove author notes, navigation, promos',
    phase: 'Phase 3'
  },
  {
    key: 'grammar',
    label: 'Grammar Assist (Legacy)',
    description: 'Optional LLM-based grammar correction',
    phase: 'Phase 5'
  },
  {
    key: 'detect',
    label: 'TTS Detection',
    description: 'Detect TTS problems with small model',
    phase: 'Phase 6'
  },
  {
    key: 'apply',
    label: 'Apply Fixes',
    description: 'Apply detected fixes with validation',
    phase: 'Phase 7'
  },
  {
    key: 'fix',
    label: 'Light Polish',
    description: 'Final polish on text nodes with larger model',
    phase: 'Phase 8'
  }
];

export const StepToggles = ({ enabledSteps, onToggleStep, disabled = false }: StepTogglesProps) => {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
          Pipeline Steps
        </h3>
        <span className="text-xs text-gray-500 dark:text-gray-400">
          mask (Phase 1) always enabled
        </span>
      </div>
      
      <div className="space-y-1.5">
        {PIPELINE_STEPS.map((step) => {
          const isEnabled = enabledSteps[step.key] ?? false;
          
          return (
            <button
              key={step.key}
              type="button"
              onClick={() => !disabled && onToggleStep(step.key)}
              disabled={disabled}
              className={`
                w-full flex items-start gap-3 p-3 rounded-lg border transition-all
                ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:border-blue-400 dark:hover:border-blue-500'}
                ${isEnabled 
                  ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800' 
                  : 'bg-gray-50 dark:bg-gray-800/50 border-gray-200 dark:border-gray-700'
                }
              `}
            >
              <div className="flex-shrink-0 mt-0.5">
                {isEnabled ? (
                  <CheckSquare className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                ) : (
                  <Square className="w-5 h-5 text-gray-400 dark:text-gray-500" />
                )}
              </div>
              
              <div className="flex-1 text-left">
                <div className="flex items-center justify-between gap-2">
                  <span className={`text-sm font-medium ${
                    isEnabled 
                      ? 'text-blue-900 dark:text-blue-100' 
                      : 'text-gray-700 dark:text-gray-300'
                  }`}>
                    {step.label}
                  </span>
                  <span className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
                    {step.phase}
                  </span>
                </div>
                <p className={`text-xs mt-0.5 ${
                  isEnabled 
                    ? 'text-blue-700 dark:text-blue-300' 
                    : 'text-gray-600 dark:text-gray-400'
                }`}>
                  {step.description}
                </p>
              </div>
            </button>
          );
        })}
      </div>
      
      <div className="mt-3 p-2 bg-gray-100 dark:bg-gray-800 rounded text-xs text-gray-600 dark:text-gray-400">
        <strong>Note:</strong> Phase 1 (Markdown masking) is always applied automatically to protect code blocks, links, and structural elements.
      </div>
    </div>
  );
};
