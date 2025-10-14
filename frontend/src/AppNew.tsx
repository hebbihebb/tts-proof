import { useCallback, useEffect, useMemo, useState } from 'react';
import { ThemeProvider, useTheme } from './components/ThemeContext';
import { ThemeToggle } from './components/ThemeToggle';
import { PromptEditor } from './components/PromptEditor';
import { RunHistory } from './components/RunHistory';
import { ArtifactBrowser } from './components/ArtifactBrowser';
import { ReportDisplay } from './components/ReportDisplay';
import { DiffViewer } from './components/DiffViewer';
import { ConnectionPanel } from './components/ConnectionPanel';
import { PresetPanel } from './components/PresetPanel';
import { InputPanel } from './components/InputPanel';
import { OptionsPanel } from './components/OptionsPanel';
import { RunPanel } from './components/RunPanel';
import { Button } from './components/Button';
import { AppStoreProvider, useAppStore } from './state/appStore';
import { apiService, WebSocketMessage } from './services/api';

type LogKind = 'info' | 'warning' | 'error' | 'success';

interface LogEntry {
  id: string;
  message: string;
  timestamp: Date;
  type: LogKind;
}

const MAX_LOGS = 250;

const DEFAULT_ENABLED_STEPS: Record<string, boolean> = {
  'prepass-basic': true,
  'prepass-advanced': true,
  scrubber: false,
  grammar: true,
  detect: true,
  apply: true,
  fix: true,
};

const FALLBACK_PROMPT = `You are a grammar and spelling corrector for Markdown text.

Primary focus:
1) Fix grammar, spelling, and punctuation errors
2) Improve sentence flow and readability
3) Normalize spacing and formatting inconsistencies

Preservation rules:
- Never edit Markdown syntax, code blocks, inline code, links/URLs, images, or HTML tags
- Keep all Markdown structure exactly as-is
- Preserve meaning and tone
- Keep valid acronyms (NASA, GPU, API, etc.)

Output only the corrected Markdown; no explanations.`;

const calculateEstimatedChunks = (text: string, size: number): number => {
  if (!text || size <= 0) {
    return 0;
  }
  return Math.ceil(text.length / size);
};

const formatServerSummary = (provider: string, baseUrl: string): string => {
  if (!baseUrl) {
    return `${provider} • not connected`;
  }
  try {
    const url = new URL(baseUrl);
    return `${provider} • ${url.host}`;
  } catch {
    return `${provider} • ${baseUrl}`;
  }
};

