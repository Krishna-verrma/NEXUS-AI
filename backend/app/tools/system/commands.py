import subprocess
import shlex
import time
from typing import Dict, Any

def execute_command(command: str, timeout_seconds: int = 15) -> Dict[str, Any]:
    """Execute a system shell command. Flagged as sensitive for user confirmation."""
    start_time = time.time()
    try:
        # Run command with timeout
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        duration_ms = round((time.time() - start_time) * 1000, 2)
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "durationMs": duration_ms,
            "command": command
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Command timed out after {timeout_seconds} seconds",
            "durationMs": round((time.time() - start_time) * 1000, 2),
            "command": command
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "durationMs": round((time.time() - start_time) * 1000, 2),
            "command": command
        }
