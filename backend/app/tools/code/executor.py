import sys
import io
import contextlib
import time
from typing import Dict, Any

def execute_code_sandbox(code: str, timeout_seconds: int = 5) -> Dict[str, Any]:
    """Execute Python code in an isolated execution sandbox and capture stdout."""
    start_time = time.time()
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    # Restricted builtins for safety
    safe_globals = {
        "__builtins__": {
            "print": print,
            "range": range,
            "len": len,
            "int": int,
            "float": float,
            "str": str,
            "list": list,
            "dict": dict,
            "set": set,
            "tuple": tuple,
            "bool": bool,
            "sum": sum,
            "min": min,
            "max": max,
            "abs": abs,
            "round": round,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
            "sorted": sorted,
        }
    }
    local_scope = {}

    try:
        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
            exec(code, safe_globals, local_scope)
        
        output = stdout_capture.getvalue()
        err_output = stderr_capture.getvalue()
        duration_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "success": True,
            "output": output if output else "(Execution finished with no stdout output)",
            "errors": err_output,
            "durationMs": duration_ms,
            "variables": {k: str(v)[:100] for k, v in local_scope.items() if not k.startswith("_")}
        }
    except Exception as e:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        return {
            "success": False,
            "error": f"{type(e).__name__}: {str(e)}",
            "durationMs": duration_ms
        }
