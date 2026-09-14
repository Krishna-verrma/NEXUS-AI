import logging
from typing import Any, Optional
from app.core.config import settings
from app.database.repository import Repository
from app.ai.providers.base import BaseAIProvider
from app.ai.providers.gemini import GeminiProvider
from app.ai.providers.openai import OpenAIProvider
from app.ai.providers.groq import GroqProvider

logger = logging.getLogger("nexus.ai.model_router")

class ModelRouter:
    """
    Central AI Model Router.
    Routes requests to Groq (default), Google Gemini, or OpenAI providers.
    All agents must use this centralized router.
    """

    def __init__(self):
        self._provider_name: str = settings.ai_provider or "groq"
        self._api_key: str = settings.ai_api_key or ""
        self._base_url: str = settings.ai_base_url or GroqProvider.DEFAULT_ENDPOINT
        self._model: str = settings.ai_model or GroqProvider.DEFAULT_MODEL
        self._temperature: float = settings.ai_temperature
        self._max_tokens: int = settings.ai_max_tokens
        self._demo_mode: bool = settings.demo_mode
        self._provider_instance: Optional[BaseAIProvider] = None

        self._init_from_db_or_defaults()

    def _init_from_db_or_defaults(self):
        try:
            db_settings = Repository.get_all_settings()
            if db_settings:
                self._provider_name = db_settings.get("ai_provider", self._provider_name)
                self._api_key = db_settings.get("ai_api_key", self._api_key)
                self._base_url = db_settings.get("ai_base_url", self._base_url)
                self._model = db_settings.get("ai_model", self._model)
                self._temperature = float(db_settings.get("ai_temperature", self._temperature))
                self._max_tokens = int(db_settings.get("ai_max_tokens", self._max_tokens))
                self._demo_mode = db_settings.get("demo_mode", str(self._demo_mode)).lower() in ("true", "1")
        except Exception as e:
            logger.warning(f"Could not load settings from DB for ModelRouter: {e}")

        self._refresh_provider_instance()

    def _refresh_provider_instance(self):
        p_name = (self._provider_name or "groq").lower().strip()
        if p_name in ("groq", "groq ai"):
            self._provider_name = "groq"
            if not self._model or self._model.startswith("gpt-4") or self._model.startswith("gemini"):
                self._model = GroqProvider.DEFAULT_MODEL
            if not self._base_url or "api.openai.com" in self._base_url or "googleapis.com" in self._base_url:
                self._base_url = GroqProvider.DEFAULT_ENDPOINT
            self._provider_instance = GroqProvider(
                api_key=self._api_key,
                base_url=self._base_url,
                model=self._model,
                temperature=self._temperature,
                max_tokens=self._max_tokens
            )
        elif p_name in ("gemini", "google", "google gemini"):
            self._provider_name = "gemini"
            if not self._model or self._model.startswith("gpt-") or "claude" in self._model:
                self._model = GeminiProvider.DEFAULT_MODEL
            if not self._base_url or "openai.com" in self._base_url or "groq.com" in self._base_url:
                self._base_url = GeminiProvider.DEFAULT_ENDPOINT
            self._provider_instance = GeminiProvider(
                api_key=self._api_key,
                base_url=self._base_url,
                model=self._model,
                temperature=self._temperature,
                max_tokens=self._max_tokens
            )
        else:
            self._provider_name = "openai"
            if not self._model or self._model.startswith("gemini-") or "google" in self._model:
                self._model = OpenAIProvider.DEFAULT_MODEL
            if not self._base_url or "googleapis.com" in self._base_url or "groq.com" in self._base_url:
                self._base_url = OpenAIProvider.DEFAULT_ENDPOINT
            self._provider_instance = OpenAIProvider(
                api_key=self._api_key,
                base_url=self._base_url,
                model=self._model,
                temperature=self._temperature,
                max_tokens=self._max_tokens
            )

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
        self._provider_name = provider
        self._api_key = api_key
        self._base_url = base_url
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._demo_mode = demo_mode
        self._refresh_provider_instance()

    def is_configured(self) -> bool:
        return bool(self._api_key and self._api_key.strip() and not self._api_key.startswith("***"))

    @property
    def provider(self) -> str:
        return self._provider_name

    @property
    def model(self) -> str:
        return self._model

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def api_key(self) -> str:
        return self._api_key

    @property
    def temperature(self) -> float:
        return self._temperature

    @property
    def max_tokens(self) -> int:
        return self._max_tokens

    async def complete(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format_json: bool = False,
        tools: Optional[list[dict[str, Any]]] = None
    ) -> str:
        if not self._provider_instance:
            self._refresh_provider_instance()
        return await self._provider_instance.complete(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
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
        """
        Unified helper for agents expecting {success: bool, content: str, error: Optional[str]}.
        Prevents crashes across coding, data, research, security, and report agents.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        try:
            content = await self.complete(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format_json=response_format_json
            )
            return {"success": True, "content": content, "error": None}
        except Exception as e:
            logger.error(f"ModelRouter generation failed: {e}")
            return {"success": False, "content": "", "error": str(e)}

    async def test_connection(
        self,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ) -> dict[str, Any]:
        target_provider = (provider or self._provider_name).lower().strip()
        target_key = api_key if (api_key is not None and not api_key.startswith("***")) else self._api_key

        if not target_key or not target_key.strip():
            return {
                "success": False,
                "provider": target_provider,
                "model": model or self._model,
                "error": "No API key entered. Please enter a valid API key."
            }

        if target_provider in ("groq", "groq ai"):
            target_model = model or GroqProvider.DEFAULT_MODEL
            target_base = base_url or GroqProvider.DEFAULT_ENDPOINT
            prov = GroqProvider(
                api_key=target_key,
                base_url=target_base,
                model=target_model
            )
        elif target_provider in ("gemini", "google"):
            target_model = model or GeminiProvider.DEFAULT_MODEL
            target_base = base_url or GeminiProvider.DEFAULT_ENDPOINT
            prov = GeminiProvider(
                api_key=target_key,
                base_url=target_base,
                model=target_model
            )
        else:
            target_model = model or OpenAIProvider.DEFAULT_MODEL
            target_base = base_url or OpenAIProvider.DEFAULT_ENDPOINT
            prov = OpenAIProvider(
                api_key=target_key,
                base_url=target_base,
                model=target_model
            )

        res = await prov.test_connection()
        # If connection test succeeded, save connection verification state in DB
        if res.get("success"):
            try:
                Repository.set_setting("ai_connection_verified", "true")
            except Exception:
                pass
        else:
            try:
                Repository.set_setting("ai_connection_verified", "false")
            except Exception:
                pass
        return res

model_router = ModelRouter()
