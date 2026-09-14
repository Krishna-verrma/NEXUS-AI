from pydantic import BaseModel
from typing import List, Optional

class AgentResponse(BaseModel):
    id: str
    role: str
    name: str
    description: str
    avatar: str
    color: str
    capabilities: List[str]
    tools: List[str]
    status: str
    currentTask: Optional[str] = None
    totalExecutions: int = 0

class AgentExecutionRequest(BaseModel):
    agent_role: str
    prompt: str
    parameters: Optional[dict] = None
