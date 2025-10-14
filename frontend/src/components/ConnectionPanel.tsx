import { useEffect, useState } from 'react';
import { Button } from './Button';
import { useAppStore, Provider } from '../state/appStore';
import { apiService } from '../services/api';

interface ConnectionPanelProps {
  onLog(message: string, type?: 'info' | 'warning' | 'error' | 'success'): void;
}

const PROVIDER_OPTIONS: { value: Provider; label: string }[] = [
  { value: 'openai-compatible', label: 'OpenAI-compatible' },
  { value: 'kobold', label: 'Kobold' },
  { value: 'other', label: 'Other' },
];

export function ConnectionPanel({ onLog }: ConnectionPanelProps) {
  const { server, setServer } = useAppStore();
  const [provider, setProvider] = useState<Provider>(server.provider);
  const [baseUrl, setBaseUrl] = useState<string>(server.baseUrl);
  const [apiKey, setApiKey] = useState<string>(server.apiKey ?? '');
  const [isFetching, setIsFetching] = useState<boolean>(false);

  useEffect(() => {
    setProvider(server.provider);
    setBaseUrl(server.baseUrl);
    setApiKey(server.apiKey ?? '');
  }, [server.provider, server.baseUrl, server.apiKey]);

  const handleFetchModels = async () => {
    const trimmedBase = baseUrl.trim();
    if (!trimmedBase) {
      onLog('Base URL is required to fetch models', 'error');
      return;
    }

    const normalizedBase = trimmedBase
      .replace(/\/?chat\/completions\/?$/i, '')
      .replace(/\/?models\/?$/i, '')
      .replace(/\/+$/g, '');

    const baseUrlToUse = normalizedBase || trimmedBase.replace(/\/+$/g, '');

    setIsFetching(true);
    try {
      const models = await apiService.fetchModels({
        provider,
        baseUrl: baseUrlToUse,
        apiKey: apiKey.trim() || undefined,
      });
      setServer({
        provider,
        baseUrl: baseUrlToUse,
        apiKey: apiKey.trim() || undefined,
        modelList: models,
        fetchedAt: Date.now(),
      });
      setBaseUrl(baseUrlToUse);
      onLog(`Fetched ${models.length} model${models.length === 1 ? '' : 's'} from server`, 'success');
    } catch (error) {
      console.error('Failed to fetch models', error);
      onLog(`Failed to fetch models: ${error instanceof Error ? error.message : String(error)}`, 'error');
    } finally {
      setIsFetching(false);
    }
  };

  return (
    <section className="bg-light-crust dark:bg-catppuccin-crust border border-light-surface1 dark:border-catppuccin-surface1 rounded-xl p-5 space-y-4 shadow-sm">
      <header>
        <h2 className="text-lg font-semibold text-light-text dark:text-catppuccin-text">Connection</h2>
        <p className="text-sm text-gray-600 dark:text-gray-400">Configure the upstream server and fetch an updated model list.</p>
      </header>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <label className="flex flex-col text-sm font-medium text-light-text dark:text-catppuccin-text">
          Server Type
          <select
            className="mt-1 rounded-lg border border-light-surface1 dark:border-catppuccin-surface1 bg-white dark:bg-catppuccin-base px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-catppuccin-mauve"
            value={provider}
            onChange={(event) => setProvider(event.target.value as Provider)}
          >
            {PROVIDER_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col text-sm font-medium text-light-text dark:text-catppuccin-text">
          Base URL
          <input
            className="mt-1 rounded-lg border border-light-surface1 dark:border-catppuccin-surface1 bg-white dark:bg-catppuccin-base px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-catppuccin-mauve"
            value={baseUrl}
            onChange={(event) => setBaseUrl(event.target.value)}
            placeholder="http://127.0.0.1:1234/v1"
            spellCheck={false}
          />
        </label>
        <label className="flex flex-col text-sm font-medium text-light-text dark:text-catppuccin-text md:col-span-2">
          API Key (optional)
          <input
            className="mt-1 rounded-lg border border-light-surface1 dark:border-catppuccin-surface1 bg-white dark:bg-catppuccin-base px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-catppuccin-mauve"
            value={apiKey}
            onChange={(event) => setApiKey(event.target.value)}
            placeholder="sk-..."
            type="password"
          />
        </label>
      </div>
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="text-xs text-gray-600 dark:text-gray-400">
          {server.modelList.length > 0 ? (
            <span>
              Last fetched {server.modelList.length} model{server.modelList.length === 1 ? '' : 's'}
              {server.fetchedAt ? ` • ${new Date(server.fetchedAt).toLocaleTimeString()}` : ''}
            </span>
          ) : (
            <span>No models fetched yet.</span>
          )}
        </div>
        <Button onClick={handleFetchModels} isLoading={isFetching}>
          Fetch models
        </Button>
      </div>
    </section>
  );
}
