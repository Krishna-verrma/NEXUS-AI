import { request } from './api';

export interface TaskStepData {
  id: string;
  title: string;
  agentRole: string;
  status: string;
  details?: string;
  toolUsed?: string;
}

export interface TaskData {
  id: string;
  title: string;
  description?: string;
  priority: string;
  status: string;
  progress: number;
  assignedAgent: string;
  steps: TaskStepData[];
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
}

export const taskApi = {
  getTasks: (): Promise<TaskData[]> => {
    return request<TaskData[]>('/api/tasks');
  },

  createTask: (title: string, description?: string, priority = 'medium', assignedAgent = 'orchestrator'): Promise<TaskData> => {
    return request<TaskData>('/api/tasks', {
      method: 'POST',
      body: JSON.stringify({ title, description, priority, assigned_agent: assignedAgent }),
    });
  },

  cancelTask: (taskId: string): Promise<any> => {
    return request<any>(`/api/tasks/${taskId}/cancel`, {
      method: 'POST',
    });
  },
};
