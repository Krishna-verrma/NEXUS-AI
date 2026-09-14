from abc import ABC, abstractmethod
from typing import Any, Optional

class BaseAIProvider(ABC):
    """Abstract base class for LLM providers (Google Gemini, OpenAI)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        self.api_key = api_key or ""
        self.base_url = (base_url or "").rstrip("/")
        self.model = model or ""
        self.temperature = temperature
        self.max_tokens = max_tokens

    @abstractmethod
    def validate_configuration(self) -> None:
        """Validate that provider, model, and endpoint are compatible."""
        pass

    @abstractmethod
    async def complete(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format_json: bool = False,
        tools: Optional[list[dict[str, Any]]] = None,
    ) -> str:
        """Execute chat completion and return response string."""
        pass

    @abstractmethod
    async def test_connection(self) -> dict[str, Any]:
        """Test live connection to the provider and return status + latency."""
        pass
