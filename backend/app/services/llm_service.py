import asyncio
from typing import AsyncGenerator, Dict, Any, Optional
from app.core.config import settings

class LLMService:
    def __init__(self):
        self.demo_mode = settings.DEMO_MODE

    async def generate_response(
        self,
        prompt: str,
        system_instruction: str = "",
        model_name: Optional[str] = None
    ) -> str:
        """Generate full text response via provider or demo engine."""
        # Real provider logic if API keys exist
        if settings.GEMINI_API_KEY:
            try:
                import httpx
                # Call Gemini REST endpoint
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
                payload = {
                    "contents": [{"parts": [{"text": f"{system_instruction}\n\n{prompt}"}]}]
                }
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        return data["candidates"][0]["content"]["parts"][0]["text"]
            except Exception as e:
                print(f"Gemini API invocation fallback to demo: {e}")

        # Default Demo Mode intelligence
        return f"Nexus AI autonomous response: Processed query '{prompt}'."

    async def stream_response(
        self,
        full_text: str,
        chunk_size: int = 12
    ) -> AsyncGenerator[str, None]:
        """Simulate realistic token streaming for rich UI response feeling."""
        words = full_text.split(" ")
        for i in range(0, len(words), 3):
            chunk = " ".join(words[i:i+3]) + " "
            yield chunk
            await asyncio.sleep(0.02)

llm_service = LLMService()
