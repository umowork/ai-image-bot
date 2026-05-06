"""
Tests for payment service (YooKassa).
"""
from __future__ import annotations

import pytest
import respx
from httpx import Response

from services.payment_service import PaymentService


@pytest.mark.asyncio
async def test_create_payment_mock():
    svc = PaymentService(
        shop_id="test_shop",
        secret_key="test_secret",
        mock_mode=True,
    )
    result = await svc.create_payment(100.0, "Test payment")
    assert result["status"] == "pending"
    assert "mock-payment" in result["id"]
    assert result["confirmation"]["confirmation_url"]


@pytest.mark.asyncio
async def test_create_payment_real():
    svc = PaymentService(
        shop_id="test_shop",
        secret_key="test_secret",
        mock_mode=False,
    )
    with respx.mock:
        route = respx.post("https://api.yookassa.ru/v3/payments").mock(
            return_value=Response(
                200,
                json={
                    "id": "pmt_123",
                    "status": "pending",
                    "confirmation": {
                        "type": "redirect",
                        "confirmation_url": "https://yookassa.ru/pay/pmt_123",
                    },
                    "amount": {"value": "100.00", "currency": "RUB"},
                },
            )
        )
        result = await svc.create_payment(100.0, "Test")
        assert route.called
        assert result["id"] == "pmt_123"
        assert result["status"] == "pending"


@pytest.mark.asyncio
async def test_get_payment():
    svc = PaymentService(
        shop_id="test_shop",
        secret_key="test_secret",
        mock_mode=False,
    )
    with respx.mock:
        route = respx.get("https://api.yookassa.ru/v3/payments/pmt_123").mock(
            return_value=Response(
                200,
                json={"id": "pmt_123", "status": "succeeded"},
            )
        )
        result = await svc.get_payment("pmt_123")
        assert route.called
        assert result["status"] == "succeeded"


@pytest.mark.asyncio
async def test_create_payment_api_error():
    svc = PaymentService(
        shop_id="test_shop",
        secret_key="test_secret",
        mock_mode=False,
    )
    with respx.mock:
        respx.post("https://api.yookassa.ru/v3/payments").mock(
            return_value=Response(400, text='{"code":"invalid_request"}')
        )
        with pytest.raises(Exception) as exc:
            await svc.create_payment(100.0, "Test")
        assert "400" in str(exc.value) or "Error" in str(exc.value)
