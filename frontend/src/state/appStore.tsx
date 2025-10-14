import React, { createContext, useContext, useMemo, useState } from 'react';

export type Provider = 'openai-compatible' | 'kobold' | 'other';

export interface ServerConfig {
  provider: Provider;
  baseUrl: string;
  apiKey?: string;
  modelList: string[];
  fetchedAt?: number;
}

export interface PresetSelection {
  name: string;
  grammar: string;
  detector: string;
  fixer: string;
}

export interface AppState {
  server: ServerConfig;
  preset: PresetSelection;
  overrides?: Partial<PresetSelection>;
  advancedOverridesEnabled: boolean;
}

interface AppStore extends AppState {
  setServer(update: Partial<ServerConfig>): void;
  setPreset(update: Partial<PresetSelection>): void;
  setPresetName(name: string): void;
  setOverrides(update?: Partial<PresetSelection>): void;
  toggleAdvancedOverrides(enabled: boolean): void;
  resetModelsFromPreset(models: Pick<PresetSelection, 'grammar' | 'detector' | 'fixer'>): void;
}

const defaultServer: ServerConfig = {
  provider: 'openai-compatible',
  baseUrl: 'http://127.0.0.1:1234/v1',
  apiKey: undefined,
  modelList: [],
  fetchedAt: undefined,
};

const defaultPreset: PresetSelection = {
  name: 'default',
  grammar: '',
  detector: '',
  fixer: '',
};

const AppStoreContext = createContext<AppStore | undefined>(undefined);

export function AppStoreProvider({ children }: { children: React.ReactNode }) {
  const [server, setServerState] = useState<ServerConfig>(defaultServer);
  const [preset, setPresetState] = useState<PresetSelection>(defaultPreset);
  const [overrides, setOverridesState] = useState<Partial<PresetSelection> | undefined>();
  const [advancedOverridesEnabled, setAdvancedOverridesEnabled] = useState<boolean>(false);

  const value = useMemo<AppStore>(() => ({
    server,
    preset,
    overrides,
    advancedOverridesEnabled,
    setServer(update) {
      setServerState((prev) => ({
        ...prev,
        ...update,
        modelList: update.modelList ?? prev.modelList,
        fetchedAt: update.fetchedAt ?? prev.fetchedAt,
      }));
    },
    setPreset(update) {
      setPresetState((prev) => ({
        ...prev,
        ...update,
      }));
    },
    setPresetName(name) {
      setPresetState((prev) => ({
        ...prev,
        name,
      }));
    },
    setOverrides(update) {
      setOverridesState(update && Object.keys(update).length > 0 ? update : undefined);
    },
    toggleAdvancedOverrides(enabled) {
      setAdvancedOverridesEnabled(enabled);
      if (!enabled) {
        setOverridesState(undefined);
      }
    },
    resetModelsFromPreset(models) {
      setPresetState((prev) => ({
        ...prev,
        ...models,
      }));
      setOverridesState(undefined);
    },
  }), [server, preset, overrides, advancedOverridesEnabled]);

  return (
    <AppStoreContext.Provider value={value}>{children}</AppStoreContext.Provider>
  );
}

export function useAppStore(): AppStore {
  const ctx = useContext(AppStoreContext);
  if (!ctx) {
    throw new Error('useAppStore must be used within an AppStoreProvider');
  }
  return ctx;
}
