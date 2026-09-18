import type {
  ComprehensiveHealthResponse,
  LivenessResponse,
  ReadinessResponse,
  SystemInfoResponse,
  CurrentUserResponse,
  AuthResponse,
  ApiErrorResponse,
} from '@/types/api';

export class ApiError extends Error {
  code: string;
  status: number;
  details: Record<string, any>;
  requestId: string | null;

  constructor(
    message: string,
    status: number,
    code: string = 'API_ERROR',
    details: Record<string, any> = {},
    requestId: string | null = null,
  ) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
    this.requestId = requestId;
  }
}

export class ApiClient {
  private baseUrl: string;
  private onUnauthorizedCallback?: () => void;

  constructor(baseUrl: string = '') {
    this.baseUrl = baseUrl;
  }

  public setOnUnauthorized(callback: () => void) {
    this.onUnauthorizedCallback = callback;
  }

  private getFullUrl(path: string): string {
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    return `${this.baseUrl}${cleanPath}`;
  }

  async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const url = this.getFullUrl(path);

    const headers = new Headers(init.headers || {});
    if (!headers.has('Accept')) {
      headers.set('Accept', 'application/json');
    }
    if (init.body && typeof init.body === 'string' && !headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }

    const response = await fetch(url, {
      ...init,
      headers,
      credentials: 'include', // Ensure cookies are sent with all requests
    });

    const requestId = response.headers.get('x-request-id');

