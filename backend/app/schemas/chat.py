from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ChatMessageCreate(BaseModel):
    session_id: Optional[str] = None
    message: str = Field(..., min_length=1)
    target_agent: Optional[str] = None

class ToolCallTraceSchema(BaseModel):
    toolName: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Any] = None
    status: str = "success"
    executionTimeMs: Optional[float] = None

class AgentActivityTraceSchema(BaseModel):
    agentRole: str
    action: str
    status: str = "finished"
    timestamp: str
    detail: Optional[str] = None
    toolCalls: Optional[List[ToolCallTraceSchema]] = None

class ChatMessageResponse(BaseModel):
    id: str
    sessionId: str
    sender: str
    content: str
    timestamp: str
    agentRole: Optional[str] = None
    status: str = "completed"
    activityTraces: Optional[List[AgentActivityTraceSchema]] = None
    securityTicketId: Optional[str] = None

class ChatSessionResponse(BaseModel):
    id: str
    title: str
    createdAt: str
    updatedAt: str
    messageCount: int = 0
