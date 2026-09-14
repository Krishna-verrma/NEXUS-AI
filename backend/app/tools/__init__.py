from app.tools.base import BaseTool, ToolResult, PermissionLevel
from app.tools.registry import ToolRegistry, tool_registry
from app.tools.filesystem import ReadFileTool, SearchFilesTool, ListDirectoryTool, WriteFileTool, EditFileTool
from app.tools.terminal import RunCommandTool
from app.tools.web import WebSearchTool, FetchUrlTool
from app.tools.documents import ParseDocumentTool
from app.tools.github import GitHubInspectTool
from app.tools.browser import BrowserFetchTool
from app.tools.google_calendar import (
    GetCalendarEventsTool,
    CreateCalendarEventTool,
    UpdateCalendarEventTool,
    DeleteCalendarEventTool,
)

def register_default_tools() -> None:
    """Register all standard built-in tools into the global ToolRegistry."""
    tool_registry.register(ReadFileTool())
    tool_registry.register(SearchFilesTool())
    tool_registry.register(ListDirectoryTool())
    tool_registry.register(WriteFileTool())
    tool_registry.register(EditFileTool())
    tool_registry.register(RunCommandTool())
    tool_registry.register(WebSearchTool())
    tool_registry.register(FetchUrlTool())
    tool_registry.register(ParseDocumentTool())
    tool_registry.register(GitHubInspectTool())
    tool_registry.register(BrowserFetchTool())

    # Google Calendar Tools
    tool_registry.register(GetCalendarEventsTool())
    tool_registry.register(CreateCalendarEventTool())
    tool_registry.register(UpdateCalendarEventTool())
    tool_registry.register(DeleteCalendarEventTool())

    # Unified Google Tools
    from app.tools.google.calendar import GoogleCalendarTool
    from app.tools.google.gmail import GmailTool
    from app.tools.google.meet import GoogleMeetTool
    tool_registry.register(GoogleCalendarTool())
    tool_registry.register(GmailTool())
    tool_registry.register(GoogleMeetTool())

    # Unified Microsoft Tools
    from app.tools.microsoft.outlook_calendar import OutlookCalendarTool
    from app.tools.microsoft.outlook_mail import OutlookMailTool
    from app.tools.microsoft.teams import TeamsTool
    tool_registry.register(OutlookCalendarTool())
    tool_registry.register(OutlookMailTool())
    tool_registry.register(TeamsTool())

# Initialize default tool registrations
register_default_tools()

__all__ = [
    "BaseTool",
    "ToolResult",
    "PermissionLevel",
    "ToolRegistry",
    "tool_registry",
    "register_default_tools"
]
