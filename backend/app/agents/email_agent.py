import time
import logging
from typing import Any
from app.agents.base import BaseAgent, AgentResult
from app.database.repository import Repository

logger = logging.getLogger("nexus.agents.email")

class EmailAgent(BaseAgent):
    """Specialized Agent for Cross-Platform Email Communication Intelligence."""

    def __init__(self):
        super().__init__(
            agent_id="email_agent",
            name="Email Agent",
            role="Cross-Platform Email Specialist"
        )

    async def run(self, context: dict[str, Any]) -> AgentResult:
        start_time = time.perf_counter()
        emails = Repository.get_important_emails(limit=15)
        unread = Repository.get_unread_emails_count()
        preview = f"Indexed {len(emails)} important emails ({unread} unread) across Gmail and Outlook."
        duration = round(time.perf_counter() - start_time, 2)
        return AgentResult(
            agent_id=self.agent_id,
            agent_name=self.name,
            success=True,
            output={"emails": emails, "unread_count": unread},
            preview=preview,
            duration_seconds=duration
        )
