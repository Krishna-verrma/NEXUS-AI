import logging
from typing import Any
from app.tools.base import BaseTool, ToolResult, PermissionLevel
from app.services.calendar_service import CalendarService

logger = logging.getLogger("nexus.tools.google_calendar.delete_event")

class DeleteCalendarEventTool(BaseTool):
    """Tool to delete an event from Google Calendar."""

    def __init__(self):
        super().__init__(
            name="google_calendar.delete_event",
            description="Delete a Google Calendar event by ID.",
            permission_level=PermissionLevel.CONFIRMATION_REQUIRED
        )
        self.input_schema = {
            "eventId": "string ID of the event to delete"
        }
        self.output_schema = {
            "success": "boolean",
            "message": "string"
        }

    async def execute(self, eventId: str, **kwargs: Any) -> ToolResult:
        try:
            ok = await CalendarService.delete_event_async(eventId)
            if not ok:
                return ToolResult(success=False, error=f"Event '{eventId}' not found or could not be deleted.")
            return ToolResult(success=True, data={"success": True, "message": f"Event '{eventId}' deleted."})
        except Exception as e:
            logger.error(f"DeleteCalendarEventTool error: {e}", exc_info=True)
            return ToolResult(success=False, error=f"Failed to delete event: {str(e)}")
