"""
Bot initialization and main entry point.
"""
from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.middleware.rate_limit import RateLimitMiddleware
from config import Config
from models import Database
from services.generation_queue import GenerationQueue
from services.image_service import ImageService
from services.payment_service import PaymentService
from services.referral_service import ReferralService

from .handlers.admin import register_admin
from .handlers.balance import register_balance
from .handlers.generate import register_generate
from .handlers.referral import register_referral
from .handlers.start import register_start

logger = logging.getLogger(__name__)


def create_bot_app(
    config: Config,
    db: Database,
    image_service: ImageService,
    payment_service: PaymentService,
    referral_service: ReferralService,
) -> tuple[Bot, Dispatcher, GenerationQueue]:
    """Create and configure bot + dispatcher with all handlers."""
    storage = MemoryStorage()
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=storage)

    # Rate limiting middleware (5 msgs per 10 sec per user)
    dp.message.middleware(RateLimitMiddleware(max_messages=5, window_seconds=10.0))

    # Background generation queue (3 parallel workers)
    gen_queue = GenerationQueue(
        bot=bot, db=db, image_service=image_service, max_workers=3,
    )

    # Register handlers from submodules
    register_start(dp, db, referral_service)
    register_generate(dp, db, gen_queue)
    register_balance(dp, db, payment_service, config)
    register_referral(dp, db, bot)

    # Admin commands (only activated for configured admin IDs)
    if config.admin_ids:
        register_admin(dp, db, config.admin_ids)

    return bot, dp, gen_queue


async def main() -> None:
    config = Config.from_env()
    db = Database(config.database_url)
    await db.create_tables()

    image_service = ImageService(
        openai_api_key=config.openai_api_key,
        replicate_api_token=config.replicate_api_token,
        image_provider=config.image_provider,
        mock_mode=config.mock_mode,
    )
    payment_service = PaymentService(
        shop_id=config.yookassa_shop_id,
        secret_key=config.yookassa_secret_key,
        return_url=config.webhook_base_url,
        mock_mode=config.mock_mode,
    )
    referral_service = ReferralService(db)

    bot, dp, gen_queue = create_bot_app(
        config, db, image_service, payment_service, referral_service,
    )

    # Start background workers
    await gen_queue.start()

    # Start webhook server in background if not mock
    if not config.mock_mode:
        import uvicorn

        from webhook.yookassa_webhook import create_webhook_app
        webhook_app = create_webhook_app(db, payment_service)
        config_instance = uvicorn.Config(
            webhook_app,
            host=config.webhook_host,
            port=config.webhook_port,
            log_level="info",
        )
        server = uvicorn.Server(config_instance)
        asyncio.create_task(server.serve())

    logger.info("bot starting polling")
    try:
        await dp.start_polling(bot)
    finally:
        await gen_queue.stop()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
        stream=sys.stdout,
    )
    asyncio.run(main())
