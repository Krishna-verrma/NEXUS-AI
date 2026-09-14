import uuid
import datetime
import logging
from typing import Any, Optional
import httpx

from app.database.connection import db_session
from app.database.repository import Repository
from app.services.calendar_service import CalendarService

logger = logging.getLogger("nexus.github_service")

class GitHubService:
    @staticmethod
    async def test_connection(token: str) -> dict[str, Any]:
        """Verify a GitHub Personal Access Token (PAT)."""
        if not token or not token.strip():
            return {"success": False, "message": "Please enter a GitHub Personal Access Token."}

        token = token.strip()

        # Offline / Demo mode simulation
        if token.lower().startswith("demo") or token == "ghp_demo_token_12345":
            Repository.set_setting("github_username", "demo-developer")
            return {
                "success": True,
                "login": "demo-developer",
                "name": "Nexus Demo Engineer",
                "public_repos": 12,
                "avatar_url": "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png",
                "message": "Demo GitHub account connected successfully (Offline Sandbox)!"
            }

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "NexusAI-Desktop/1.0"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get("https://api.github.com/user", headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    login = data.get("login", "User")
                    name = data.get("name") or login
                    repos_count = data.get("public_repos", 0) + data.get("total_private_repos", 0)
                    Repository.set_setting("github_username", login)
                    return {
                        "success": True,
                        "login": login,
                        "name": name,
                        "public_repos": repos_count,
                        "avatar_url": data.get("avatar_url"),
                        "message": f"Successfully authenticated as @{login} ({name}) with {repos_count} repositories!"
                    }
                elif resp.status_code == 401:
                    return {"success": False, "message": "Invalid GitHub Token: Bad credentials or token expired."}
                elif resp.status_code == 403:
                    return {"success": False, "message": "GitHub API rate limit exceeded or token lacks required permissions."}
                else:
                    return {"success": False, "message": f"GitHub API error: HTTP {resp.status_code}"}
        except Exception as e:
            logger.warning(f"Failed to reach GitHub API: {e}")
            return {"success": False, "message": f"Could not reach GitHub API: {str(e)}"}

    @staticmethod
    async def sync_github_deliverables(token: Optional[str] = None, repo: Optional[str] = None) -> dict[str, Any]:
        """Fetch active GitHub pull requests and issues and index them as agenda tasks."""
        CalendarService.ensure_table()
        db_settings = Repository.get_all_settings()
        actual_token = (token or db_settings.get("github_token", "")).strip()

        if not actual_token:
            return {"success": False, "count": 0, "message": "No GitHub token configured. Please save your token in Settings."}

        # Clear existing github tasks before re-syncing
        with db_session() as conn:
            conn.execute("DELETE FROM calendar_events WHERE source = 'github'")

        now = datetime.datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        imported = 0

        # Offline / Demo mode simulation
        if actual_token.lower().startswith("demo") or actual_token == "ghp_demo_token_12345":
            demo_items = [
                (
                    "GitHub PR #42: Dynamic Multi-Agent DAG Execution Loop",
                    f"{today_str} 11:30:00",
                    f"{today_str} 12:30:00",
                    "https://github.com/nexus-org/nexus-ai/pull/42",
                    "Review code changes for non-deterministic fallback handlers and streaming token callbacks.",
                    "high",
                    1
                ),
                (
                    "GitHub Issue #108: Fix Outlook COM COMError timeout on Windows 11",
                    f"{today_str} 14:00:00",
                    f"{today_str} 15:30:00",
                    "https://github.com/nexus-org/nexus-ai/issues/108",
                    "Handle localized folder names for Outlook calendars when MAPI folder 9 is queried.",
                    "medium",
                    0
                ),
                (
                    "GitHub PR #77: UI Polish - Soft Glassmorphic Cards & Badges",
                    f"{today_str} 16:00:00",
                    f"{today_str} 17:00:00",
                    "https://github.com/nexus-org/nexus-ai/pull/77",
                    "Approve responsive flex layout and soft CSS borders for application connector cards.",
                    "normal",
                    0
                )
            ]
            with db_session() as conn:
                for title, start, end, url, desc, priority, is_imp in demo_items:
                    conn.execute("""
                        INSERT INTO calendar_events (id, title, start_time, end_time, location, description, category, source, priority, join_url, is_important)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (str(uuid.uuid4()), title, start, end, url, desc, "task", "github", priority, url, is_imp))
                    imported += 1

            return {
                "success": True,
                "count": imported,
                "message": f"Successfully indexed {imported} GitHub pull requests and issues into your agenda!"
            }

        headers = {
            "Authorization": f"Bearer {actual_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "NexusAI-Desktop/1.0"
        }

        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                items_to_process = []
                if repo and "/" in repo.strip():
                    target_repo = repo.strip()
                    url = f"https://api.github.com/repos/{target_repo}/issues?state=open&per_page=15"
                    resp = await client.get(url, headers=headers)
                    if resp.status_code == 200:
                        items_to_process = resp.json()
                else:
                    # User's assigned or participated issues & PRs
                    resp = await client.get("https://api.github.com/user/issues?filter=all&state=open&per_page=15", headers=headers)
                    if resp.status_code == 200:
                        items_to_process = resp.json()

                with db_session() as conn:
                    for item in items_to_process:
                        if not isinstance(item, dict):
                            continue
                        is_pr = "pull_request" in item
                        prefix = "GitHub PR" if is_pr else "GitHub Issue"
                        title = f"{prefix} #{item.get('number')}: {item.get('title', 'Untitled')}"
                        url = item.get("html_url", "")
                        body = (item.get("body") or "")[:300]
                        labels = [l.get("name", "").lower() for l in item.get("labels", []) if isinstance(l, dict)]
                        is_high = any(k in " ".join(labels) for k in ["urgent", "bug", "critical", "p0", "priority"])
                        priority = "high" if is_high else "medium"

                        start = f"{today_str} 10:00:00"
                        end = f"{today_str} 18:00:00"

                        conn.execute("""
                            INSERT INTO calendar_events (id, title, start_time, end_time, location, description, category, source, priority, join_url, is_important)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            str(uuid.uuid4()),
                            title,
                            start,
                            end,
                            url,
                            body,
                            "task",
                            "github",
                            priority,
                            url,
                            1 if is_high else 0
                        ))
                        imported += 1

                return {
                    "success": True,
                    "count": imported,
                    "message": f"Successfully indexed {imported} active GitHub issues & pull requests!"
                }
        except Exception as e:
            logger.warning(f"Error syncing GitHub: {e}")
            return {"success": False, "count": 0, "message": f"Failed to sync GitHub: {str(e)}"}
