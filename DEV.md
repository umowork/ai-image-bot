# 02 — AI Image+Video Bot

> 🎨 Telegram-бот для генерации **изображений** с ЮKassa-оплатой и реферальной программой.

## Что умеет

- 🎨 Генерация изображений (1 кредит) — DALL-E 3 / Flux Schnell
- 💰 Пополнение баланса через ЮKassa
- 🔗 Реферальная программа (+5 кредитов за друга, +10 новому пользователю)
- 📜 История генераций
- 📊 Админ-команды: `/stats`, `/give_credits`
- 🔔 Webhook для уведомлений об оплате

## Quick Start

```bash
# 1. Clone and prepare
cp .env.example .env
# edit .env — add BOT_TOKEN, YOOKASSA_* keys

# 2. Install deps
pip install -r requirements.txt
pip install -r requirements-test.txt

# 3. Run tests
pytest tests/ -v --tb=short

# 4. Run bot (mock mode — no real API keys needed)
MOCK_MODE=1 python -m bot.bot
```

## Structure

```
bot/
  bot.py              — entry point, DI wiring
  handlers/
    start.py          — /start, /help
    generate.py       — image generation flow (FSM)
    balance.py        — balance, payments, history, admin
    referral.py       — referral link
config.py             — Config dataclass from env
models/__init__.py    — User, Generation, Payment, Database
services/
  image_service.py    — DALL-E 3 / Flux Schnell
  payment_service.py  — YooKassa API
  referral_service.py — referral logic
webhook/
  yookassa_webhook.py — FastAPI webhook for payment notifications
run_webhook.py        — webhook entry point
tests/
  test_image_service.py
  test_payment_service.py
  test_referral.py
  test_webhook.py
  test_smoke.py
```

## Docker

```bash
docker-compose up --build
```

## Tech

- Python 3.12 + **aiogram 3.13**
- SQLAlchemy 2.0 async (SQLite)
- httpx (async HTTP for APIs)
- FastAPI (webhook for YooKassa)
- respx (HTTP mock for tests)

## Environment Variables

| Variable | Description |
|----------|-------------|
| BOT_TOKEN | Telegram bot token |
| DATABASE_URL | SQLite path |
| IMAGE_PROVIDER | dalle / flux |
| OPENAI_API_KEY | For DALL-E 3 |
| REPLICATE_API_TOKEN | For Flux Schnell |
| YOOKASSA_SHOP_ID | YooKassa shop id |
| YOOKASSA_SECRET_KEY | YooKassa secret key |
| MOCK_MODE | 1 to run without real keys |

---

*Built with AI assistance.*
