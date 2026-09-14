import time
import logging
from typing import Any
from app.agents.base import BaseAgent, AgentResult
from app.database.repository import Repository
from app.services.oauth.microsoft_oauth import MicrosoftOAuthService

logger = logging.getLogger("nexus.agents.outlook")

class OutlookAgent(BaseAgent):
    """Specialized Agent for Microsoft Outlook mail, calendar, and Teams."""

    def __init__(self):
        super().__init__(
            agent_id="outlook_agent",
            name="Outlook Agent",
            role="Microsoft 365 / Outlook Specialist"
        )

    async def run(self, context: dict[str, Any]) -> AgentResult:
        start_time = time.perf_counter()
        events = Repository.get_calendar_events(source="outlook", limit=15)
        preview = f"Retrieved {len(events)} Outlook calendar events."
        duration = round(time.perf_counter() - start_time, 2)
        return AgentResult(
            agent_id=self.agent_id,
            agent_name=self.name,
            success=True,
            output={"events": events, "count": len(events)},
            preview=preview,
            duration_seconds=duration
        )
