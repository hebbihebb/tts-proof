// API service for communicating with the FastAPI backend
const API_BASE_URL = 'http://localhost:8000/api';
const WS_BASE_URL = 'ws://localhost:8000/ws';

export interface ProcessRequest {
  content: string;
  model_name?: string;
  api_base?: string;
  prompt_template?: string;
  stream?: boolean;
  show_progress?: boolean;
  resume?: boolean;
  force?: boolean;
  fsync_each?: boolean;
  chunk_size?: number;
  preview_chars?: number;
  use_prepass?: boolean;
  prepass_report?: any;
}

export interface JobStatus {
  status: 'started' | 'processing' | 'completed' | 'error';
  progress: number;
  result?: string;
  error?: string;
}

export interface WebSocketMessage {
  type: 'progress' | 'completed' | 'error' | 'chunk_complete' | 'chunk_error' | 'paused';
  source?: 'prepass' | 'grammar' | 'mask' | 'prepass-basic' | 'prepass-advanced' | 'scrubber' | 'detect' | 'apply' | 'fix' | 'pipeline'; // Phase 11 PR-1: Extended sources
  progress?: number;
  message: string;
  result?: string | any;  // Final processed text or prepass report
  chunks_processed?: number;
  total_chunks?: number;
  total_processed?: number;
  chunk?: any;
  chunk_index?: number;
  output_size?: number;
  exit_code?: number;  // Phase 11 PR-1: Exit code for error mapping
  steps?: string[];    // Phase 11 PR-1: Steps being executed
  current_step?: string;  // Phase 11 PR-1: Current step name
  stats?: any;         // Phase 11 PR-1: Pipeline statistics
  output_path?: string; // Phase 11 PR-1: Output file path
  run_id?: string;     // Phase 11 PR-2: Run ID for accessing artifacts
}

export interface RunSummary {
  run_id: string;
  status: string;
  created_at: string;
  completed_at?: string;
  steps: string[];
  models: Record<string, string>;
  exit_code?: number;
  input_name?: string;
  input_size?: number;
  artifact_count: number;
  total_size?: number;
  has_rejected?: boolean;
}

export interface ArtifactInfo {
  name: string;
  size_bytes: number;
  modified_at: string;
  media_type: string;
  is_text: boolean;
  preview?: string | null;
}

export interface ArtifactListResponse {
  run_id: string;
  artifacts: ArtifactInfo[];
  total_size: number;
}

export interface PresetListResponse {
  presets: Record<string, Record<string, any>>;
  active: string;
  active_source: string;
  resolved: Record<string, any>;
  env_overrides: Record<string, string>;
}

export interface AcronymListResponse {
  items: string[];
}

export interface FetchModelsParams {
  provider: string;
  baseUrl: string;
  apiKey?: string;
}

export interface RunServerPayload {
  provider: string;
  baseUrl: string;
  apiKey?: string;
}

export interface RunModelsPayload {
  grammar?: string;
  detector?: string;
  fixer?: string;
}

export interface RunOverridesPayload extends RunModelsPayload {}

class ApiService {
  private ws: WebSocket | null = null;
  private clientId: string = Math.random().toString(36).substring(7);

  async fetchModels(params: FetchModelsParams): Promise<string[]> {
    const query = new URLSearchParams({
      provider: params.provider,
      api_base: params.baseUrl,
    });
    const response = await fetch(`${API_BASE_URL}/models?${query.toString()}`, {
      headers: params.apiKey ? { Authorization: `Bearer ${params.apiKey}` } : undefined,
    });
    if (!response.ok) {
      const message = await response.text();
      throw new Error(message || `Failed to fetch models (${response.status})`);
    }
    const data = await response.json();

    const normalizeEntry = (entry: unknown): string => {
      if (typeof entry === 'string') {
        return entry;
      }
      if (entry && typeof entry === 'object') {
        const candidate = (entry as { id?: string; name?: string }).id ?? (entry as { name?: string }).name;
        return typeof candidate === 'string' ? candidate : '';
      }
      return '';
    };

    if (Array.isArray(data)) {
      return data
        .map(normalizeEntry)
        .filter((value: string): value is string => value.length > 0);
    }

    if (Array.isArray(data.models)) {
      return data.models
        .map(normalizeEntry)
        .filter((value: string): value is string => value.length > 0);
    }

    if (Array.isArray(data.data)) {
      return data.data
        .map(normalizeEntry)
        .filter((value: string): value is string => value.length > 0);
    }

    return [];
  }

