import { request } from './api';

export interface ChatMessagePayload {
  session_id?: string;
  message: string;
  target_agent?: string;
}

export interface ChatMessageData {
  id: string;
  sessionId: string;
  sender: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  agentRole?: string;
  status: string;
  activityTraces?: any[];
  securityTicketId?: string;
}

export interface ChatSessionData {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messageCount: number;
}

export const chatApi = {
  sendMessage: (payload: ChatMessagePayload): Promise<ChatMessageData> => {
    return request<ChatMessageData>('/api/chat', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  getSessions: (): Promise<ChatSessionData[]> => {
    return request<ChatSessionData[]>('/api/chat/sessions');
  },

  getSessionMessages: (sessionId: string): Promise<ChatMessageData[]> => {
    return request<ChatMessageData[]>(`/api/chat/sessions/${sessionId}/messages`);
  },
};
