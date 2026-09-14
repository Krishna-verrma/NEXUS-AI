import pytest
from app.tools import dispatch_tool, TOOL_REGISTRY
from app.core.security import is_operation_sensitive

def test_tool_registry_contains_required_tools():
    required = [
        "search_files", "create_file", "read_file", "delete_file",
        "launch_app", "capture_screenshot", "get_system_info",
        "search_web", "fetch_webpage",
        "analyze_code_structure", "execute_code_sandbox",
        "list_calendar_events", "schedule_calendar_event",
        "execute_command"
    ]
    for tool_name in required:
        assert tool_name in TOOL_REGISTRY, f"Tool missing from registry: {tool_name}"

def test_dispatch_safe_tool():
    res = dispatch_tool("get_system_info", {})
    assert res["success"] is True
    assert "cpuUsagePercent" in res["data"]
    assert res["execution_time_ms"] >= 0

def test_dispatch_sensitive_tool_requires_approval():
    res = dispatch_tool("delete_file", {"target_path": "critical_data.bin"}, auto_approve=False)
    assert res["requires_approval"] is True
    assert "ticket_id" in res
    assert res["ticket"]["status"] == "pending"
