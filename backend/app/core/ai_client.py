import logging
from typing import Any, Optional
from app.ai.model_router import model_router

logger = logging.getLogger("nexus.ai_client")

class AIClient:
    """
    Modular AI Client facade delegating directly to the centralized ModelRouter.
    Supports Google Gemini Native REST API and OpenAI endpoints with strict compatibility.
    """

    def __init__(self):
        pass

    @property
    def provider(self) -> str:
        return model_router.provider

    @property
    def api_key(self) -> str:
        return model_router.api_key

    @property
    def base_url(self) -> str:
        return model_router.base_url

    @property
    def model(self) -> str:
        return model_router.model

    @property
    def temperature(self) -> float:
        return model_router.temperature

    @property
    def max_tokens(self) -> int:
        return model_router.max_tokens

    @property
    def demo_mode(self) -> bool:
        return model_router._demo_mode

    def update_config(
        self,
        provider: str,
        api_key: str,
        base_url: str,
        model: str,
        temperature: float,
        max_tokens: int,
        demo_mode: bool
    ):
        model_router.update_config(
            provider=provider,
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            demo_mode=demo_mode
        )

    def is_configured(self) -> bool:
        return model_router.is_configured()

    async def complete(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        response_format_json: bool = False,
        tools: Optional[list[dict[str, Any]]] = None
    ) -> str:
        return await model_router.complete(
            messages=messages,
            temperature=temperature,
            response_format_json=response_format_json,
            tools=tools
        )

    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format_json: bool = False
    ) -> dict[str, Any]:
        """Unified helper used across coding, data, research, security, and report agents."""
        return await model_router.generate(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format_json=response_format_json
        )

    async def test_connection(
        self,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ) -> dict[str, Any]:
        return await model_router.test_connection(
            provider=provider,
            api_key=api_key,
            base_url=base_url,
            model=model
        )

ai_client = AIClient()
