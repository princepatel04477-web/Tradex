"""OpenAI Text Embedding Provider for RAG vector indexing (SRS §6.1.1)."""

from typing import List, Optional
import httpx

from app.core.config import settings
from app.core.logging import logger
from app.providers.base import EmbeddingProvider


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_EMBEDDING_MODEL
        self.base_url = "https://api.openai.com/v1/embeddings"

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not configured")
        if not texts:
            return []

        payload = {
            "model": self.model,
            "input": texts,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(self.base_url, json=payload, headers=headers)
            if res.status_code != 200:
                logger.error(f"OpenAI Embedding error: {res.status_code} {res.text}")
                raise RuntimeError(f"OpenAI Embedding error {res.status_code}")

            data = res.json()
            return [item["embedding"] for item in data["data"]]
