import time
import logging
from typing import Any
from app.agents.base import BaseAgent, AgentResult
from app.database.repository import Repository

logger = logging.getLogger("nexus.agents.meeting")

class MeetingAgent(BaseAgent):
    """Specialized Agent for Meeting lifecycle, attendees, join links, and prep briefings."""

    def __init__(self):
        super().__init__(
            agent_id="meeting_agent",
            name="Meeting Agent",
            role="Meeting Lifecycle Specialist"
        )

    async def run(self, context: dict[str, Any]) -> AgentResult:
        start_time = time.perf_counter()
        events = Repository.get_calendar_events(limit=20)
        preview = f"Tracking {len(events)} meetings across Google and Outlook."
        duration = round(time.perf_counter() - start_time, 2)
        return AgentResult(
            agent_id=self.agent_id,
            agent_name=self.name,
            success=True,
            output={"meetings": events, "count": len(events)},
            preview=preview,
            duration_seconds=duration
        )
