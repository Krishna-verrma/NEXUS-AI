import { request } from './api';

export interface AgentDescriptorData {
  id: string;
  role: string;
  name: string;
  description: string;
  avatar: string;
  color: string;
  capabilities: string[];
  tools: string[];
  status: string;
  currentTask?: string;
  totalExecutions: number;
}

export const agentApi = {
  getAgents: (): Promise<AgentDescriptorData[]> => {
    return request<AgentDescriptorData[]>('/api/agents');
  },

  getAgentDetails: (role: string): Promise<AgentDescriptorData> => {
    return request<AgentDescriptorData>(`/api/agents/${role}`);
  },

  executeAgent: (agentRole: string, prompt: string): Promise<any> => {
    return request<any>('/api/agents/execute', {
      method: 'POST',
      body: JSON.stringify({ agent_role: agentRole, prompt }),
    });
  },
};