    if (response.status === 401) {
      if (this.onUnauthorizedCallback) {
        this.onUnauthorizedCallback();
      }
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('jenna:unauthorized'));
      }
    }

    // Try parsing JSON body
    let responseData: any = null;
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      try {
        responseData = await response.json();
      } catch {
        responseData = null;
      }
    }

    if (!response.ok) {
      const errorObj = (responseData as ApiErrorResponse)?.error;
      const message = errorObj?.message || responseData?.message || `Request failed with HTTP ${response.status}`;
      const code = errorObj?.code || `HTTP_${response.status}`;
      const details = errorObj?.details || {};
      const reqId = errorObj?.request_id || requestId;

      throw new ApiError(message, response.status, code, details, reqId);
    }

    return responseData as T;
  }

  // --- Health Endpoints ---
  async getHealth(): Promise<ComprehensiveHealthResponse> {
    return this.request<ComprehensiveHealthResponse>('/api/v1/health');
  }

  async getLiveness(): Promise<LivenessResponse> {
    return this.request<LivenessResponse>('/api/v1/health/live');
  }

  async getReadiness(): Promise<ReadinessResponse> {
    return this.request<ReadinessResponse>('/api/v1/health/ready');
  }

  async getSystemInfo(): Promise<SystemInfoResponse> {
    return this.request<SystemInfoResponse>('/api/v1/system/info');
  }

  // --- Auth Endpoints ---
  async getMe(): Promise<CurrentUserResponse> {
    return this.request<CurrentUserResponse>('/api/v1/auth/me');
  }

  async login(email: string, password: string): Promise<AuthResponse> {
    return this.request<AuthResponse>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async register(email: string, password: string): Promise<AuthResponse> {
    return this.request<AuthResponse>('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async logout(): Promise<{ status: string; message: string }> {
    return this.request<{ status: string; message: string }>('/api/v1/auth/logout', {
      method: 'POST',
    });
  }

  // --- AI Endpoints (Part 2) ---
  async generateAICompletion(request: import('@jenna/types').AIRequest): Promise<import('@jenna/types').AIResponse> {
    return this.request<import('@jenna/types').AIResponse>('/api/v1/ai/generate', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getAIModels(): Promise<import('@jenna/types').AIModelMetadata[]> {
    return this.request<import('@jenna/types').AIModelMetadata[]>('/api/v1/ai/models');
  }

  async getAIStatus(): Promise<any> {
    return this.request<any>('/api/v1/ai/status');
  }

  async getAIUsage(): Promise<any> {
    return this.request<any>('/api/v1/ai/usage');
  }

  async streamAICompletion(
    request: import('@jenna/types').AIRequest,
    onEvent: (event: import('@jenna/types').AIStreamEvent) => void,
  ): Promise<void> {
    const url = this.getFullUrl('/api/v1/ai/stream');
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
      },
      credentials: 'include',
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      let errData: any = null;
      try {
        errData = await response.json();
      } catch {
        // ignore
      }
      const msg = errData?.detail?.message || errData?.message || `Streaming request failed with status ${response.status}`;
      throw new ApiError(msg, response.status, errData?.detail?.code || 'STREAM_ERROR');
    }

    if (!response.body) {
      throw new ApiError('ReadableStream not supported on response', 500);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith('data:')) {
          try {
            const jsonStr = trimmed.slice(5).trim();
            if (jsonStr) {
              const parsed = JSON.parse(jsonStr) as import('@jenna/types').AIStreamEvent;
              onEvent(parsed);
            }
          } catch (e) {
            console.warn('Failed to parse SSE chunk:', trimmed, e);
          }
        }
      }
    }
  }

  // ==========================================
  // Part 2 Phase 2: Conversation & Personality
  // ==========================================

  async listConversations(limit = 50, offset = 0): Promise<import('@jenna/types').Conversation[]> {
    return this.request<import('@jenna/types').Conversation[]>(
      `/api/v1/conversations?limit=${limit}&offset=${offset}`,
    );
  }

  async createConversation(title = 'New Conversation'): Promise<import('@jenna/types').Conversation> {
    return this.request<import('@jenna/types').Conversation>('/api/v1/conversations', {
      method: 'POST',
      body: JSON.stringify({ title }),
    });
  }

  async getConversationDetail(conversationId: string): Promise<{
    conversation: import('@jenna/types').Conversation;
    messages: import('@jenna/types').ConversationMessage[];
    total_messages: number;
  }> {
    return this.request<{
      conversation: import('@jenna/types').Conversation;
      messages: import('@jenna/types').ConversationMessage[];
      total_messages: number;
    }>(`/api/v1/conversations/${conversationId}`);
  }

  async updateConversationTitle(
    conversationId: string,
    title: string,
  ): Promise<import('@jenna/types').Conversation> {
    return this.request<import('@jenna/types').Conversation>(`/api/v1/conversations/${conversationId}`, {
      method: 'PATCH',
      body: JSON.stringify({ title }),
    });
  }

  async deleteConversation(conversationId: string): Promise<void> {
    await this.request(`/api/v1/conversations/${conversationId}`, {
      method: 'DELETE',
    });
  }

  async sendConversationMessage(
    conversationId: string,
    content: string,
    model?: string,
    provider?: string,
  ): Promise<any> {
    return this.request(`/api/v1/conversations/${conversationId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ content, model, provider }),
    });
  }

  async streamConversationMessage(
    conversationId: string,
    content: string,
    onEvent: (event: any) => void,
    abortSignal?: AbortSignal,
    model?: string,
    provider?: string,
    options?: {
      web_search?: boolean;
      deep_research?: boolean;
      attachments?: any[];
      personal_intelligence?: boolean;
      persona?: string;
    },
  ): Promise<void> {
    const url = this.getFullUrl(`/api/v1/conversations/${conversationId}/stream`);
    const payload: Record<string, any> = {
      content,
      model,
      provider,
      web_search: Boolean(options?.web_search),
      deep_research: Boolean(options?.deep_research),
      attachments: options?.attachments || [],
      personal_intelligence: options?.personal_intelligence !== false,
      persona: options?.persona,
    };
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
      },
      credentials: 'include',
      signal: abortSignal,
      body: JSON.stringify(payload),
    });


    if (!response.ok) {
      let errData: any = null;
      try {
        errData = await response.json();
      } catch {
        // ignore
      }
      const msg =
        errData?.detail?.message ||
        errData?.message ||
        `Streaming request failed with status ${response.status}`;
      throw new ApiError(msg, response.status, errData?.detail?.code || 'STREAM_ERROR');
    }

    if (!response.body) {
      throw new ApiError('ReadableStream not supported on response', 500);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith('data:')) {
          try {
            const jsonStr = trimmed.slice(5).trim();
            if (jsonStr) {
              const parsed = JSON.parse(jsonStr);
              onEvent(parsed);
            }
          } catch (e) {
            console.warn('Failed to parse SSE chunk:', trimmed, e);
          }
        }
      }
    }
  }

  async getPersonalitySettings(): Promise<{
    settings: import('@jenna/types').PersonalitySettings;
    user_id: string;
  }> {
    return this.request<{
      settings: import('@jenna/types').PersonalitySettings;
      user_id: string;
    }>('/api/v1/settings/personality');
  }

  async updatePersonalitySettings(
    settings: Partial<import('@jenna/types').PersonalitySettings>,
  ): Promise<{
    settings: import('@jenna/types').PersonalitySettings;
    user_id: string;
  }> {
    return this.request<{
      settings: import('@jenna/types').PersonalitySettings;
      user_id: string;
    }>('/api/v1/settings/personality', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }

  // ==========================================
  // Part 3 Phase 1: Memory API
  // ==========================================

  async listMemories(params?: {
    memory_type?: string;
    status?: string;
    search?: string;
    min_importance?: number;
    limit?: number;
    offset?: number;
  }): Promise<import('@jenna/types').MemoryListResponse> {
    const query = new URLSearchParams();
    if (params?.memory_type) query.set('memory_type', params.memory_type);
    if (params?.status) query.set('status', params.status);
    if (params?.search) query.set('search', params.search);
    if (params?.min_importance !== undefined) query.set('min_importance', String(params.min_importance));
    if (params?.limit !== undefined) query.set('limit', String(params.limit));
    if (params?.offset !== undefined) query.set('offset', String(params.offset));

    const qs = query.toString() ? `?${query.toString()}` : '';
    return this.request<import('@jenna/types').MemoryListResponse>(`/api/v1/memory${qs}`);
  }

  async getMemory(id: string): Promise<import('@jenna/types').MemoryRecord> {
    return this.request<import('@jenna/types').MemoryRecord>(`/api/v1/memory/${id}`);
  }

  async createMemory(payload: import('@jenna/types').MemoryCreateInput): Promise<import('@jenna/types').MemoryRecord> {
    return this.request<import('@jenna/types').MemoryRecord>('/api/v1/memory', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async updateMemory(id: string, payload: import('@jenna/types').MemoryUpdateInput): Promise<import('@jenna/types').MemoryRecord> {
    return this.request<import('@jenna/types').MemoryRecord>(`/api/v1/memory/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  async deleteMemory(id: string): Promise<void> {
    await this.request<void>(`/api/v1/memory/${id}`, {
      method: 'DELETE',
    });
  }

  async archiveMemory(id: string): Promise<import('@jenna/types').MemoryActionResponse> {
    return this.request<import('@jenna/types').MemoryActionResponse>(`/api/v1/memory/${id}/archive`, {
      method: 'POST',
    });
  }

  async restoreMemory(id: string): Promise<import('@jenna/types').MemoryActionResponse> {
    return this.request<import('@jenna/types').MemoryActionResponse>(`/api/v1/memory/${id}/restore`, {
      method: 'POST',
    });
  }

  async feedbackMemory(
    id: string,
    feedbackType: import('@jenna/types').FeedbackType,
    comment?: string,
    updatedContent?: string,
  ): Promise<import('@jenna/types').MemoryActionResponse> {
    return this.request<import('@jenna/types').MemoryActionResponse>(`/api/v1/memory/${id}/feedback`, {
      method: 'POST',
      body: JSON.stringify({
        feedback_type: feedbackType,
        comment,
        updated_content: updatedContent,
      }),
    });
  }

  async extractMemories(
    content: string,
    conversationId?: string,
  ): Promise<import('@jenna/types').MemoryExtractResponse> {
    return this.request<import('@jenna/types').MemoryExtractResponse>('/api/v1/memory/extract', {
      method: 'POST',
      body: JSON.stringify({
        content,
        conversation_id: conversationId,
      }),
    });
  }

  async confirmMemory(
    candidate: import('@jenna/types').MemoryCandidate,
    confirm = true,
  ): Promise<import('@jenna/types').MemoryActionResponse> {
    return this.request<import('@jenna/types').MemoryActionResponse>('/api/v1/memory/confirm', {
      method: 'POST',
      body: JSON.stringify({
        candidate,
        confirm,
      }),
    });
  }

  async searchMemories(
    query: string,
    limit = 5,
    threshold = 0.35,
    memory_types?: string[],
  ): Promise<import('@jenna/types').MemorySearchResponse> {
    return this.request<import('@jenna/types').MemorySearchResponse>('/api/v1/memory/search', {
      method: 'POST',
      body: JSON.stringify({
        query,
        limit,
        threshold,
        memory_types,
      }),
    });
  }

  async getWorkingMemory(conversationId?: string): Promise<import('@jenna/types').WorkingMemoryResponse> {
    const qs = conversationId ? `?conversation_id=${encodeURIComponent(conversationId)}` : '';
    return this.request<import('@jenna/types').WorkingMemoryResponse>(`/api/v1/memory/working${qs}`);
  }

  async setWorkingMemory(
    key: string,
    value: any,
    ttlSeconds = 86400,
    conversationId?: string,
  ): Promise<any> {
    return this.request<any>('/api/v1/memory/working', {
      method: 'POST',
      body: JSON.stringify({
        key,
        value,
        ttl_seconds: ttlSeconds,
        conversation_id: conversationId,
      }),
    });
  }

  async clearWorkingMemory(conversationId?: string): Promise<any> {
    const qs = conversationId ? `?conversation_id=${encodeURIComponent(conversationId)}` : '';
    return this.request<any>(`/api/v1/memory/working${qs}`, {
      method: 'DELETE',
    });
  }

  // ==========================================
  // Part 4: Specialized Agents & Orchestration
  // ==========================================

  async getAgentRegistry(): Promise<import('@jenna/types').AgentRegistryItem[]> {
    return this.request<import('@jenna/types').AgentRegistryItem[]>('/api/v1/agents/registry');
  }

  async decomposeAgentTask(
    title: string,
    description: string = '',
  ): Promise<import('@jenna/types').AgentDecompositionPlan> {
    return this.request<import('@jenna/types').AgentDecompositionPlan>('/api/v1/agents/decompose', {
      method: 'POST',
      body: JSON.stringify({ title, description }),
    });
  }

  async createAgentTask(
    payload: import('@jenna/types').AgentTaskCreateInput,
  ): Promise<import('@jenna/types').AgentTask> {
    return this.request<import('@jenna/types').AgentTask>('/api/v1/agents/tasks', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async listAgentTasks(params?: {
    status?: string;
    agent_type?: string;
    parent_only?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<{ tasks: import('@jenna/types').AgentTask[]; total: number; limit: number; offset: number }> {
    const sp = new URLSearchParams();
    if (params?.status) sp.set('status', params.status);
    if (params?.agent_type) sp.set('agent_type', params.agent_type);
    if (params?.parent_only !== undefined) sp.set('parent_only', String(params.parent_only));
    if (params?.limit) sp.set('limit', String(params.limit));
    if (params?.offset) sp.set('offset', String(params.offset));
    const qs = sp.toString() ? `?${sp.toString()}` : '';
    return this.request<{ tasks: import('@jenna/types').AgentTask[]; total: number; limit: number; offset: number }>(
      `/api/v1/agents/tasks${qs}`
    );
  }

  async getAgentTask(id: string): Promise<import('@jenna/types').AgentTaskDetail> {
    return this.request<import('@jenna/types').AgentTaskDetail>(`/api/v1/agents/tasks/${id}`);
  }

  async executeAgentTask(id: string): Promise<import('@jenna/types').AgentTask> {
    return this.request<import('@jenna/types').AgentTask>(`/api/v1/agents/tasks/${id}/execute`, {
      method: 'POST',
    });
  }

  async cancelAgentTask(id: string): Promise<import('@jenna/types').AgentTask> {
    return this.request<import('@jenna/types').AgentTask>(`/api/v1/agents/tasks/${id}/cancel`, {
      method: 'POST',
    });
  }

  async getAgentTaskTraces(id: string): Promise<import('@jenna/types').AgentStepTrace[]> {
    return this.request<import('@jenna/types').AgentStepTrace[]>(`/api/v1/agents/tasks/${id}/traces`);
  }

  // ==========================================
  // Part 5: Tools, MCP & Web Research
  // ==========================================

  async listTools(category?: import('@jenna/types').ToolCategory): Promise<import('@jenna/types').ToolDefinition[]> {
    const qs = category ? `?category=${encodeURIComponent(category)}` : '';
    return this.request<import('@jenna/types').ToolDefinition[]>(`/api/v1/tools${qs}`);
  }

  async executeTool(
    tool_name: string,
    parameters: Record<string, any> = {},
    confirmed = false,
  ): Promise<import('@jenna/types').ToolExecutionResult> {
    return this.request<import('@jenna/types').ToolExecutionResult>('/api/v1/tools/execute', {
      method: 'POST',
      body: JSON.stringify({
        tool_name,
        parameters,
        confirmed,
      }),
    });
  }

  async performResearch(
    query: string,
    max_sources = 4,
  ): Promise<import('@jenna/types').ResearchResponse> {
    return this.request<import('@jenna/types').ResearchResponse>('/api/v1/tools/research', {
      method: 'POST',
      body: JSON.stringify({
        query,
        max_sources,
      }),
    });
  }

  async listMcpServers(): Promise<import('@jenna/types').MCPServerInfo[]> {
    return this.request<import('@jenna/types').MCPServerInfo[]>('/api/v1/tools/mcp/servers');
  }

  async connectMcpServer(
    server_name: string,
    server_type = 'mock',
  ): Promise<{ status: string; server_name: string; tools_registered: number; tools: string[] }> {
    return this.request<{ status: string; server_name: string; tools_registered: number; tools: string[] }>(
      `/api/v1/tools/mcp/connect?server_name=${encodeURIComponent(server_name)}&server_type=${encodeURIComponent(server_type)}`,
      { method: 'POST' }
    );
  }

  // ==========================================
  // Part 6 — Voice & Vision API Methods
  // ==========================================

  async getVoiceProfiles(): Promise<import('@jenna/types').VoiceProfile[]> {
    return this.request<import('@jenna/types').VoiceProfile[]>('/api/v1/voice/voices');
  }

  async getVoiceSettings(): Promise<import('@jenna/types').VoiceSettings> {
    return this.request<import('@jenna/types').VoiceSettings>('/api/v1/voice/settings');
  }

  async updateVoiceSettings(
    settings: import('@jenna/types').VoiceSettings
  ): Promise<import('@jenna/types').VoiceSettings> {
    return this.request<import('@jenna/types').VoiceSettings>('/api/v1/voice/settings', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }

  async transcribeAudio(
    audio_base64: string,
    mime_type = 'audio/webm',
    language?: string
  ): Promise<import('@jenna/types').AudioTranscription> {
    return this.request<import('@jenna/types').AudioTranscription>('/api/v1/voice/transcribe', {
      method: 'POST',
      body: JSON.stringify({ audio_base64, mime_type, language }),
    });
  }

  async synthesizeSpeech(
    text: string,
    voice_profile?: import('@jenna/types').VoiceProfile,
    output_format = 'audio/mp3'
  ): Promise<Blob> {
    const url = `${this.baseUrl}/api/v1/voice/synthesize`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: output_format,
      },
      credentials: 'include',
      body: JSON.stringify({ text, voice_profile, output_format }),
    });
    if (!response.ok) {
      throw new Error(`Voice synthesis failed: ${response.statusText}`);
    }
    return response.blob();
  }

  async interruptVoice(
    conversation_id?: string,
    reason = 'user_speaking'
  ): Promise<import('@jenna/types').InterruptionResponse> {
    return this.request<import('@jenna/types').InterruptionResponse>('/api/v1/voice/interrupt', {
      method: 'POST',
      body: JSON.stringify({ conversation_id, reason }),
    });
  }

  async getCameraStatus(): Promise<import('@jenna/types').CameraContext> {
    return this.request<import('@jenna/types').CameraContext>('/api/v1/vision/camera-status');
  }

  async getVisionSettings(): Promise<import('@jenna/types').VisionPrivacySettings> {
    return this.request<import('@jenna/types').VisionPrivacySettings>('/api/v1/vision/settings');
  }

  async updateVisionSettings(
    settings: import('@jenna/types').VisionPrivacySettings
  ): Promise<import('@jenna/types').VisionPrivacySettings> {
    return this.request<import('@jenna/types').VisionPrivacySettings>('/api/v1/vision/settings', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }

  async analyzeImage(
    image_base64: string,
    mime_type = 'image/jpeg',
    prompt?: string,
    detect_elements = true
  ): Promise<import('@jenna/types').VisionAnalysisResult> {
    return this.request<import('@jenna/types').VisionAnalysisResult>('/api/v1/vision/analyze', {
      method: 'POST',
      body: JSON.stringify({ image_base64, mime_type, prompt, detect_elements }),
    });
  }

  async analyzeScreen(
    screen_base64: string,
    mime_type = 'image/png',
    detect_ui_elements = true
  ): Promise<import('@jenna/types').VisionAnalysisResult> {
    return this.request<import('@jenna/types').VisionAnalysisResult>('/api/v1/vision/screen', {
      method: 'POST',
      body: JSON.stringify({ screen_base64, mime_type, detect_ui_elements }),
    });
  }

  // ==========================================
  // Part 7 — Computer Control API Methods
  // ==========================================

  async listPairedDevices(): Promise<import('@jenna/types').PairedComputer[]> {
    return this.request<import('@jenna/types').PairedComputer[]>('/api/v1/devices');
  }

  async initiateDevicePairing(
    device_name: string,
    os_platform = 'linux',
    requested_scopes: import('@jenna/types').ComputerScope[] = []
  ): Promise<import('@jenna/types').PairingResponse> {
    return this.request<import('@jenna/types').PairingResponse>('/api/v1/devices/pair/initiate', {
      method: 'POST',
      body: JSON.stringify({ device_name, os_platform, requested_scopes }),
    });
  }

  async confirmDevicePairing(
    device_id: string,
    pairing_code: string
  ): Promise<import('@jenna/types').PairedComputer> {
    return this.request<import('@jenna/types').PairedComputer>('/api/v1/devices/pair/confirm', {
      method: 'POST',
      body: JSON.stringify({ device_id, pairing_code }),
    });
  }

  async revokePairedDevice(device_id: string): Promise<void> {
    return this.request<void>(`/api/v1/devices/${device_id}`, {
      method: 'DELETE',
    });
  }

  async executeComputerCommand(
    device_id: string,
    action_type: import('@jenna/types').ComputerActionType,
    parameters: Record<string, any> = {},
    confirmed = false
  ): Promise<{
    result: import('@jenna/types').ComputerExecutionResult;
    steps: import('@jenna/types').ComputerStepProgress[];
  }> {
    return this.request<{
      result: import('@jenna/types').ComputerExecutionResult;
      steps: import('@jenna/types').ComputerStepProgress[];
    }>('/api/v1/devices/execute', {
      method: 'POST',
      body: JSON.stringify({ device_id, action_type, parameters, confirmed }),
    });
  }

  async triggerEmergencyStop(): Promise<{ status: string; halted_at: string; message: string }> {
    return this.request<{ status: string; halted_at: string; message: string }>(
      '/api/v1/devices/emergency-stop',
      { method: 'POST' }
    );
  }

  async clearEmergencyStop(): Promise<{ status: string; message: string }> {
    return this.request<{ status: string; message: string }>(
      '/api/v1/devices/emergency-stop/clear',
      { method: 'POST' }
    );
  }

  async getEmergencyStopStatus(): Promise<{ is_emergency_stopped: boolean }> {
    return this.request<{ is_emergency_stopped: boolean }>(
      '/api/v1/devices/emergency-stop/status'
    );
  }

  // ==========================================
  // Part 8 — Controlled Self-Improvement Methods
  // ==========================================

  async listProposals(): Promise<import('@jenna/types').ImprovementProposal[]> {
    return this.request<import('@jenna/types').ImprovementProposal[]>('/api/v1/improvement/proposals');
  }

  async createProposal(
    title: string,
    category: import('@jenna/types').ImprovementCategory,
    rationale: string,
    proposed_changes: Record<string, any> = {}
  ): Promise<import('@jenna/types').ImprovementProposal> {
    return this.request<import('@jenna/types').ImprovementProposal>('/api/v1/improvement/proposals', {
      method: 'POST',
      body: JSON.stringify({ title, category, rationale, proposed_changes }),
    });
  }

  async getProposal(proposal_id: string): Promise<import('@jenna/types').ImprovementProposal> {
    return this.request<import('@jenna/types').ImprovementProposal>(`/api/v1/improvement/proposals/${proposal_id}`);
  }

  async runSandboxEvaluation(
    proposal_id: string
  ): Promise<import('@jenna/types').SandboxEvaluationResult> {
    return this.request<import('@jenna/types').SandboxEvaluationResult>(
      `/api/v1/improvement/proposals/${proposal_id}/sandbox-eval`,
      { method: 'POST' }
    );
  }

  async approveProposal(
    proposal_id: string
  ): Promise<import('@jenna/types').ImprovementProposal> {
    return this.request<import('@jenna/types').ImprovementProposal>(
      `/api/v1/improvement/proposals/${proposal_id}/approve`,
      { method: 'POST' }
    );
  }

  async deployCanary(
    proposal_id: string,
    traffic_percentage = 5
  ): Promise<import('@jenna/types').CanaryDeploymentRecord> {
    return this.request<import('@jenna/types').CanaryDeploymentRecord>(
      `/api/v1/improvement/proposals/${proposal_id}/deploy-canary`,
      {
        method: 'POST',
        body: JSON.stringify({ traffic_percentage }),
      }
    );
  }

  async promoteProduction(
    proposal_id: string
  ): Promise<import('@jenna/types').ImprovementProposal> {
    return this.request<import('@jenna/types').ImprovementProposal>(
      `/api/v1/improvement/proposals/${proposal_id}/promote`,
      { method: 'POST' }
    );
  }

  async rollbackProposal(
    proposal_id: string,
    reason = 'Manual operator rollback'
  ): Promise<import('@jenna/types').RollbackRecord> {
    return this.request<import('@jenna/types').RollbackRecord>(
      `/api/v1/improvement/proposals/${proposal_id}/rollback`,
      {
        method: 'POST',
        body: JSON.stringify({ reason }),
      }
    );
  }

  // ==========================================
  // Part 9 — Dashboard, Audit & Usage Methods
  // ==========================================

  async listAuditEvents(
    eventType?: string,
    limit = 50,
    offset = 0
  ): Promise<import('@jenna/types').AuditEventItem[]> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });
    if (eventType) params.set('event_type', eventType);
    return this.request<import('@jenna/types').AuditEventItem[]>(`/api/v1/audit/events?${params.toString()}`);
  }

  async getAuditStats(): Promise<import('@jenna/types').AuditStats> {
    return this.request<import('@jenna/types').AuditStats>('/api/v1/audit/stats');
  }

  async getPendingApprovals(): Promise<import('@jenna/types').PendingApprovalsResponse> {
    return this.request<import('@jenna/types').PendingApprovalsResponse>('/api/v1/approvals/pending');
  }

  async submitApprovalDecision(
    req: import('@jenna/types').ApprovalDecisionRequest
  ): Promise<{ status: string; item_type: string; item_id: string; result_status: string; confirmed: boolean }> {
    return this.request<{ status: string; item_type: string; item_id: string; result_status: string; confirmed: boolean }>(
      '/api/v1/approvals/decide',
      {
        method: 'POST',
        body: JSON.stringify(req),
      }
    );
  }

  async getApprovalHistory(limit = 20): Promise<import('@jenna/types').AuditEventItem[]> {
    return this.request<import('@jenna/types').AuditEventItem[]>(`/api/v1/approvals/history?limit=${limit}`);
  }

  async getPermissionPolicies(): Promise<import('@jenna/types').PermissionPoliciesResponse> {
    return this.request<import('@jenna/types').PermissionPoliciesResponse>('/api/v1/approvals/policies');
  }

  async getUsageSummary(): Promise<import('@jenna/types').UsageSummaryResponse> {
    return this.request<import('@jenna/types').UsageSummaryResponse>('/api/v1/usage/summary');
  }

  async getUsageLogs(limit = 50): Promise<import('@jenna/types').UsageLogEntry[]> {
    return this.request<import('@jenna/types').UsageLogEntry[]>(`/api/v1/usage/logs?limit=${limit}`);
  }

  // ==========================================
  // Part 10 — Android Integration Methods
  // ==========================================

  async generateAndroidPairingCode(): Promise<{ pairing_code: string; expires_in_seconds: number }> {
    return this.request<{ pairing_code: string; expires_in_seconds: number }>(
      '/api/v1/android/pair/generate-code',
      { method: 'POST' }
    );
  }

  async pairAndroidCompanion(payload: {
    pairing_code: string;
    device_name: string;
    model?: string;
    android_version?: string;
    sdk_version?: number;
    granted_permissions?: string[];
  }): Promise<{ device: import('@jenna/types').AndroidDevice; device_token: string }> {
    return this.request<{ device: import('@jenna/types').AndroidDevice; device_token: string }>(
      '/api/v1/android/pair',
      {
        method: 'POST',
        body: JSON.stringify(payload),
      }
    );
  }

  async listAndroidDevices(): Promise<import('@jenna/types').AndroidDevice[]> {
    return this.request<import('@jenna/types').AndroidDevice[]>('/api/v1/android/devices');
  }

  async revokeAndroidDevice(deviceId: string): Promise<import('@jenna/types').AndroidDevice> {
    return this.request<import('@jenna/types').AndroidDevice>(
      `/api/v1/android/devices/${deviceId}/revoke`,
      { method: 'POST' }
    );
  }

  async getAndroidContext(
    deviceId: string
  ): Promise<import('@jenna/types').AndroidContextPayload | null> {
    return this.request<import('@jenna/types').AndroidContextPayload | null>(
      `/api/v1/android/devices/${deviceId}/context`
    );
  }

  async dispatchAndroidAction(
    deviceId: string,
    request: import('@jenna/types').AndroidActionRequest
  ): Promise<import('@jenna/types').AndroidActionResult> {
    return this.request<import('@jenna/types').AndroidActionResult>(
      `/api/v1/android/devices/${deviceId}/action`,
      {
        method: 'POST',
        body: JSON.stringify(request),
      }
    );
  }
}

export const apiClient = new ApiClient();




