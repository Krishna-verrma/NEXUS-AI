import json
import logging
import time
import httpx
from typing import Any, Optional
from app.ai.providers.base import BaseAIProvider

logger = logging.getLogger("nexus.ai.openai")

class OpenAIProvider(BaseAIProvider):
    DEFAULT_MODEL = "gpt-4o-mini"
    DEFAULT_ENDPOINT = "https://api.openai.com/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        clean_model = (model or "").strip()
        # Enforce provider compatibility: Never send a Gemini model to OpenAI
        if not clean_model or clean_model.startswith("gemini-") or "google" in clean_model:
            clean_model = self.DEFAULT_MODEL

        clean_url = (base_url or "").strip().rstrip("/")
        if not clean_url or "googleapis.com" in clean_url:
            clean_url = self.DEFAULT_ENDPOINT

        super().__init__(
            api_key=api_key,
            base_url=clean_url,
            model=clean_model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        self.validate_configuration()

    def validate_configuration(self) -> None:
        if self.model.startswith("gemini-") or "gemini" in self.model:
            raise ValueError(f"Incompatible model '{self.model}' for OpenAI provider. Use '{self.DEFAULT_MODEL}'.")

    async def complete(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format_json: bool = False,
        tools: Optional[list[dict[str, Any]]] = None,
    ) -> str:
        if not self.api_key or not self.api_key.strip():
            raise RuntimeError("OpenAI API key is missing. Please set your OpenAI API key in Settings.")

        self.validate_configuration()

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "Content-Type": "application/json"
        }

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
        }
        if response_format_json:
            payload["response_format"] = {"type": "json_object"}
        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=40.0) as client:
            try:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code != 200:
                    err_msg = resp.text
                    try:
                        err_json = resp.json()
                        err_msg = err_json.get("error", {}).get("message", resp.text)
                    except Exception:
                        pass
                    if resp.status_code == 401:
                        raise RuntimeError(f"OpenAI Error (401 Unauthorized): Invalid API key. Please check your OpenAI API key in Settings.")
                    elif resp.status_code == 429:
                        raise RuntimeError(f"OpenAI Error (429 Rate Limit): Rate limit reached or quota exceeded.")
                    raise RuntimeError(f"OpenAI Error ({resp.status_code}): {err_msg}")

                data = resp.json()
                choices = data.get("choices", [])
                if not choices:
                    raise RuntimeError("OpenAI returned empty choices in response.")
                return choices[0]["message"]["content"] or ""
            except httpx.RequestError as e:
                raise RuntimeError(f"Failed to connect to OpenAI endpoint: {str(e)}")

    async def test_connection(self) -> dict[str, Any]:
        if not self.api_key or not self.api_key.strip():
            return {
                "success": False,
                "provider": "openai",
                "model": self.model,
                "error": "No API key entered. Please paste your OpenAI API key."
            }

        start_time = time.time()
        try:
            test_prompt = [{"role": "user", "content": "Respond with 'READY'"}]
            resp_text = await self.complete(test_prompt, temperature=0.1, max_tokens=10)
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "success": True,
                "provider": "openai",
                "model": self.model,
                "latency": latency_ms,
                "preview": resp_text.strip(),
                "message": f"Successfully connected to OpenAI ({self.model}) in {latency_ms}ms"
            }
        except Exception as e:
            return {
                "success": False,
                "provider": "openai",
                "model": self.model,
                "error": str(e)
            }
