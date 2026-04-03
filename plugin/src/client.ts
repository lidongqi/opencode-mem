export interface MemoryClientConfig {
  baseUrl: string;
  apiKey?: string;
  timeout?: number;
}

export interface MemoryAddRequest {
  content: string;
  user_id?: string;
  metadata?: Record<string, any>;
}

export interface MemorySearchRequest {
  query: string;
  user_id?: string;
  limit?: number;
}

export interface IntelligentMemoryRequest {
  user_input: string;
  user_id?: string;
  session_id: string;
  conversation_history?: Array<{ role: string; content: string }>;
  token_budget?: number;
}

export interface IntelligentMemoryResponse {
  success: boolean;
  context?: string;
  memories_count: number;
  query_type?: string;
  cache_hit: boolean;
  latency_ms?: number;
  error?: string;
}

export interface MemoryItem {
  id: string;
  content: string;
  score?: number;
  metadata?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

export interface ApiResponse<T> {
  success: boolean;
  error?: string;
  [key: string]: any;
}

export class MemoryClient {
  private baseUrl: string;
  private apiKey?: string;
  private timeout: number;

  constructor(config: MemoryClientConfig) {
    this.baseUrl = config.baseUrl.replace(/\/$/, '');
    this.apiKey = config.apiKey;
    this.timeout = config.timeout || 30000;
  }

  private async fetch<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.apiKey) {
      headers['X-API-Key'] = this.apiKey;
    }

    try {
      const response = await fetch(`${this.baseUrl}${path}`, {
        ...options,
        signal: controller.signal,
        headers: {
          ...headers,
          ...options.headers,
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.text();
        return { success: false, error };
      }

      return await response.json() as ApiResponse<T>;
    } catch (error) {
      clearTimeout(timeoutId);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  async addMemory(request: MemoryAddRequest): Promise<ApiResponse<{ memory_id: string }>> {
    return this.fetch('/api/memory/add', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async searchMemories(request: MemorySearchRequest): Promise<ApiResponse<{ memories: MemoryItem[]; count: number }>> {
    return this.fetch('/api/memory/search', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getContext(query: string, userId?: string): Promise<ApiResponse<{ context: string }>> {
    const params = new URLSearchParams({ query });
    if (userId) params.append('user_id', userId);
    return this.fetch(`/api/memory/context?${params}`);
  }

  async getIntelligentMemories(request: IntelligentMemoryRequest): Promise<IntelligentMemoryResponse> {
    const response = await this.fetch<IntelligentMemoryResponse>('/api/memory/intelligent', {
      method: 'POST',
      body: JSON.stringify(request),
    });
    return response as IntelligentMemoryResponse;
  }

  async getMetrics(): Promise<ApiResponse<{ report: any }>> {
    return this.fetch('/api/metrics');
  }

  async getCacheStats(): Promise<ApiResponse<{ stats: any }>> {
    return this.fetch('/api/cache/stats');
  }

  async clearCache(userId?: string): Promise<ApiResponse<{ message: string }>> {
    const params = userId ? `?user_id=${encodeURIComponent(userId)}` : '';
    return this.fetch(`/api/cache/clear${params}`, {
      method: 'POST',
    });
  }
}