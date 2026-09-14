from pydantic import BaseModel, Field
from typing import List, Optional

class TaskStepSchema(BaseModel):
    id: str
    title: str
    agentRole: str
    status: str = "pending"
    details: Optional[str] = None
    toolUsed: Optional[str] = None
    startedAt: Optional[str] = None
    completedAt: Optional[str] = None

class TaskItemResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    status: str = "queued"
    progress: int = 0
    assignedAgent: str = "orchestrator"
    steps: List[TaskStepSchema] = Field(default_factory=list)
    createdAt: str
    updatedAt: str
    completedAt: Optional[str] = None

class TaskCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    assigned_agent: Optional[str] = "orchestrator"
