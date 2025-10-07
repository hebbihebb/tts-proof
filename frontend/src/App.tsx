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
import { EditIcon, PlayIcon, SaveIcon } from 'lucide-react';
import { apiService, WebSocketMessage } from './services/api';
// Use the high-quality grammar prompt that matches the original
const DEFAULT_PROMPT = `You are a Markdown-preserving cleaner for TTS.
Rules (apply to text only; never edit Markdown syntax, code blocks, inline code,
links/URLs, images, or HTML tags):

1) Normalize stylized Unicode letters to plain ASCII; keep accents in real words.
2) Fix weird casing: mid-word caps → normal; ALL-CAPS → Title/normal unless a true acronym (≤5 letters and common: NASA, GPU).
3) Collapse inter-letter spacing artifacts to single words (already mostly done).
4) Keep onomatopoeia but avoid spelled-out effects.
5) Keep brackets; normalize inside: "[M ᴇ ɢ ᴀ B ᴜ s ᴛ ᴇ ʀ]" → "[Mega Buster]".
6) Light grammar/spelling/punctuation spacing; do not change meaning or tone.
7) Preserve all Markdown structure exactly.
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
  const [isPromptEditorOpen, setIsPromptEditorOpen] = useState<boolean>(false);
  const [prompt, setPrompt] = useState<string>(DEFAULT_PROMPT);
  const [progress, setProgress] = useState<number>(0);
  const [status, setStatus] = useState<string>('Ready to process');
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [logs, setLogs] = useState(MOCK_LOGS);
  const [originalText, setOriginalText] = useState<string>('');
  const [processedText, setProcessedText] = useState<string>('');
  const [currentJobId, setCurrentJobId] = useState<string>('');
  const [chunkSize, setChunkSize] = useState<number>(8000);

  // Calculate estimated chunks based on text length and chunk size
  const calculateEstimatedChunks = (text: string, size: number) => {
    if (!text) return 0;
    return Math.ceil(text.length / size);
  };

  // Initialize WebSocket connection
  useEffect(() => {
    const handleWebSocketMessage = (message: WebSocketMessage) => {
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
            addLog(`Completed chunk ${message.chunks_processed}/${message.total_chunks}`, 'success');
          }
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
          
          // Use result directly from the completion message (like original md_proof.py)
          console.log('Completion message received with result:', message.result ? `${message.result.length} chars` : 'no result');
          if (message.result) {
            setProcessedText(message.result);
            addLog(`Processing completed with ${message.result.length} characters`, 'success');
          } else {
            addLog('No result in completion message', 'warning');
          }
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
      setProcessedText('');
      addLog('Sending file for processing...', 'info');

      // Set the job ID early (it's the same as client ID) to avoid race condition
      const clientId = apiService.getClientId();
      setCurrentJobId(clientId);
      console.log('Set currentJobId to:', clientId);

      // Start processing job
      const jobResult = await apiService.startProcessing({
        content: originalText,
        model_name: selectedModelId,
        prompt_template: prompt,
        stream: false,
        show_progress: true,
        chunk_size: chunkSize,
        preview_chars: 500
      });

      addLog(`Processing job started: ${jobResult.job_id}`, 'info');

    } catch (error) {
      console.error('Error starting processing:', error);
      setIsProcessing(false);
      addLog(`Failed to start processing: ${error}`, 'error');
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
  return <div className={`min-h-screen w-full transition-colors duration-300 ${isDarkMode ? 'dark bg-catppuccin-base text-catppuccin-text' : 'bg-light-base text-light-text'}`}>
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <header className="flex justify-between items-center mb-8">
          <div className="flex items-center">
            <div className="w-10 h-10 bg-gradient-to-br from-catppuccin-mauve to-catppuccin-blue rounded-lg flex items-center justify-center shadow-lg mr-4">
              <span className="text-white font-bold text-lg">TP</span>
            </div>
            <div>
              <h1 className="text-3xl font-bold text-light-text dark:text-catppuccin-text">
                TTS-Proof
              </h1>
              <span className="px-2.5 py-1 bg-catppuccin-lavender/20 dark:bg-catppuccin-lavender/10 text-catppuccin-lavender dark:text-catppuccin-lavender text-xs font-medium rounded-full ml-2">
                v2.1.0
              </span>
            </div>
          </div>
          <ThemeToggle />
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left column - Controls */}
          <div className="lg:col-span-1 space-y-6">
            <section className="bg-light-mantle dark:bg-catppuccin-mantle rounded-xl p-6 shadow-lg border border-light-surface0 dark:border-catppuccin-surface0">
              <h2 className="text-xl font-semibold mb-4 text-light-text dark:text-catppuccin-text">
                File Selection
              </h2>
              <FileSelector onFileSelect={handleFileSelect} />
            </section>

            <section className="bg-light-mantle dark:bg-catppuccin-mantle rounded-xl p-6 shadow-lg border border-light-surface0 dark:border-catppuccin-surface0">
              <h2 className="text-xl font-semibold mb-4 text-light-text dark:text-catppuccin-text">
                Model Selection
              </h2>
              <ModelPicker onModelSelect={setSelectedModelId} />
            </section>

            {/* File Analysis - Show when file is selected */}
            {file && originalText && (
              <section className="bg-light-mantle dark:bg-catppuccin-mantle rounded-xl p-6 shadow-lg border border-light-surface0 dark:border-catppuccin-surface0">
                <FileAnalysis 
                  totalCharacters={originalText.length}
                  estimatedChunks={calculateEstimatedChunks(originalText, chunkSize)}
                  fileName={file.name}
                />
              </section>
            )}

            {/* Chunk Size Control */}
            <section className="bg-light-mantle dark:bg-catppuccin-mantle rounded-xl p-6 shadow-lg border border-light-surface0 dark:border-catppuccin-surface0">
              <ChunkSizeControl 
                chunkSize={chunkSize}
                onChunkSizeChange={setChunkSize}
                disabled={isProcessing}
              />
            </section>

            <section className="bg-light-mantle dark:bg-catppuccin-mantle rounded-xl p-6 shadow-lg border border-light-surface0 dark:border-catppuccin-surface0">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold text-light-text dark:text-catppuccin-text">
                  Prompt Template
                </h2>
                <Button variant="outline" size="sm" icon={<EditIcon className="w-4 h-4" />} onClick={() => setIsPromptEditorOpen(true)}>
                  Edit
                </Button>
              </div>
              <div className="bg-light-crust dark:bg-catppuccin-crust p-3 rounded-lg border border-light-surface1 dark:border-catppuccin-surface1">
                <pre className="text-sm text-light-subtext1 dark:text-catppuccin-subtext1 whitespace-pre-wrap">
                  {prompt.length > 150 ? `${prompt.substring(0, 150)}...` : prompt}
                </pre>
              </div>
            </section>

            <section className="bg-light-mantle dark:bg-catppuccin-mantle rounded-xl p-6 shadow-lg border border-light-surface0 dark:border-catppuccin-surface0">
              <h2 className="text-xl font-semibold mb-4 text-light-text dark:text-catppuccin-text">
                Processing
              </h2>
              <ProgressBar progress={progress} status={status} isProcessing={isProcessing} />
              <div className="mt-4 flex space-x-3">
                <Button onClick={handleProcess} disabled={!file || isProcessing} isLoading={isProcessing} icon={<PlayIcon className="w-4 h-4" />} className="flex-1">
                  Process Text
                </Button>
                <Button variant="outline" onClick={handleSaveProcessedText} disabled={!processedText} icon={<SaveIcon className="w-4 h-4" />} className="flex-1">
                  Save Result
                </Button>
              </div>
            </section>
          </div>

          {/* Right column - Preview and Logs */}
          <div className="lg:col-span-2 grid grid-rows-2 gap-6 h-[calc(100vh-10rem)]">
            <section className="row-span-1">
              <h2 className="text-xl font-semibold mb-4 text-light-text dark:text-catppuccin-text">
                Text Preview
              </h2>
              <div className="h-[calc(100%-2.5rem)]">
                <PreviewWindow originalText={originalText} processedText={processedText} onDelete={handleClearPreview} />
              </div>
            </section>

            <section className="row-span-1">
              <h2 className="text-xl font-semibold mb-4 text-light-text dark:text-catppuccin-text">
                Process Log
              </h2>
              <div className="h-[calc(100%-2.5rem)]">
                <LogArea logs={logs} />
              </div>
            </section>
          </div>
        </div>
      </div>

      {/* Prompt Editor Modal */}
      <PromptEditor isOpen={isPromptEditorOpen} onClose={() => setIsPromptEditorOpen(false)} onSave={setPrompt} initialPrompt={prompt} />
    </div>;
};
export function App() {
  return <ThemeProvider>
      <AppContent />
    </ThemeProvider>;
}