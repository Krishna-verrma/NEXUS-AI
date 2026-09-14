from typing import Any, Optional
from app.tools.base import BaseTool, ToolResult, PermissionLevel
from app.services.github_service import GitHubService

class GitHubInspectTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="github:inspect",
            description="Inspects GitHub repositories, commits, issues, and pull requests.",
            permission_level=PermissionLevel.READ_ONLY,
            input_schema={
                "action": "string ('status' | 'commits' | 'issues' | 'pulls' | 'file')",
                "repo": "string (optional 'owner/repo')",
                "path": "string (optional file path for 'file' action)"
            },
            output_schema={"status": "string", "data": "any"}
        )

    async def execute(self, action: str = "status", repo: Optional[str] = None, path: Optional[str] = None, **kwargs: Any) -> ToolResult:
        try:
            if action == "status":
                status = GitHubService.get_connector_status()
                return ToolResult(success=True, data=status)
            elif action == "commits":
                commits = await GitHubService.get_recent_commits(repo=repo, limit=5)
                return ToolResult(success=True, data={"commits": commits})
            elif action == "issues":
                issues = await GitHubService.get_issues(repo=repo, state="open", limit=5)
                return ToolResult(success=True, data={"issues": issues})
            elif action == "pulls":
                pulls = await GitHubService.get_pull_requests(repo=repo, state="open", limit=5)
                return ToolResult(success=True, data={"pulls": pulls})
            elif action == "file" and path:
                file_info = await GitHubService.get_file_content(path=path, repo=repo)
                return ToolResult(success=True, data=file_info)
            else:
                return ToolResult(success=False, error=f"Unsupported GitHub action: '{action}'")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
