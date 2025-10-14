import { useEffect, useMemo, useState } from 'react';
import { Button } from './Button';
import { useAppStore } from '../state/appStore';
import { apiService, PresetListResponse } from '../services/api';

interface PresetPanelProps {
  onLog(message: string, type?: 'info' | 'warning' | 'error' | 'success'): void;
  disabled?: boolean;
}

export function PresetPanel({ onLog, disabled = false }: PresetPanelProps) {
  const {
    server,
    preset,
    overrides,
    advancedOverridesEnabled,
    setPreset,
    setPresetName,
    toggleAdvancedOverrides,
    resetModelsFromPreset,
    setOverrides,
  } = useAppStore();

  const [presetData, setPresetData] = useState<PresetListResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const modelOptions = useMemo(() => server.modelList, [server.modelList]);

  useEffect(() => {
    refreshPresets();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const refreshPresets = async () => {
    setIsLoading(true);
    try {
      const data = await apiService.getPresets();
      setPresetData(data);
      setPresetName(data.active);
      const resolvedGrammar = data.resolved?.grammar?.model ?? '';
      const resolvedDetector = data.resolved?.detector?.model ?? '';
      const resolvedFixer = data.resolved?.fixer?.model ?? '';
      resetModelsFromPreset({
        grammar: resolvedGrammar,
        detector: resolvedDetector,
        fixer: resolvedFixer,
      });
      onLog(`Loaded presets (active: ${data.active})`, 'info');
    } catch (error) {
      console.error('Failed to load presets', error);
      onLog(`Failed to load presets: ${error instanceof Error ? error.message : String(error)}`, 'warning');
    } finally {
      setIsLoading(false);
    }
  };

  const handlePresetChange = async (name: string) => {
    if (!name || name === preset.name) {
      return;
    }
    setIsLoading(true);
    try {
      const data = await apiService.activatePreset(name);
      setPresetData(data);
      setPresetName(data.active);
      const resolvedGrammar = data.resolved?.grammar?.model ?? '';
      const resolvedDetector = data.resolved?.detector?.model ?? '';
      const resolvedFixer = data.resolved?.fixer?.model ?? '';
      resetModelsFromPreset({
        grammar: resolvedGrammar,
        detector: resolvedDetector,
        fixer: resolvedFixer,
      });
      onLog(`Preset switched to ${data.active}`, 'success');
    } catch (error) {
      console.error('Failed to activate preset', error);
      onLog(`Failed to activate preset: ${error instanceof Error ? error.message : String(error)}`, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleModelChange = (stage: 'grammar' | 'detector' | 'fixer', model: string) => {
    if (!advancedOverridesEnabled) {
      return;
    }
    setOverrides({
      ...(overrides ?? {}),
      [stage]: model,
    });
    setPreset({ [stage]: model });
  };

  const handleToggleAdvanced = (event: React.ChangeEvent<HTMLInputElement>) => {
    const enabled = event.target.checked;
    toggleAdvancedOverrides(enabled);
    if (!enabled) {
      if (presetData?.resolved) {
        const resolvedGrammar = presetData.resolved.grammar?.model ?? preset.grammar;
        const resolvedDetector = presetData.resolved.detector?.model ?? preset.detector;
        const resolvedFixer = presetData.resolved.fixer?.model ?? preset.fixer;
        resetModelsFromPreset({
          grammar: resolvedGrammar,
          detector: resolvedDetector,
          fixer: resolvedFixer,
        });
      }
    }
  };

  const handleClearOverrides = () => {
    if (presetData?.resolved) {
      const resolvedGrammar = presetData.resolved.grammar?.model ?? preset.grammar;
      const resolvedDetector = presetData.resolved.detector?.model ?? preset.detector;
      const resolvedFixer = presetData.resolved.fixer?.model ?? preset.fixer;
      resetModelsFromPreset({
        grammar: resolvedGrammar,
        detector: resolvedDetector,
        fixer: resolvedFixer,
      });
    }
    toggleAdvancedOverrides(false);
    onLog('Cleared advanced overrides', 'info');
  };

  const presetNames = useMemo(() => Object.keys(presetData?.presets ?? {}).sort(), [presetData]);

  const resolvedEnvOverrides = useMemo(() => presetData?.env_overrides ?? {}, [presetData]);

  return (
    <section className="bg-light-crust dark:bg-catppuccin-crust border border-light-surface1 dark:border-catppuccin-surface1 rounded-xl p-5 space-y-4 shadow-sm">
      <header className="space-y-1">
        <h2 className="text-lg font-semibold text-light-text dark:text-catppuccin-text">Models & Preset</h2>
        <p className="text-sm text-gray-600 dark:text-gray-400">Pick a preset and adjust stage models as needed. Presets update all stages at once; overrides are optional.</p>
      </header>

      <div className="flex flex-col sm:flex-row sm:items-center gap-3">
        <label className="flex-1 text-sm font-medium text-light-text dark:text-catppuccin-text">
          Preset
          <select
            className="mt-1 w-full rounded-lg border border-light-surface1 dark:border-catppuccin-surface1 bg-white dark:bg-catppuccin-base px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-catppuccin-mauve"
            value={preset.name}
            onChange={(event) => handlePresetChange(event.target.value)}
            disabled={isLoading || disabled}
          >
            {presetNames.length === 0 && <option value="">No presets</option>}
            {presetNames.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </label>
        <Button variant="outline" onClick={refreshPresets} isLoading={isLoading} disabled={disabled}>
          Refresh
        </Button>
      </div>

      <div className="space-y-2 text-xs text-gray-600 dark:text-gray-400">
        <div>
          Active source: <span className="font-semibold text-light-text dark:text-catppuccin-text">{presetData?.active_source ?? 'default'}</span>
        </div>
        {Object.keys(resolvedEnvOverrides).length > 0 && (
          <div>
            Env overrides: {Object.entries(resolvedEnvOverrides).map(([key, value]) => `${key}=${value}`).join(', ')}
          </div>
        )}
      </div>

      <div className="flex items-center justify-between">
        <label className="flex items-center gap-2 text-sm text-light-text dark:text-catppuccin-text">
          <input
            type="checkbox"
            className="h-4 w-4 rounded border-light-surface1 dark:border-catppuccin-surface1"
            checked={advancedOverridesEnabled}
            onChange={handleToggleAdvanced}
            disabled={disabled}
          />
          Advanced overrides
        </label>
        {advancedOverridesEnabled && (
          <Button variant="outline" size="sm" onClick={handleClearOverrides} disabled={disabled}>
            Clear overrides
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {(['grammar', 'detector', 'fixer'] as const).map((stage) => (
          <label key={stage} className="flex flex-col text-sm font-medium text-light-text dark:text-catppuccin-text">
            {stage.charAt(0).toUpperCase() + stage.slice(1)}
            <select
              className="mt-1 rounded-lg border border-light-surface1 dark:border-catppuccin-surface1 bg-white dark:bg-catppuccin-base px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-catppuccin-mauve"
              value={preset[stage] ?? ''}
              onChange={(event) => handleModelChange(stage, event.target.value)}
              disabled={!advancedOverridesEnabled || disabled || modelOptions.length === 0}
            >
              <option value="" disabled>
                {modelOptions.length === 0 ? 'Fetch models first' : 'Select model'}
              </option>
              {modelOptions.map((modelId) => (
                <option key={modelId} value={modelId}>
                  {modelId}
                </option>
              ))}
            </select>
          </label>
        ))}
      </div>

      {advancedOverridesEnabled && overrides && (
        <div className="text-xs text-gray-600 dark:text-gray-400">
          Overrides in use: {Object.entries(overrides).map(([stage, model]) => `${stage} → ${model}`).join(', ')}
        </div>
      )}
    </section>
  );
}