const createLogId = () => `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

const AppShell = () => {
  const { isDarkMode } = useTheme();
  const { server, preset, overrides, advancedOverridesEnabled } = useAppStore();

  const [file, setFile] = useState<File | null>(null);
  const [originalText, setOriginalText] = useState('');
  const [processedText, setProcessedText] = useState('');
  const [chunkSize, setChunkSize] = useState(8000);
  const [enabledSteps, setEnabledSteps] = useState<Record<string, boolean>>(() => ({ ...DEFAULT_ENABLED_STEPS }));
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('Ready to process');
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);

  const [prompt, setPrompt] = useState(FALLBACK_PROMPT);
  const [isPromptEditorOpen, setIsPromptEditorOpen] = useState(false);

  const [acronymText, setAcronymText] = useState('');
  const [lastSavedAcronyms, setLastSavedAcronyms] = useState('');
  const [isSavingAcronyms, setIsSavingAcronyms] = useState(false);

  const [logs, setLogs] = useState<LogEntry[]>([]);

  const [artifactRunId, setArtifactRunId] = useState<string | null>(null);
  const [detailRunId, setDetailRunId] = useState<string | null>(null);
  const [showReport, setShowReport] = useState(false);
  const [showDiff, setShowDiff] = useState(false);
  const [completedRunId, setCompletedRunId] = useState<string | null>(null);

  const normalizedAcronymText = useMemo(() => acronymText.replace(/\r/g, '\n'), [acronymText]);
  const hasAcronymChanges = useMemo(
    () => normalizedAcronymText !== lastSavedAcronyms,
    [normalizedAcronymText, lastSavedAcronyms],
  );
  const estimatedChunks = useMemo(
    () => calculateEstimatedChunks(originalText, chunkSize),
    [originalText, chunkSize],
  );
  const serverSummary = useMemo(
    () => formatServerSummary(server.provider, server.baseUrl),
    [server.provider, server.baseUrl],
  );
  const overridesActive = advancedOverridesEnabled && overrides && Object.keys(overrides).length > 0;

  const addLog = useCallback((message: string, type: LogKind = 'info') => {
    setLogs((prev) => {
      const entry: LogEntry = {
        id: createLogId(),
        message,
        timestamp: new Date(),
        type,
      };
      const next = [...prev, entry];
      if (next.length > MAX_LOGS) {
        return next.slice(next.length - MAX_LOGS);
      }
      return next;
    });
  }, []);

  useEffect(() => {
    if (server.baseUrl) {
      localStorage.setItem('tts-proof-endpoint', server.baseUrl);
    }
  }, [server.baseUrl]);

  useEffect(() => {
    let isActive = true;

    const loadPrompts = async () => {
      try {
        const grammarData = await apiService.getGrammarPrompt();
        if (!isActive) {
          return;
        }
        setPrompt(grammarData.prompt);
        addLog(`Loaded grammar prompt from ${grammarData.source}`, 'info');
      } catch (error) {
        if (!isActive) {
          return;
        }
        addLog('Using fallback grammar prompt', 'warning');
      }

    };

    const loadAcronyms = async () => {
      try {
        const items = await apiService.getAcronyms();
        if (!isActive) {
          return;
        }
        const formatted = items.join('\n');
        setAcronymText(formatted);
        setLastSavedAcronyms(formatted);
        addLog(`Loaded acronym whitelist (${items.length} items)`, 'info');
      } catch (error) {
        if (!isActive) {
          return;
        }
        addLog('Failed to load acronym whitelist', 'warning');
      }
    };

    void loadPrompts();
    void loadAcronyms();

    return () => {
      isActive = false;
    };
  }, [addLog]);

  useEffect(() => {
    const handleMessage = (message: WebSocketMessage) => {
      switch (message.type) {
        case 'progress': {
          if (message.progress !== undefined) {
            setProgress(message.progress);
          }
          const base = message.message ?? 'Processing...';
          const composed = message.current_step ? `${base} (Step: ${message.current_step})` : base;
          setStatus(composed);
          if (message.message) {
            const scoped = message.source ? `[${message.source}] ${message.message}` : message.message;
            addLog(scoped, 'info');
          }
          break;
        }
        case 'chunk_complete': {
          if (message.progress !== undefined) {
            setProgress(message.progress);
          }
          if (message.chunk?.processed_content) {
            const chunkText = message.chunk.processed_content;
            setProcessedText((prev) => (prev ? `${prev}\n${chunkText}` : chunkText));
          }
          if (message.message) {
            addLog(message.message, 'info');
          }
          break;
        }
        case 'chunk_error':
          addLog(message.message ?? 'Chunk processing error', 'warning');
          break;
        case 'paused':
          setIsProcessing(false);
          setCurrentJobId(null);
          setStatus(message.message ?? 'Processing paused');
          if (message.message) {
            addLog(message.message, 'info');
          }
          break;
        case 'completed': {
          setIsProcessing(false);
          setCurrentJobId(null);
          setProgress(100);
          setStatus(message.message ?? 'Pipeline completed');
          if (message.output_path) {
            addLog(`Output saved to ${message.output_path}`, 'success');
          }
          if (message.exit_code !== undefined) {
            addLog(`Exit code ${message.exit_code}`, message.exit_code === 0 ? 'success' : 'warning');
          }
          if (message.stats) {
            addLog(`Stats: ${JSON.stringify(message.stats)}`, 'info');
          }
          const runId = message.run_id;
          if (runId) {
            setCompletedRunId(runId);
            setDetailRunId(runId);
            void (async () => {
              try {
                const blob = await apiService.downloadArtifact(runId, 'output');
                const text = await blob.text();
                setProcessedText(text);
                addLog(`Loaded output preview for ${runId}`, 'success');
              } catch (error) {
                const reason = error instanceof Error ? error.message : String(error);
                addLog(`Failed to load output preview: ${reason}`, 'warning');
              }
            })();
          }
          break;
        }
        case 'error':
          setIsProcessing(false);
          setCurrentJobId(null);
          setStatus(message.message ?? 'Processing failed');
          addLog(message.message ?? 'Processing failed', 'error');
          break;
      }
    };

    apiService.connectWebSocket(
      handleMessage,
      (error) => {
        const type = 'type' in error ? (error as ErrorEvent).type : 'unknown';
        addLog(`WebSocket error: ${type}`, 'error');
      },
      () => {
        addLog('WebSocket connection closed', 'warning');
      },
    );

    return () => {
      apiService.disconnectWebSocket();
    };
  }, [addLog]);

  const handleFileSelect = useCallback(async (selected: File | null) => {
    setFile(selected);
    setProcessedText('');
    setCompletedRunId(null);
    setDetailRunId(null);
    setShowReport(false);
    setShowDiff(false);
    setArtifactRunId(null);

    if (!selected) {
      setOriginalText('');
      setStatus('Ready to process');
      return;
    }

    try {
      addLog(`Loading ${selected.name} (${(selected.size / 1024).toFixed(1)} KB)`, 'info');
      const uploadResult = await apiService.uploadFile(selected);
      const content = uploadResult.full_content || uploadResult.content_preview || '';
      setOriginalText(content);
      setStatus(`Loaded ${selected.name}`);
      addLog(`File ready: ${uploadResult.temp_path}`, 'success');
    } catch (error) {
      const reason = error instanceof Error ? error.message : String(error);
      addLog(`Failed to upload file: ${reason}`, 'error');
      const reader = new FileReader();
      reader.onload = (event) => {
        const content = (event.target?.result as string) ?? '';
        setOriginalText(content);
        setStatus(`Loaded ${selected.name}`);
      };
      reader.readAsText(selected);
    }
  }, [addLog]);

  const handleClearPreview = useCallback(() => {
    setFile(null);
    setOriginalText('');
    setProcessedText('');
    setStatus('Ready to process');
    addLog('Cleared loaded input', 'info');
  }, [addLog]);

  const handleToggleStep = useCallback((step: string) => {
    setEnabledSteps((prev) => {
      const nextValue = !prev[step];
      const next = { ...prev, [step]: nextValue };
      addLog(`Step ${step} ${nextValue ? 'enabled' : 'disabled'}`, 'info');
      return next;
    });
  }, [addLog]);

  const handleSaveAcronyms = useCallback(async () => {
    try {
      setIsSavingAcronyms(true);
      const items = normalizedAcronymText
        .split('\n')
        .map((token) => token.trim())
        .filter(Boolean);
      const updated = await apiService.updateAcronyms(items);
      const formatted = updated.join('\n');
      setAcronymText(formatted);
      setLastSavedAcronyms(formatted);
      addLog(`Acronym whitelist saved (${updated.length} items)`, 'success');
    } catch (error) {
      const reason = error instanceof Error ? error.message : String(error);
      addLog(`Failed to save acronyms: ${reason}`, 'error');
    } finally {
      setIsSavingAcronyms(false);
    }
  }, [normalizedAcronymText, addLog]);

  const handleResetAcronyms = useCallback(() => {
    setAcronymText(lastSavedAcronyms);
    addLog('Reverted acronym edits', 'info');
  }, [lastSavedAcronyms, addLog]);

  const stepsForRun = useMemo(() => {
    const steps: string[] = ['mask'];
    for (const [key, enabled] of Object.entries(enabledSteps)) {
      if (enabled) {
        steps.push(key);
      }
    }
    return steps;
  }, [enabledSteps]);

  const handleProcess = async () => {
    if (!file || !originalText) {
      addLog('Select a file before running the pipeline', 'error');
      return;
    }

    if (!preset.grammar && !advancedOverridesEnabled) {
      addLog('Preset has no grammar model configured', 'error');
      return;
    }

    try {
      setIsProcessing(true);
      setStatus('Starting pipeline...');
      setProgress(0);
      setProcessedText('');
      setCompletedRunId(null);
      setDetailRunId(null);
      setShowReport(false);
      setShowDiff(false);
      setArtifactRunId(null);

      addLog(`Running pipeline with preset ${preset.name}`, 'info');

      const uploadResult = await apiService.uploadFile(file);
      const clientId = apiService.getClientId();
      setCurrentJobId(clientId);

      const runResponse = await apiService.runPipeline({
        input_path: uploadResult.temp_path,
        steps: stepsForRun,
        models: {
          grammar: preset.grammar,
          detector: preset.detector,
          fixer: preset.fixer,
        },
        server: {
          provider: server.provider,
          baseUrl: server.baseUrl,
          apiKey: server.apiKey,
        },
        preset: preset.name,
        overrides: advancedOverridesEnabled ? overrides : undefined,
        report_pretty: true,
        client_id: clientId,
      });

      addLog(`Pipeline started (run ${runResponse.run_id})`, 'success');
      setStatus('Pipeline running...');
    } catch (error) {
      const reason = error instanceof Error ? error.message : String(error);
      setIsProcessing(false);
      setCurrentJobId(null);
      setStatus('Failed to start pipeline');
      addLog(`Failed to start pipeline: ${reason}`, 'error');
    }
  };

  const handleCancelProcess = async () => {
    if (!currentJobId) {
      setIsProcessing(false);
      setStatus('No active run');
      return;
    }

    try {
      setStatus('Cancelling run...');
      const cancelled = await apiService.cancelJob(currentJobId);
      if (cancelled) {
        addLog('Processing cancelled', 'warning');
      } else {
        addLog('Cancellation request failed', 'warning');
      }
    } catch (error) {
      const reason = error instanceof Error ? error.message : String(error);
      addLog(`Failed to cancel run: ${reason}`, 'error');
    } finally {
      setIsProcessing(false);
      setProgress(0);
      setCurrentJobId(null);
      setStatus('Processing cancelled');
    }
  };

  return (
    <div
      className={`min-h-screen w-full ${
        isDarkMode ? 'dark bg-catppuccin-base text-catppuccin-text' : 'bg-light-base text-light-text'
      }`}
    >
      <div className="sticky top-0 z-40 border-b border-light-surface1 dark:border-catppuccin-surface1 bg-light-crust/90 dark:bg-catppuccin-crust/90 backdrop-blur">
        <div className="max-w-5xl mx-auto flex items-center justify-between gap-4 px-4 py-3 sm:px-6 lg:px-8">
          <div className="flex flex-wrap items-center gap-2 text-xs uppercase tracking-wide text-gray-600 dark:text-gray-400">
            <span className="rounded-full bg-light-surface0 px-2 py-1 text-light-text dark:bg-catppuccin-surface0 dark:text-catppuccin-text">
              {serverSummary}
            </span>
            <span className="rounded-full bg-light-surface0 px-2 py-1 text-light-text dark:bg-catppuccin-surface0 dark:text-catppuccin-text">
              Preset {preset.name || '—'}
            </span>
            {overridesActive && (
              <span className="rounded-full bg-catppuccin-yellow/20 px-2 py-1 text-catppuccin-yellow">
                Overrides active
              </span>
            )}
          </div>
          <ThemeToggle />
        </div>
      </div>

      <main className="max-w-5xl mx-auto space-y-6 px-4 pb-28 pt-6 sm:px-6 lg:px-8">
        <header className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">TTS-Proof</h1>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Local-first Markdown cleanup with LLM assist
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={() => setIsPromptEditorOpen(true)}>
              Edit grammar prompt
            </Button>
          </div>
        </header>

        <ConnectionPanel onLog={addLog} />
        <PresetPanel onLog={addLog} disabled={isProcessing} />
        <InputPanel
          file={file}
          onFileSelect={handleFileSelect}
          originalText={originalText}
          processedText={processedText}
          estimatedChunks={estimatedChunks}
          chunkSize={chunkSize}
          onClearPreview={handleClearPreview}
        />
        <OptionsPanel
          acronymText={acronymText}
          onAcronymTextChange={setAcronymText}
          onSaveAcronyms={handleSaveAcronyms}
          onResetAcronyms={handleResetAcronyms}
          isSavingAcronyms={isSavingAcronyms}
          hasAcronymChanges={hasAcronymChanges}
          chunkSize={chunkSize}
          onChunkSizeChange={setChunkSize}
          enabledSteps={enabledSteps}
          onToggleStep={handleToggleStep}
          isProcessing={isProcessing}
        />
        <RunPanel
          isProcessing={isProcessing}
          progress={progress}
          status={status}
          onRunPipeline={handleProcess}
          onCancelPipeline={handleCancelProcess}
          logs={logs}
          activePresetName={preset.name || '—'}
          serverSummary={serverSummary}
        />
        <RunHistory
          activeRunId={completedRunId}
          onViewArtifacts={(runId) => setArtifactRunId(runId)}
          onViewReport={(runId) => {
            setDetailRunId(runId);
            setShowReport(true);
          }}
          onViewDiff={(runId) => {
            setDetailRunId(runId);
            setShowDiff(true);
          }}
          onLog={(message, kind) => addLog(message, kind ?? 'info')}
        />
      </main>

      <div className="sticky bottom-0 z-40 border-t border-light-surface1 bg-light-crust/95 backdrop-blur dark:border-catppuccin-surface1 dark:bg-catppuccin-crust/95">
        <div className="max-w-5xl mx-auto flex items-center justify-between gap-3 px-4 py-3 sm:px-6 lg:px-8">
          <span className="truncate text-sm text-gray-600 dark:text-gray-400">{status}</span>
          {isProcessing ? (
            <Button variant="outline" onClick={handleCancelProcess}>
              Cancel run
            </Button>
          ) : (
            <Button onClick={handleProcess} disabled={!file || !originalText}>
              Run pipeline
            </Button>
          )}
        </div>
      </div>

      <PromptEditor
        isOpen={isPromptEditorOpen}
        onClose={() => setIsPromptEditorOpen(false)}
        onSave={setPrompt}
        initialPrompt={prompt}
        onLog={addLog}
      />

      {showReport && detailRunId && (
        <ReportDisplay runId={detailRunId} onClose={() => setShowReport(false)} />
      )}
      {showDiff && detailRunId && (
        <DiffViewer runId={detailRunId} onClose={() => setShowDiff(false)} />
      )}
      {artifactRunId && (
        <ArtifactBrowser
          runId={artifactRunId}
          onClose={() => setArtifactRunId(null)}
          onLog={(message, kind) => addLog(message, kind ?? 'info')}
        />
      )}
    </div>
  );
};

export function App() {
  return (
    <ThemeProvider>
      <AppStoreProvider>
        <AppShell />
      </AppStoreProvider>
    </ThemeProvider>
  );
}
