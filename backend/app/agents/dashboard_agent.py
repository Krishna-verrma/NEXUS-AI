import time
import logging
from datetime import datetime
from typing import Any
from app.agents.base import BaseAgent, AgentResult
from app.database.repository import Repository

logger = logging.getLogger("nexus.agents.dashboard")

class DashboardAgent(BaseAgent):
    """Command Center Dashboard Orchestrator Agent."""

    def __init__(self):
        super().__init__(
            agent_id="dashboard_agent",
            name="Dashboard Command Agent",
            role="Workspace Command Center Orchestrator"
        )

    async def run(self, context: dict[str, Any]) -> AgentResult:
        start_time = time.perf_counter()
        now = datetime.now()
        today_date = now.strftime("%Y-%m-%d")

        today_meetings = Repository.get_today_meetings(today_date)
        upcoming_meetings = Repository.get_upcoming_meetings(now.strftime("%Y-%m-%d %H:%M:%S"), limit=10)
        conflicts = Repository.get_calendar_conflicts()
        unread_emails = Repository.get_unread_emails_count()
        important_emails = Repository.get_important_emails(limit=5)

        preview = f"Dashboard aggregated: {len(today_meetings)} today's meetings, {unread_emails} unread emails, {len(conflicts)} conflicts."
        duration = round(time.perf_counter() - start_time, 2)
        return AgentResult(
            agent_id=self.agent_id,
            agent_name=self.name,
            success=True,
            output={
                "today_meetings": today_meetings,
                "upcoming_meetings": upcoming_meetings,
                "conflicts": conflicts,
                "unread_emails_count": unread_emails,
                "important_emails": important_emails
            },
            preview=preview,
            duration_seconds=duration
        )
