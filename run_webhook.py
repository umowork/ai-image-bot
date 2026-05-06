"""
Webhook entry point for YooKassa payment notifications.
"""
import uvicorn

from config import Config
from models import Database
from services.payment_service import PaymentService
from webhook.yookassa_webhook import create_webhook_app


def main():
    config = Config.from_env()

    # Use in-memory or same DB
    import asyncio
    db = Database(config.database_url)

    payment_service = PaymentService(
        shop_id=config.yookassa_shop_id,
        secret_key=config.yookassa_secret_key,
        mock_mode=config.mock_mode,
    )

    # Create tables if not exist
    loop = asyncio.new_event_loop()
    loop.run_until_complete(db.create_tables())

    app = create_webhook_app(db, payment_service)
    uvicorn.run(
        app,
        host=config.webhook_host,
        port=config.webhook_port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
