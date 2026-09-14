import logging
from typing import Any, Optional
from app.tools.registry import tool_registry

logger = logging.getLogger("nexus.ai.tool_router")

class ToolRouter:
    """Dispatches tool execution requests from agents or chat loops."""

    @classmethod
    def list_available_tools(cls) -> list[dict[str, Any]]:
        return tool_registry.list_tools()

    @classmethod
    async def execute(cls, tool_name: str, **kwargs: Any) -> dict[str, Any]:
        logger.info(f"ToolRouter executing tool '{tool_name}' with args: {list(kwargs.keys())}")
        result = await tool_registry.execute_tool(
            name=tool_name,
            confirm_dangerous=True,
            **kwargs
        )
        return {
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "duration_seconds": result.duration_seconds
        }
