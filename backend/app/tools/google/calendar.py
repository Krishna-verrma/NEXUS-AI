import logging
from typing import Any, Optional
from datetime import datetime, timedelta
from app.tools.base import BaseTool, ToolResult, PermissionLevel
from app.integrations.calendar.unified_calendar import UnifiedCalendarEngine
from app.database.repository import Repository

logger = logging.getLogger("nexus.tools.google.calendar")

class GoogleCalendarTool(BaseTool):
    """Real tool to query verified Google Calendar events for the user."""

    def __init__(self):
        super().__init__(
            name="google.calendar.get_events",
            description="Query Google Calendar events for a given time window (e.g. today, tomorrow, this week). Returns verified meetings where user is attendee or organizer.",
            permission_level=PermissionLevel.READ_ONLY
        )
        self.input_schema = {
            "start_datetime": "string (format 'YYYY-MM-DD HH:MM:SS' or 'today' or 'tomorrow')",
            "end_datetime": "optional string (format 'YYYY-MM-DD HH:MM:SS')",
            "include_all_providers": "optional boolean (default: true)"
        }
        self.output_schema = {
            "events": "list of verified meetings",
            "count": "integer count",
            "summary": "overview summary of schedule"
        }

    async def execute(
        self,
        start_datetime: Optional[str] = None,
        end_datetime: Optional[str] = None,
        include_all_providers: bool = True,
        **kwargs: Any
    ) -> ToolResult:
        try:
            now = datetime.now()
            today_str = now.strftime("%Y-%m-%d")

            # Resolve query range
            s_dt = start_datetime or kwargs.get("date") or today_str
            if s_dt == "today":
                start_dt = f"{today_str} 00:00:00"
                end_dt = f"{today_str} 23:59:59"
            elif s_dt == "tomorrow":
                tom = (now + timedelta(days=1)).strftime("%Y-%m-%d")
                start_dt = f"{tom} 00:00:00"
                end_dt = f"{tom} 23:59:59"
            elif s_dt == "week" or s_dt == "this_week":
                start_dt = f"{today_str} 00:00:00"
                end_dt = (now + timedelta(days=7)).strftime("%Y-%m-%d 23:59:59")
            else:
                start_dt = s_dt if " " in s_dt else f"{s_dt} 00:00:00"
                end_dt = end_datetime or (now + timedelta(days=1)).strftime("%Y-%m-%d 23:59:59")

            source_filter = None if include_all_providers else "google"
            events = Repository.get_calendar_events(
                start_datetime=start_dt,
                end_datetime=end_dt,
                source=source_filter,
                status_filter=["MY_MEETING", "INVITED", "OPTIONAL", "ORGANIZER"]
            )

            return ToolResult(
                success=True,
                data={
                    "events": events,
                    "count": len(events),
                    "time_range": {"start": start_dt, "end": end_dt},
                    "has_meetings": len(events) > 0
                }
            )
        except Exception as e:
            logger.error(f"GoogleCalendarTool error: {e}")
            return ToolResult(
                success=False,
                error=f"Failed to query Google Calendar: {str(e)}"
            )
