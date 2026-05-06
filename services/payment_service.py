"""
Real YooKassa payment service via httpx.
"""
from __future__ import annotations

import asyncio
import base64
import logging

import httpx

logger = logging.getLogger(__name__)

# YooKassa API endpoints
YOOKASSA_API = "https://api.yookassa.ru/v3"


class PaymentError(Exception):
    pass


class PaymentService:
    def __init__(
        self,
        shop_id: str,
        secret_key: str,
        return_url: str = "https://t.me/",
        mock_mode: bool = False,
    ):
        self.shop_id = shop_id
        self.secret_key = secret_key
        self.return_url = return_url
        self.mock_mode = mock_mode

    def _auth_header(self) -> str:
        raw = f"{self.shop_id}:{self.secret_key}"
        return f"Basic {base64.b64encode(raw.encode()).decode()}"

    async def create_payment(
        self, amount: float, description: str,
        metadata: dict | None = None,
    ) -> dict:
        if self.mock_mode:
            await asyncio.sleep(0.3)
            pid = f"mock-payment-{hash(description) % 1000000}"
            return {
                "id": pid,
                "status": "pending",
                "confirmation": {
                    "confirmation_url": f"https://yookassa.ru/mock-payment?pid={pid}",
                    "type": "redirect",
                },
                "amount": {"value": f"{amount:.2f}", "currency": "RUB"},
                "metadata": metadata or {},
            }

        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "amount": {"value": f"{amount:.2f}", "currency": "RUB"},
                "confirmation": {
                    "type": "redirect",
                    "return_url": self.return_url,
                },
                "capture": True,
                "description": description[:128],
            }
            if metadata:
                payload["metadata"] = metadata

            resp = await client.post(
                f"{YOOKASSA_API}/payments",
                headers={
                    "Authorization": self._auth_header(),
                    "Content-Type": "application/json",
                    "Idempotence-Key": f"payment-{hash(description)}-{amount}",
                },
                json=payload,
            )
            if resp.status_code >= 400:
                logger.error(
                    "yookassa create payment failed: %s %s",
                    resp.status_code,
                    resp.text,
                )
                raise PaymentError(
                    f"YooKassa error {resp.status_code}: {resp.text}"
                )
            data = resp.json()
            logger.info(
                "payment created: %s amount=%s",
                data["id"],
                amount,
            )
            return data

    async def get_payment(self, payment_id: str) -> dict:
        if self.mock_mode:
            return {
                "id": payment_id,
                "status": "succeeded",
            }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{YOOKASSA_API}/payments/{payment_id}",
                headers={"Authorization": self._auth_header()},
            )
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    def verify_webhook_signature(
        body: bytes, signature: str, secret_key: str
    ) -> bool:
        """Verify YooKassa webhook notification signature."""
        import hashlib
        import hmac
        expected = hmac.new(
            secret_key.encode(), body, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(f"SHA-256;{expected}", signature)
