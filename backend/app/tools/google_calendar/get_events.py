import logging
from typing import Any, Optional
from app.tools.base import BaseTool, ToolResult, PermissionLevel
from app.services.calendar_service import CalendarService
from app.services.datetime_service import DateTimeService

logger = logging.getLogger("nexus.tools.google_calendar.get_events")

class GetCalendarEventsTool(BaseTool):
    """Tool to query and retrieve Google Calendar events."""

    def __init__(self):
        super().__init__(
            name="google_calendar.get_events",
            description="Query Google Calendar events for a given time range or natural language date (e.g., 'today', 'tomorrow', '15 September').",
            permission_level=PermissionLevel.READ_ONLY
        )
        self.input_schema = {
            "startDateTime": "string (ISO format 'YYYY-MM-DD HH:MM:SS' or natural language like 'tomorrow', '15 September')",
            "endDateTime": "optional string (ISO format 'YYYY-MM-DD HH:MM:SS')",
            "calendarId": "optional string (default: 'primary')"
        }
        self.output_schema = {
            "events": "list of event objects {id, title, start_time, end_time, location, description, join_url, priority}",
            "count": "integer count of events found",
            "time_range": "dict with start and end"
        }

    async def execute(
        self,
        startDateTime: Optional[str] = None,
        endDateTime: Optional[str] = None,
        calendarId: Optional[str] = "primary",
        **kwargs: Any
    ) -> ToolResult:
        try:
            raw_start = startDateTime or kwargs.get("start_datetime") or kwargs.get("date") or "today"
            raw_end = endDateTime or kwargs.get("end_datetime")

            # Resolve natural language date if needed
            if not raw_end:
                resolved_start, resolved_end = DateTimeService.parse_natural_date_range(raw_start)
            else:
                resolved_start = raw_start
                resolved_end = raw_end

            events = CalendarService.get_events(
                start_datetime=resolved_start,
                end_datetime=resolved_end,
                calendar_id=calendarId
            )

            return ToolResult(
                success=True,
                data={
                    "events": events,
                    "count": len(events),
                    "time_range": {
                        "start": resolved_start,
                        "end": resolved_end
                    }
                }
            )
        except Exception as e:
            logger.error(f"GetCalendarEventsTool error: {e}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Failed to retrieve Google Calendar events: {str(e)}"
            )
