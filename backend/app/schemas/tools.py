from pydantic import BaseModel
from typing import Dict, Any, Optional

class ToolExecutionRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]

class ToolExecutionResult(BaseModel):
    tool_name: str
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float
    requires_approval: bool = False
    ticket_id: Optional[str] = None
