export type StepStatus = 'waiting' | 'planning' | 'running' | 'completed' | 'failed' | 'needs_review';
export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
export type TaskComplexity = 'simple' | 'moderate' | 'complex';

export interface TaskStep {
  id: string;
  task_id: string;
  step_order: number;
  agent_id: string;
  agent_name: string;
  status: StepStatus;
  operation?: string;
  input_data?: any;
  output_data?: any;
  start_time?: string;
  end_time?: string;
  duration_seconds?: number;
  retry_count?: number;
  error_message?: string;
}

export interface Task {
  id: string;
  title: string;
  user_prompt: string;
  status: TaskStatus;
  complexity: TaskComplexity;
  is_demo: boolean;
  created_at: string;
  updated_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  error_message?: string;
  final_result?: string;
  steps: TaskStep[];
}

export interface TaskSummary {
  id: string;
  title: string;
  user_prompt: string;
  status: TaskStatus;
  complexity: TaskComplexity;
  is_demo: boolean;
  created_at: string;
  completed_at?: string;
  duration_seconds?: number;
  agents_count: number;
}

export interface Agent {
  id: string;
  name: string;
  icon: string;
  role: string;
  description: string;
  capabilities: string[];
  is_enabled: boolean;
  is_system: boolean;
}

export interface FileItem {
  id: string;
  filename: string;
  original_name: string;
  file_type: string;
  file_size: number;
  file_path: string;
  task_id?: string;
  status: string;
  metadata?: any;
  created_at: string;
}

export interface ReportRisk {
  title: string;
  category?: string;
  severity: 'Critical' | 'High' | 'Medium' | 'Low';
  probability?: 'High' | 'Medium' | 'Low';
  impact?: string;
  mitigation: string;
}

export interface Report {
  id: string;
  task_id?: string;
  title: string;
  summary?: string;
  executive_summary?: string;
  methodology?: string;
  key_findings: string[];
  analysis?: string;
  risks: ReportRisk[];
  recommendations: string[];
  conclusion?: string;
  full_markdown?: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  task_id?: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  answer?: string;
  created_at?: string;
  intent?: string;
  usedTaskContext?: boolean;
  used_task_context?: boolean;
  newTaskId?: string;
  execution_steps?: string[];
  steps?: string[];
  raw_tool_data?: any;
  account_connected?: boolean;
}

export interface Settings {
  ai_provider: string;
  ai_api_key?: string;
  ai_base_url: string;
  ai_model: string;
  ai_temperature: number;
  ai_max_tokens: number;
  demo_mode: boolean;
  enable_web_search: boolean;
  google_calendar_url?: string;
  outlook_calendar_url?: string;
  auto_scan_pc?: boolean;
  web_search_api_key?: string;
  github_token?: string;
  github_repo?: string;
  is_configured: boolean;
}

export interface CalendarEvent {
  id: string;
  title: string;
  start_time: string;
  end_time: string;
  location?: string;
  description?: string;
  category: 'meeting' | 'task' | 'review';
  source: string;
  priority?: 'high' | 'medium' | 'normal';
  join_url?: string | null;
  meeting_url?: string | null;
  is_important?: boolean | number;
  platform?: 'google_meet' | 'zoom' | 'teams' | 'webex' | 'in_person' | string;
  starts_in_minutes?: number;
  ownership_status?: string;
  status?: string;
  organizer?: string;
  attendees_count?: number;
  attendees_list?: any[];
  duration?: string;
  discrepancy_note?: string;
  is_conflict?: boolean | number;
}

export interface TodayScheduleResponse {
  date: string;
  day_of_week: string;
  current_time: string;
  greeting?: string;
  total_meetings_today: number;
  meetings_today_count?: number;
  unread_important_emails_count?: number;
  upcoming_meetings_count?: number;
  tasks_count?: number;
  calendar_conflicts_count?: number;
  important_meetings_count?: number;
  meetings: CalendarEvent[];
  upcoming_meetings?: CalendarEvent[];
  conflicts?: CalendarEvent[];
  important_emails?: any[];
  work_tasks: CalendarEvent[];
  next_meeting?: CalendarEvent | null;
}

export interface AppConnector {
  name: string;
  connected: boolean;
  events_count: number;
  type: string;
  status: string;
}

export interface ConnectorsStatusResponse {
  outlook: AppConnector;
  google_calendar: AppConnector;
  gmail?: AppConnector;
  github?: AppConnector;
  local_pc: AppConnector;
}

export interface ProviderAuthStatus {
  name?: string;
  connected: boolean;
  email?: string;
  account_email?: string;
  type?: string;
  scopes?: string[];
  calendar_sync?: boolean;
  gmail_sync?: boolean;
  mail_sync?: boolean;
  last_sync?: string;
  client_id?: string;
  client_secret?: string;
  has_secret?: boolean;
  redirect_uri?: string;
}

export interface AuthStatusResponse {
  google: ProviderAuthStatus;
  gmail?: ProviderAuthStatus;
  google_calendar?: ProviderAuthStatus;
  google_meet?: ProviderAuthStatus;
  microsoft: ProviderAuthStatus;
  outlook_mail?: ProviderAuthStatus;
  outlook_calendar?: ProviderAuthStatus;
  teams?: ProviderAuthStatus;
  last_synced_at?: string;
}

declare global {
  interface Window {
    nexusBridge?: {
      openFileDialog: () => Promise<string[] | null>;
      getAppVersion: () => Promise<string>;
      openExternal: (url: string) => Promise<void>;
    };
  }
}



