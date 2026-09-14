import time
import logging
from typing import Any
from app.agents.base import BaseAgent, AgentResult
from app.database.repository import Repository

logger = logging.getLogger("nexus.agents.meet")

class MeetAgent(BaseAgent):
    """Specialized Agent for Google Meet link extraction and conference intelligence."""

    def __init__(self):
        super().__init__(
            agent_id="meet_agent",
            name="Google Meet Agent",
            role="Video Conferencing Specialist"
        )

    async def run(self, context: dict[str, Any]) -> AgentResult:
        start_time = time.perf_counter()
        events = Repository.get_calendar_events(limit=30)
        meet_events = [
            e for e in events 
            if e.get("platform") == "google_meet" or (e.get("join_url") and "meet.google.com" in e["join_url"])
        ]
        preview = f"Identified {len(meet_events)} Google Meet video meetings."
        duration = round(time.perf_counter() - start_time, 2)
        return AgentResult(
            agent_id=self.agent_id,
            agent_name=self.name,
            success=True,
            output={"meet_events": meet_events, "count": len(meet_events)},
            preview=preview,
            duration_seconds=duration
        )
