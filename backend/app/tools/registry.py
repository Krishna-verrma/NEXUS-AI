import logging
from typing import Any, Optional
from app.tools.base import BaseTool, ToolResult, PermissionLevel

logger = logging.getLogger("nexus.tools")

class ToolRegistry:
    """Central registry of executable tools for NEXUS AI agents."""
    _instance: Optional["ToolRegistry"] = None

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    @classmethod
    def get_instance(cls) -> "ToolRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name} [{tool.permission_level.value}]")

    def get(self, name: str) -> Optional[BaseTool]:
        if name in self._tools:
            return self._tools[name]
        alt = name.replace(":", ".") if ":" in name else name.replace(".", ":")
        return self._tools.get(alt)

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "permission_level": t.permission_level.value,
                "input_schema": t.input_schema,
                "output_schema": t.output_schema
            }
            for t in self._tools.values()
        ]

    def list_for_agent(self, allowed_tools: list[str]) -> list[BaseTool]:
        """Return tool instances permitted for a specific agent."""
        res = []
        for name in allowed_tools:
            # support wildcard e.g. "filesystem:*" or exact match
            if name.endswith(":*"):
                prefix = name[:-2] + ":"
                res.extend([t for n, t in self._tools.items() if n.startswith(prefix)])
            elif name in self._tools:
                res.append(self._tools[name])
        return res

    async def execute_tool(
        self,
        name: str,
        allowed_tools: Optional[list[str]] = None,
        confirm_dangerous: bool = False,
        **kwargs: Any
    ) -> ToolResult:
        tool = self.get(name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool '{name}' is not registered in ToolRegistry."
            )

        # Permission check for agent
        if allowed_tools is not None:
            is_allowed = False
            for allowed in allowed_tools:
                if allowed == "*" or allowed == name or (allowed.endswith(":*") and name.startswith(allowed[:-2] + ":")):
                    is_allowed = True
                    break
            if not is_allowed:
                return ToolResult(
                    success=False,
                    error=f"Permission denied: Agent is not authorized to use tool '{name}'."
                )

        # Danger level check
        if tool.permission_level == PermissionLevel.DANGEROUS and not confirm_dangerous:
            return ToolResult(
                success=False,
                error=f"Tool '{name}' is classified as DANGEROUS and requires explicit user confirmation."
            )

        try:
            return await tool.execute(**kwargs)
        except Exception as e:
            logger.error(f"Error executing tool '{name}': {e}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Execution error in tool '{name}': {str(e)}"
            )

tool_registry = ToolRegistry.get_instance()
