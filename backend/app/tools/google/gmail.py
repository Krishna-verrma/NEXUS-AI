import logging
from typing import Any, Optional
from app.tools.base import BaseTool, ToolResult, PermissionLevel
from app.services.oauth.google_oauth import GoogleOAuthService
from app.database.repository import Repository

logger = logging.getLogger("nexus.tools.google.gmail")

class GmailTool(BaseTool):
    """Tool to search and retrieve Gmail messages related to work and meetings."""

    def __init__(self):
        super().__init__(
            name="google.gmail.search_emails",
            description="Search Gmail messages for work communications, meeting updates, invitations, reschedules, or important threads.",
            permission_level=PermissionLevel.READ_ONLY
        )
        self.input_schema = {
            "query": "string search query (e.g. 'important', 'meeting', 'project review')",
            "limit": "optional integer (default: 10)"
        }
        self.output_schema = {
            "messages": "list of matching email metadata",
            "count": "integer count"
        }

    async def execute(
        self,
        query: str = "meeting OR important",
        limit: int = 10,
        **kwargs: Any
    ) -> ToolResult:
        try:
            # 1. Try real live Gmail API if connected
            live_emails = await GoogleOAuthService.fetch_gmail_messages(query=query, max_results=limit)
            if live_emails:
                for em in live_emails:
                    Repository.save_email_metadata({
                        "id": em["id"],
                        "provider": "google",
                        "thread_id": em.get("thread_id"),
                        "subject": em.get("subject", ""),
                        "sender": em.get("from", ""),
                        "snippet": em.get("snippet", ""),
                        "received_at": em.get("date"),
                        "is_read": 0 if em.get("is_unread") else 1,
                        "is_important": 1 if em.get("is_important") else 0
                    })
                return ToolResult(
                    success=True,
                    data={"messages": live_emails, "count": len(live_emails), "source": "live_gmail_api"}
                )

            # 2. Fall back to cached email metadata
            cached_emails = Repository.get_important_emails(limit=limit)
            return ToolResult(
                success=True,
                data={"messages": cached_emails, "count": len(cached_emails), "source": "cached_metadata"}
            )
        except Exception as e:
            logger.error(f"GmailTool error: {e}")
            return ToolResult(
                success=False,
                error=f"Failed to query Gmail messages: {str(e)}"
            )
