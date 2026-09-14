import asyncio
import shlex
import sys
from typing import Any, Optional
from app.tools.base import BaseTool, ToolResult, PermissionLevel
from app.core.config import BASE_DIR

DANGEROUS_PATTERNS = [
    "rm -rf", "rmdir /s", "del /s", "del /f", "format ", "mkfs",
    ":(){ :|:& };:", "drop database", "drop table", "shutdown", "reboot"
]

class RunCommandTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="terminal:run_command",
            description="Executes a safe command in the project workspace (e.g. pytest, python, git status).",
            permission_level=PermissionLevel.SAFE_WRITE,
            input_schema={
                "command": "string (the command line to execute)",
                "cwd": "string (optional working directory, defaults to project root)",
                "timeout_seconds": "integer (optional timeout, default 30)"
            },
            output_schema={
                "exit_code": "integer",
                "stdout": "string",
                "stderr": "string",
                "duration_seconds": "float"
            }
        )

    async def execute(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout_seconds: int = 30,
        confirm_dangerous: bool = False,
        **kwargs: Any
    ) -> ToolResult:
        cmd_lower = command.lower()
        if any(dp in cmd_lower for dp in DANGEROUS_PATTERNS) and not confirm_dangerous:
            return ToolResult(
                success=False,
                error=f"Command '{command}' is classified as DANGEROUS and was blocked."
            )

        working_dir = BASE_DIR
        if cwd:
            from app.tools.filesystem import _resolve_safe_path
            try:
                working_dir = _resolve_safe_path(cwd)
            except Exception as e:
                return ToolResult(success=False, error=str(e))

        # Use system python executable if command refers to python/pytest
        cmd_to_run = command
        venv_python = BASE_DIR / "backend" / "venv" / "Scripts" / "python.exe"
        if venv_python.exists():
            if command.startswith("pytest"):
                cmd_to_run = f'"{venv_python}" -m pytest {command[6:]}'
            elif command.startswith("python "):
                cmd_to_run = f'"{venv_python}" {command[7:]}'

        import time
        start = time.time()

        try:
            # Execute command asynchronously
            proc = await asyncio.create_subprocess_shell(
                cmd_to_run,
                cwd=str(working_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(),
                timeout=float(timeout_seconds)
            )

            stdout_str = stdout_bytes.decode("utf-8", errors="replace").strip()
            stderr_str = stderr_bytes.decode("utf-8", errors="replace").strip()
            duration = round(time.time() - start, 2)
            exit_code = proc.returncode or 0

            return ToolResult(
                success=(exit_code == 0),
                data={
                    "command": command,
                    "executed_command": cmd_to_run,
                    "exit_code": exit_code,
                    "stdout": stdout_str,
                    "stderr": stderr_str,
                    "duration_seconds": duration
                },
                error=None if exit_code == 0 else f"Command exited with code {exit_code}: {stderr_str or stdout_str}"
            )

        except asyncio.TimeoutError:
            try:
                proc.kill()
            except Exception:
                pass
            return ToolResult(
                success=False,
                error=f"Command timed out after {timeout_seconds} seconds."
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))
