import enum
from typing import Any, Optional
from pydantic import BaseModel, Field

class PermissionLevel(str, enum.Enum):
    READ_ONLY = "READ_ONLY"
    SAFE_WRITE = "SAFE_WRITE"
    CONFIRMATION_REQUIRED = "CONFIRMATION_REQUIRED"
    DANGEROUS = "DANGEROUS"

class ToolResult(BaseModel):
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata
        }

class BaseTool:
    """Base class for all tools executable by NEXUS AI specialized agents."""
    def __init__(
        self,
        name: str,
        description: str,
        permission_level: PermissionLevel,
        input_schema: Optional[dict[str, Any]] = None,
        output_schema: Optional[dict[str, Any]] = None
    ):
        self.name = name
        self.description = description
        self.permission_level = permission_level
        self.input_schema = input_schema or {}
        self.output_schema = output_schema or {}

    async def execute(self, **kwargs: Any) -> ToolResult:
        raise NotImplementedError("Subclasses must implement execute()")
