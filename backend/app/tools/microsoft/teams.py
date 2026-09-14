import re
import logging
from typing import Any, Optional
from app.tools.base import BaseTool, ToolResult, PermissionLevel
from app.database.repository import Repository

logger = logging.getLogger("nexus.tools.microsoft.teams")

class TeamsTool(BaseTool):
    """Tool to inspect Microsoft Teams online meeting links and conference details."""

    def __init__(self):
        super().__init__(
            name="microsoft.teams.get_meeting_info",
            description="Retrieve Microsoft Teams meeting join link, conference details, and attendee info for a specific meeting.",
            permission_level=PermissionLevel.READ_ONLY
        )
        self.input_schema = {
            "meeting_title": "optional string title",
            "event_id": "optional string event id"
        }
        self.output_schema = {
            "has_teams": "boolean",
            "meeting_url": "string Microsoft Teams URL",
            "platform": "string 'Microsoft Teams'"
        }

    async def execute(
        self,
        meeting_title: Optional[str] = None,
        event_id: Optional[str] = None,
        **kwargs: Any
    ) -> ToolResult:
        try:
            events = Repository.get_calendar_events(limit=50)
            target = None

            if event_id:
                for e in events:
                    if e.get("id") == event_id or e.get("provider_event_id") == event_id:
                        target = e
                        break
            elif meeting_title:
                norm = meeting_title.lower().strip()
                for e in events:
                    if norm in e.get("title", "").lower():
                        target = e
                        break

            if not target:
                for e in events:
                    if e.get("platform") == "teams" or (e.get("join_url") and "teams.microsoft.com" in e["join_url"]):
                        target = e
                        break

            if not target or not (target.get("platform") == "teams" or (target.get("join_url") and "teams.microsoft.com" in target["join_url"])):
                return ToolResult(
                    success=True,
                    data={"has_teams": False, "meeting_url": None, "message": "No Teams meeting found."}
                )

            return ToolResult(
                success=True,
                data={
                    "has_teams": True,
                    "meeting_title": target.get("title"),
                    "meeting_url": target.get("join_url") or target.get("meeting_url"),
                    "platform": "Microsoft Teams",
                    "start_time": target.get("start_time"),
                    "organizer": target.get("organizer")
                }
            )
        except Exception as e:
            logger.error(f"TeamsTool error: {e}")
            return ToolResult(
                success=False,
                error=f"Error inspecting Teams meeting info: {str(e)}"
            )
