import re
from typing import Any, Optional
import httpx
from app.tools.base import BaseTool, ToolResult, PermissionLevel

class BrowserFetchTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="browser:browser_fetch",
            description="Navigates to a web page and extracts its title, headings, and readable body text.",
            permission_level=PermissionLevel.READ_ONLY,
            input_schema={"url": "string (web URL to browse)"},
            output_schema={
                "title": "string",
                "headings": "list of str",
                "body_text": "string",
                "url": "string"
            }
        )

    async def execute(self, url: str, **kwargs: Any) -> ToolResult:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 NEXUS/1.0"
            }
            async with httpx.AsyncClient(timeout=15.0, headers=headers, follow_redirects=True) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return ToolResult(success=False, error=f"Navigation failed with status {resp.status_code}")

                html = resp.text
                title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
                title = title_match.group(1).strip() if title_match else url

                headings = re.findall(r'<h[1-3][^>]*>(.*?)</h[1-3]>', html, re.IGNORECASE | re.DOTALL)
                clean_headings = [re.sub(r'<[^>]+>', '', h).strip() for h in headings if h.strip()][:8]

                # Strip script and style tags
                clean_html = re.sub(r'<script.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
                clean_html = re.sub(r'<style.*?</style>', '', clean_html, flags=re.DOTALL | re.IGNORECASE)
                body = re.sub(r'<[^>]+>', ' ', clean_html)
                clean_body = " ".join(body.split())[:3000]

                return ToolResult(
                    success=True,
                    data={
                        "title": title,
                        "headings": clean_headings,
                        "body_text": clean_body,
                        "url": url
                    }
                )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
