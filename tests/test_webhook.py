"""
Tests for YooKassa webhook.
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from models import Database
from webhook.yookassa_webhook import create_webhook_app


@pytest.fixture
def db():
    d = Database("sqlite+aiosqlite:///:memory:")
    import asyncio
    asyncio.run(d.create_tables())
    return d


@pytest.fixture
def app(db):
    from services.payment_service import PaymentService
    ps = PaymentService(shop_id="test", secret_key="test", mock_mode=True)
    return create_webhook_app(db, ps)


@pytest.fixture
def client(app):
    return TestClient(app)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_webhook_unknown_payment(client):
    """Webhook with unknown payment id should return ok."""
    payload = {
        "event": "payment.succeeded",
        "object": {
            "id": "unknown_pmt",
            "status": "succeeded",
            "amount": {"value": "100.00", "currency": "RUB"},
        },
    }
    resp = client.post(
        "/webhook/yookassa",
        content=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_webhook_invalid_json(client):
    resp = client.post(
        "/webhook/yookassa",
        content=b"not json",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 400


def test_webhook_unhandled_event(client):
    """Unhandled events should return ok without error."""
    payload = {
        "event": "payment.refunded",
        "object": {"id": "pmt_1", "status": "succeeded"},
    }
    resp = client.post(
        "/webhook/yookassa",
        content=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_webhook_updates_balance(db):
    """Webhook should update balance when payment succeeds."""
    from services.payment_service import PaymentService
    ps = PaymentService(shop_id="test", secret_key="test", mock_mode=True)
    app = create_webhook_app(db, ps)
    client = TestClient(app)

    # Create user and payment record
    user = await db.get_or_create_user(
        telegram_id=500, username="test", full_name="Test"
    )
    _pmt = await db.create_payment_record(
        user_id=user.id,
        amount=100.0,
        description="Test",
        yookassa_id="pmt_real_1",
    )

    payload = {
        "event": "payment.succeeded",
        "object": {
            "id": "pmt_real_1",
            "status": "succeeded",
            "amount": {"value": "100.00", "currency": "RUB"},
        },
    }
    resp = client.post(
        "/webhook/yookassa",
        content=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 200

    # Check balance updated
    updated_user = await db.get_user_by_telegram_id(500)
    assert updated_user is not None
    assert updated_user.balance >= 100.0
