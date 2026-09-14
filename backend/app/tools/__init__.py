import time
from typing import Dict, Any, Callable
from app.core.security import is_operation_sensitive, get_operation_risk, create_security_ticket

# Filesystem
from app.tools.filesystem.search import search_files
from app.tools.filesystem.create import create_file, read_file
from app.tools.filesystem.move import move_file
from app.tools.filesystem.delete import delete_file

# Computer
from app.tools.computer.launch import launch_app
from app.tools.computer.screenshot import capture_screenshot
from app.tools.computer.system_info import get_system_info

# Browser
from app.tools.browser.search import search_web
from app.tools.browser.webpage import fetch_webpage

# Documents
from app.tools.documents.pdf import inspect_pdf
from app.tools.documents.docx import inspect_docx, create_docx_summary
from app.tools.documents.excel import inspect_excel

# Code
from app.tools.code.analyzer import analyze_code_structure
from app.tools.code.executor import execute_code_sandbox

# Calendar
from app.tools.calendar.google_calendar import list_calendar_events, schedule_calendar_event

# System
from app.tools.system.commands import execute_command

TOOL_REGISTRY: Dict[str, Callable] = {
    "search_files": search_files,
    "create_file": create_file,
    "read_file": read_file,
    "move_file": move_file,
    "delete_file": delete_file,
    "launch_app": launch_app,
    "capture_screenshot": capture_screenshot,
    "get_system_info": get_system_info,
    "search_web": search_web,
    "fetch_webpage": fetch_webpage,
    "inspect_pdf": inspect_pdf,
    "inspect_docx": inspect_docx,
    "create_docx_summary": create_docx_summary,
    "inspect_excel": inspect_excel,
    "analyze_code_structure": analyze_code_structure,
    "execute_code_sandbox": execute_code_sandbox,
    "list_calendar_events": list_calendar_events,
    "schedule_calendar_event": schedule_calendar_event,
    "execute_command": execute_command,
}

def dispatch_tool(tool_name: str, arguments: Dict[str, Any], agent_role: str = "orchestrator", auto_approve: bool = False) -> Dict[str, Any]:
    """Execute a tool with risk validation and timing."""
    if tool_name not in TOOL_REGISTRY:
        return {
            "tool_name": tool_name,
            "success": False,
            "error": f"Tool '{tool_name}' is not registered in TOOL_REGISTRY",
            "execution_time_ms": 0.0,
            "requires_approval": False
        }

    # Check security requirement
    if is_operation_sensitive(tool_name) and not auto_approve:
        ticket = create_security_ticket(
            operation_name=tool_name,
            description=f"Agent '{agent_role}' requested to execute sensitive tool '{tool_name}'",
            command_or_payload=str(arguments),
            agent_role=agent_role
        )
        return {
            "tool_name": tool_name,
            "success": False,
            "requires_approval": True,
            "ticket": ticket,
            "ticket_id": ticket["id"],
            "error": "Human-in-the-loop authorization required before executing this sensitive operation",
            "execution_time_ms": 0.0
        }

    start = time.time()
    try:
        fn = TOOL_REGISTRY[tool_name]
        result = fn(**arguments)
        duration_ms = round((time.time() - start) * 1000, 2)
        return {
            "tool_name": tool_name,
            "success": True,
            "data": result,
            "execution_time_ms": duration_ms,
            "requires_approval": False
        }
    except Exception as e:
        duration_ms = round((time.time() - start) * 1000, 2)
        return {
            "tool_name": tool_name,
            "success": False,
            "error": str(e),
            "execution_time_ms": duration_ms,
            "requires_approval": False
        }
