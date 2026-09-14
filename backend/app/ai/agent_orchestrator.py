import logging
from typing import Any, Optional
from app.services.datetime_service import DateTimeService

logger = logging.getLogger("nexus.ai.agent_orchestrator")

class MultiAgentOrchestrator:
    """
    Coordinates specialized agents:
      1. Planner Agent
      2. Calendar Agent
      3. Research Agent
      4. File Agent
      5. System/Task Agent
      6. Reasoning Agent
      7. Response Agent
    Selects optimal execution route without running every agent for every request.
    """

    @classmethod
    def get_route(cls, intent: str, message: str, has_files: bool = False) -> list[str]:
        lower = message.lower()
        if intent in ("CALENDAR_QUERY", "CALENDAR_ACTION") or any(kw in lower for kw in ["meeting", "calendar", "schedule", "tomorrow", "september"]):
            return ["planner", "calendar", "response"]
        if has_files or any(kw in lower for kw in ["pdf", "csv", "xlsx", "file", "document", "attachment"]):
            return ["planner", "file", "reasoning", "response"]
        if any(kw in lower for kw in ["research", "latest", "news", "trend", "competitor", "market"]):
            return ["planner", "research", "reasoning", "response"]
        if any(kw in lower for kw in ["run", "execute", "build", "compile", "terminal", "command"]):
            return ["planner", "system", "reasoning", "response"]
        # Default simple route: Planner directly to Response
        return ["planner", "response"]
