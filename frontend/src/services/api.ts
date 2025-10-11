// API service for communicating with the FastAPI backend
const API_BASE_URL = 'http://localhost:8000/api';
const WS_BASE_URL = 'ws://localhost:8000/ws';

export interface Model {
  id: string;
  name: string;
  description: string;
}

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
  progress?: number;
  message: string;
  result?: string;  // Final processed text (included in completion message)
  chunks_processed?: number;
  total_chunks?: number;
  total_processed?: number;
  chunk?: any;
  chunk_index?: number;
  output_size?: number;
}

class ApiService {
  private ws: WebSocket | null = null;
  private clientId: string = Math.random().toString(36).substring(7);

  async fetchModels(apiBase?: string): Promise<Model[]> {
    try {
      const url = new URL(`${API_BASE_URL}/models`);
      if (apiBase) {
        url.searchParams.set('api_base', apiBase);
      }
      
      const response = await fetch(url.toString());
      if (!response.ok) {
        throw new Error('Failed to fetch models');
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching models:', error);
      // Return default models as fallback
      return [
        { id: 'default', name: 'Default Model', description: 'Local LLM model' },
        { id: 'gpt-4', name: 'GPT-4', description: 'OpenAI GPT-4 model' }
      ];
    }
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
      body: JSON.stringify(request),
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

  getClientId(): string {
    return this.clientId;
  }
}

export const apiService = new ApiService();