import time
import logging
from typing import Any
from app.agents.base import BaseAgent, AgentResult
from app.database.repository import Repository
from app.integrations.calendar.unified_calendar import UnifiedCalendarEngine
from app.ai.model_router import model_router

logger = logging.getLogger("nexus.agents.calendar")

class CalendarAgent(BaseAgent):
    """Specialized Agent for Calendar queries, conflict detection, and schedule management."""

    def __init__(self):
        super().__init__(
            agent_id="calendar_agent",
            name="Calendar Agent",
            role="Personal Calendar Specialist"
        )

    async def run(self, context: dict[str, Any]) -> AgentResult:
        start_time = time.perf_counter()
        query = context.get("query", context.get("user_prompt", "today's schedule"))
        
        # Query verified calendar events
        events = Repository.get_calendar_events(
            status_filter=["MY_MEETING", "INVITED", "OPTIONAL", "ORGANIZER"],
            limit=50
        )
        conflicts = Repository.get_calendar_conflicts()

        summary_lines = [f"Found {len(events)} verified meetings. Total conflicts: {len(conflicts)}."]
        for ev in events[:5]:
            summary_lines.append(f"- {ev.get('start_time')} | {ev.get('title')} ({ev.get('platform') or 'In-person'})")

        content = "\n".join(summary_lines)
        duration = round(time.perf_counter() - start_time, 2)
        return AgentResult(
            agent_id=self.agent_id,
            agent_name=self.name,
            success=True,
            output={"events": events, "conflicts": conflicts, "summary": content},
            preview=self.format_preview(content),
            duration_seconds=duration
        )
