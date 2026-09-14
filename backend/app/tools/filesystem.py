import re
from pathlib import Path
from typing import Any, Optional
from app.tools.base import BaseTool, ToolResult, PermissionLevel
from app.core.config import BASE_DIR, DATA_DIR, WORKSPACE_DIR

PROJECT_ROOT = WORKSPACE_DIR

def _resolve_safe_path(target_path: str) -> Path:
    """Resolve and sanitize file path to avoid path traversal outside the project directory."""
    raw = Path(target_path)
    if not raw.is_absolute():
        # Check in PROJECT_ROOT first (nexus-ai), then BASE_DIR (nexus-ai/backend)
        candidate1 = (PROJECT_ROOT / raw).resolve()
        candidate2 = (BASE_DIR / raw).resolve()
        resolved = candidate1 if candidate1.exists() or not candidate2.exists() else candidate2
    else:
        resolved = raw.resolve()

    # Allow operations within PROJECT_ROOT or system tempdir (for uploaded files / tests)
    try:
        resolved.relative_to(PROJECT_ROOT)
    except ValueError:
        try:
            resolved.relative_to(PROJECT_ROOT.parent)
        except ValueError:
            import tempfile
            temp_dir = Path(tempfile.gettempdir()).resolve()
            try:
                resolved.relative_to(temp_dir)
            except ValueError:
                raise PermissionError(f"Access denied: Path '{target_path}' is outside the authorized project root.")
    return resolved

class ReadFileTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="filesystem:read_file",
            description="Reads the text contents of a file in the project workspace.",
            permission_level=PermissionLevel.READ_ONLY,
            input_schema={
                "path": "string (path to file)",
                "start_line": "integer (optional 1-based start line)",
                "end_line": "integer (optional 1-based end line)"
            },
            output_schema={
                "content": "string (file contents)",
                "total_lines": "integer",
                "path": "string (resolved path)"
            }
        )

    async def execute(self, path: str, start_line: Optional[int] = None, end_line: Optional[int] = None, **kwargs: Any) -> ToolResult:
        try:
            safe_p = _resolve_safe_path(path)
            if not safe_p.exists():
                return ToolResult(success=False, error=f"File not found: '{path}'")
            if safe_p.is_dir():
                return ToolResult(success=False, error=f"Path '{path}' is a directory, not a file.")

            content = safe_p.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()
            total_lines = len(lines)

            if start_line is not None or end_line is not None:
                s = max(1, start_line or 1) - 1
                e = min(total_lines, end_line or total_lines)
                sliced_lines = lines[s:e]
                return ToolResult(
                    success=True,
                    data={
                        "content": "\n".join(sliced_lines),
                        "total_lines": total_lines,
                        "range": [s + 1, e],
                        "path": str(safe_p)
                    }
                )

            return ToolResult(
                success=True,
                data={
                    "content": content,
                    "total_lines": total_lines,
                    "path": str(safe_p)
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

class SearchFilesTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="filesystem:search_files",
            description="Searches for a text pattern or regex across files in a directory.",
            permission_level=PermissionLevel.READ_ONLY,
            input_schema={
                "query": "string (text or regex to search)",
                "directory": "string (directory path, default project root)",
                "extension": "string (optional file extension filter e.g. .py, .csv)"
            },
            output_schema={
                "matches": "list of { file: str, line_number: int, line: str }"
            }
        )

    async def execute(self, query: str, directory: Optional[str] = None, extension: Optional[str] = None, **kwargs: Any) -> ToolResult:
        try:
            target_dir = _resolve_safe_path(directory or str(PROJECT_ROOT))
            if not target_dir.exists() or not target_dir.is_dir():
                return ToolResult(success=False, error=f"Directory '{directory}' does not exist.")

            pattern = re.compile(query, re.IGNORECASE)
            matches = []

            # Exclude virtual environment and cache folders for speed and relevance
            ignore_dirs = {".git", "venv", "__pycache__", "node_modules", ".pytest_cache", "dist", "build"}

            for p in target_dir.rglob("*"):
                if any(ignored in p.parts for ignored in ignore_dirs):
                    continue
                if p.is_file():
                    if extension and not p.name.endswith(extension):
                        continue
                    try:
                        text = p.read_text(encoding="utf-8", errors="ignore")
                        for idx, line in enumerate(text.splitlines(), start=1):
                            if pattern.search(line):
                                rel = str(p.relative_to(PROJECT_ROOT)) if p.is_relative_to(PROJECT_ROOT) else str(p)
                                matches.append({
                                    "file": rel,
                                    "line_number": idx,
                                    "line": line.strip()
                                })
                                if len(matches) >= 50:
                                    break
                    except Exception:
                        continue
                if len(matches) >= 50:
                    break

            return ToolResult(success=True, data={"matches": matches, "count": len(matches)})
        except Exception as e:
            return ToolResult(success=False, error=str(e))

class ListDirectoryTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="filesystem:list_directory",
            description="Lists files and subdirectories in a directory path.",
            permission_level=PermissionLevel.READ_ONLY,
            input_schema={"directory": "string (optional path, default project root)"},
            output_schema={"items": "list of { name: str, is_dir: bool, size_bytes: int }"}
        )

    async def execute(self, directory: Optional[str] = None, **kwargs: Any) -> ToolResult:
        try:
            target_dir = _resolve_safe_path(directory or str(PROJECT_ROOT))
            if not target_dir.exists():
                return ToolResult(success=False, error=f"Directory not found: '{directory}'")
            if not target_dir.is_dir():
                return ToolResult(success=False, error=f"Path is not a directory: '{directory}'")

            items = []
            for item in sorted(target_dir.iterdir()):
                items.append({
                    "name": item.name,
                    "is_dir": item.is_dir(),
                    "size_bytes": item.stat().st_size if item.is_file() else 0
                })
            return ToolResult(success=True, data={"items": items, "path": str(target_dir)})
        except Exception as e:
            return ToolResult(success=False, error=str(e))

class WriteFileTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="filesystem:write_file",
            description="Writes new text content to a target file in the workspace or data directory.",
            permission_level=PermissionLevel.SAFE_WRITE,
            input_schema={
                "path": "string (target file path)",
                "content": "string (content to write)"
            },
            output_schema={
                "path": "string",
                "bytes_written": "integer"
            }
        )

    async def execute(self, path: str, content: str, **kwargs: Any) -> ToolResult:
        try:
            safe_p = _resolve_safe_path(path)
            safe_p.parent.mkdir(parents=True, exist_ok=True)
            bytes_written = safe_p.write_text(content, encoding="utf-8")
            return ToolResult(
                success=True,
                data={
                    "path": str(safe_p),
                    "bytes_written": bytes_written
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

class EditFileTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="filesystem:edit_file",
            description="Replaces target content with replacement content in an existing file.",
            permission_level=PermissionLevel.SAFE_WRITE,
            input_schema={
                "path": "string (target file path)",
                "target_content": "string (exact text to replace)",
                "replacement_content": "string (new text to insert)"
            },
            output_schema={
                "path": "string",
                "modified": "boolean",
                "occurrences_replaced": "integer"
            }
        )

    async def execute(self, path: str, target_content: str, replacement_content: str, **kwargs: Any) -> ToolResult:
        try:
            safe_p = _resolve_safe_path(path)
            if not safe_p.exists() or not safe_p.is_file():
                return ToolResult(success=False, error=f"File '{path}' does not exist.")

            original = safe_p.read_text(encoding="utf-8")
            if target_content not in original:
                return ToolResult(
                    success=False,
                    error=f"target_content was not found in '{path}'. No modifications made."
                )

            occurrences = original.count(target_content)
            modified_text = original.replace(target_content, replacement_content, 1)
            safe_p.write_text(modified_text, encoding="utf-8")

            return ToolResult(
                success=True,
                data={
                    "path": str(safe_p),
                    "modified": True,
                    "occurrences_replaced": 1
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
