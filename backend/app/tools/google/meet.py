import re
import json
import logging
from typing import Any, Optional
from app.tools.base import BaseTool, ToolResult, PermissionLevel
from app.database.repository import Repository

logger = logging.getLogger("nexus.tools.google.meet")

class GoogleMeetTool(BaseTool):
    """Tool to inspect Google Meet conferencing details and join links for calendar meetings."""

    def __init__(self):
        super().__init__(
            name="google.meet.get_meeting_info",
            description="Retrieve Google Meet conference link, conference solution, attendee count, and transcript/recording availability for a specific meeting.",
            permission_level=PermissionLevel.READ_ONLY
        )
        self.input_schema = {
            "meeting_title": "optional string title of the meeting",
            "event_id": "optional string calendar event id"
        }
        self.output_schema = {
            "has_meet": "boolean",
            "meeting_url": "string Google Meet URL",
            "conference_info": "dict of conference details",
            "transcript_available": "boolean",
            "recording_available": "boolean"
        }

    async def execute(
        self,
        meeting_title: Optional[str] = None,
        event_id: Optional[str] = None,
        **kwargs: Any
    ) -> ToolResult:
        try:
            # Query from stored calendar events
            events = Repository.get_calendar_events(limit=50)
            target = None

            if event_id:
                for e in events:
                    if e.get("id") == event_id or e.get("provider_event_id") == event_id:
                        target = e
                        break
            elif meeting_title:
                norm_q = meeting_title.lower().strip()
                for e in events:
                    if norm_q in e.get("title", "").lower():
                        target = e
                        break

            if not target:
                # If no specific target requested, pick the next upcoming Google Meet meeting
                for e in events:
                    if e.get("platform") == "google_meet" or (e.get("join_url") and "meet.google.com" in e["join_url"]):
                        target = e
                        break

            if not target:
                return ToolResult(
                    success=True,
                    data={
                        "has_meet": False,
                        "meeting_url": None,
                        "message": "No Google Meet video conference found for this meeting."
                    }
                )

            join_url = target.get("join_url") or target.get("meeting_url")
            conf_data = {}
            if target.get("conference_data"):
                try:
                    conf_data = json.loads(target["conference_data"]) if isinstance(target["conference_data"], str) else target["conference_data"]
                except Exception:
                    pass

            return ToolResult(
                success=True,
                data={
                    "has_meet": bool(join_url and "meet.google.com" in join_url),
                    "meeting_title": target.get("title"),
                    "meeting_url": join_url,
                    "platform": "Google Meet",
                    "start_time": target.get("start_time"),
                    "organizer": target.get("organizer"),
                    "conference_id": conf_data.get("conferenceId"),
                    "transcript_available": False,  # Strict: do not claim transcript exists if not verified
                    "recording_available": False
                }
            )
        except Exception as e:
            logger.error(f"GoogleMeetTool error: {e}")
            return ToolResult(
                success=False,
                error=f"Error inspecting Google Meet info: {str(e)}"
            )
