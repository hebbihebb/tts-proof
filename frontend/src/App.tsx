import { useState, useEffect } from 'react';
import { ThemeProvider, useTheme } from './components/ThemeContext';
import { ThemeToggle } from './components/ThemeToggle';
import { FileSelector } from './components/FileSelector';
import { ModelPicker } from './components/ModelPicker';
import { PromptEditor } from './components/PromptEditor';
import { ProgressBar } from './components/ProgressBar';
import { LogArea } from './components/LogArea';
import { PreviewWindow } from './components/PreviewWindow';
import { Button } from './components/Button';
import { FileAnalysis } from './components/FileAnalysis';
import { ChunkSizeControl } from './components/ChunkSizeControl';
import { PrepassControl } from './components/PrepassControl';
import { EditIcon, PlayIcon, SaveIcon, Square, FolderIcon } from 'lucide-react';
import { apiService, WebSocketMessage } from './services/api';
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

  // Calculate estimated chunks based on text length and chunk size
  const calculateEstimatedChunks = (text: string, size: number) => {
    if (!text) return 0;
    return Math.ceil(text.length / size);
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
        const fallbackPrompt = `You are a TTS preprocessing detector. Find problematic patterns and suggest specific replacements.

Analyze the text and return JSON with problem words AND their recommended TTS-friendly replacements:
- Stylized/spaced letters: "F ʟ ᴀ s ʜ" → "Flash"
- Hyphenated letters: "U-N-I-T-E-D" → "United" 
- ALL-CAPS titles: "REALLY LONG TITLE" → "Really Long Title"
- Underscore caps: "WEIRD_CAPS_THING" → "Weird Caps Thing"
- Bracket stylized: "[M ᴇ ɢ ᴀ B ᴜ s ᴛ ᴇ ʀ]" → "[Mega Buster]"

Skip valid acronyms (NASA, GPU, API, etc.) and preserve code blocks.

Return JSON only:
{ "replacements": [ { "find": "<exact_text>", "replace": "<tts_friendly_version>", "reason": "<why>" } ] }`;
        setPrepassPrompt(fallbackPrompt);
        addLog('Using fallback prepass prompt', 'warning');
      }
    };
    loadGrammarPrompt();
    loadPrepassPrompt();
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
          } else {
            setStatus(message.message);
          }
          addLog(message.message, 'info');
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
          if (message.total_processed) {
            setStatus(`Processing completed! Processed ${message.total_processed} chunks.`);
          } else {
            setStatus('Processing completed successfully!');
          }
          
          // The result is now built chunk-by-chunk, so we just log the final message.
          addLog(`Processing completed with ${message.output_size || 0} characters`, 'success');
          break;
        case 'error':
          setIsProcessing(false);
          setStatus('Processing failed');
          addLog(message.message, 'error');
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

    if (!selectedModelId) {
      addLog('No model selected', 'error');
      return;
    }

    try {
      setIsProcessing(true);
      setProgress(0);
      setStatus('Starting processing...');
      setProcessedText(''); // Clear previous results
      addLog('Sending file for processing...', 'info');

      // Set the job ID early (it's the same as client ID) to avoid race condition
      const clientId = apiService.getClientId();
      setCurrentJobId(clientId);
      console.log('Set currentJobId to:', clientId);

      // Start processing job
      const jobResult = await apiService.startProcessing({
        content: originalText,
        model_name: selectedModelId,
        api_base: currentEndpoint,
        prompt_template: prompt,
        stream: false,
        show_progress: true,
        chunk_size: chunkSize,
        preview_chars: 500,
        use_prepass: usePrepass,
        prepass_report: usePrepass ? prepassReport : undefined
      });

      addLog(`Processing job started: ${jobResult.job_id}`, 'info');

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
            <Button variant="outline" size="icon" onClick={handleOpenTempDir} title="Open Temp Directory">
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

          {/* Column 3: Main Processing */}
          <div className="flex-1 flex flex-col gap-6">
            <section className="bg-light-mantle dark:bg-catppuccin-mantle rounded-xl p-4 shadow-lg border border-light-surface0 dark:border-catppuccin-surface0 flex-grow">
              <h2 className="text-lg font-semibold mb-3 text-light-text dark:text-catppuccin-text">
                3. Main Processing
              </h2>
              <div className="space-y-4">
                <ModelPicker
                  onModelSelect={setSelectedModelId}
                  onEndpointChange={setCurrentEndpoint}
                  currentEndpoint={currentEndpoint}
                  label="Grammar Model"
                />
                <div className="bg-light-crust dark:bg-catppuccin-crust p-3 rounded-lg border border-light-surface1 dark:border-catppuccin-surface1">
                  <div className="flex justify-between items-center mb-2">
                    <h3 className="text-md font-semibold text-light-text dark:text-catppuccin-text">
                      Grammar Prompt
                    </h3>
                    <Button variant="outline" size="sm" icon={<EditIcon className="w-4 h-4" />} onClick={() => setIsPromptEditorOpen(true)}>
                      Edit
                    </Button>
                  </div>
                  <pre className="text-sm text-light-subtext1 dark:text-catppuccin-subtext1 whitespace-pre-wrap">
                    {prompt.length > 100 ? `${prompt.substring(0, 100)}...` : prompt}
                  </pre>
                </div>
                <div>
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
                </div>
              </div>
            </section>
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
    </div>;
};
export function App() {
  return <ThemeProvider>
      <AppContent />
    </ThemeProvider>;
}