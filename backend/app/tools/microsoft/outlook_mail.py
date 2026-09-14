import logging
from typing import Any, Optional
from app.tools.base import BaseTool, ToolResult, PermissionLevel
from app.services.oauth.microsoft_oauth import MicrosoftOAuthService
from app.database.repository import Repository

logger = logging.getLogger("nexus.tools.microsoft.outlook_mail")

class OutlookMailTool(BaseTool):
    """Tool to search Outlook messages for meetings, changes, and important communications."""

    def __init__(self):
        super().__init__(
            name="microsoft.mail.search_messages",
            description="Search Outlook messages for unread emails, meeting invitations, cancellations, or important messages.",
            permission_level=PermissionLevel.READ_ONLY
        )
        self.input_schema = {
            "query": "optional string search query",
            "limit": "optional integer count (default: 10)"
        }
        self.output_schema = {
            "messages": "list of Outlook messages",
            "count": "integer count"
        }

    async def execute(
        self,
        query: Optional[str] = None,
        limit: int = 10,
        **kwargs: Any
    ) -> ToolResult:
        try:
            # Try live Microsoft Graph API
            live_msgs = await MicrosoftOAuthService.fetch_outlook_messages(query=query, max_results=limit)
            if live_msgs:
                for msg in live_msgs:
                    Repository.save_email_metadata({
                        "id": msg["id"],
                        "provider": "microsoft",
                        "thread_id": msg.get("thread_id"),
                        "subject": msg.get("subject", ""),
                        "sender": msg.get("from", ""),
                        "sender_email": msg.get("sender_email", ""),
                        "snippet": msg.get("snippet", ""),
                        "received_at": msg.get("received_at"),
                        "is_read": 1 if msg.get("is_read") else 0,
                        "is_important": 1 if msg.get("is_important") else 0
                    })
                return ToolResult(
                    success=True,
                    data={"messages": live_msgs, "count": len(live_msgs), "source": "live_graph_api"}
                )

            # Fallback to cached email metadata
            cached = Repository.get_important_emails(limit=limit)
            ms_cached = [m for m in cached if m.get("provider") == "microsoft"]
            return ToolResult(
                success=True,
                data={"messages": ms_cached, "count": len(ms_cached), "source": "cached_metadata"}
            )
        except Exception as e:
            logger.error(f"OutlookMailTool error: {e}")
            return ToolResult(
                success=False,
                error=f"Failed to query Outlook mail: {str(e)}"
            )
