import logging
from typing import Any, Optional
from datetime import datetime, timedelta
from app.tools.base import BaseTool, ToolResult, PermissionLevel
from app.database.repository import Repository

logger = logging.getLogger("nexus.tools.microsoft.outlook_calendar")

class OutlookCalendarTool(BaseTool):
    """Tool to query Microsoft Outlook calendar events."""

    def __init__(self):
        super().__init__(
            name="microsoft.calendar.get_events",
            description="Query Microsoft Outlook calendar events for today, upcoming days, or specific time range.",
            permission_level=PermissionLevel.READ_ONLY
        )
        self.input_schema = {
            "start_datetime": "optional string (format 'YYYY-MM-DD HH:MM:SS' or 'today')",
            "end_datetime": "optional string"
        }
        self.output_schema = {
            "events": "list of Outlook meetings",
            "count": "integer count"
        }

    async def execute(
        self,
        start_datetime: Optional[str] = None,
        end_datetime: Optional[str] = None,
        **kwargs: Any
    ) -> ToolResult:
        try:
            now = datetime.now()
            today_str = now.strftime("%Y-%m-%d")
            s_dt = start_datetime or kwargs.get("date") or today_str

            if s_dt == "today":
                start_dt = f"{today_str} 00:00:00"
                end_dt = f"{today_str} 23:59:59"
            elif s_dt == "tomorrow":
                tom = (now + timedelta(days=1)).strftime("%Y-%m-%d")
                start_dt = f"{tom} 00:00:00"
                end_dt = f"{tom} 23:59:59"
            else:
                start_dt = s_dt if " " in s_dt else f"{s_dt} 00:00:00"
                end_dt = end_datetime or (now + timedelta(days=7)).strftime("%Y-%m-%d 23:59:59")

            events = Repository.get_calendar_events(
                start_datetime=start_dt,
                end_datetime=end_dt,
                source="outlook",
                status_filter=["MY_MEETING", "INVITED", "OPTIONAL", "ORGANIZER"]
            )

            return ToolResult(
                success=True,
                data={
                    "events": events,
                    "count": len(events),
                    "provider": "outlook"
                }
            )
        except Exception as e:
            logger.error(f"OutlookCalendarTool error: {e}")
            return ToolResult(
                success=False,
                error=f"Failed to query Outlook Calendar: {str(e)}"
            )
