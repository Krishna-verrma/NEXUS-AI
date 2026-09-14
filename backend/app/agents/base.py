import time
import datetime
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from app.tools import dispatch_tool

class AgentResult:
    def __init__(
        self,
        agent_role: str,
        response: str,
        status: str = "completed",
        activity_traces: Optional[List[Dict[str, Any]]] = None,
        security_ticket: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None
    ):
        self.agent_role = agent_role
        self.response = response
        self.status = status
        self.activity_traces = activity_traces or []
        self.security_ticket = security_ticket
        self.data = data

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_role": self.agent_role,
            "response": self.response,
            "status": self.status,
            "activity_traces": self.activity_traces,
            "security_ticket": self.security_ticket,
            "data": self.data,
        }

class BaseAgent(ABC):
    def __init__(
        self,
        role: str,
        name: str,
        description: str,
        capabilities: List[str],
        allowed_tools: List[str]
    ):
        self.role = role
        self.name = name
        self.description = description
        self.capabilities = capabilities
        self.allowed_tools = allowed_tools

    @abstractmethod
    def execute(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> AgentResult:
        """Execute agent workflow on user prompt with optional live progress callback."""
        pass

    def emit_trace(
        self,
        action: str,
        detail: str = "",
        status: str = "step",
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        trace = {
            "agentRole": self.role,
            "action": action,
            "status": status,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "detail": detail,
            "toolCalls": tool_calls or []
        }
        if callback:
            callback(trace)
        return trace

    def invoke_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name not in self.allowed_tools:
            return {"success": False, "error": f"Tool '{tool_name}' not allowed for agent '{self.role}'"}
        return dispatch_tool(tool_name, arguments, agent_role=self.role)
