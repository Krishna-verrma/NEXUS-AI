import { Task, TaskSummary, Agent, FileItem, Report, Settings, ChatMessage } from '../types';

const API_BASE = 'http://127.0.0.1:8000';

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        'Accept': 'application/json',
        ...(options?.headers || {})
      }
    });
    if (!res.ok) {
      let errDetail = `HTTP ${res.status}`;
      try {
        const body = await res.json();
        errDetail = body.detail || body.error || errDetail;
      } catch {}
      throw new Error(errDetail);
    }
    return await res.json();
  } catch (err: any) {
    console.error(`API error on ${endpoint}:`, err);
    throw err;
  }
}

export const api = {
  // Tasks
  async createTask(prompt: string, fileIds: string[] = [], isDemo: boolean = false): Promise<Task> {
    return request<Task>('/api/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt, file_ids: fileIds, is_demo: isDemo })
    });
  },

  async startDemoTask(): Promise<Task> {
    return request<Task>('/api/tasks/demo', { method: 'POST' });
  },

  async listTasks(): Promise<TaskSummary[]> {
    return request<TaskSummary[]>('/api/tasks');
  },

  async getTask(taskId: string): Promise<Task> {
    return request<Task>(`/api/tasks/${taskId}`);
  },

  async cancelTask(taskId: string): Promise<Task> {
    return request<Task>(`/api/tasks/${taskId}/cancel`, { method: 'POST' });
  },

  async runTask(taskId: string): Promise<Task> {
    return request<Task>(`/api/tasks/${taskId}/run`, { method: 'POST' });
  },

  // Agents
  async listAgents(): Promise<Agent[]> {
    return request<Agent[]>('/api/agents');
  },

  async toggleAgent(agentId: string, isEnabled: boolean): Promise<Agent> {
    return request<Agent>(`/api/agents/${agentId}/toggle`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_enabled: isEnabled })
    });
  },

  // Files
  async uploadFile(file: File, taskId?: string): Promise<FileItem> {
    const formData = new FormData();
    formData.append('file', file);
    if (taskId) formData.append('task_id', taskId);

    const res = await fetch(`${API_BASE}/api/files/upload`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },

  async listFiles(taskId?: string): Promise<FileItem[]> {
    const url = taskId ? `/api/files?task_id=${taskId}` : '/api/files';
    return request<FileItem[]>(url);
  },

  async deleteFile(fileId: string): Promise<void> {
    await request(`/api/files/${fileId}`, { method: 'DELETE' });
  },

  // Reports
  async listReports(): Promise<Report[]> {
    return request<Report[]>('/api/reports');
  },

  async getReport(reportId: string): Promise<Report> {
    return request<Report>(`/api/reports/${reportId}`);
  },

  async renameReport(reportId: string, title: string): Promise<Report> {
    return request<Report>(`/api/reports/${reportId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title })
    });
  },

  async deleteReport(reportId: string): Promise<void> {
    await request(`/api/reports/${reportId}`, { method: 'DELETE' });
  },

  // Chat
  async sendChatMessage(message: string, taskId?: string): Promise<ChatMessage> {
    return request<ChatMessage>('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        task_id: taskId,
        activeTaskId: taskId,
        mode: 'live'
      })
    });
  },

  async getChatMessages(taskId?: string): Promise<ChatMessage[]> {
    const url = taskId ? `/api/chat/messages?task_id=${taskId}` : '/api/chat/messages';
    return request<ChatMessage[]>(url);
  },

  // Settings & Health
  async getSettings(): Promise<Settings> {
    return request<Settings>('/api/settings');
  },

  async updateSettings(settings: Partial<Settings>): Promise<Settings> {
    return request<Settings>('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings)
    });
  },

  async checkHealth(): Promise<{ status: string; demo_mode: boolean }> {
    return request<{ status: string; demo_mode: boolean }>('/api/health');
  },

  async testAiConnection(params?: { provider?: string; api_key?: string; base_url?: string; model?: string }): Promise<{ success: boolean; latency_ms?: number; model?: string; provider?: string; preview?: string; error?: string; message: string }> {
    return request('/api/settings/test-ai', {
      method: 'POST',
      headers: params ? { 'Content-Type': 'application/json' } : undefined,
      body: params ? JSON.stringify(params) : undefined
    });
  },

  async testGithubConnection(token?: string): Promise<{ success: boolean; login?: string; name?: string; public_repos?: number; message: string }> {
    return request('/api/settings/test-github', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token })
    });
  },

  async syncGithub(token?: string, repo?: string): Promise<{ success: boolean; count: number; message: string }> {
    return request('/api/settings/sync-github', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, repo })
    });
  },

  // Calendar & Schedule
  async getTodaySchedule(): Promise<any> {
    return request<any>('/api/calendar/today');
  },

  async getUpcomingSchedule(days: number = 365): Promise<any> {
    return request<any>(`/api/calendar/upcoming?days=${days}`);
  },

  async getCalendarConnectors(): Promise<any> {
    return request<any>('/api/calendar/connectors');
  },

  async syncCalendarUrl(url: string, sourceName: string = 'google_calendar'): Promise<any> {
    return request<any>('/api/calendar/sync-url', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, source_name: sourceName })
    });
  },

  async scanPcCalendar(): Promise<any> {
    return request<any>('/api/calendar/scan-pc', {
      method: 'POST'
    });
  },

  async importCalendarIcs(icsContent: string, sourceName: string = 'ics_upload'): Promise<any> {
    return request<any>('/api/calendar/import', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ics_content: icsContent, source_name: sourceName })
    });
  },

  async clearSampleCalendarEvents(): Promise<any> {
    return request<any>('/api/calendar/clear-samples', {
      method: 'POST'
    });
  },

  // OAuth & Workspace Command Center
  async getAuthStatus(): Promise<any> {
    return request<any>('/api/auth/status');
  },

  async getOAuthLoginUrl(provider: 'google' | 'microsoft'): Promise<{ url: string }> {
    return request<{ url: string }>(`/api/auth/login/${provider}`);
  },

  async disconnectOAuth(provider: 'google' | 'microsoft'): Promise<{ success: boolean; message: string }> {
    return request<{ success: boolean; message: string }>(`/api/auth/disconnect/${provider}`, {
      method: 'POST'
    });
  },

  async configureOAuth(provider: 'google' | 'microsoft', config: { client_id: string; client_secret: string }): Promise<{ success: boolean; message: string }> {
    return request<{ success: boolean; message: string }>(`/api/auth/config/${provider}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
  },

  async triggerCalendarSync(): Promise<{ success: boolean; message: string }> {
    return request<{ success: boolean; message: string }>('/api/auth/sync', {
      method: 'POST'
    });
  },

  async testGmailConnection(query: string = 'meeting OR invite OR scheduled OR project'): Promise<{ success: boolean; count: number; messages?: any[]; message: string }> {
    return request<{ success: boolean; count: number; messages?: any[]; message: string }>(`/api/auth/google/test-gmail?query=${encodeURIComponent(query)}`);
  }
};

