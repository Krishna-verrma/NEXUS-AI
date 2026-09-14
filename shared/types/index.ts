/**
 * Nexus AI - Shared TypeScript Definitions
 * Standard interface contract between Frontend, Backend, and Desktop layers.
 */

export type AgentRole =
  | 'orchestrator'
  | 'computer_agent'
  | 'file_agent'
  | 'web_agent'
  | 'coding_agent'
  | 'productivity_agent'
  | 'communication_agent'
  | 'data_agent'
  | 'creative_agent';

export type AgentStatus = 'idle' | 'planning' | 'executing' | 'waiting_approval' | 'completed' | 'error';

export interface AgentDescriptor {
  id: string;
  name: string;
  role: AgentRole;
  description: string;
  avatar: string;
  color: string;
  capabilities: string[];
  tools: string[];
  status: AgentStatus;
  currentTask?: string;
  totalExecutions: number;
}

export type TaskPriority = 'low' | 'medium' | 'high' | 'critical';
export type TaskStatus = 'queued' | 'in_progress' | 'waiting_approval' | 'completed' | 'failed' | 'cancelled';

export interface TaskStep {
  id: string;
  title: string;
  agentRole: AgentRole;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  details?: string;
  toolUsed?: string;
  startedAt?: string;
  completedAt?: string;
}

export interface TaskItem {
  id: string;
  title: string;
  description?: string;
  priority: TaskPriority;
  status: TaskStatus;
  progress: number; // 0 - 100
  assignedAgent: AgentRole;
  steps: TaskStep[];
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
}

export type MessageSender = 'user' | 'assistant' | 'system' | 'agent';

export interface ToolCallTrace {
  toolName: string;
  parameters: Record<string, any>;
  result?: any;
  status: 'pending' | 'success' | 'failed' | 'requires_permission';
  executionTimeMs?: number;
}

export interface AgentActivityTrace {
  agentRole: AgentRole;
  action: string;
  status: 'started' | 'step' | 'tool_call' | 'finished';
  timestamp: string;
  detail?: string;
  toolCalls?: ToolCallTrace[];
}

export interface ChatMessage {
  id: string;
  sessionId: string;
  sender: MessageSender;
  content: string;
  timestamp: string;
  agentRole?: AgentRole;
  status?: 'sending' | 'streaming' | 'completed' | 'failed';
  activityTraces?: AgentActivityTrace[];
  securityTicketId?: string;
}

export interface ChatSession {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messageCount: number;
}

export type SecurityRiskLevel = 'low' | 'medium' | 'high' | 'critical';
export type SecurityTicketStatus = 'pending' | 'approved' | 'rejected' | 'timeout';

export interface SecurityTicket {
  id: string;
  riskLevel: SecurityRiskLevel;
  operationName: string;
  description: string;
  commandOrPayload: string;
  agentRole: AgentRole;
  status: SecurityTicketStatus;
  createdAt: string;
  resolvedAt?: string;
}

export interface SystemVitals {
  cpuUsagePercent: number;
  memoryUsagePercent: number;
  diskFreeGb: number;
  uptimeSeconds: number;
  isDemoMode: boolean;
  activeAgentsCount: number;
  activeTasksCount: number;
  backendVersion: string;
}

export interface AutomationRule {
  id: string;
  name: string;
  description: string;
  triggerType: 'cron' | 'event' | 'interval';
  triggerSchedule: string;
  enabled: boolean;
  targetAgent: AgentRole;
  actionPrompt: string;
  lastRun?: string;
  nextRun?: string;
}
