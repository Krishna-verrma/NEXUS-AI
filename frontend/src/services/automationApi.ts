import { request } from './api';

export interface AutomationData {
  id: string;
  name: string;
  description: string;
  trigger_type: string;
  trigger_schedule: string;
  enabled: boolean;
  target_agent: string;
  action_prompt: string;
  last_run?: string;
  next_run?: string;
}

export const automationApi = {
  getAutomations: (): Promise<AutomationData[]> => {
    return request<AutomationData[]>('/api/automations');
  },

  toggleAutomation: (id: string): Promise<{ success: boolean; automation: AutomationData }> => {
    return request<{ success: boolean; automation: AutomationData }>(`/api/automations/${id}/toggle`, {
      method: 'POST',
    });
  },

  triggerAutomation: (id: string): Promise<{ success: boolean; automation: AutomationData; result: any }> => {
    return request<{ success: boolean; automation: AutomationData; result: any }>(`/api/automations/${id}/trigger`, {
      method: 'POST',
    });
  },
};
