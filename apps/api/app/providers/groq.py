"""Groq LLM Provider for low-latency LLaMA 3 inference (SRS §6.1.3, NFR-P4)."""

from typing import Optional
import httpx

from app.core.config import settings
from app.core.logging import logger
from app.providers.base import LLMProvider


class GroqProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_MODEL
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 800,
    ) -> str:
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not configured")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(self.base_url, json=payload, headers=headers)
            if res.status_code != 200:
                logger.error(f"Groq API error: {res.status_code} {res.text}")
                raise RuntimeError(f"Groq API error {res.status_code}")

            data = res.json()
            return data["choices"][0]["message"]["content"]
