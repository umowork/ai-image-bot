"""
Config for 02-ai-image-bot.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    bot_token: str
    database_url: str
    admin_ids: list[int]

    # LLM (for referral messages etc.)
    llm_provider: str = "gigachat"
    gigachat_api_key: str = ""
    gigachat_credentials: str = ""
    openai_api_key: str = ""

    # Image generation
    image_provider: str = "dalle"
    replicate_api_token: str = ""

    # YooKassa
    yookassa_shop_id: str = ""
    yookassa_secret_key: str = ""

    # Webhook
    webhook_host: str = "0.0.0.0"
    webhook_port: int = 8000
    webhook_base_url: str = "https://example.com"

    # Mode
    mock_mode: bool = False

    @classmethod
    def from_env(cls) -> Config:
        raw = os.getenv("ADMIN_IDS", "")
        admin_ids = [int(x.strip()) for x in raw.split(",") if x.strip()]
        return cls(
            bot_token=os.getenv("BOT_TOKEN", ""),
            database_url=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///bot.db"),
            admin_ids=admin_ids,
            llm_provider=os.getenv("LLM_PROVIDER", "gigachat"),
            gigachat_api_key=os.getenv("GIGACHAT_API_KEY", ""),
            gigachat_credentials=os.getenv("GIGACHAT_CREDENTIALS", ""),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            image_provider=os.getenv("IMAGE_PROVIDER", "dalle"),
            replicate_api_token=os.getenv("REPLICATE_API_TOKEN", ""),
            yookassa_shop_id=os.getenv("YOOKASSA_SHOP_ID", ""),
            yookassa_secret_key=os.getenv("YOOKASSA_SECRET_KEY", ""),
            webhook_host=os.getenv("WEBHOOK_HOST", "0.0.0.0"),
            webhook_port=int(os.getenv("WEBHOOK_PORT", "8000")),
            webhook_base_url=os.getenv("WEBHOOK_BASE_URL", "https://example.com"),
            mock_mode=os.getenv("MOCK_MODE", "0") == "1",
        )
