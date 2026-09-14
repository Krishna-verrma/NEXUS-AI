import logging
import datetime
import re
from typing import Any, Optional
from app.tools.base import BaseTool, ToolResult, PermissionLevel
from app.services.calendar_service import CalendarService
from app.services.datetime_service import DateTimeService

logger = logging.getLogger("nexus.tools.google_calendar.create_event")

class CreateCalendarEventTool(BaseTool):
    """Tool to create a new calendar event in Google Calendar."""

    def __init__(self):
        super().__init__(
            name="google_calendar.create_event",
            description="Create a new event in Google Calendar with title, startDateTime, endDateTime, and optional location/description.",
            permission_level=PermissionLevel.SAFE_WRITE
        )
        self.input_schema = {
            "title": "string (event summary/name)",
            "startDateTime": "string (e.g. '2026-09-15 17:00:00' or natural language like 'tomorrow at 5 PM')",
            "endDateTime": "optional string (e.g. '2026-09-15 18:00:00')",
            "location": "optional string",
            "description": "optional string"
        }
        self.output_schema = {
            "event": "created event object",
            "message": "confirmation message"
        }

    async def execute(
        self,
        title: str,
        startDateTime: Optional[str] = None,
        endDateTime: Optional[str] = None,
        location: str = "",
        description: str = "",
        confirmed: bool = True,
        **kwargs: Any
    ) -> ToolResult:
        try:
            raw_start = startDateTime or kwargs.get("start_time") or "tomorrow 17:00:00"
            raw_end = endDateTime or kwargs.get("end_time")

            # Parse start time if natural language (e.g. "tomorrow at 5 PM")
            parsed_start, parsed_end = self._parse_datetime(raw_start, raw_end)

            event = await CalendarService.create_event_async(
                title=title,
                start_time=parsed_start,
                end_time=parsed_end,
                location=location,
                description=description,
                source="google_calendar"
            )

            return ToolResult(
                success=True,
                data={
                    "event": event,
                    "message": f"Successfully scheduled '{title}' on {parsed_start} in Google Calendar."
                }
            )
        except Exception as e:
            logger.error(f"CreateCalendarEventTool error: {e}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Failed to create Google Calendar event: {str(e)}"
            )

    def _parse_datetime(self, start_str: str, end_str: Optional[str]) -> tuple[str, str]:
        lower = start_str.lower()
        now = DateTimeService.get_current_datetime()
        target_date = now.date()

        if "tomorrow" in lower:
            target_date = now.date() + datetime.timedelta(days=1)
        elif "yesterday" in lower:
            target_date = now.date() - datetime.timedelta(days=1)
        else:
            # Check for specific date
            iso_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", start_str)
            if iso_match:
                y, m, d = map(int, iso_match.group(1).split("-"))
                target_date = datetime.date(y, m, d)

        # Parse hour/minute, e.g. "5 PM", "17:00", "5:00 pm"
        time_match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", lower)
        hour = 17 # default 5 PM
        minute = 0
        if time_match:
            h = int(time_match.group(1))
            m = int(time_match.group(2)) if time_match.group(2) else 0
            meridiem = time_match.group(3)
            if meridiem == "pm" and h < 12:
                h += 12
            elif meridiem == "am" and h == 12:
                h = 0
            hour = h
            minute = m

        start_dt = datetime.datetime(target_date.year, target_date.month, target_date.day, hour, minute, 0)
        end_dt = start_dt + datetime.timedelta(hours=1)

        start_formatted = start_dt.strftime("%Y-%m-%d %H:%M:%S")
        end_formatted = end_str or end_dt.strftime("%Y-%m-%d %H:%M:%S")

        return start_formatted, end_formatted
