import time
import logging
from typing import Any
from app.agents.base import BaseAgent, AgentResult
from app.database.repository import Repository
from app.services.oauth.google_oauth import GoogleOAuthService

logger = logging.getLogger("nexus.agents.gmail")

class GmailAgent(BaseAgent):
    """Specialized Agent for Gmail communications and meeting intelligence."""

    def __init__(self):
        super().__init__(
            agent_id="gmail_agent",
            name="Gmail Agent",
            role="Gmail Intelligence Specialist"
        )

    async def run(self, context: dict[str, Any]) -> AgentResult:
        start_time = time.perf_counter()
        query = context.get("query", "important")

        emails = await GoogleOAuthService.fetch_gmail_messages(query=query, max_results=10)
        if not emails:
            emails = Repository.get_important_emails(limit=10)

        preview = f"Indexed {len(emails)} relevant emails from Gmail."
        duration = round(time.perf_counter() - start_time, 2)
        return AgentResult(
            agent_id=self.agent_id,
            agent_name=self.name,
            success=True,
            output={"messages": emails, "count": len(emails)},
            preview=preview,
            duration_seconds=duration
        )
