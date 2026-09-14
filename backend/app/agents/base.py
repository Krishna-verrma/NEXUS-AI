import time
from typing import Any, Optional
from pydantic import BaseModel, Field

class AgentResult(BaseModel):
    agent_id: str
    agent_name: str
    success: bool
    output: Any
    preview: str
    confidence: float = 1.0
    metrics: dict[str, Any] = Field(default_factory=dict)
    duration_seconds: float = 0.0
    error: Optional[str] = None

class BaseAgent:
    """Base class for all specialized and orchestrator agents in Nexus AI."""
    def __init__(self, agent_id: str, name: str, role: str):
        self.agent_id = agent_id
        self.name = name
        self.role = role

    async def run(self, context: dict[str, Any]) -> AgentResult:
        """Execute the agent's core workflow on the provided context."""
        raise NotImplementedError("Subclasses must implement run()")

    def format_preview(self, text: str, max_chars: int = 240) -> str:
        """Generate a clean, high-level preview string."""
        cleaned = " ".join(text.split())
        if len(cleaned) <= max_chars:
            return cleaned
        return cleaned[:max_chars].rstrip() + "..."
