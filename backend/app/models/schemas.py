from typing import Any, Optional
from pydantic import BaseModel, Field

# TASKS
class TaskCreateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="The user's goal or prompt")
    file_ids: list[str] = Field(default_factory=list, description="IDs of files attached to this task")
    is_demo: bool = Field(default=False, description="Whether to execute in deterministic Demo Mode")

class TaskStepResponse(BaseModel):
    id: str
    task_id: str
    step_order: int
    agent_id: str
    agent_name: str
    status: str
    operation: Optional[str] = None
    input_data: Optional[Any] = None
    output_data: Optional[Any] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_seconds: Optional[float] = 0.0
    retry_count: Optional[int] = 0
    error_message: Optional[str] = None

class TaskResponse(BaseModel):
    id: str
    title: str
    user_prompt: str
    status: str
    complexity: str
    is_demo: bool
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = 0.0
    error_message: Optional[str] = None
    final_result: Optional[str] = None
    steps: list[TaskStepResponse] = Field(default_factory=list)

class TaskListItem(BaseModel):
    id: str
    title: str
    user_prompt: str
    status: str
    complexity: str
    is_demo: bool
    created_at: str
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = 0.0
    agents_count: int = 0

# AGENTS
class AgentResponse(BaseModel):
    id: str
    name: str
    icon: str
    role: str
    description: str
    capabilities: list[str]
    is_enabled: bool
    is_system: bool

class AgentToggleRequest(BaseModel):
    is_enabled: bool

# FILES
class FileResponse(BaseModel):
    id: str
    filename: str
    original_name: str
    file_type: str
    file_size: int
    file_path: str
    task_id: Optional[str] = None
    status: str
    metadata: Optional[Any] = None
    created_at: str

# REPORTS
class ReportResponse(BaseModel):
    id: str
    task_id: Optional[str]
    title: str
    summary: Optional[str] = None
    executive_summary: Optional[str] = None
    methodology: Optional[str] = None
    key_findings: list[str] = Field(default_factory=list)
    analysis: Optional[str] = None
    risks: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    conclusion: Optional[str] = None
    full_markdown: Optional[str] = None
    created_at: str
    updated_at: str

class ReportRenameRequest(BaseModel):
    title: str = Field(..., min_length=1)

# CHAT
class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1)
    task_id: Optional[str] = None
    activeTaskId: Optional[str] = None
    conversationId: Optional[str] = None
    mode: Optional[str] = "live"

class ChatMessageResponse(BaseModel):
    id: str
    task_id: Optional[str] = None
    activeTaskId: Optional[str] = None
    role: str = "assistant"
    content: str
    answer: Optional[str] = None
    intent: Optional[str] = "GENERAL_QUESTION"
    usedTaskContext: bool = False
    used_task_context: bool = False
    newTaskId: Optional[str] = None
    newExecutionId: Optional[str] = None
    created_at: Optional[str] = None
    execution_steps: Optional[list[str]] = None

# SETTINGS
class SettingsDTO(BaseModel):
    ai_provider: str
    ai_api_key: Optional[str] = None
    ai_base_url: str
    ai_model: str
    ai_temperature: float
    ai_max_tokens: int
    demo_mode: bool
    enable_web_search: bool
    google_calendar_url: Optional[str] = None
    outlook_calendar_url: Optional[str] = None
    auto_scan_pc: bool = True
    web_search_api_key: Optional[str] = None
    github_token: Optional[str] = None
    github_repo: Optional[str] = None
    is_configured: bool = False

class SettingsUpdateRequest(BaseModel):
    ai_provider: Optional[str] = None
    ai_api_key: Optional[str] = None
    ai_base_url: Optional[str] = None
    ai_model: Optional[str] = None
    ai_temperature: Optional[float] = None
    ai_max_tokens: Optional[int] = None
    demo_mode: Optional[bool] = None
    enable_web_search: Optional[bool] = None
    google_calendar_url: Optional[str] = None
    outlook_calendar_url: Optional[str] = None
    auto_scan_pc: Optional[bool] = None
    web_search_api_key: Optional[str] = None
    github_token: Optional[str] = None
    github_repo: Optional[str] = None
