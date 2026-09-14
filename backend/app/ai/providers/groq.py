import time
import httpx
import logging
from typing import Any, Optional
from app.ai.providers.base import BaseAIProvider

logger = logging.getLogger("nexus.ai.providers.groq")

class GroqProvider(BaseAIProvider):
    """
    Dedicated AI Provider for Groq.
    Base URL: https://api.groq.com/openai/v1
    Default model: openai/gpt-oss-120b
    Keeps API key strictly on the backend.
    """
    DEFAULT_ENDPOINT = "https://api.groq.com/openai/v1"
    DEFAULT_MODEL = "openai/gpt-oss-120b"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        super().__init__(
            api_key=api_key,
            base_url=base_url or self.DEFAULT_ENDPOINT,
            model=model or self.DEFAULT_MODEL,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def validate_configuration(self) -> None:
        if not self.api_key or not self.api_key.strip():
            raise ValueError("Groq API key is required.")
        if not self.model:
            self.model = self.DEFAULT_MODEL
        if not self.base_url:
            self.base_url = self.DEFAULT_ENDPOINT

    async def complete(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format_json: bool = False,
        tools: Optional[list[dict[str, Any]]] = None,
    ) -> str:
        self.validate_configuration()

        temp = temperature if temperature is not None else self.temperature
        max_t = max_tokens if max_tokens is not None else self.max_tokens

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "Content-Type": "application/json",
            "User-Agent": "Nexus-AI-CommandCenter/1.0",
        }

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": max(0.0, min(temp, 2.0)),
            "max_tokens": min(max_t, 8192),
        }

        if response_format_json:
            payload["response_format"] = {"type": "json_object"}

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        async with httpx.AsyncClient(timeout=45.0) as client:
            try:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code != 200:
                    err_msg = f"Groq API Error {resp.status_code}: {resp.text}"
                    logger.error(err_msg)
                    raise RuntimeError(err_msg)

                data = resp.json()
                choices = data.get("choices", [])
                if not choices:
                    raise RuntimeError("Groq API returned an empty choices list.")

                msg = choices[0].get("message", {})
                content = msg.get("content")
                if content is not None:
                    return str(content).strip()
                
                # If tool calls were returned
                if "tool_calls" in msg:
                    import json
                    return json.dumps({"tool_calls": msg["tool_calls"]})

                return ""
            except httpx.TimeoutException:
                raise TimeoutError("Groq API request timed out after 45 seconds.")
            except Exception as e:
                logger.error(f"Groq API completion exception: {e}")
                raise

    async def test_connection(self) -> dict[str, Any]:
        self.validate_configuration()
        start = time.perf_counter()
        try:
            res = await self.complete(
                messages=[{"role": "user", "content": "Respond with 'NEXUS_OK'."}],
                max_tokens=10,
                temperature=0.1,
            )
            latency = int((time.perf_counter() - start) * 1000)
            return {
                "success": True,
                "provider": "groq",
                "model": self.model,
                "latency_ms": latency,
                "message": f"Groq AI brain active ({self.model}) - Latency: {latency}ms",
            }
        except Exception as e:
            latency = int((time.perf_counter() - start) * 1000)
            return {
                "success": False,
                "provider": "groq",
                "model": self.model,
                "latency_ms": latency,
                "error": str(e),
                "message": f"Groq connection test failed: {str(e)}",
            }
