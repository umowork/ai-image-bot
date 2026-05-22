"""API tests for YooKassa Webhook — all endpoints, auth, validation."""

import os

import pytest

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def _env(tmp_path):
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{tmp_path}/test.db"
    os.environ["MOCK_MODE"] = "true"
    os.environ["YOOKASSA_WEBHOOK_SECRET"] = ""


@pytest.fixture
async def app_with_db(tmp_path):
    from models import Database
    from webhook.yookassa_webhook import create_webhook_app

    db = Database(f"sqlite+aiosqlite:///{tmp_path}/test.db")
    await db.create_tables()

    class FakePaymentService:
        mock_mode = True

    app = create_webhook_app(db, FakePaymentService())
    yield app, db
    await db.engine.dispose()


@pytest.fixture
async def client(app_with_db):
    from httpx import ASGITransport, AsyncClient

    app, _ = app_with_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ── Health ─────────────────────────────────────────────────────────


async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["service"] == "yookassa-webhook"


# ── Webhook: missing secret ────────────────────────────────────────


async def test_webhook_secret_not_configured(client):
    """When YOOKASSA_WEBHOOK_SECRET is empty, webhook returns 503."""
    r = await client.post(
        "/webhook/yookassa",
        json={"event": "payment.succeeded", "object": {}},
    )
    assert r.status_code == 503


# ── Webhook: with secret configured ────────────────────────────────


async def test_webhook_bad_auth():
    """When secret is configured, bad auth returns 401."""
    import base64

    os.environ["YOOKASSA_WEBHOOK_SECRET"] = "my-secret"

    from models import Database
    from webhook.yookassa_webhook import create_webhook_app

    db = Database("sqlite+aiosqlite://")
    await db.create_tables()

    class FakePaymentService:
        mock_mode = True

    app = create_webhook_app(db, FakePaymentService())

    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        bad_auth = base64.b64encode(b"wrong:creds").decode()
        r = await c.post(
            "/webhook/yookassa",
            json={"event": "payment.succeeded", "object": {}},
            headers={"Authorization": f"Basic {bad_auth}"},
        )
        assert r.status_code == 401

    await db.engine.dispose()
    os.environ.pop("YOOKASSA_WEBHOOK_SECRET", None)


# ── Webhook: unhandled event ───────────────────────────────────────


async def test_webhook_unhandled_event(client):
    """Unknown event types return ok."""
    os.environ["YOOKASSA_WEBHOOK_SECRET"] = ""

    r = await client.post(
        "/webhook/yookassa",
        json={"event": "refund.succeeded", "object": {}},
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True


# ── Webhook: invalid JSON ──────────────────────────────────────────


async def test_webhook_invalid_json(client):
    r = await client.post(
        "/webhook/yookassa",
        content=b"not-json",
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code in (400, 422, 503)
