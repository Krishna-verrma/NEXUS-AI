import logging
from typing import Any, Optional
from app.tools.base import BaseTool, ToolResult, PermissionLevel
from app.services.calendar_service import CalendarService
from app.database.repository import Repository

logger = logging.getLogger("nexus.tools.google_calendar.update_event")

class UpdateCalendarEventTool(BaseTool):
    """Tool to update or reschedule an existing calendar event in Google Calendar."""

    def __init__(self):
        super().__init__(
            name="google_calendar.update_event",
            description="Update or reschedule an existing Google Calendar event by ID or title with new start time, end time, title, or location.",
            permission_level=PermissionLevel.SAFE_WRITE
        )
        self.input_schema = {
            "eventId": "optional string ID of the event to update",
            "title": "optional meeting title to find or update",
            "updates": "dict of fields to update (start_time, end_time, title, location, description)"
        }
        self.output_schema = {
            "event": "updated event object",
            "success": "boolean"
        }

    async def execute(
        self,
        eventId: Optional[str] = None,
        updates: Optional[dict[str, Any]] = None,
        **kwargs: Any
    ) -> ToolResult:
        try:
            upd = updates or {}
            for k, v in kwargs.items():
                if k not in ("eventId", "event_id") and k not in upd:
                    upd[k] = v

            target_id = eventId or kwargs.get("event_id")

            # If no target_id is provided, try finding by title or query
            if not target_id:
                search_title = upd.get("title") or kwargs.get("query") or kwargs.get("meeting_name")
                events = Repository.get_calendar_events(limit=30)
                if search_title:
                    for ev in events:
                        if search_title.lower() in ev.get("title", "").lower():
                            target_id = ev.get("id")
                            break
                if not target_id and events:
                    target_id = events[0].get("id")

            if not target_id:
                return ToolResult(success=False, error="No target meeting could be identified to update.")

            updated = await CalendarService.update_event_async(target_id, upd)
            if not updated:
                return ToolResult(success=False, error=f"Meeting '{target_id}' could not be updated in Google Calendar.")

            title = updated.get("title", "Meeting")
            time_str = updated.get("start_time", "")
            return ToolResult(
                success=True,
                data={
                    "event": updated,
                    "message": f"Successfully updated '{title}' to {time_str} in Google Calendar."
                }
            )
        except Exception as e:
            logger.error(f"UpdateCalendarEventTool error: {e}", exc_info=True)
            return ToolResult(success=False, error=f"Failed to update Google Calendar event: {str(e)}")
