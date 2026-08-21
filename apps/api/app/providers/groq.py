"""Groq LLM Provider for low-latency inference (SRS §6.1.3, NFR-P4)."""

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

        models_to_try = [self.model, "openai/gpt-oss-120b", "groq/compound", "qwen/qwen3.6-27b", "openai/gpt-oss-20b"]
        # Remove duplicates while preserving order
        seen = set()
        models = [m for m in models_to_try if not (m in seen or seen.add(m))]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            last_err = None
            for candidate_model in models:
                payload = {
                    "model": candidate_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                try:
                    res = await client.post(self.base_url, json=payload, headers=headers)
                    if res.status_code == 200:
                        data = res.json()
                        return data["choices"][0]["message"]["content"]
                    else:
                        last_err = f"{res.status_code}: {res.text}"
                        logger.warning(f"Groq candidate model {candidate_model} failed ({last_err}), trying next model...")
                except Exception as e:
                    last_err = str(e)
                    logger.warning(f"Groq request error on {candidate_model}: {e}")

            raise RuntimeError(f"All Groq models failed. Last error: {last_err}")
