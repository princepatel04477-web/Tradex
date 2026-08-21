"""Resend Transactional Email Provider for price & indicator alert notifications (SRS §7.2, FR-6.9)."""

from typing import Optional
import httpx

from app.core.config import settings
from app.core.logging import logger
from app.providers.base import EmailProvider


class ResendProvider(EmailProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.RESEND_API_KEY
        self.base_url = "https://api.resend.com/emails"

    async def send_email(self, to: str, subject: str, body_html: str) -> bool:
        if not self.api_key:
            logger.warning("RESEND_API_KEY is not configured; skipping email dispatch")
            return False

        payload = {
            "from": "Tradly Alerts <alerts@tradly.ai>",
            "to": [to],
            "subject": subject,
            "html": body_html,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.post(self.base_url, json=payload, headers=headers)
            if res.status_code not in (200, 201):
                logger.error(f"Resend Email error: {res.status_code} {res.text}")
                return False
            return True
