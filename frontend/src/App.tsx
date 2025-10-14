import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
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
import { PrepassControlHandle } from './components/PrepassControl';
// Fallback prompt if API fails to load
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
// Mock log entries
const MOCK_LOGS: Array<{
  id: string;
  message: string;
  timestamp: Date;
  type: 'info' | 'success' | 'warning' | 'error';
}> = [{
  id: '1',
  message: 'Application initialized',
  timestamp: new Date(),
  type: 'info' as const
}, {
  id: '2',
  message: 'Connected to local LLM server',
  timestamp: new Date(),
  type: 'success' as const
}];
const AppContent = () => {
  const {
    isDarkMode
  } = useTheme();
  const [file, setFile] = useState<File | null>(null);
  const [selectedModelId, setSelectedModelId] = useState<string>('');
  const [prepassModelId, setPrepassModelId] = useState<string>('');
  const [isPromptEditorOpen, setIsPromptEditorOpen] = useState<boolean>(false);
  const [isPrepassPromptEditorOpen, setIsPrepassPromptEditorOpen] = useState<boolean>(false);
  const [prompt, setPrompt] = useState<string>(FALLBACK_PROMPT);
  const [prepassPrompt, setPrepassPrompt] = useState<string>('');
  const [progress, setProgress] = useState<number>(0);
  const [status, setStatus] = useState<string>('Ready to process');
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [logs, setLogs] = useState(MOCK_LOGS);
  const [originalText, setOriginalText] = useState<string>('');
  const [processedText, setProcessedText] = useState<string>('');
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [chunkSize, setChunkSize] = useState<number>(8000);
  const [currentEndpoint, setCurrentEndpoint] = useState<string>(() => {
    const saved = localStorage.getItem('tts-proof-endpoint');
    return saved || 'http://127.0.0.1:1234/v1';
  });
  const [prepassReport, setPrepassReport] = useState<any>(null);
  const [usePrepass, setUsePrepass] = useState<boolean>(false);
  const [isRunningPrepass, setIsRunningPrepass] = useState<boolean>(false);
  const [prepassProgress, setPrepassProgress] = useState<number>(0);
  const [prepassStatus, setPrepassStatus] = useState<string>('');
  const [prepassChunksProcessed, setPrepassChunksProcessed] = useState<number>(0);
  const [prepassTotalChunks, setPrepassTotalChunks] = useState<number>(0);
  const [isRunningTest, setIsRunningTest] = useState<boolean>(false);
  const [artifactRunId, setArtifactRunId] = useState<string | null>(null);
  const [detailRunId, setDetailRunId] = useState<string | null>(null);

  // Phase 11 PR-1: Pipeline step toggles and blessed models
  const [enabledSteps, setEnabledSteps] = useState<Record<string, boolean>>({
    'prepass-basic': true,
    'prepass-advanced': true,
    'scrubber': false,  // Disabled by default
    'grammar': true,
    'detect': true,
    'apply': true,
    'fix': true
  });
  const [presets, setPresets] = useState<Record<string, Record<string, any>>>({});
  const [activePreset, setActivePreset] = useState<string>('default');
  const [resolvedPreset, setResolvedPreset] = useState<Record<string, any>>({});
  const [presetEnvOverrides, setPresetEnvOverrides] = useState<Record<string, string>>({});
  const [presetSource, setPresetSource] = useState<string>('default');
  const [isLoadingPresets, setIsLoadingPresets] = useState<boolean>(false);
  const [acronymText, setAcronymText] = useState<string>('');
  const [lastSavedAcronyms, setLastSavedAcronyms] = useState<string>('');
  const [isSavingAcronyms, setIsSavingAcronyms] = useState<boolean>(false);

  // Phase 11 PR-2: Results display state
  const [completedRunId, setCompletedRunId] = useState<string | null>(null);
  const [showReport, setShowReport] = useState<boolean>(false);
  const [showDiff, setShowDiff] = useState<boolean>(false);

  // Calculate estimated chunks based on text length and chunk size
  const calculateEstimatedChunks = (text: string, size: number) => {
    if (!text) return 0;
    return Math.ceil(text.length / size);
  };

  const presetNames = Object.keys(presets).sort();
  const resolvedGrammar = (resolvedPreset?.grammar ?? {}) as Record<string, any>;
  const resolvedDetector = (resolvedPreset?.detector ?? {}) as Record<string, any>;
  const resolvedFixer = (resolvedPreset?.fixer ?? {}) as Record<string, any>;
  const envOverrideKeys = Object.keys(presetEnvOverrides || {});
  const hasPresetEnvOverrides = envOverrideKeys.length > 0;
  const normalizedAcronymText = acronymText.replace(/\r/g, '\n');
  const hasAcronymChanges = normalizedAcronymText !== lastSavedAcronyms;
  const presetSelectValue = presetNames.includes(activePreset) ? activePreset : '';
  const acronymCount = normalizedAcronymText
    ? normalizedAcronymText
        .split('\n')
        .map((token) => token.trim())
        .filter(Boolean).length
    : 0;

  const renderModelSummary = (label: string, data?: Record<string, any>) => {
    const hasCustomConfig = data && Object.keys(data).length > 0;
    const provider = data?.provider ?? 'inherit';
    const modelName = data?.model ?? 'inherit';
    const endpoint = data?.base_url ?? data?.api_base;
    const temperature = Object.prototype.hasOwnProperty.call(data ?? {}, 'temperature') ? data?.temperature : undefined;
  const extraEntries = Object.entries(data || {}).filter(([key]) => !['provider', 'model', 'base_url', 'api_base', 'temperature'].includes(key));

    return (
      <div key={label} className="bg-light-crust dark:bg-catppuccin-crust p-3 rounded-lg border border-light-surface1 dark:border-catppuccin-surface1">
        <div className="flex items-center justify-between text-xs uppercase tracking-wide text-gray-600 dark:text-gray-400">
          <span>{label}</span>
          <span>{provider}</span>
        </div>
        <div className="mt-1 text-sm font-medium text-light-text dark:text-catppuccin-text break-words">
          {modelName}
        </div>
        {endpoint && (
          <div className="mt-1 text-xs text-gray-600 dark:text-gray-400 break-all">
            Endpoint: {endpoint}
          </div>
        )}
        {temperature !== undefined && (
          <div className="mt-1 text-xs text-gray-600 dark:text-gray-400">
            Temperature: {temperature}
          </div>
        )}
        {extraEntries.map(([key, value]) => {
          const formatted = typeof value === 'object' ? JSON.stringify(value) : String(value);
          return (
            <div key={key} className="mt-1 text-xs text-gray-600 dark:text-gray-400 break-words">
              {key}: {formatted}
            </div>
          );
        })}
        {!hasCustomConfig && (
          <div className="mt-2 text-xs italic text-gray-500 dark:text-gray-500">
            Inherits project defaults
          </div>
        )}
      </div>
    );
  };

  const handlePresetChange = async (name: string) => {
    if (name === activePreset) {
      return;
    }
    try {
      setIsLoadingPresets(true);
      const data = await apiService.activatePreset(name);
      setPresets(data.presets);
      setActivePreset(data.active);
      setResolvedPreset(data.resolved || {});
      setPresetEnvOverrides(data.env_overrides || {});
      setPresetSource(data.active_source || 'default');
      addLog(`Preset switched to ${data.active}`, 'info');
    } catch (error) {
      console.error('Failed to activate preset:', error);
      addLog(`Failed to activate preset ${name}`, 'error');
    } finally {
      setIsLoadingPresets(false);
    }
  };

  const handleSaveAcronyms = async () => {
    try {
      setIsSavingAcronyms(true);
      const entries = normalizedAcronymText
        .split('\n')
        .map((token) => token.trim())
        .filter(Boolean);
      const updated = await apiService.updateAcronyms(entries);
      const formatted = updated.join('\n');
      setAcronymText(formatted);
      setLastSavedAcronyms(formatted);
      addLog(`Acronym whitelist updated (${updated.length} items)`, 'success');
    } catch (error) {
      console.error('Failed to update acronyms:', error);
      addLog('Failed to update acronym whitelist', 'error');
    } finally {
      setIsSavingAcronyms(false);
    }
  };

  const handleResetAcronyms = () => {
    setAcronymText(lastSavedAcronyms);
    addLog('Reverted acronym edits', 'info');
  };

  // Load grammar prompt from backend on startup
  useEffect(() => {
    const loadGrammarPrompt = async () => {
      try {
        const grammarData = await apiService.getGrammarPrompt();
        setPrompt(grammarData.prompt);
        addLog(`Loaded grammar prompt from ${grammarData.source}`, 'info');
      } catch (error) {
        console.error('Failed to load grammar prompt:', error);
        addLog('Using fallback grammar prompt', 'warning');
      }
    };
    const loadPrepassPrompt = async () => {
      try {
        const prepassData = await apiService.getPrepassPrompt();
        setPrepassPrompt(prepassData.prompt);
        addLog(`Loaded prepass prompt from ${prepassData.source}`, 'info');
      } catch (error) {
        console.error('Failed to load prepass prompt:', error);
        // Set fallback prompt that matches the default in prepass.py
        const fallbackPrompt = `You are a TTS preprocessing detector working with English text. Find problematic patterns and suggest specific English replacements.

Analyze the text and return JSON with problem words AND their recommended TTS-friendly English replacements:
- Stylized/spaced letters: "F ʟ ᴀ s ʜ" → "Flash"
- Hyphenated letters: "U-N-I-T-E-D" → "United" 
- ALL-CAPS titles: "REALLY LONG TITLE" → "Really Long Title"
- Underscore caps: "WEIRD_CAPS_THING" → "Weird Caps Thing"
- Bracket stylized: "[M ᴇ ɢ ᴀ B ᴜ s ᴛ ᴇ ʀ]" → "[Mega Buster]"

Skip valid acronyms (NASA, GPU, API, etc.) and preserve code blocks.

IMPORTANT: All replacements must be in standard English. Do not add accents or non-English characters.

Return JSON only:
{ "replacements": [ { "find": "<exact_text>", "replace": "<tts_friendly_version>", "reason": "<why>" } ] }`;
        setPrepassPrompt(fallbackPrompt);
        addLog('Using fallback prepass prompt', 'warning');
      }
    };
    loadGrammarPrompt();
    loadPrepassPrompt();
  }, []);

  const refreshPresets = async () => {
    try {
      setIsLoadingPresets(true);
      const data = await apiService.getPresets();
      setPresets(data.presets);
      setActivePreset(data.active);
      setResolvedPreset(data.resolved || {});
      setPresetEnvOverrides(data.env_overrides || {});
      setPresetSource(data.active_source || 'default');
      addLog(`Loaded presets (active: ${data.active})`, 'info');
    } catch (error) {
      console.error('Failed to load presets:', error);
      addLog('Failed to load presets', 'warning');
    } finally {
      setIsLoadingPresets(false);
    }
  };

  const refreshAcronyms = async () => {
    try {
      const items = await apiService.getAcronyms();
      const formatted = items.join('\n');
      setAcronymText(formatted);
      setLastSavedAcronyms(formatted);
      addLog(`Loaded acronym whitelist (${items.length} items)`, 'info');
    } catch (error) {
      console.error('Failed to load acronyms:', error);
      addLog('Failed to load acronym whitelist', 'warning');
    }
  };

  useEffect(() => {
    refreshPresets();
    refreshAcronyms();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Save endpoint to localStorage when it changes
  useEffect(() => {
    localStorage.setItem('tts-proof-endpoint', currentEndpoint);
  }, [currentEndpoint]);

  // Initialize WebSocket connection
  useEffect(() => {
    const handleWebSocketMessage = (message: WebSocketMessage) => {
      // Handle prepass messages separately
      if (message.source === 'prepass') {
        console.log('Received prepass WebSocket message:', message);
        switch (message.type) {
          case 'progress':
            console.log(`Prepass progress: ${message.progress}% (${message.chunks_processed}/${message.total_chunks})`);
            if (message.progress !== undefined) {
              setPrepassProgress(message.progress);
            }
            if (message.chunks_processed !== undefined) {
              setPrepassChunksProcessed(message.chunks_processed);
            }
            if (message.total_chunks !== undefined) {
              setPrepassTotalChunks(message.total_chunks);
            }
            setPrepassStatus(message.message);
            addLog(message.message, 'info');
            break;
          case 'completed':
            setIsRunningPrepass(false);
            setPrepassProgress(100);
            setPrepassStatus('Prepass completed');
            if (message.result) {
              setPrepassReport(message.result);
            }
            addLog(message.message, 'success');
            // Auto-start grammar processing after prepass completion
            addLog('Starting grammar processing automatically...', 'info');
            setTimeout(() => handleProcess(), 1000); // Small delay for UI feedback
            break;
          case 'error':
            setIsRunningPrepass(false);
            setPrepassProgress(0);
            setPrepassStatus('Prepass failed');
            addLog(message.message, 'error');
            break;
        }
        return;
      }

      // Handle main processing messages
      switch (message.type) {
        case 'progress':
          if (message.progress !== undefined) {
            setProgress(message.progress);
          }
          if (message.chunks_processed && message.total_chunks) {
            setStatus(`Processing: ${message.chunks_processed}/${message.total_chunks} chunks completed`);
          } else if (message.current_step) {
            // Phase 11 PR-1: Show current step in status
            setStatus(`${message.message} (Step: ${message.current_step})`);
          } else {
            setStatus(message.message);
          }
          // Log with source context if available
          const logMsg = message.source ? `[${message.source}] ${message.message}` : message.message;
          addLog(logMsg, 'info');
          break;
        case 'chunk_complete':
          if (message.progress !== undefined) {
            setProgress(message.progress);
          }
          if (message.chunks_processed && message.total_chunks) {
            setStatus(`Chunk ${message.chunks_processed}/${message.total_chunks} completed`);
          }
          if (message.chunk?.processed_content) {
            setProcessedText(prev => prev + message.chunk.processed_content + '\n');
          }
          addLog(message.message, 'info');
          break;
        case 'chunk_error':
          addLog(message.message, 'warning');
          break;
        case 'paused':
          setIsProcessing(false);
          setStatus('Processing paused');
          addLog(message.message, 'info');
          break;
        case 'completed':
          setIsProcessing(false);
          setProgress(100);
          
          // Phase 11 PR-2: Store run_id for accessing report/diff
          if (message.run_id) {
            setCompletedRunId(message.run_id);
            setDetailRunId(message.run_id);
            addLog(`✓ Run ID: ${message.run_id}`, 'info');
          }
          
          // Phase 11 PR-1: Handle new pipeline completion with output path
          if (message.output_path) {
            setStatus('Pipeline completed successfully!');
            addLog(`✓ Output saved to: ${message.output_path}`, 'success');
            
            // Load processed text if available (for preview)
            if (message.result && typeof message.result === 'string') {
              setProcessedText(message.result);
            }
            
            // Show stats summary
            if (message.stats) {
              const statsMsg = `Stats: ${JSON.stringify(message.stats, null, 2)}`;
              addLog(statsMsg, 'info');
            }
            
            // Phase 11 PR-1: Exit code 0 = success
            if (message.exit_code === 0) {
              addLog('✓ Pipeline completed with exit code 0 (Success)', 'success');
            }
          } else if (message.total_processed) {
            setStatus(`Processing completed! Processed ${message.total_processed} chunks.`);
            addLog(`Processing completed with ${message.output_size || 0} characters`, 'success');
          } else {
            setStatus('Processing completed successfully!');
            addLog(message.message, 'success');
          }
          break;
        case 'error':
          setIsProcessing(false);
          setStatus('Processing failed');
          
          // Phase 11 PR-1: Map exit codes to user-friendly messages
          let errorType: 'error' | 'warning' = 'error';
          let friendlyMsg = message.message;
          
          if (message.exit_code === 2) {
            friendlyMsg = '⚠️ Model server unreachable. Please check that LM Studio is running.';
            errorType = 'warning';
          } else if (message.exit_code === 3) {
            friendlyMsg = `⚠️ Validation failed: ${message.message}. Output rejected to prevent data loss.`;
            errorType = 'error';
          } else if (message.exit_code === 4) {
            friendlyMsg = `⚠️ Plan parse error: ${message.message}. Check detector output format.`;
            errorType = 'error';
          }
          
          addLog(friendlyMsg, errorType);
          break;
      }
    };

    apiService.connectWebSocket(
      handleWebSocketMessage,
      (error) => {
        console.error('WebSocket error:', error);
        addLog('Connection error occurred', 'error');
      },
      () => {
        console.log('WebSocket disconnected');
        addLog('Connection closed', 'warning');
      }
    );

    return () => {
      apiService.disconnectWebSocket();
    };
  }, []);
  const handleFileSelect = async (file: File | null) => {
    setFile(file);
    if (file) {
      try {
        // Upload file to backend and get full content
        const uploadResult = await apiService.uploadFile(file);
        setOriginalText(uploadResult.full_content || uploadResult.content_preview);
        addLog(`File loaded: ${file.name} (${(uploadResult.size / 1024).toFixed(2)} KB)`, 'info');
      } catch (error) {
        console.error('Error uploading file:', error);
        addLog(`Failed to upload file: ${error}`, 'error');
        
        // Fallback: read file locally for preview
        const reader = new FileReader();
        reader.onload = e => {
          const content = e.target?.result as string;
          setOriginalText(content);
          addLog(`File loaded locally: ${file.name}`, 'info');
        };
        reader.readAsText(file);
      }
    } else {
      setOriginalText('');
      setProcessedText('');
    }
  };

  const handleProcess = async () => {
    if (!file || !originalText) {
      addLog('No file selected or content available', 'error');
      return;
    }

    try {
      setIsProcessing(true);
      setProgress(0);
      setStatus('Starting processing...');
      setProcessedText(''); // Clear previous results
      addLog('Uploading file...', 'info');

      // Upload file to get temp path
      const uploadResult = await apiService.uploadFile(file);
      addLog(`File uploaded: ${uploadResult.temp_path}`, 'info');

      // Get client ID
      const clientId = apiService.getClientId();
      setCurrentJobId(clientId);

      // Phase 11 PR-1: Build steps array from enabled steps
      const steps: string[] = ['mask']; // mask always implied/first
      Object.entries(enabledSteps).forEach(([step, enabled]) => {
        if (enabled) {
          steps.push(step);
        }
      });

      addLog(`Pipeline steps: ${steps.join(', ')}`, 'info');
      addLog(`Preset: ${activePreset}`, 'info');

      // Phase 11 PR-1: Call new unified /api/run endpoint
      const runResult = await apiService.runPipeline({
        input_path: uploadResult.temp_path,
        steps,
        report_pretty: true,
        client_id: clientId
      });

      addLog(`Pipeline run started: ${runResult.run_id}`, 'info');

    } catch (error) {
      console.error('Error starting processing:', error);
      setIsProcessing(false);
      addLog(`Failed to start processing: ${error}`, 'error');
    }
  };

  const handleCancelProcess = async () => {
    if (currentJobId) {
      try {
        await apiService.cancelJob(currentJobId);
        addLog('Processing cancelled by user', 'warning');
      } catch (error) {
        addLog(`Failed to cancel processing: ${error}`, 'error');
      }
    }
    setIsProcessing(false);
    setProgress(0);
    setStatus('Processing cancelled');
    setCurrentJobId(null);
  };

  const handleCancelPrepass = async () => {
    // This will be called by PrepassControl when cancel is clicked
    try {
      await apiService.cancelPrepass();
      addLog('Prepass cancelled by user', 'warning');
    } catch (error) {
      addLog(`Failed to cancel prepass: ${error}`, 'error');
    }
  };

  const addLog = (message: string, type: 'info' | 'warning' | 'error' | 'success') => {
    setLogs(prev => [...prev, {
      id: Date.now().toString(),
      message,
      timestamp: new Date(),
      type
    }]);
  };

  const handleToggleStep = (step: string) => {
    setEnabledSteps(prev => ({
      ...prev,
      [step]: !prev[step]
    }));
    addLog(`Toggled step: ${step} ${enabledSteps[step] ? 'OFF' : 'ON'}`, 'info');
  };

  const handleClearPreview = () => {
    setProcessedText('');
    setOriginalText('');
    setFile(null);
    addLog('Preview cleared', 'info');
  };
  const handleSaveProcessedText = () => {
    if (!processedText) return;
    // Create a download link for the processed text
    const blob = new Blob([processedText], {
      type: 'text/plain'
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = file ? `processed-${file.name}` : 'processed-text.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    addLog('Processed text saved to file', 'success');
  };

  const handleOpenTempDir = async () => {
    try {
      const { path } = await apiService.getTempDirectory();
      alert(`Temporary files are located at: ${path}\n\nThis path has been copied to your clipboard.`);
      await navigator.clipboard.writeText(path);
      addLog(`Copied temp directory path to clipboard: ${path}`, 'info');
    } catch (error) {
      addLog(`Failed to get temporary directory: ${error}`, 'error');
    }
  };

  const handleRunTest = async () => {
    if (isRunningTest) return;
    
    setIsRunningTest(true);
    addLog('Starting comprehensive test with webui_test.md...', 'info');
    
    try {
      const result = await apiService.runTest({
        model_name: selectedModelId || undefined,
        api_base: currentEndpoint,
        chunk_size: chunkSize
      });
      
      addLog(`Test completed: ${result.message}`, 'success');
      addLog(`Found ${result.summary.prepass_problems} prepass problems, processed ${result.summary.chunks_processed} chunks`, 'info');
      
      if (result.summary.errors > 0) {
        addLog(`Test had ${result.summary.errors} errors - check test_log.md for details`, 'warning');
      }
      
      // Optionally display the log content in a modal or save it
      addLog(`Test log saved to: ${result.log_file}`, 'info');
      
      // Copy log content to clipboard for easy review
      try {
        await navigator.clipboard.writeText(result.log_content);
        addLog('Test log copied to clipboard', 'info');
      } catch (clipError) {
        addLog('Could not copy to clipboard, but log is saved to file', 'warning');
      }
      
    } catch (error) {
      addLog(`Test failed: ${error}`, 'error');
    } finally {
      setIsRunningTest(false);
    }
  };

  return <div className={`min-h-screen h-full w-full transition-colors duration-300 ${isDarkMode ? 'dark bg-catppuccin-base text-catppuccin-text' : 'bg-light-base text-light-text'}`}>
      <div className="container mx-auto px-4 py-6 max-w-[1600px] pb-12">
        {/* Header */}
        <header className="flex justify-between items-center mb-6">
          <div className="flex items-center">
            <div className="w-10 h-10 bg-gradient-to-br from-catppuccin-mauve to-catppuccin-blue rounded-lg flex items-center justify-center shadow-lg mr-4">
              <span className="text-white font-bold text-lg">TP</span>
            </div>
            <div>
              <h1 className="text-3xl font-bold text-light-text dark:text-catppuccin-text">
                TTS-Proof
              </h1>
              <div className="flex items-center gap-2 ml-2">
                <span className="px-2.5 py-1 bg-catppuccin-lavender/20 dark:bg-catppuccin-lavender/10 text-catppuccin-lavender dark:text-catppuccin-lavender text-xs font-medium rounded-full">
                  v2.2.0
                </span>
                <span className="px-2.5 py-1 bg-catppuccin-mauve/20 dark:bg-catppuccin-mauve/10 text-catppuccin-mauve dark:text-catppuccin-mauve text-xs font-medium rounded-full">
                  "Responsive Fix"
                </span>
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Button variant="outline" size="sm" onClick={handleOpenTempDir} title="Open Temp Directory">
              <FolderIcon className="w-5 h-5" />
            </Button>
            <ThemeToggle />
          </div>
        </header>

        {/* Main control layout - 3 columns */}
        <div className="flex flex-col lg:flex-row gap-6 mb-6">

          {/* Column 1: Input & Setup */}
          <div className="flex-1 flex flex-col gap-6">
            <section className="bg-light-mantle dark:bg-catppuccin-mantle rounded-xl p-4 shadow-lg border border-light-surface0 dark:border-catppuccin-surface0 flex-grow">
              <h2 className="text-lg font-semibold mb-3 text-light-text dark:text-catppuccin-text">
                1. Input & Setup
              </h2>
              <div className="space-y-4">
                <FileSelector onFileSelect={handleFileSelect} />
                {file && originalText && (
                  <FileAnalysis
                    totalCharacters={originalText.length}
                    estimatedChunks={calculateEstimatedChunks(originalText, chunkSize)}
                    fileName={file.name}
                  />
                )}
                <ChunkSizeControl
                  chunkSize={chunkSize}
                  onChunkSizeChange={setChunkSize}
                  disabled={isProcessing}
                />
              </div>
            </section>
          </div>

          {/* Column 2: Pre-processing (Optional) */}
          <div className="flex-1 flex flex-col gap-6">
            <section className="bg-light-mantle dark:bg-catppuccin-mantle rounded-xl p-4 shadow-lg border border-light-surface0 dark:border-catppuccin-surface0 flex-grow">
              <h2 className="text-lg font-semibold mb-3 text-light-text dark:text-catppuccin-text">
                2. Pre-processing (Optional)
              </h2>
              <div className="space-y-4">
                <ModelPicker
                  onModelSelect={setPrepassModelId}
                  onEndpointChange={setCurrentEndpoint}
                  currentEndpoint={currentEndpoint}
                  label="Prepass Model"
                />
                <Button variant="outline" size="sm" icon={<EditIcon className="w-4 h-4" />} onClick={() => setIsPrepassPromptEditorOpen(true)}>
                  Edit Prepass Prompt
                </Button>
                <PrepassControl
                  onPrepassComplete={(report) => {
                    setPrepassReport(report);
                    setUsePrepass(true);
                  }}
                  onPrepassClear={() => setPrepassReport(null)}
                  prepassReport={prepassReport}
                  usePrepass={usePrepass}
                  onUsePrepassChange={setUsePrepass}
                  isRunningPrepass={isRunningPrepass}
                  onRunningPrepassChange={setIsRunningPrepass}
                  onPrepassCancel={handleCancelPrepass}
                  content={originalText}
                  modelId={prepassModelId || selectedModelId}
                  endpoint={currentEndpoint}
                  chunkSize={chunkSize}
                  onLog={addLog}
                  prepassProgress={prepassProgress}
                  prepassStatus={prepassStatus}
                  prepassChunksProcessed={prepassChunksProcessed}
                  prepassTotalChunks={prepassTotalChunks}
                />
              </div>
            </section>
          </div>

          {/* Column 3: Pipeline Configuration & Processing */}
          <div className="flex-1 flex flex-col gap-6">
            <section className="bg-light-mantle dark:bg-catppuccin-mantle rounded-xl p-4 shadow-lg border border-light-surface0 dark:border-catppuccin-surface0 flex-grow">
              <h2 className="text-lg font-semibold mb-3 text-light-text dark:text-catppuccin-text">
                3. Pipeline Configuration
              </h2>
              <div className="space-y-4">
                {/* Phase 11 PR-1: Step Toggles */}
                <StepToggles 
                  enabledSteps={enabledSteps}
                  onToggleStep={handleToggleStep}
                  disabled={isProcessing}
                />

                {/* Phase 14A: Preset selector and acronym whitelist */}
                <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                  <h3 className="text-md font-semibold mb-2 text-light-text dark:text-catppuccin-text">
                    Model Preset
                  </h3>
                  <div className="space-y-3">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:space-x-3 space-y-2 sm:space-y-0">
                      <select
                        className="flex-1 rounded-lg border border-light-surface1 dark:border-catppuccin-surface1 bg-white dark:bg-catppuccin-base px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-catppuccin-mauve"
                        value={presetSelectValue}
                        onChange={(event) => handlePresetChange(event.target.value)}
                        disabled={isLoadingPresets || isProcessing || presetNames.length === 0}
                      >
                        <option value="" disabled>
                          {presetNames.length === 0 ? 'No presets available' : 'Select a preset'}
                        </option>
                        {presetNames.map((name) => (
                          <option key={name} value={name}>
                            {name}
                          </option>
                        ))}
                      </select>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={refreshPresets}
                        isLoading={isLoadingPresets}
                        icon={<RotateCcw className="w-4 h-4" />}
                      >
                        Refresh
                      </Button>
                    </div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">
                      Active preset: <span className="font-semibold text-light-text dark:text-catppuccin-text">{activePreset}</span>
                      {presetSource && (
                        <span className="ml-2">• Source: {presetSource}</span>
                      )}
                      {hasPresetEnvOverrides && (
                        <span className="ml-2">
                          • Env overrides: {envOverrideKeys.join(', ')}
                        </span>
                      )}
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      {renderModelSummary('Grammar', resolvedGrammar)}
                      {renderModelSummary('Detector', resolvedDetector)}
                      {renderModelSummary('Fixer', resolvedFixer)}
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                  <h3 className="text-md font-semibold mb-2 text-light-text dark:text-catppuccin-text">
                    Acronym Whitelist
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                    Keep one acronym per line. These entries are preserved during hazard detection. Currently tracking {acronymCount} items.
                  </p>
                  <textarea
                    className="w-full h-40 rounded-lg border border-light-surface1 dark:border-catppuccin-surface1 bg-white dark:bg-catppuccin-base px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-catppuccin-mauve"
                    value={acronymText}
                    onChange={(event) => setAcronymText(event.target.value)}
                    disabled={isSavingAcronyms || isProcessing}
                    spellCheck={false}
                  />
                  <div className="mt-3 flex flex-col sm:flex-row sm:items-center sm:space-x-3 space-y-2 sm:space-y-0">
                    <Button
                      onClick={handleSaveAcronyms}
                      isLoading={isSavingAcronyms}
                      disabled={!hasAcronymChanges}
                      icon={<SaveIcon className="w-4 h-4" />}
                    >
                      Save Acronyms
                    </Button>
                    <Button
                      variant="outline"
                      onClick={handleResetAcronyms}
                      disabled={!hasAcronymChanges || isSavingAcronyms}
                      icon={<RotateCcw className="w-4 h-4" />}
                    >
                      Reset
                    </Button>
                  </div>
                </div>

                {/* Legacy: Keep old model picker and grammar prompt for backward compatibility */}
                <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                  <details className="text-sm">
                    <summary className="cursor-pointer text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200">
                      Legacy Options (Old Pipeline)
                    </summary>
                    <div className="mt-3 space-y-3">
                      <ModelPicker
                        onModelSelect={setSelectedModelId}
                        onEndpointChange={setCurrentEndpoint}
                        currentEndpoint={currentEndpoint}
                        label="Grammar Model (Legacy)"
                      />
                      <div className="bg-light-crust dark:bg-catppuccin-crust p-3 rounded-lg border border-light-surface1 dark:border-catppuccin-surface1">
                        <div className="flex justify-between items-center mb-2">
                          <h3 className="text-sm font-semibold text-light-text dark:text-catppuccin-text">
                            Grammar Prompt
                          </h3>
                          <Button variant="outline" size="sm" icon={<EditIcon className="w-4 h-4" />} onClick={() => setIsPromptEditorOpen(true)}>
                            Edit
                          </Button>
                        </div>
                        <pre className="text-xs text-light-subtext1 dark:text-catppuccin-subtext1 whitespace-pre-wrap">
                          {prompt.length > 100 ? `${prompt.substring(0, 100)}...` : prompt}
                        </pre>
                      </div>
                    </div>
                  </details>
                </div>

                {/* Processing Controls */}
                <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                  <h3 className="text-md font-semibold mb-2 text-light-text dark:text-catppuccin-text">
                    Process Document
                  </h3>
                  <ProgressBar progress={progress} status={status} isProcessing={isProcessing} />
                  <div className="mt-3 flex space-x-3">
                    {!isProcessing ? (
                      <Button onClick={handleProcess} disabled={!file} icon={<PlayIcon className="w-4 h-4" />} className="flex-1">
                        Process Text
                      </Button>
                    ) : (
                      <Button onClick={handleCancelProcess} variant="outline" icon={<Square className="w-4 h-4" />} className="flex-1">
                        Cancel
                      </Button>
                    )}
                    <Button variant="outline" onClick={handleSaveProcessedText} disabled={!processedText} icon={<SaveIcon className="w-4 h-4" />} className="flex-1">
                      Save Result
                    </Button>
                  </div>
                  <div className="mt-3">
                    <Button 
                      onClick={handleRunTest} 
                      disabled={isRunningTest || isProcessing} 
                      variant="outline" 
                      icon={<FlaskConical className="w-4 h-4" />} 
                      className="w-full"
                    >
                      {isRunningTest ? 'Running Test...' : 'Run Test (webui_test.md)'}
                    </Button>
                  </div>
                </div>
              </div>
            </section>

            {/* Phase 11 PR-2: Results Section */}
            {completedRunId && (
              <section>
                <div className="bg-light-surface dark:bg-catppuccin-surface0 rounded-lg shadow-md p-5">
                  <h3 className="text-md font-semibold mb-3 text-light-text dark:text-catppuccin-text">
                    Pipeline Results
                  </h3>
                  <div className="space-y-2">
                    <div className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                      Run ID: <code className="bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded text-xs">{completedRunId}</code>
                    </div>
                    
                    {/* Report and Diff Buttons */}
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                      <Button 
                        onClick={() => {
                          if (completedRunId) {
                            setDetailRunId(completedRunId);
                            setShowReport(true);
                          }
                        }} 
                        variant="outline" 
                        icon={<BarChart3 className="w-4 h-4" />}
                        className="w-full"
                      >
                        View Report
                      </Button>
                      <Button 
                        onClick={() => {
                          if (completedRunId) {
                            setDetailRunId(completedRunId);
                            setShowDiff(true);
                          }
                        }} 
                        variant="outline" 
                        icon={<FileText className="w-4 h-4" />}
                        className="w-full"
                      >
                        View Diff
                      </Button>
                      <Button
                        onClick={() => {
                          if (completedRunId) {
                            setDetailRunId(completedRunId);
                            setArtifactRunId(completedRunId);
                          }
                        }}
                        variant="outline"
                        icon={<FolderOpen className="w-4 h-4" />}
                        className="w-full"
                      >
                        View Artifacts
                      </Button>
                    </div>

                    {/* Artifact Downloads */}
                      <div className="pt-3 border-t dark:border-gray-700">
                      <div className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-2">Download Artifacts:</div>
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                        <button
                          onClick={async () => {
                            const blob = await apiService.downloadArtifact(completedRunId, 'output');
                            const url = window.URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = `${completedRunId}_output.md`;
                            a.click();
                          }}
                          className="text-xs px-3 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded flex items-center justify-center gap-1"
                        >
                          <Download className="w-3 h-3" />
                          Output
                        </button>
                        <button
                          onClick={async () => {
                            const blob = await apiService.downloadArtifact(completedRunId, 'plan');
                            const url = window.URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = `${completedRunId}_plan.json`;
                            a.click();
                          }}
                          className="text-xs px-3 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded flex items-center justify-center gap-1"
                        >
                          <Download className="w-3 h-3" />
                          Plan
                        </button>
                        <button
                          onClick={async () => {
                            const blob = await apiService.downloadRunArchive(completedRunId);
                            const url = window.URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = `${completedRunId}_artifacts.zip`;
                            a.click();
                          }}
                          className="text-xs px-3 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded flex items-center justify-center gap-1"
                        >
                          <Download className="w-3 h-3" />
                          All
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </section>
            )}
          </div>
        </div>

        {/* Bottom section - Preview and Logs */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <section>
            <h2 className="text-lg font-semibold mb-3 text-light-text dark:text-catppuccin-text">
              Text Preview
            </h2>
            <div className="h-80 sm:h-96 lg:h-[28rem] max-h-[32rem]">
              <PreviewWindow originalText={originalText} processedText={processedText} onDelete={handleClearPreview} />
            </div>
          </section>

          <section>
            <h2 className="text-lg font-semibold mb-3 text-light-text dark:text-catppuccin-text">
              Process Log
            </h2>
            <div className="h-80 sm:h-96 lg:h-[28rem] max-h-[32rem]">
              <LogArea logs={logs} />
            </div>
          </section>
        </div>

        <RunHistory
          onViewArtifacts={(runId) => {
            setDetailRunId(runId);
            setArtifactRunId(runId);
          }}
          onViewReport={(runId) => {
            setDetailRunId(runId);
            setShowReport(true);
          }}
          onViewDiff={(runId) => {
            setDetailRunId(runId);
            setShowDiff(true);
          }}
          onLog={(message, kind) => addLog(message, kind ?? 'info')}
          activeRunId={completedRunId}
        />
      </div>

      {/* Prompt Editor Modal */}
      <PromptEditor 
        isOpen={isPromptEditorOpen} 
        onClose={() => setIsPromptEditorOpen(false)} 
        onSave={setPrompt} 
        initialPrompt={prompt} 
        onLog={addLog}
      />
      <PromptEditor
        isOpen={isPrepassPromptEditorOpen}
        onClose={() => setIsPrepassPromptEditorOpen(false)}
        onSave={setPrepassPrompt}
        initialPrompt={prepassPrompt}
        onLog={addLog}
        isPrepass={true}
      />

      {/* Phase 11 PR-2: Report and Diff Modals */}
      {showReport && detailRunId && (
        <ReportDisplay
          runId={detailRunId}
          onClose={() => setShowReport(false)}
        />
      )}
      {showDiff && detailRunId && (
        <DiffViewer
          runId={detailRunId}
          onClose={() => setShowDiff(false)}
        />
      )}
      {artifactRunId && (
        <ArtifactBrowser
          runId={artifactRunId}
          onClose={() => setArtifactRunId(null)}
          onLog={(message, kind) => addLog(message, kind ?? 'info')}
        />
      )}
    </div>;
};
export function App() {
  return <ThemeProvider>
      <AppContent />
    </ThemeProvider>;
}