  // Phase 11 PR-1: Get blessed models for detector and fixer roles
  async getBlessedModels(): Promise<{detector: string[], fixer: string[]}> {
    try {
      const response = await fetch(`${API_BASE_URL}/blessed-models`);
      if (!response.ok) {
        throw new Error('Failed to fetch blessed models');
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching blessed models:', error);
      // Return default blessed models as fallback
      return {
        detector: ['qwen2.5-1.5b-instruct'],
        fixer: ['qwen2.5-1.5b-instruct']
      };
    }
  }

  // Phase 11 PR-1: Run unified pipeline with selected steps and models
  async runPipeline(request: {
    input_path: string;
    steps: string[];
    models?: RunModelsPayload;
    server?: RunServerPayload;
    preset?: string;
    overrides?: RunOverridesPayload;
    report_pretty?: boolean;
    client_id?: string;
  }): Promise<{ run_id: string; status: string }> {
    const response = await fetch(`${API_BASE_URL}/run`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ...request,
        client_id: request.client_id || this.clientId,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to start pipeline run');
    }

    return await response.json();
  }

  async getPresets(): Promise<PresetListResponse> {
    const response = await fetch(`${API_BASE_URL}/presets`);
    if (!response.ok) {
      throw new Error('Failed to load presets');
    }
    return await response.json();
  }

  async activatePreset(name: string): Promise<PresetListResponse> {
    const response = await fetch(`${API_BASE_URL}/presets/active`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    });
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`Preset "${name}" not found`);
      }
      throw new Error('Failed to activate preset');
    }
    return await response.json();
  }

  async getAcronyms(): Promise<string[]> {
    const response = await fetch(`${API_BASE_URL}/acronyms`);
    if (!response.ok) {
      throw new Error('Failed to load acronyms');
    }
    const data: AcronymListResponse = await response.json();
    return data.items;
  }

  async updateAcronyms(items: string[]): Promise<string[]> {
    const response = await fetch(`${API_BASE_URL}/acronyms`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ items })
    });
    if (!response.ok) {
      throw new Error('Failed to update acronyms');
    }
    const data: AcronymListResponse = await response.json();
    return data.items;
  }

  async uploadFile(file: File): Promise<{
    file_id: string;
    filename: string;
    size: number;
    content_preview: string;
    full_content?: string;
    temp_path: string;
  }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Failed to upload file');
    }

    return await response.json();
  }

  async getPrepassPrompt(): Promise<{
    prompt: string;
    source: string;
  }> {
    const response = await fetch(`${API_BASE_URL}/prepass-prompt`);

    if (!response.ok) {
      throw new Error('Failed to fetch prepass prompt');
    }

    return await response.json();
  }

  async savePrepassPrompt(prompt: string): Promise<{
    status: string;
    message: string;
    source: string;
  }> {
    const response = await fetch(`${API_BASE_URL}/prepass-prompt`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ prompt }),
    });

    if (!response.ok) {
      throw new Error('Failed to save prepass prompt');
    }

    return await response.json();
  }

  async runPrepass(request: {
    content: string;
    model_name?: string;
    api_base?: string;
    chunk_size?: number;
  }): Promise<{
    status: string;
    report: any;
    summary: {
      unique_problems: number;
      chunks_processed: number;
      sample_problems: string[];
    };
  }> {
    const response = await fetch(`${API_BASE_URL}/prepass`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ...request,
        client_id: this.clientId
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to run prepass detection');
    }

    return await response.json();
  }

  async uploadPrepassReport(file: File): Promise<{
    status: string;
    report: any;
    summary: {
      source: string;
      unique_problems: number;
      chunks: number;
      created_at: string;
    };
  }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/upload-prepass`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Failed to upload prepass report');
    }

    return await response.json();
  }

  async getGrammarPrompt(): Promise<{
    prompt: string;
    source: string;
  }> {
    const response = await fetch(`${API_BASE_URL}/grammar-prompt`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch grammar prompt');
    }

    return await response.json();
  }

  async saveGrammarPrompt(prompt: string): Promise<{
    status: string;
    message: string;
    source: string;
  }> {
    const response = await fetch(`${API_BASE_URL}/grammar-prompt`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ prompt }),
    });

    if (!response.ok) {
      throw new Error('Failed to save grammar prompt');
    }

    return await response.json();
  }

  async startProcessing(request: ProcessRequest): Promise<{ job_id: string; status: string }> {
    const response = await fetch(`${API_BASE_URL}/process/${this.clientId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error('Failed to start processing');
    }

    return await response.json();
  }

  async getJobStatus(jobId: string): Promise<JobStatus> {
    const response = await fetch(`${API_BASE_URL}/job/${jobId}`);
    
    if (!response.ok) {
      throw new Error('Failed to get job status');
    }

    return await response.json();
  }

  connectWebSocket(
    onMessage: (message: WebSocketMessage) => void,
    onError?: (error: Event) => void,
    onClose?: () => void
  ): void {
    try {
      this.ws = new WebSocket(`${WS_BASE_URL}/${this.clientId}`);
      
      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          onMessage(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        if (onError) {
          onError(error);
        }
      };

      this.ws.onclose = () => {
        console.log('WebSocket connection closed');
        if (onClose) {
          onClose();
        }
      };

      this.ws.onopen = () => {
        console.log('WebSocket connected');
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      if (onError) {
        onError(error as Event);
      }
    }
  }

  disconnectWebSocket(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  async getJobResult(jobId: string): Promise<string | null> {
    try {
      console.log('Fetching job result from:', `${API_BASE_URL}/job/${jobId}`);
      const response = await fetch(`${API_BASE_URL}/job/${jobId}`);
      console.log('Job result response status:', response.status, response.statusText);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Job result fetch failed:', response.status, errorText);
        throw new Error(`Failed to fetch job status: ${response.status} ${errorText}`);
      }
      
      const jobStatus = await response.json();
      console.log('Job status received:', jobStatus);
      return jobStatus.result || null;
    } catch (error) {
      console.error('Error fetching job result:', error);
      return null;
    }
  }

  async pauseJob(jobId: string): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/job/${jobId}/pause`, {
        method: 'POST'
      });
      return response.ok;
    } catch (error) {
      console.error('Error pausing job:', error);
      return false;
    }
  }

  async resumeJob(jobId: string): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/job/${jobId}/resume`, {
        method: 'POST'
      });
      return response.ok;
    } catch (error) {
      console.error('Error resuming job:', error);
      return false;
    }
  }

  async cancelJob(jobId: string): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/job/${jobId}/cancel`, {
        method: 'POST'
      });
      return response.ok;
    } catch (error) {
      console.error('Error cancelling job:', error);
      return false;
    }
  }

  async cancelPrepass(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/prepass/cancel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          client_id: this.clientId
        }),
      });
      return response.ok;
    } catch (error) {
      console.error('Error cancelling prepass:', error);
      return false;
    }
  }

  getClientId(): string {
    return this.clientId;
  }

  async runTest(request: {
    model_name?: string;
    api_base?: string;
    chunk_size?: number;
  }): Promise<{
    status: string;
    message: string;
    log_file: string;
    summary: {
      prepass_problems: number;
      errors: number;
      chunks_processed: number;
    };
    log_content: string;
  }> {
    const response = await fetch(`${API_BASE_URL}/run-test`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error('Failed to run test');
    }

    return await response.json();
  }

  async getTempDirectory(): Promise<{ path: string }> {
    const response = await fetch(`${API_BASE_URL}/temp-directory`);
    if (!response.ok) {
      throw new Error('Failed to fetch temp directory');
    }
    return await response.json();
  }

  // Phase 11 PR-2: Get pretty-formatted report for a run
  async getRunReport(runId: string): Promise<{
    pretty_report: string;
    json_report_path: string | null;
  }> {
    const response = await fetch(`${API_BASE_URL}/runs/${encodeURIComponent(runId)}/report`);
    if (!response.ok) {
      throw new Error('Failed to fetch run report');
    }
    return await response.json();
  }

  // Phase 11 PR-2: Get unified diff for a run
  async getRunDiff(runId: string, maxLines: number = 200): Promise<{
    diff_head: string;
    has_more: boolean;
    rejected: boolean;
  }> {
    const response = await fetch(`${API_BASE_URL}/runs/${encodeURIComponent(runId)}/diff?max_lines=${maxLines}`);
    if (!response.ok) {
      throw new Error('Failed to fetch run diff');
    }
    return await response.json();
  }

  // Phase 11 PR-2: Get result summary for a run
  async getRunResult(runId: string): Promise<{
    exit_code: number;
    output_path: string | null;
    rejected_path: string | null;
    plan_path: string | null;
    json_report_path: string | null;
  }> {
    const response = await fetch(`${API_BASE_URL}/runs/${encodeURIComponent(runId)}/result`);
    if (!response.ok) {
      throw new Error('Failed to fetch run result');
    }
    return await response.json();
  }

  // Phase 11 PR-2: Download an artifact file
  async downloadArtifact(runId: string, name: string): Promise<Blob> {
    const params = new URLSearchParams({ run_id: runId, name });
    const response = await fetch(`${API_BASE_URL}/artifact?${params.toString()}`);
    if (!response.ok) {
      throw new Error(`Failed to download artifact: ${name}`);
    }
    return await response.blob();
  }

  // Phase 11 PR-3: List historical runs
  async listRuns(): Promise<RunSummary[]> {
    const response = await fetch(`${API_BASE_URL}/runs`);
    if (!response.ok) {
      throw new Error('Failed to fetch run history');
    }
    const data = await response.json();
    return data.runs ?? [];
  }

  // Phase 11 PR-3: List artifacts for a run
  async listRunArtifacts(runId: string): Promise<ArtifactListResponse> {
    const response = await fetch(`${API_BASE_URL}/runs/${encodeURIComponent(runId)}/artifacts`);
    if (!response.ok) {
      throw new Error('Failed to fetch run artifacts');
    }
    return await response.json();
  }

  // Phase 11 PR-3: Delete a run and its artifacts
  async deleteRun(runId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/runs/${encodeURIComponent(runId)}`, {
      method: 'DELETE'
    });
    if (!response.ok) {
      throw new Error('Failed to delete run');
    }
  }

  // Phase 11 PR-3: Download all artifacts as a ZIP
  async downloadRunArchive(runId: string): Promise<Blob> {
    const response = await fetch(`${API_BASE_URL}/runs/${encodeURIComponent(runId)}/artifacts/archive`);
    if (!response.ok) {
      throw new Error('Failed to download run archive');
    }
    return await response.blob();
  }

  // Phase 11 PR-3: Download specific artifact by filename
  async downloadRunArtifact(runId: string, artifactName: string): Promise<Blob> {
    const response = await fetch(`${API_BASE_URL}/runs/${encodeURIComponent(runId)}/artifacts/${encodeURIComponent(artifactName)}`);
    if (!response.ok) {
      throw new Error('Failed to download artifact');
    }
    return await response.blob();
  }
}

export const apiService = new ApiService();