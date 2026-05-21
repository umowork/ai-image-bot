"""
YooKassa webhook handler (FastAPI).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os

from fastapi import FastAPI, HTTPException, Request, Security, Depends
from fastapi.security import APIKeyHeader
import os

_api_key_header = APIKeyHeader(name='X-API-Key', auto_error=False)

def require_api_key(api_key: str | None = Security(_api_key_header)):
    expected = os.getenv('API_KEY')
    if expected and api_key != expected:
        raise HTTPException(status_code=401, detail='Invalid API key')
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)


def _rate_limit_exceeded_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please try again later."},
    )

from models import Database
from services.payment_service import PaymentService

logger = logging.getLogger(__name__)


def create_webhook_app(
    db: Database,
    payment_service: PaymentService,
) -> FastAPI:
    app = FastAPI(title="YooKassa Webhook")
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    @app.post("/webhook/yookassa")
    @limiter.limit("30/minute")
    async def yookassa_webhook(request: Request):
        body = await request.body()

        # Verify YooKassa webhook signature (HTTP Basic Auth)
        # YooKassa sends: Authorization: Basic <base64(shop_id:secret_key)>
        # We verify against our configured secret
        webhook_secret = os.getenv("YOOKASSA_WEBHOOK_SECRET", "")
        if webhook_secret:
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Basic "):
                logger.warning("missing or invalid Authorization header")
                raise HTTPException(status_code=401, detail="Unauthorized")

            try:
                encoded = auth_header.split(" ", 1)[1]
                decoded = base64.b64decode(encoded).decode("utf-8")
                # Format: shop_id:secret_key
                _, provided_secret = decoded.split(":", 1)
                if not hmac.compare_digest(provided_secret, webhook_secret):
                    logger.warning("webhook signature mismatch")
                    raise HTTPException(status_code=401, detail="Unauthorized")
            except (ValueError, IndexError) as e:
                logger.warning("failed to parse Authorization header: %s", e)
                raise HTTPException(status_code=401, detail="Unauthorized") from e
        else:
            logger.warning("YOOKASSA_WEBHOOK_SECRET not set — skipping signature verification")

        try:
            data = json.loads(body)
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid JSON") from e

        event = data.get("event", "")
        if event not in ("payment.waiting_for_capture", "payment.succeeded"):
            logger.info("unhandled event: %s", event)
            return {"ok": True}

        payment_obj = data.get("object", {})
        yookassa_id = payment_obj.get("id")
        status = payment_obj.get("status", "")

        if not yookassa_id:
            raise HTTPException(status_code=400, detail="Missing payment id")

        # Find our payment record
        pmt = await db.get_payment_by_yookassa_id(yookassa_id)
        if not pmt:
            logger.warning("unknown payment notification: %s", yookassa_id)
            return {"ok": True}  # might be a test notification

        if status == "succeeded":
            await db.update_payment_status(pmt.id, "succeeded")
            await db.add_balance(pmt.user_id, pmt.amount)
            logger.info(
                "payment succeeded: user_id=%s amount=%s payment_id=%s",
                pmt.user_id, pmt.amount, pmt.id,
            )
        elif status == "waiting_for_capture":
            # Auto-capture
            try:
                # For auto-capture, we set capture=true on creation
                await db.update_payment_status(pmt.id, "succeeded")
                await db.add_balance(pmt.user_id, pmt.amount)
                logger.info(
                    "payment auto-captured: user_id=%s amount=%s",
                    pmt.user_id, pmt.amount,
                )
            except Exception as e:
                logger.error("capture failed: %s", e)

        return {"ok": True}

    @app.get("/health")
    async def health():
        checks = {"status": "ok", "service": "yookassa-webhook"}
        try:
            async with db.session_factory() as session:
                from sqlalchemy import text
                await session.execute(text("SELECT 1"))
            checks["database"] = "ok"
        except Exception as e:
            checks["database"] = f"error: {e}"
            checks["status"] = "degraded"
        return checks

    return app
