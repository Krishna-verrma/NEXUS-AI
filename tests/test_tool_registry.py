import pytest
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.tools import tool_registry, PermissionLevel

@pytest.mark.asyncio
async def test_tool_registry_registration():
    tools = tool_registry.list_tools()
    assert len(tools) >= 8
    names = [t["name"] for t in tools]
    assert "filesystem:read_file" in names
    assert "filesystem:search_files" in names
    assert "filesystem:write_file" in names
    assert "filesystem:edit_file" in names
    assert "terminal:run_command" in names
    assert "web:web_search" in names
    assert "documents:parse_document" in names

@pytest.mark.asyncio
async def test_tool_registry_permission_enforcement():
    # Attempting to run a tool not allowed for agent should fail
    res = await tool_registry.execute_tool(
        name="terminal:run_command",
        allowed_tools=["filesystem:read_file"],
        command="echo Hello"
    )
    assert res.success is False
    assert "Permission denied" in res.error

@pytest.mark.asyncio
async def test_filesystem_read_and_search():
    # Read README.md
    res = await tool_registry.execute_tool(
        name="filesystem:read_file",
        allowed_tools=["filesystem:*"],
        path="README.md"
    )
    assert res.success is True
    assert "content" in res.data
    assert len(res.data["content"]) > 10

    # Search files
    search_res = await tool_registry.execute_tool(
        name="filesystem:search_files",
        allowed_tools=["filesystem:*"],
        query="NEXUS"
    )
    assert search_res.success is True
    assert "matches" in search_res.data
    assert len(search_res.data["matches"]) > 0

@pytest.mark.asyncio
async def test_terminal_run_command_safe():
    res = await tool_registry.execute_tool(
        name="terminal:run_command",
        allowed_tools=["terminal:*"],
        command="python -c \"print('nexus_terminal_ok')\""
    )
    assert res.success is True
    assert "nexus_terminal_ok" in res.data["stdout"]

@pytest.mark.asyncio
async def test_terminal_dangerous_command_blocked():
    res = await tool_registry.execute_tool(
        name="terminal:run_command",
        allowed_tools=["terminal:*"],
        command="rm -rf /"
    )
    assert res.success is False
    assert "DANGEROUS" in res.error
