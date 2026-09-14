import json
import logging
import time
import httpx
from typing import Any, Optional
from app.ai.providers.base import BaseAIProvider

logger = logging.getLogger("nexus.ai.gemini")

class GeminiProvider(BaseAIProvider):
    DEFAULT_MODEL = "gemini-2.5-flash"
    DEFAULT_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta"
    FALLBACK_MODELS = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.0-flash"]

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        clean_model = (model or "").strip()
        # Enforce provider compatibility: Never send an OpenAI model to Gemini
        if not clean_model or clean_model.startswith("gpt-") or "claude" in clean_model or "llama" in clean_model:
            clean_model = self.DEFAULT_MODEL
            
        clean_url = (base_url or "").strip().rstrip("/")
        if not clean_url or "openai.com" in clean_url:
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
        if self.model.startswith("gpt-") or "openai" in self.model:
            raise ValueError(f"Incompatible model '{self.model}' for Google Gemini provider. Use '{self.DEFAULT_MODEL}'.")

    async def complete(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format_json: bool = False,
        tools: Optional[list[dict[str, Any]]] = None,
    ) -> str:
        if not self.api_key or not self.api_key.strip():
            raise RuntimeError("Google Gemini API key is missing. Please set your Gemini API key in Settings.")

        self.validate_configuration()

        models_to_try = [self.model]
        for fb in self.FALLBACK_MODELS:
            if fb not in models_to_try:
                models_to_try.append(fb)

        last_error = None
        for current_model in models_to_try:
            try:
                return await self._call_gemini_api(
                    model_name=current_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format_json=response_format_json,
                    tools=tools
                )
            except Exception as e:
                err_str = str(e)
                last_error = e
                # Only retry on 404 Not Found (e.g. if 2.5-flash is not yet enabled for a given key, fallback to 1.5-flash)
                if "404" in err_str or "not found" in err_str.lower():
                    logger.warning(f"Model {current_model} unavailable, trying fallback...")
                    continue
                raise e

        raise last_error or RuntimeError("Google Gemini request failed across all model attempts.")

    async def _call_gemini_api(
        self,
        model_name: str,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format_json: bool = False,
        tools: Optional[list[dict[str, Any]]] = None,
    ) -> str:
        url = f"{self.base_url}/models/{model_name}:generateContent?key={self.api_key.strip()}"

        contents = []
        system_instruction = None

        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "system":
                system_instruction = {"parts": [{"text": content}]}
            elif role in ("assistant", "model"):
                contents.append({"role": "model", "parts": [{"text": content}]})
            else:
                contents.append({"role": "user", "parts": [{"text": content}]})

        if not contents:
            contents.append({"role": "user", "parts": [{"text": "Hello"}]})

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature if temperature is not None else self.temperature,
                "maxOutputTokens": max_tokens if max_tokens is not None else self.max_tokens,
            }
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction
        if response_format_json:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        async with httpx.AsyncClient(timeout=40.0) as client:
            resp = await client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            if resp.status_code != 200:
                err_text = resp.text
                try:
                    err_json = resp.json()
                    err_text = err_json.get("error", {}).get("message", resp.text)
                except Exception:
                    pass
                if resp.status_code == 401:
                    raise RuntimeError(f"Google Gemini Error (401 Unauthorized): Invalid API key. Please check your Gemini API key in Settings.")
                elif resp.status_code == 403:
                    raise RuntimeError(f"Google Gemini Error (403 Forbidden): Permission denied or quota exceeded. Detail: {err_text}")
                elif resp.status_code == 429:
                    raise RuntimeError(f"Google Gemini Error (429 Rate Limit): Rate limit reached. Please wait a moment before trying again.")
                raise RuntimeError(f"Google Gemini Error ({resp.status_code}): {err_text}")

            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise RuntimeError("Gemini returned empty candidate response.")

            parts = candidates[0].get("content", {}).get("parts", [])
            if parts and "text" in parts[0]:
                return parts[0]["text"]
            return ""

    async def test_connection(self) -> dict[str, Any]:
        if not self.api_key or not self.api_key.strip():
            return {
                "success": False,
                "provider": "gemini",
                "model": self.model,
                "error": "No API key entered. Please paste your Google Gemini API key."
            }

        start_time = time.time()
        try:
            test_prompt = [{"role": "user", "content": "Respond with the word 'READY' and nothing else."}]
            resp_text = await self.complete(test_prompt, temperature=0.1, max_tokens=10)
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "success": True,
                "provider": "gemini",
                "model": self.model,
                "latency": latency_ms,
                "preview": resp_text.strip(),
                "message": f"Successfully connected to Google Gemini ({self.model}) in {latency_ms}ms"
            }
        except Exception as e:
            return {
                "success": False,
                "provider": "gemini",
                "model": self.model,
                "error": str(e)
            }
